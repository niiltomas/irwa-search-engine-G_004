### README

This notebook contains **Part 2 of the IRWA project: Indexing, TF-IDF Ranking and Evaluation**.

**Team G_004**  
Alex De La Haya Gutiérrez (268169)  
Marc Guiu Armengol (268920)  
Nil Tomàs Plans (268384)

---

#### Dependencies
Run on **Google Colab (Python 3.12)**.  
Required packages:
```
pip install pandas numpy matplotlib
```
Optional (for text preprocessing or visualization):
```
pip install nltk wordcloud spacy
python -m spacy download en_core_web_sm
```

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

#### Part 2 – Indexing & Ranking
- Build an **inverted index** containing term → document mappings with term positions.  
- Support **conjunctive (AND) queries**.  
- Implement a **TF-IDF ranking model** to score and order retrieved documents.  
- Evaluate results for several test queries relevant to the dataset.

---

#### Evaluation Metrics Implemented
- Precision@K  
- Recall@K  
- Average Precision@K  
- F1-Score@K  
- Mean Average Precision (MAP)  
- Mean Reciprocal Rank (MRR)  
- Normalized Discounted Cumulative Gain (NDCG)

---

Executed entirely in **Google Colab**, fulfilling all **Part 2** requirements (Indexing + Ranking + Evaluation).
