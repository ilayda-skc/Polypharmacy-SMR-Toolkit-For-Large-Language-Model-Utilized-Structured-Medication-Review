Tools for drug‑burden assessment and Structured Medication Review (SMR) workflows in polypharmacy research. The codebase covers ACB score retrieval, BNF PDF parsing, burden matrix generation, and tokenizer experiments to support evidence‑based deprescribing and clinical decision support.

Contents

ACBscraper.py — automates Anticholinergic Cognitive Burden (ACB) lookups and saves per‑patient ACB mappings. Expects a CSV with a Medications column; writes patient_data_with_acb.csv. Uses Selenium + Chrome.

burden_matrix.py — builds a binary impairment matrix by scanning BNF text for each drug (flags: Renal, Hepatic, Cognitive/Other via regex e.g., “renal impairment”, “hepatic impairment”, “elderly”). Expects SMR.csv with Case and Current Medication.

pdf_parser.py — parses two‑column BNF PDFs, associates drugs found per patient, and extracts paragraphs containing BNF “grade letters” (default hijk). Expects SMR.csv (Case, Current Medication).

pdf_parser_by_burden.py — like above but also collects excerpts and computes a per‑drug Burden Score (= Renal + Hepatic + Cognitive), writing a readable text file per patient. Expects SMR.csv.

pdf_parser_by_medication.py — finds graded BNF passages for a patient’s medications (using grade letters hijk) and writes a per‑patient text report. Expects SMR.csv.

pdf_parser_by_condition.py — same pipeline but keyed on conditions. Builds Condition List from Current Medical History, searches BNF, and exports graded passages. Expects SMR.csv.

pdf_parser_synth_data.py — synthetic‑data variant. Expects synthdata.csv with PatientID and Medications; computes Renal/Hepatic/Cognitive‑Other burden + excerpts and writes a readable file.

Tokenizo_DeepSeek.py — minimal tokenizer experiment (Hugging Face AutoTokenizer w/ gpt2) to pre‑tokenize clinical phrases and count token frequencies.

Requirements

Python 3.9+

Core libraries:

PDF/text: pymupdf (fitz), re, pandas

Scraping (ACB): selenium, webdriver-manager, pandas

NLP demo: transformers (for Tokenizo_DeepSeek.py)
