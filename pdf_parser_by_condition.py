# -*- coding: utf-8 -*-
"""
Created on Thu May  1 01:26:46 2025

@author: HP
"""
import fitz
import pandas as pd
import re
from collections import defaultdict

def load_patient_data(csv_path):
    df = pd.read_csv(csv_path, encoding="latin1")
    df['Condition List'] = df['Current Medical History'].apply(extract_conditions)
    return df  

def extract_conditions(condition_string):
    # Normalize and split on newlines, commas, or semicolons
    condition_string = re.sub(r'[\n;]+', ',', condition_string)
    condition_string = re.sub(r'\s{2,}', ' ', condition_string)
    conditions = [c.strip() for c in condition_string.split(',') if c.strip()]
    
    seen = set()
    return [c for c in conditions if not (c.lower() in seen or seen.add(c.lower()))]

def get_patient_conditions(df):
    conditions_by_patient = df.explode('Condition List')[['Case', 'Condition List']]
    return conditions_by_patient.groupby('Case')['Condition List'].apply(list).to_dict()

def search_conditions_in_text(patient_id, conditions, bnf_text):
    return [condition for condition in conditions if condition.lower() in bnf_text.lower()]

def get_graded_passages_for_patient(patient_id, conditions, bnf_text, grade_letters="hijk"):
    grade_pattern = re.compile(rf"\.\s([{grade_letters}])\s*(?:\n|$)", re.IGNORECASE)
    paragraphs = [p.strip() for p in bnf_text.split('\n\n') if p.strip()]
    paragraph_map = {p.lower(): p for p in paragraphs}
    matched = []

    for condition in conditions:
        condition_lower = condition.lower()
        for para_lower, para_original in paragraph_map.items():
            if condition_lower in para_lower and grade_pattern.search(para_lower):
                matched.append((condition, para_original))

    return matched

# Extract text from two-column BNF PDF ---
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

# Load data
csv_path = "C:/Users/HP/OneDrive/Masaüstü/Project/SMR.csv"
pdf_path = "C:/Users/HP/OneDrive/Masaüstü/Project/British-National-Formulary-82-2021.pdf"

df = load_patient_data(csv_path)
patient_conditions_dict = get_patient_conditions(df)
bnf_text = extract_two_column_text(pdf_path)

# Manually check for a specific patient
patient_id = 2
  
if patient_id in patient_conditions_dict:
    conditions = patient_conditions_dict[patient_id]
    found = search_conditions_in_text(patient_id, conditions, bnf_text)
    print(f"Conditions found in PDF for Patient {patient_id}: {found}")

    graded = get_graded_passages_for_patient(patient_id, conditions, bnf_text)
    for condition, paragraph in graded:
        print(f"\nCondition: {condition}")
        print(paragraph)
        print("-" * 40)
else:
    print(f"Patient ID {patient_id} not found.")

# Write to file
output_path = f"C:/Users/HP/OneDrive/Masaüstü/Project/patient_{patient_id}_bnf_output.txt"

with open(output_path, "w", encoding="utf-8") as file:
    if patient_id in patient_conditions_dict:
        conditions = patient_conditions_dict[patient_id]
        found = search_conditions_in_text(patient_id, conditions, bnf_text)
        file.write(f"Conditions found in PDF for Patient {patient_id}: {found}\n\n")

        graded = get_graded_passages_for_patient(patient_id, conditions, bnf_text)
        for condition, paragraph in graded:
            file.write(f"\nCondition: {condition}\n")
            file.write(paragraph + "\n")
            file.write("-" * 40 + "\n")
        
        print(f"BNF sections written to {output_path}")
    else:
        msg = f"Patient ID {patient_id} not found.\n"
        file.write(msg)
        print(msg)