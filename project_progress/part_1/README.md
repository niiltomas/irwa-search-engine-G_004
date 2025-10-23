### README

This notebook contains **Part 1 of the IRWA project: Text Processing and Exploratory Data Analysis**.

**Team G_004**  
Alex De La Haya Gutiérrez  (268169)
Marc Guiu Armengol (268920)  
Nil Tomàs Plans (268384)

---

####  Dependencies
Run on **Google Colab (Python 3.12)**.  
Required packages:
```
pip install nltk matplotlib wordcloud tqdm pandas
```
Optional (for NER):
```
pip install spacy
python -m spacy download en_core_web_sm
```

NLTK resources:
```python
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
```

---

####  Data
Dataset: `fashion_products_dataset.json` (≈28,000 products)  
Loaded from Google Drive:
```python
from google.colab import drive
drive.mount('/content/drive')
```

---

####  Part 1 – Text Processing
Applied to `title` and `description`:
- Lowercasing  
- Punctuation removal  
- Tokenization  
- Stopword removal  
- Stemming (`PorterStemmer`)  

Extra fields added:
`title_proc`, `description_proc`.

Categorical fields (`brand`, `category`, `sub_category`, `seller`, `product_details`)  
→ kept as **separate processed fields** for better retrieval.

Numeric fields (`price`, `discount`, `rating`, `out_of_stock`)  
→ cleaned and converted to numeric/boolean, **not indexed as text**.

---

####  Part 2 – Exploratory Data Analysis
Includes:
- Word frequency distribution (Zipf’s Law)  
- Top 20 frequent words  
- Product ranking by average rating  
- Average sentence length & vocabulary size  
- Top sellers and brands  
- Out_of_stock distribution  
- Word cloud visualization  

Done entirely in **Google Colab**, fully meeting Part 1 requirements (Data Preparation + EDA).

