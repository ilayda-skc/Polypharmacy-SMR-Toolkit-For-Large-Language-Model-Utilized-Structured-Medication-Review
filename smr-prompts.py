import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import json
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


# Load DeepSeek model
print("\nLoading DeepSeek model...")
model_id = "deepseek-ai/DeepSeek-R1-Distill-Llama-8B"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)
model = model.to("cpu")  # Specify CPU

def generate_response(prompt, max_tokens=512):
    inputs = tokenizer(prompt, return_tensors="pt").to("cpu")
    input_length = inputs["input_ids"].shape[1]  # Length of the prompt tokens

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_tokens = outputs[0][input_length:]  # Remove the prompt tokens
    return tokenizer.decode(generated_tokens, skip_special_tokens=True)
# Load prompts from JSON
prompts_data = {
    "P1": {
        "Task": "You are a clinical pharmacist in the UK. Review diagnoses and identify therapeutic objectives with respect to: Management of existing health problems. Prevention of future health problems. Reference the relevant sections in BNF/NICE and where it is sourced in a tabular format.",
        "Patient Profile": {
            "Sex": "F/M",
            "Age": "",
            "Renal": "eGFR",
            "Smoking": "",
            "Comorbidities": ""
        }
    },
    "P2": {
        "Task": "Act as a clinical pharmacist. For this …ទ0patient, categorize:",
        "Categories": [
            {
                "Category": "Drugs NEVER to stop without specialist input",
                "Format": "Drug, Action (Stop/Keep), Key Reason (max 5 words), Reference",
                "Abbreviations": True
            },
            {
                "Category": "Drugs to consider deprescribing",
                "Format": "Drug, Action (Stop/Keep), Key Reason (max 5 words), Reference",
                "Abbreviations": True
            }
        ]
    },
    "P3": {
        "Task": "Score drugs' renal, other burden (1=BNF-cited elderly risk), and anticholinergic burden (ACB calculator score).",
        "Format": "Drug|1/0|\"BNF-risk-phrase\"|",
        "Abbreviations": True
    },
    "PE": {
            "Task": "You are a clinical pharmacist in the UK. Using the UK BNF and the Anticholinergic Burden (ACB) calculator, analyze the following drugs and produce a table for each drug with:\n\n- Drug name (formatted as per BNF)\n-Renal burden (1 = significant risk, 0 = no significant risk)\n- Other burden (1 = BNF-cited elderly risk, 0 = no risk)\n- Anticholinergic burden (ACB calculator score)",            "Drugs": [
              "Amitriptyline",
              "Furosemide",
              "Ramipril",
              "Cetirizine"
                     ],
            "Format": "Drug | Renal (1/0) | Other (1/0) | ACB Score",
            "Abbreviations": True
    },
    "P4": {
        "Task": "Generate a structured matrix for UK pharmacists with the following columns for each drug:",
        "Columns": [
            "Drug name (generic/formatted per BNF)",
            "Renal burden (1 = significant risk in renal impairment in BNF; 0 = low/no risk)",
            "BNF-cited elderly risk (1 = high risk/poor tolerance in elderly per BNF; 0 = low risk)",
            "BNF risk phrase (Direct quote from BNF, e.g., ‘avoid in severe CKD’ or ‘reduce dose in elderly’)",
            "Anticholinergic Burden (ACB) (Score 0–3 per ACB calculator criteria; cite source)"
        ],
        "Rules": [
            "Only use UK BNF/BNFC (latest edition) and ACB calculator (e.g., https://www.acbcalc.com).",
            "Flag drugs with combined burdens (renal + elderly + ACB ≥3) as ‘P4: High-risk cascade review needed’.",
            "Use ‘§’ to mark incomplete data needing verification.",
            "Format concisely (e.g., ‘Metformin|1|“Avoid if eGFR <30”|0’)."
        ],
        "Abbreviations": True
    },
    "ALT": {
        "Task": "Generate a structured matrix for UK pharmacists with the following columns for each drug:",
        "Columns": [
            "Drug name (generic/formatted per BNF)",
            "Renal burden (1 = significant risk in renal impairment in BNF; 0 = low/no risk)",
            "BNF-cited elderly risk (1 = high risk/poor tolerance in elderly per BNF; 0 = low risk)",
            "BNF risk phrase (Direct quote from BNF, e.g., ‘avoid in severe CKD’ or ‘reduce dose in elderly’)"
        ],
        "Rules": [
            "Only use UK BNF/BNFC (latest edition).",
            "Use ‘§’ to mark incomplete data needing verification.",
            "Format concisely (e.g., ‘Metformin|1|“Avoid if eGFR <30”|0’)."
        ],
        "Abbreviations": True
    },
}

# Sample drug list 
drugs = [
    {"name": "Metformin", "renal_burden": 1, "elderly_risk": 0, "bnf_phrase": "Avoid if eGFR <30", "acb_score": 0},
    {"name": "Amlodipine", "renal_burden": 0, "elderly_risk": 0, "bnf_phrase": "No dose adjustment needed", "acb_score": 0},
    {"name": "Amitriptyline", "renal_burden": 0, "elderly_risk": 1, "bnf_phrase": "Caution in elderly", "acb_score": 3},
    {"name": "Furosemide", "renal_burden": 1, "bnf_phrase": "Monitor electrolytes in CKD", "elderly_risk": 0, "acb_score": 0},
    {"name": "Atorvastatin", "renal_burden": 0, "elderly_risk": 0, "bnf_phrase": "No specific elderly risk", "acb_score": 0}
]
# Dummy patient info / for Prompt 1
patient_profile = prompts_data["P1"]["Patient Profile"]
patient_info = (
    f"Sex: {patient_profile['Sex']}\n"
    f"Age: 68\n"
    f"Renal: eGFR 38\n"
    f"Smoking: Former smoker\n"
    f"Comorbidities: Type 2 diabetes, CKD stage 3, hypertension"
)

# Dummy patient info / for Prompt E
drug_list = prompts_data["PE"]["Drugs"]
formatted_drugs = "\n".join(f"- {drug}" for drug in drug_list)

# Construct full prompt for P4
prompt_text = (
    f"{prompts_data['PE']['Task']}\n\n"
    f"{formatted_drugs}\n\n"
)

# Get DeepSeek's response
print("DeepSeek output for PE:")
print(generate_response(prompt_text))
