# -*- coding: utf-8 -*-
"""
Created on Mon May 19 14:50:35 2025

@author: HP
"""

import fitz
import pandas as pd
import re
from collections import defaultdict

# --- Step 1: Load patient data and process medications ---

def load_patient_data(csv_path):
    df = pd.read_csv(csv_path, encoding="latin1")
    df['Medication List'] = df['Current Medication'].apply(extract_drugs)
    return df

def extract_drugs(med_string):
    # Normalize the string and split on commas or newlines (real delimiters)
    med_string = re.sub(r'[\n;]+', ',', med_string)  # replace newline or semicolon with comma
    med_string = re.sub(r'\s{2,}', ' ', med_string)  # collapse multiple spaces

    # Split by commas only (real delimiters), not spaces
    drugs = [d.strip() for d in med_string.split(',') if d.strip()]

    # Remove duplicates while preserving order
    seen = set()
    return [d for d in drugs if not (d.lower() in seen or seen.add(d.lower()))]

def get_patient_drugs(df):
    drugs_by_patient = df.explode('Medication List')[['Case', 'Medication List']]
    return drugs_by_patient.groupby('Case')['Medication List'].apply(list).to_dict()

# --- Step 2: Extract text from two-column BNF PDF ---

def extract_two_column_text(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        rect = page.rect
        mid_x = rect.width / 2
        left_text = page.get_text("text", clip=fitz.Rect(0, 0, mid_x, rect.height))
        right_text = page.get_text("text", clip=fitz.Rect(mid_x, 0, rect.width, rect.height))
        full_text += left_text + "\n" + right_text + "\n"
    return full_text

# --- Step 3: Search drugs for a single patient in BNF text ---

def search_drugs_in_text(patient_id, drugs, bnf_text):
    found_drugs = [drug for drug in drugs if drug.lower() in bnf_text.lower()]
    return found_drugs

# --- Step 4: Get paragraphs for a patient’s drugs ---

def get_impairment_info_matrix_only(drugs, bnf_text):
    impairments = {
        "Renal": re.compile(r"\brenal impairment\b", re.IGNORECASE),
        "Hepatic": re.compile(r"\bhepatic impairment\b", re.IGNORECASE),
        "Cognitive/Other": re.compile(r"\belderly\b", re.IGNORECASE)
    }

    paragraphs = [p.strip() for p in bnf_text.split('\n\n') if p.strip()]
    result_rows = []

    for drug in drugs:
        drug_lower = drug.lower()
        matching_paras = [p for p in paragraphs if drug_lower in p.lower()]

        row = {
            "Drug": drug,
            "Renal": 0,
            "Hepatic": 0,
            "Cognitive/Other": 0
        }

        for para in matching_paras:
            for imp_name, pattern in impairments.items():
                if pattern.search(para):
                    row[imp_name] = 1

        result_rows.append(row)

    return pd.DataFrame(result_rows)

# Load data
csv_path = "C:/Users/HP/OneDrive/Masaüstü/Project/SMR.csv"
pdf_path = "C:/Users/HP/OneDrive/Masaüstü/Project/British-National-Formulary-82-2021.pdf"

df = load_patient_data(csv_path)
patient_drugs_dict = get_patient_drugs(df)
bnf_text = extract_two_column_text(pdf_path)

# Call manually for a patient
patient_id = 1
  
if patient_id in patient_drugs_dict:
    drugs = patient_drugs_dict[patient_id]
    found = search_drugs_in_text(patient_id, drugs, bnf_text)
    print(f"\nDrugs found in PDF for Patient {patient_id}: {found}\n")

    impairment_matrix = get_impairment_info_matrix_only(drugs, bnf_text)
    print(impairment_matrix)

else:
    print(f"Patient ID {patient_id} not found.")
    
