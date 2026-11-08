import pandas as pd

# Load the real job-posting dataset
df = pd.read_csv("data/fake_job_postings.csv")

# Count all job postings
print("Total postings:", len(df))

# COunt legitimate and fraudulent postings
print("\nClass distribution:")
print(df["fraudulent"].value_counts().sort_index())

# Calculate the percentage of fraudulent postings
fraud_rate = df["fraudulent"].mean() * 100

print(f"\nFraud percentage: {fraud_rate:.2f}%")

# Check for missing descriptions
print(
    "\nMissing descriptions:",
    df["description"].isna().sum()    
)