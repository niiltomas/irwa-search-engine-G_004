import json
import random
import time

import altair as alt
import pandas as pd


class AnalyticsData:
    """
    In-memory persistence object.
    """

    # clicks totales por doc_id
    fact_clicks = dict([])

    # lista de peticiones HTTP
    fact_requests = []

    # lista de queries
    fact_queries = []

    # eventos de click (query + doc + rank)
    fact_click_events = []

    # tiempos de permanencia (dwell time)
    fact_dwell_times = []

    def save_query_terms(self, terms: str) -> int:
        """
        Guarda info básica de la query y devuelve un ID.
        """
        query_id = random.randint(0, 100000)
        tokens = [t for t in terms.split() if t]

        self.fact_queries.append(
            {
                "query_id": query_id,
                "query": terms,
                "n_terms": len(tokens),
                "terms_order": tokens,
                "timestamp": time.time(),
            }
        )
        return query_id

    # registrar cada request HTTP
    def register_request(self, path: str, method: str, user_agent: str, ip: str, session_id: str):
        self.fact_requests.append(
            {
                "path": path,
                "method": method,
                "user_agent": user_agent,
                "ip": ip,
                "session_id": session_id,
                "timestamp": time.time(),
            }
        )

    # registrar un click en un documento con el rank en la lista
    def register_click_event(self, search_id: str | None, doc_id: str, rank: int | None, session_id: str):
        self.fact_click_events.append(
            {
                "search_id": search_id,
                "doc_id": doc_id,
                "rank": rank,
                "session_id": session_id,
                "timestamp": time.time(),
            }
        )

    # registrar dwell time
    def register_dwell_time(self, doc_id: str, dwell_seconds: float, session_id: str):
        self.fact_dwell_times.append(
            {
                "doc_id": doc_id,
                "dwell_seconds": dwell_seconds,
                "session_id": session_id,
                "timestamp": time.time(),
            }
        )

    def plot_number_of_views(self):
        """
        Altair bar chart: número de vistas por documento.
        """
        if not self.fact_clicks:
            return "<h3>No clicks registered yet</h3>"

        data = [
            {"Document ID": doc_id, "Number of Views": count}
            for doc_id, count in self.fact_clicks.items()
        ]
        df = pd.DataFrame(data)

        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x="Document ID:N",
                y="Number of Views:Q",
            )
            .properties(title="Number of Views per Document")
        )

        return chart.to_html()


class ClickedDoc:
    def __init__(self, doc_id, description, counter):
        self.doc_id = doc_id
        self.description = description
        self.counter = counter

    def to_json(self):
        return self.__dict__

    def __str__(self):
        """
        Print the object content as a JSON string
        """
        return json.dumps(self)
