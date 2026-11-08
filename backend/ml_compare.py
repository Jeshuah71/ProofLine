
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import precision_score, recall_score, f1_score

# Load the same dataset
data_path = Path(__file__).resolve().parent / "data" / "fake_job_postings.csv"
df = pd.read_csv(data_path)

# Prepare text
df["text"] = (
    df["title"].fillna("") + " " +
    df["description"].fillna("")
)

df = df[df["text"].str.strip() != ""]
df = df.drop_duplicates(subset=["text"])

X = df["text"]
y = df["fraudulent"]

# Reproduce our original development/holdout split
X_dev, X_holdout, y_dev, y_holdout = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

# Use only training and validation data for comparison
X_train, X_val, y_train, y_val = train_test_split(
    X_dev, y_dev, test_size=0.25,
    random_state=42, stratify=y_dev
)

# Compare two feature extraction methods
vectorizers = {
    "Word-based": TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 2)
    ),
    "Character-based": TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        max_features=20000,
        min_df=3
    )
}

thresholds = [0.4, 0.5, 0.6, 0.7]

for name, vectorizer in vectorizers.items():
    print(f"\n--- {name} ---")

    model = Pipeline([
        ("tfidf", vectorizer),
        ("classifier", LogisticRegression(
            class_weight="balanced",
            max_iter=1000
        ))
    ])

    # Train on training data only
    model.fit(X_train, y_train)

    # Get scores on validation data
    scores = model.predict_proba(X_val)[:, 1]

    for threshold in thresholds:
        predictions = (scores >= threshold).astype(int)

        precision = precision_score(
            y_val, predictions, zero_division=0
        )
        recall = recall_score(
            y_val, predictions, zero_division=0
        )
        f1 = f1_score(
            y_val, predictions, zero_division=0
        )

        print(
            f"Threshold {threshold:.1f} | "
            f"Precision {precision:.2f} | "
            f"Recall {recall:.2f} | "
            f"F1 {f1:.2f}"
        )
