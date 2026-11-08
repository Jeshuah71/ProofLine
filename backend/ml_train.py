
import pandas as pd

from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score


# Step 1: Load the dataset
df = pd.read_csv("data/fake_job_postings.csv")

# Step 2: Prepare text and labels
df["title"] = df["title"].fillna("")
df["description"] = df["description"].fillna("")

# Combine job title and description
df["text"] = df["title"] + " " + df["description"]

# Remove empty and exactly duplicated text
df = df[df["text"].str.strip() != ""]
df = df.drop_duplicates(subset=["text"])

X = df["text"]
y = df["fraudulent"]

# Step 3: Split the data BEFORE training
X_dev, X_test, y_dev, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Split the remaining data into training and validation 
X_train, X_val, y_train, y_val = train_test_split(
    X_dev, y_dev,
    test_size=0.25,
    random_state=42,
    stratify=y_dev
)

# Step 4: Create our ML pipeline
model = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 2)
    )),
    ("classifier", LogisticRegression(
        class_weight="balanced",
        max_iter=1000
    ))
])

# Step 5: Train the model
print("Training model...")
model.fit(X_train, y_train)


# Get model scores on validation data
validation_scores = model.predict_proba(X_val)[:, 1]

thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]

best_threshold = 0.5
best_f1 = -1

for threshold in thresholds:
    # Convert scores into predicted labels
    predictions = (validation_scores >= threshold).astype(int)

    precision = precision_score(y_val, predictions, zero_division=0)
    recall = recall_score(y_val, predictions, zero_division=0)
    f1 = f1_score(y_val, predictions, zero_division=0)

    print(
        f"Threshold: {threshold:.1f} | "
        f"Precision: {precision:.2f} | "
        f"Recall: {recall:.2f} | "
        f"F1: {f1:.2f}"
    )

    # Select the threshold with the highest validation F1
    if f1 > best_f1:
        best_f1 = f1
        best_threshold = threshold

print(f"\nSelected threshold: {best_threshold:.1f}")

# Evaluate the selected threshold on test data
test_scores = model.predict_proba(X_test)[:, 1]
test_predictions = (test_scores >= best_threshold).astype(int)

print("\nFinal Test Report:")
print(classification_report(y_test, test_predictions, zero_division=0))

print("\nFinal Confusion Matrix:")
print(confusion_matrix(y_test, test_predictions, labels=[0, 1]))

# Create a table to inspect infividual predictions
results = pd.DataFrame({
    "text": X_test.to_numpy(),
    "actual": y_test.to_numpy(),
    "predicted":test_predictions,
    "score": test_scores
})

# Fraudulent posting incorrectly classified as legitimate
false_negatives = results[
    (results["actual"] == 1) &
    (results["predicted"] == 0)
]

# Legitimate postings incorrectly classified as fraudulent
false_positives = results[
    (results["actual"] == 0) &
    (results["predicted"] == 1)
]

print("\nFalse negatives:", len(false_negatives))
print("False positives:", len(false_positives))

# Examine three examples from each error category
for name, errors in [
    ("FALSE NEGATIVES", false_negatives),
    ("FALSE POSITIVES", false_positives)
]:
    print(f"\n--- {name} ---")

    for _, row in errors.head(3).iterrows():
        # Shorten the description for easier reading
        excerpt = " ".join(row["text"].split())[:180]

        print(f"\nModel score: {row['score']:.3f}")
        print(f"Actual: {row['actual']}")
        print(f"Predicted: {row['predicted']}")
        print(f"Text: {excerpt}...")


# Create a directory for saved models
models_dir = Path(__file__).resolve().parent / "models"
models_dir.mkdir(exist_ok=True)

# Save the trained pipeline and its selected threshold
model_path = models_dir / "job_posting_classifier.joblib"

joblib.dump(
    {
        "pipeline": model,
        "threshold": float(best_threshold),
        "task": "job_posting_classification",
    },
    model_path
)

print(f"\nModel saved to: {model_path}")

