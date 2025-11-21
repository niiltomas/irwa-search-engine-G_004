from myapp.search.objects import Document
from myapp.search.algorithms import search_in_corpus




class SearchEngine:
    """Class that implements the search engine logic"""

    def search(self, search_query, search_id, corpus, analytics_data=None):
        """
        Search and rerank results using a hybrid of BM25 similarity and commercial metadata.

        Args:
            search_query: raw query string
            search_id: analytics id for the query
            corpus: dict of corpus documents
            analytics_data: optional AnalyticsData instance to use popularity (clicks)

        Returns:
            list of Document objects (with `score` populated) ranked by final hybrid score
        """
        print("Search query:", search_query)

        results = []

        # Retrieve top-k using BM25. search_in_corpus now returns list of (Document, bm25_score)
        bm25_results = search_in_corpus(search_query, corpus, top_k=20)

        if not bm25_results:
            return []

        # Build arrays for normalization
        bm25_scores = [s for (_d, s) in bm25_results]
        max_bm25 = max(bm25_scores) if bm25_scores else 1.0
        min_price = None
        max_price = None
        click_counts = {}

        # Collect prices and clicks for normalization
        for doc, s in bm25_results:
            price = getattr(doc, 'selling_price', None)
            if price is not None:
                if min_price is None or price < min_price:
                    min_price = price
                if max_price is None or price > max_price:
                    max_price = price

            # popularity from analytics_data.fact_clicks (if available)
            if analytics_data and hasattr(analytics_data, 'fact_clicks'):
                clicks = analytics_data.fact_clicks.get(doc.pid, 0)
            else:
                clicks = 0
            click_counts[doc.pid] = clicks

        max_clicks = max(click_counts.values()) if click_counts else 1

        # Compute hybrid final score and create result Documents
        hybrid_results = []
        for doc, s in bm25_results:
            # Normalize similarity
            sim_norm = (s / max_bm25) if max_bm25 else 0.0

            # Normalize rating (assume 5.0 max)
            rating = getattr(doc, 'average_rating', None) or 0.0
            rating_norm = min(max(rating / 5.0, 0.0), 1.0)

            # Normalize discount (assume percentage or raw number; clamp to 0-100)
            discount = getattr(doc, 'discount', None) or 0.0
            try:
                discount_val = float(discount)
            except Exception:
                discount_val = 0.0
            discount_norm = min(max(discount_val / 100.0, 0.0), 1.0)

            # Price score: lower better. If no price info, neutral 0.5
            price = getattr(doc, 'selling_price', None)
            if price is None or min_price is None or max_price is None or max_price == min_price:
                price_score = 0.5
            else:
                price_score = 1.0 - ((price - min_price) / (max_price - min_price))

            # Popularity normalized
            clicks = click_counts.get(doc.pid, 0)
            popularity_norm = (clicks / max_clicks) if max_clicks else 0.0

            # Base weighted combination (weights chosen conservatively)
            final_score = (
                0.6 * sim_norm
                + 0.15 * rating_norm
                + 0.1 * discount_norm
                + 0.05 * price_score
                + 0.05 * popularity_norm
            )

            # Apply a small multiplicative boost for in-stock items
            if not getattr(doc, 'out_of_stock', False):
                final_score *= 1.05

            hybrid_results.append((doc, final_score))

        # Sort by hybrid score descending
        hybrid_results.sort(key=lambda x: x[1], reverse=True)

        # Construct final Document objects with URL selection and attach score
        for rank, (doc, score) in enumerate(hybrid_results):
            original_url = getattr(doc, 'url', None)
            link_url = original_url if original_url else f"/doc_details?pid={doc.pid}&search_id={search_id}"

            result_doc = Document(
                _id=doc.pid,
                pid=doc.pid,
                title=doc.title,
                description=doc.description,
                brand=doc.brand,
                category=doc.category,
                sub_category=doc.sub_category,
                product_details=doc.product_details,
                seller=doc.seller,
                out_of_stock=doc.out_of_stock,
                selling_price=doc.selling_price,
                discount=doc.discount,
                actual_price=doc.actual_price,
                average_rating=doc.average_rating,
                url=link_url,
                images=doc.images,
                score=score,
            )
            results.append(result_doc)

        return results
