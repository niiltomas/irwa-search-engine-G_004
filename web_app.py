import os
import time
import random
from json import JSONEncoder

import httpagentparser  # for getting the user agent as json
from flask import Flask, render_template, session
from flask import request

from myapp.analytics.analytics_data import AnalyticsData, ClickedDoc
from myapp.search.load_corpus import load_corpus
from myapp.search.objects import Document, StatsDocument
from myapp.search.search_engine import SearchEngine
from myapp.generation.rag import RAGGenerator
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env


# *** for using method to_json in objects ***
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)


_default.default = JSONEncoder().default
JSONEncoder.default = _default
# end lines ***for using method to_json in objects ***


# instantiate the Flask application
app = Flask(__name__)

# random 'secret_key' is used for persisting data in secure cookie
app.secret_key = os.getenv("SECRET_KEY")
# open browser dev tool to see the cookies
app.session_cookie_name = os.getenv("SESSION_COOKIE_NAME")
# instantiate our search engine
search_engine = SearchEngine()
# instantiate our in memory persistence
analytics_data = AnalyticsData()
# instantiate RAG generator
rag_generator = RAGGenerator()

# load documents corpus into memory.
full_path = os.path.realpath(__file__)
path, filename = os.path.split(full_path)
file_path = path + "/" + os.getenv("DATA_FILE_PATH")
corpus = load_corpus(file_path)
# Log first element of corpus to verify it loaded correctly:
print("\nCorpus is loaded... \n First element:\n", list(corpus.values())[0])


def get_session_id() -> str:
    if "session_id" not in session:
        session["session_id"] = str(random.randint(0, 10**9))
    return session["session_id"]


# Home URL "/"
@app.route("/")
def index():
    print("starting home url /...")

    # flask server creates a session by persisting a cookie in the user's browser.
    # the 'session' object keeps data between multiple requests. Example:
    session["some_var"] = "Some value that is kept in session"

    user_agent = request.headers.get("User-Agent")
    print("Raw user browser:", user_agent)

    user_ip = request.remote_addr
    agent = httpagentparser.detect(user_agent)

    print("Remote IP: {} - JSON user browser {}".format(user_ip, agent))
    print(session)

    # registrar request
    session_id = get_session_id()
    analytics_data.register_request(
        path=request.path,
        method=request.method,
        user_agent=user_agent,
        ip=user_ip,
        session_id=session_id,
    )

    return render_template("index.html", page_title="Welcome")


@app.route("/search", methods=["POST"])
def search_form_post():
    search_query = request.form["search-query"]

    session["last_search_query"] = search_query

    # guarda info de la query en AnalyticsData
    search_id = analytics_data.save_query_terms(search_query)

    # registrar request de búsqueda
    session_id = get_session_id()
    analytics_data.register_request(
        path=request.path,
        method=request.method,
        user_agent=request.headers.get("User-Agent"),
        ip=request.remote_addr,
        session_id=session_id,
    )

    # si venimos de un click, calcula dwell time
    if "last_click_timestamp" in session and "last_click_doc_id" in session:
        dwell = time.time() - session["last_click_timestamp"]
        analytics_data.register_dwell_time(
            doc_id=session["last_click_doc_id"],
            dwell_seconds=dwell,
            session_id=session_id,
        )
        # limpiamos para el siguiente ciclo
        session.pop("last_click_timestamp", None)
        session.pop("last_click_doc_id", None)

    results = search_engine.search(
        search_query, search_id, corpus, analytics_data=analytics_data
    )

    # guardar ranking (posición) de cada doc en sesión para analytics
    session["last_ranking"] = {doc.pid: idx for idx, doc in enumerate(results)}

    # generate RAG response based on user query and retrieved results
    rag_response = rag_generator.generate_response(search_query, results)
    print("RAG response:", rag_response)

    found_count = len(results)
    session["last_found_count"] = found_count

    print(session)

    return render_template(
        "results.html",
        results_list=results,
        page_title="Results",
        found_counter=found_count,
        rag_response=rag_response,
        search_id=search_id,
    )


@app.route("/doc_details", methods=["GET"])
def doc_details():
    """
    Show document details page
    """

    # getting request parameters:
    print("doc details session: ")
    print(session)

    res = session["some_var"]
    print("recovered var from session:", res)

    # get the query string parameters from request
    clicked_doc_id = request.args["pid"]
    print("click in id={}".format(clicked_doc_id))

    search_id = request.args.get("search_id")

    # store data in statistics table 1 (clicks acumulados por doc)
    if clicked_doc_id in analytics_data.fact_clicks.keys():
        analytics_data.fact_clicks[clicked_doc_id] += 1
    else:
        analytics_data.fact_clicks[clicked_doc_id] = 1

    print(
        "fact_clicks count for id={} is {}".format(
            clicked_doc_id, analytics_data.fact_clicks[clicked_doc_id]
        )
    )
    print(analytics_data.fact_clicks)

    #registrar request de detalle
    session_id = get_session_id()
    analytics_data.register_request(
        path=request.path,
        method=request.method,
        user_agent=request.headers.get("User-Agent"),
        ip=request.remote_addr,
        session_id=session_id,
    )

    # registrar evento de click (con rank si lo tenemos)
    rank = None
    if "last_ranking" in session:
        rank = session["last_ranking"].get(clicked_doc_id)

    analytics_data.register_click_event(
        search_id=search_id,
        doc_id=clicked_doc_id,
        rank=rank,
        session_id=session_id,
    )

    # guardar timestamp para calcular dwell time al volver a /search
    session["last_click_timestamp"] = time.time()
    session["last_click_doc_id"] = clicked_doc_id

    # fetch document and render details
    doc = corpus.get(clicked_doc_id)
    return render_template(
        "doc_details.html", doc=doc, page_title="Document details", search_id=search_id
    )


@app.route("/stats", methods=["GET"])
def stats():
    """
    Show simple statistics example.
    """

    docs = []
    for doc_id in analytics_data.fact_clicks:
        row: Document = corpus[doc_id]
        count = analytics_data.fact_clicks[doc_id]
        doc = StatsDocument(
            pid=row.pid,
            title=row.title,
            description=row.description,
            url=row.url,
            count=count,
        )
        docs.append(doc)

    # simulate sort by ranking
    docs.sort(key=lambda doc: doc.count, reverse=True)
    return render_template("stats.html", clicks_data=docs)


@app.route('/dashboard')
def dashboard():
    # Top visited docs
    visited_docs = []
    for doc_id, count in analytics_data.fact_clicks.items():
        d: Document = corpus[doc_id]
        visited_docs.append({"doc_id": doc_id, "count": count})

    visited_docs = sorted(visited_docs, key=lambda x: x["count"], reverse=True)

    return render_template(
        'dashboard.html',
        clicks_data=visited_docs,
        queries_data=analytics_data.fact_queries,
        requests_data=analytics_data.fact_requests,
        click_events_data=analytics_data.fact_click_events,
        page_title="Dashboard"
    )



# New route added for generating an examples of basic Altair plot (used for dashboard)
@app.route("/plot_number_of_views", methods=["GET"])
def plot_number_of_views():
    return analytics_data.plot_number_of_views()


if __name__ == "__main__":
    app.run(port=8088, host="0.0.0.0", threaded=False, debug=os.getenv("DEBUG"))
