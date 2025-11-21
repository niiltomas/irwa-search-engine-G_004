import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class RAGGenerator:
    """Clean and unified RAG generator: Top-3 recommendation with metadata."""

    DEFAULT_ANSWER = (
        "RAG is not available. Check your credentials (.env file) or account limits."
    )

    def __init__(self, model_env_var: str = "GROQ_MODEL"):
        self.model_env_var = model_env_var
        self.model_name = os.environ.get(model_env_var, "llama-3.1-8b-instant")
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def _format_documents(self, retrieved_results, top_N):
        """Format documents into a metadata-rich block for the prompt."""
        lines = []

        for item in retrieved_results[:top_N]:
            if isinstance(item, (list, tuple)):
                doc, bm25_score = item
            else:
                doc = item
                bm25_score = getattr(doc, "score", None)

            lines.append(
                f"PID: {getattr(doc, 'pid', '')} | Title: {getattr(doc, 'title', '')} | "
                f"Price: {getattr(doc, 'selling_price', 'N/A')} | Discount: {getattr(doc, 'discount', 'N/A')} | "
                f"Rating: {getattr(doc, 'average_rating', 'N/A')} | InStock: {not bool(getattr(doc, 'out_of_stock', False))} | "
                f"BM25: {bm25_score if bm25_score is not None else 'N/A'} | URL: {getattr(doc, 'url', '')}"
            )

        return "\n".join(lines) if lines else "(no retrieved products)"

    def generate_response(self, user_query: str, retrieved_results: list, top_N: int = 20) -> str:
        """Generate a Top-3 recommendation based on retrieved products."""
        try:
            formatted_results = self._format_documents(retrieved_results, top_N)

            prompt = (
                "You are an expert product advisor. From the retrieved products below, pick the Top 3 products "
                "best suited for the user's request. For each, provide a one-line explanation referencing price, "
                "rating, discount, stock, or BM25 score.\n\n"
                "Return your answer as numbered items (1., 2., 3.) formatted exactly like:\n"
                "1. PID - Title - Why: <short justification>\n\n"
                "Retrieved Products:\n"
                f"{formatted_results}\n\n"
                f"User Request: {user_query}\n\n"
                "If none of the retrieved products fit, return exactly:\n"
                "\"There are no good products that fit the request based on the retrieved results.\""
            )

            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )

            return completion.choices[0].message.content

        except Exception as e:
            print(f"[RAG ERROR] {e}")
            return self.DEFAULT_ANSWER
