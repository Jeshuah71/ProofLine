from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# Fictional examples for learning purposes only
mesages = [
    "Pay a registration fee to secure this job",
    "Send money before your interview",
    "Transfer a processing fee to receive your offer",
    "You must purchase equipment from our payment link",
    "Pay us today to activate your employment",
    "Send a deposit before we hire you",

    "We would like to schedule a technical interview",
    "Your interview is scheduled for next Tuesday",
    "Please submit your resume through our careers page",
    "Thank you for applying to our engineering position",
    "Our hiring manager will contact you next week",
    "We would like to discuss your qualifications",
]

# 1 = suspicious pattern, 0 = routine pattern
labels = [1] * 6 + [0] * 6

# Combine text processing and classification
model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("classifier", LogisticRegression())
])

# Split our dataset into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    mesages, 
    labels,
    test_size=0.25,
    random_state=42,
    stratify=labels
)

# Train only on training data
model.fit(X_train, y_train)

# Predict the lables of unseen messages
predictions = model.predict(X_test)

# Compare actual and predicted rsults 
for message, actual, predicted in zip (
    X_test, y_test, predictions
):
    print(f"\nMessage: {message}")
    print(f"Actual: {actual}")
    print(f"Predicted: {predicted}")
    
# Evaluate our model
print("\nClassification Report:")
print(classification_report(
    y_test,
    predictions,
    zero_division=0
))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))