# -*- coding: utf-8 -*-
"""
Created on Fri Aug 22 13:45:40 2025

@author: HP
"""

"""
Evaluate a binary text classifier from a Hugging Face model on a JSON dataset.

Expected JSON format (dict-of-examples):
{
  "example_id_1": {"Text": "some text...", "Label": 0},
  "example_id_2": {"Text": "another text...", "Label": 1},
  ...
}

Outputs:
- Console metrics (classification report, confusion matrix, accuracy/precision/recall/F1)

"""


# Load and preprocess data
with open("ckd_prompts_adjusted.json") as f:
    examples = json.load(f)


# Extract keys to 'texts' and values to 'labels'
texts = list(examples.keys())  # List of all dictionary keys
labels = list(examples.values())  # List of all dictionary keys


# Initialize model and tokenizer


MODEL = "deepseek-ai/DeepSeek-R1-Distill-Llama-8B"

tokenizer = AutoTokenizer.from_pretrained(MODEL, use_fast=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL,
    num_labels=2
)

classifier = pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    device=-1  # CPU
)


# Create inference pipeline

classifier = pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    device_map="auto",
    framework="pt"
)

print(type(labels[0]))
print(labels[0])

# Extract fields correctly

texts = [ex["Text"] for ex in examples.values()]
labels = [int(ex["Label"]) for ex in examples.values()]

# Run inference

predictions = classifier(texts)
labels = [int(label) for label in labels]

# Process predictions
preds = [1 if pred['label'] == "LABEL_1" else 0 for pred in predictions]
probs = [pred['score'] if pred['label'] == "LABEL_1" else 1-pred['score'] for pred in predictions]

# Calculate metrics

print("\nClassification Report:")
print(classification_report(labels, preds, target_names=["No", "Yes"]))

print("Labels type sample:", type(labels[0]))
print("Preds type sample:", type(preds[0]))

print("\nConfusion Matrix:")
print(confusion_matrix(labels, preds))

print("\nDetailed Metrics:")
accuracy = accuracy_score(labels, preds)
precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="binary")
print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")