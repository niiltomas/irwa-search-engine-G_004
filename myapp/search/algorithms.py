"""
Search algorithms module for IRWA Search Engine.
Implements BM25 ranking algorithm for product search.
"""

import re
import math
from collections import Counter, defaultdict
from nltk.corpus import stopwords

from myapp.search.objects import Document


# Initialize English stopwords
try:
    STOPWORDS = set(stopwords.words('english'))
except LookupError:
    # Fallback if NLTK data not downloaded
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can'
    }


class BM25Index:
    """
    BM25 search index for document ranking.
    Uses Okapi BM25 algorithm with metadata boosts.
    """
    
    def __init__(self, corpus, k1=1.5, b=0.75):
        """
        Initialize BM25 index from corpus.
        
        Args:
            corpus: dict of {doc_id: Document}
            k1: term frequency saturation parameter (default: 1.5)
            b: length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        
        # Build the index
        self.doc_frequencies = defaultdict(int)  # {term: count of docs containing term}
        self.doc_lengths = {}  # {doc_id: token count}
        self.doc_term_freqs = {}  # {doc_id: {term: frequency}}
        self.avg_doc_length = 0
        
        self._build_index()
    
    def _tokenize(self, text):
        """
        Tokenize text: lowercase, remove punctuation, split, filter stopwords.
        
        Args:
            text: raw text string
            
        Returns:
            list of tokens
        """
        if not text:
            return []
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs and special characters, keep only alphanumeric and spaces
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        # Split on whitespace
        tokens = text.split()
        
        # Filter out stopwords and empty strings
        tokens = [t for t in tokens if t and t not in STOPWORDS]
        
        return tokens
    
    def _build_index(self):
        """Build the BM25 index from corpus."""
        total_length = 0
        
        for doc_id, doc in self.corpus.items():
            # Combine title and description for indexing
            text = f"{doc.title or ''} {doc.description or ''}"
            
            # Tokenize
            tokens = self._tokenize(text)
            
            # Store document length
            self.doc_lengths[doc_id] = len(tokens)
            total_length += len(tokens)
            
            # Store term frequencies for this document
            term_freq = Counter(tokens)
            self.doc_term_freqs[doc_id] = dict(term_freq)
            
            # Update document frequency (how many docs contain each term)
            for term in term_freq.keys():
                self.doc_frequencies[term] += 1
        
        # Calculate average document length
        if len(self.corpus) > 0:
            self.avg_doc_length = total_length / len(self.corpus)
        else:
            self.avg_doc_length = 0
    
    def _calculate_idf(self, term):
        """
        Calculate IDF (Inverse Document Frequency) for a term.
        
        Args:
            term: search term
            
        Returns:
            float: IDF score
        """
        df = self.doc_frequencies.get(term, 0)
        N = len(self.corpus)
        
        # BM25 IDF formula
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
        return idf
    
    def _calculate_bm25_score(self, doc_id, query_tokens):
        """
        Calculate BM25 score for a document given query tokens.
        
        Args:
            doc_id: document identifier
            query_tokens: list of query terms
            
        Returns:
            float: BM25 score
        """
        score = 0.0
        doc_length = self.doc_lengths.get(doc_id, 0)
        term_freqs = self.doc_term_freqs.get(doc_id, {})
        
        for term in query_tokens:
            # Get term frequency in document (0 if not present)
            tf = term_freqs.get(term, 0)
            
            if tf == 0:
                continue
            
            # Calculate IDF
            idf = self._calculate_idf(term)
            
            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            
            score += idf * (numerator / denominator)
        
        return score
    
    def _apply_metadata_boosts(self, score, doc):
        """
        Apply metadata-based score boosts.
        
        Args:
            score: base BM25 score
            doc: Document object
            
        Returns:
            float: boosted score
        """
        boost = 1.0
        
        # Boost highly-rated products
        if doc.average_rating and doc.average_rating >= 4.0:
            boost *= 1.2
        
        # Boost in-stock products
        if not doc.out_of_stock:
            boost *= 1.1
        
        return score * boost
    
    def search(self, query_text, top_k=20):
        """
        Search the corpus for documents matching query.
        
        Args:
            query_text: raw search query
            top_k: number of top results to return
            
        Returns:
            list of Document objects, ranked by relevance (highest first)
        """
        # Tokenize query
        query_tokens = self._tokenize(query_text)
        
        if not query_tokens:
            # Empty query, return empty results
            return []
        
        # Score all documents
        scores = {}
        for doc_id in self.corpus.keys():
            bm25_score = self._calculate_bm25_score(doc_id, query_tokens)
            doc = self.corpus[doc_id]
            final_score = self._apply_metadata_boosts(bm25_score, doc)
            scores[doc_id] = final_score
        
        # Sort by score descending
        ranked_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get top-k documents and construct Document objects with ranking
        results = []
        for rank, (doc_id, score) in enumerate(ranked_docs[:top_k]):
            doc = self.corpus[doc_id]
            # Create a new Document with the ranking score
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
                url=doc.url,
                images=doc.images
            )
            results.append((result_doc, score))
        
        return results


def search_in_corpus(query_text, corpus, top_k=20):
    """
    Main search function for searching in corpus.
    
    Args:
        query_text: search query string
        corpus: dict of {doc_id: Document}
        top_k: number of results to return (default: 20)
        
    Returns:
        list of Document objects ranked by BM25 relevance
    """
    # Create BM25 index
    index = BM25Index(corpus, k1=1.5, b=0.75)
    
    # Search and get results with scores
    results_with_scores = index.search(query_text, top_k=top_k)
    # Return the list of (Document, score) so callers can perform hybrid reranking
    return results_with_scores
