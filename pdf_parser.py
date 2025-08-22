# -*- coding: utf-8 -*-
"""
Created on Thu Apr 24 15:41:59 2025

@author: HP
"""

import fitz
import pandas as pd
import re
from collections import defaultdict

## Import patient data

# Load the CSV file
csv_path = "C:/Users/HP/OneDrive/Masaüstü/Project/SMR.csv" # <-- update this
df = pd.read_csv(csv_path, encoding="latin1")

# Preview it
print(df.head())

print(df[['Case', 'Current Medication']].head())

# Function to clean and split medication strings
def extract_drugs(med_string):
    # Replace different separators with a consistent one
    med_string = med_string.replace('\n', ' ').replace('  ', ' ').replace(' ', ', ')
    # Split into list
    drugs = [d.strip() for d in med_string.split(',') if d.strip()]
    # Remove duplicates while preserving order
    seen = set()
    return [d for d in drugs if not (d in seen or seen.add(d))]

# Apply the function to each row
df['Medication List'] = df['Current Medication'].apply(extract_drugs)

# If you want to explode the list into separate rows
drugs_by_patient = df.explode('Medication List')[['Case', 'Medication List']]

print(drugs_by_patient)

# After exploding, group drugs back by patient
patient_drugs = drugs_by_patient.groupby('Case')['Medication List'].apply(list).to_dict()

## Import BNF
pdf_path = "C:/Users/HP/OneDrive/Masaüstü/Project/British-National-Formulary-82-2021.pdf"


def extract_two_column_text(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        rect = page.rect
        mid_x = rect.width / 2

        # Left column: from left to mid
        left_rect = fitz.Rect(0, 0, mid_x, rect.height)
        left_text = page.get_text("text", clip=left_rect)

        # Right column: from mid to right
        right_rect = fitz.Rect(mid_x, 0, rect.width, rect.height)
        right_text = page.get_text("text", clip=right_rect)

        # Combine column-wise: first left, then right
        full_text += left_text + "\n" + right_text + "\n"

    return full_text

# Extract and print the text from the PDF
extracted_text = extract_two_column_text(pdf_path)

# Print the first 1000 characters to check
print(extracted_text[:1000])

# Step 3: For each patient, search their drugs in the PDF text
patient_passages = {}

for patient_id, drugs in patient_drugs.items():
    found_drugs = []
    for drug in drugs:
        if drug.lower() in extracted_text.lower():
            found_drugs.append(drug)
    patient_passages[patient_id] = found_drugs

# Step 4: Display the result
for patient, drugs_found in patient_passages.items():
    print(f"Patient {patient}: Drugs found in PDF: {drugs_found}")

# Grade symbols you care about
grade_letters = "hijk"
grade_pattern = re.compile(rf"\.\s([{grade_letters}])\s*(?:\n|$)", re.IGNORECASE)

# Split the text into paragraphs (you can tune this)
paragraphs = [p.strip() for p in extracted_text.split('\n\n') if p.strip()]

# Make all paragraphs lowercase for matching (store original too)
paragraph_map = {p.lower(): p for p in paragraphs}

# Dictionary to store results: patient -> list of (drug, paragraph)
patient_grade_passages = defaultdict(list)

# Loop through each patient and their drugs
for patient_id, drugs in patient_drugs.items():
    for drug in drugs:
        drug_lower = drug.lower()
        for para_lower, para_original in paragraph_map.items():
            if drug_lower in para_lower and grade_pattern.search(para_lower):
                patient_grade_passages[patient_id].append((drug, para_original))

# Display example output
for patient_id, matches in patient_grade_passages.items():
    print(f"\n--- Patient {patient_id} ---")
    for drug, paragraph in matches:
        print(f"Drug: {drug}")
        print(paragraph)
        print("-" * 40)
        