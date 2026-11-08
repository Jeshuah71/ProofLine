
from pathlib import Path
import joblib

# Locate the model we saved locally
model_path = (
    Path(__file__).resolve().parent
    / "models"
    / "job_posting_classifier.joblib"
)

# Load our trained model and threshold
saved = joblib.load(model_path)

model = saved["pipeline"]
threshold = saved["threshold"]

# Test a fictional job posting
message = "Pay a registration fee before starting this job"

# Get the model's score for the fraudulent class
score = model.predict_proba([message])[0, 1]

# Apply our selected decision threshold
prediction = int(score >= threshold)

print("Fraud class score:", round(float(score), 3))
print("Threshold:", threshold)
print("Prediction:", prediction)
