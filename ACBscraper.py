# -*- coding: utf-8 -*-
"""
Created on Mon Jun  9 14:55:07 2025

@author: HP
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import re
import time


def load_patient_data(csv_path):
    df = pd.read_csv(csv_path, encoding="latin1")
    df['Medication List'] = df['Medications'].apply(extract_drugs)
    return df

def clean_drug_name(name):
    name = re.sub(r'\b(tablet|capsule|inhaler|cream|gel|spray|solution|ointment|patch|drops|syrup|injection)\b', '', name, flags=re.IGNORECASE)
    return name.strip()

def extract_drugs(med_string):
    if pd.isna(med_string):
        return []

    # Replace newlines/semicolons with commas
    med_string = re.sub(r'[\n;]+\s*', ',', med_string).strip()
    med_string = re.sub(r'\s{2,}', ' ', med_string)

    seen = set()
    cleaned = []

    for item in med_string.split(','):
        # Remove trailing codes like (0406030B0) or (1234567)
        name = re.sub(r'\s*\(\s*\d{6,9}[A-Z0-9]*\s*\)\s*$', '', item.strip())
        name = name.strip()

        # Filter out pure codes
        if not name or re.fullmatch(r'\d{6,9}[A-Z0-9]*', name):
            continue

        name_lower = name.lower()
        if name_lower not in seen:
            cleaned.append(name)
            seen.add(name_lower)

    return cleaned


def get_acb_scores(drugs):
    chrome_options = Options()

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    acb_scores = {}
    not_found_drugs = []

    try:
        driver.get("https://www.acbcalc.com")
        time.sleep(3)

        for drug in drugs:
            retry_count = 0
            max_retries = 3
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    print(f"\nProcessing: {drug} (Attempt {retry_count + 1})")
                    drug = clean_drug_name(drug)
                    
                    # Get fresh reference to search box each time
                    search_box = wait.until(EC.visibility_of_element_located((By.ID, "med-textbox")))
                    
                    # Clear using multiple methods
                    search_box.clear()
                    driver.execute_script("arguments[0].value = '';", search_box)
                    time.sleep(0.5)
                    
                    # Perform search
                    search_box.send_keys(drug)
                    time.sleep(1.5)
                    
                    # Handle suggestions with stale element protection
                    try:
                        suggestion = wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".tt-suggestion"))
                        )
                        driver.execute_script("arguments[0].click();", suggestion)
                        time.sleep(1.5)
                    except:
                        search_box.send_keys(Keys.RETURN)
                        time.sleep(1.5)
                    
                    # Get score with refresh if stale
                    try:
                        score_elem = wait.until(
                            EC.visibility_of_element_located((By.CLASS_NAME, "score"))
                        )
                        score_text = score_elem.text.strip()
                        acb_scores[drug] = score_text if score_text else "0"
                        success = True
                    except:
                        driver.refresh()
                        time.sleep(2)
                        raise Exception("Score element not found")
                    
                    # Robust reset with recovery
                    try:
                        reset_btn = wait.until(
                            EC.element_to_be_clickable((By.ID, "resetMeds"))
                        )
                        driver.execute_script("arguments[0].click();", reset_btn)
                        time.sleep(1.5)
                        
                        # Verify reset
                        search_box = wait.until(EC.visibility_of_element_located((By.ID, "med-textbox")))
                        if search_box.get_attribute('value'):
                            driver.execute_script("arguments[0].value = '';", search_box)
                    except Exception as e:
                        print(f"Reset error, refreshing page: {str(e)}")
                        driver.refresh()
                        time.sleep(2)
                        
                except Exception as e:
                    print(f"Error processing {drug}: {repr(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        driver.refresh()
                        time.sleep(2)
                    else:
                        acb_scores[drug] = "Not found"
                        not_found_drugs.append(drug)

        if not_found_drugs:
            print("\nDrugs not found after retries:")
            for drug in not_found_drugs:
                print(f"- {drug}")

    except Exception as e:
        print(f"Fatal error: {repr(e)}")
    finally:
        driver.quit()

    return acb_scores



if __name__ == "__main__":
    df = load_patient_data("synthdata.csv")
    unique_drugs = list({drug for sublist in df['Medication List'] for drug in sublist})
    acb_scores = get_acb_scores(unique_drugs)

    
    df['ACB Scores'] = df['Medication List'].apply(
        lambda meds: {med: acb_scores.get(med, "Not found") for med in meds}
    )
    
    df.to_csv("patient_data_with_acb.csv", index=False)
    print("Results saved to patient_data_with_acb.csv")