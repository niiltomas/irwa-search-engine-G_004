### README

This notebook contains **Part 3 of the IRWA project: Ranking and Filtering**.

**Team G_004**  
Alex De La Haya Gutiérrez (268169)  
Marc Guiu Armengol (268920)  
Nil Tomàs Plans (268384)

---

#### Dependencies
Run on **Google Colab (Python 3.12)**.  
Required packages:
```
pip install pandas numpy matplotlib gensim

---

#### Data
Input dataset:  
`fashion_products_dataset_preprocessed.json` — output generated in **Part 1** after text cleaning.  
Loaded from Google Drive:
```python
from google.colab import drive
drive.mount('/content/drive')
```

---

#### Part 3 – Ranking & Filtering
Implements and compares four different ranking models for conjunctive (AND) queries.

1. TF-IDF + Cosine Similarity
Classical vector-space model.
Computes TF-IDF weights and ranks documents using cosine similarity.

2. BM25
Probabilistic model improving TF-IDF by adjusting term saturation and document length.
Uses parameters k1 = 1.5, b = 0.75.

3. Hybrid Custom Score
Combines textual relevance (TF-IDF) with numerical fields from the dataset:

- average_rating
- discount
- selling_price
- out_of_stock

Formula:
Score = 0.7 * TF-IDF + 0.15 * rating + 0.1 * discount + 0.05 * (1 - price) - stock_penalty

4. Word2Vec + Cosine Similarity
Each document and query is represented as the average vector of its word embeddings.
Uses gensim to train Word2Vec on the corpus (or load pretrained vectors).
Ranks by cosine similarity between the query vector and document vectors.

---

Executed entirely in **Google Colab**, fulfilling all **Part 3** requirements (Indexing + Ranking + Evaluation).
