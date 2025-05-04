import requests
import json
import time
import os
from datetime import datetime

# Configuration
EINS_TO_PROCESS = ["741152597", "530196605", "941156365"]
OUTPUT_DIR = r"D:\icd-10\forcast"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# API endpoints
BASE_URL = "https://projects.propublica.org/nonprofits/api/v2"
ORGANIZATION_URL = f"{BASE_URL}/organizations/{{ein}}.json"
FILINGS_LIST_URL = f"{BASE_URL}/organizations/{{ein}}/filings.json"
FILING_URL = f"{BASE_URL}/filings/{{filing_id}}.json"

def save_data(ein, data_type, data):
    """Save data to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"{ein}_{data_type}_{timestamp}.json")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filename
    except Exception as e:
        print(f"❌ Failed to save {data_type} data: {str(e)}")
        return None

def get_organization_data(ein):
    """Get organization metadata"""
    url = ORGANIZATION_URL.format(ein=ein)
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        print(f"⚠️ Organization endpoint returned HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️ Error fetching organization data: {str(e)}")
    return None

def get_available_filings(ein):
    """Try multiple methods to get filing information"""
    # Method 1: Standard filings endpoint
    url = FILINGS_LIST_URL.format(ein=ein)
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("filings"):
                return data["filings"]
    except Exception as e:
        print(f"⚠️ Filings list endpoint failed: {str(e)}")
    
    # Method 2: Search for recent filings
    search_url = f"https://projects.propublica.org/nonprofits/api/v2/search.json?q=ein:{ein}"
    try:
        response = requests.get(search_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("organizations"):
                for org in data["organizations"]:
                    if org.get("filings"):
                        return org["filings"]
    except Exception as e:
        print(f"⚠️ Search endpoint failed: {str(e)}")
    
    return None

# Main processing loop
for ein in EINS_TO_PROCESS:
    print(f"\n🔍 Processing EIN: {ein}")
    
    # Step 1: Get organization data
    org_data = get_organization_data(ein)
    if not org_data:
        print(f"❌ Could not retrieve organization data for EIN {ein}")
        continue
    
    org_name = org_data.get("organization", {}).get("name", "Unknown")
    print(f"Organization: {org_name}")
    
    # Save organization data regardless of filings
    org_filename = save_data(ein, "organization", org_data)
    if org_filename:
        print(f"✅ Saved organization data to {org_filename}")
    
    # Step 2: Attempt to get filings
    filings = get_available_filings(ein)
    if not filings:
        print("⚠️ No filings found through any method")
        continue
    
    print(f"Found {len(filings)} potential filings")
    
    # Step 3: Try to get the most recent filing
    for i, filing in enumerate(filings[:3]):  # Try first 3 filings
        filing_id = filing.get("filing_id")
        if not filing_id:
            continue
            
        print(f"Attempting filing {i+1}: ID {filing_id}")
        url = FILING_URL.format(filing_id=filing_id)
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                filing_data = response.json()
                filename = save_data(ein, f"filing_{filing_id}", filing_data)
                if filename:
                    print(f"✅ Successfully saved filing to {filename}")
                    break  # Stop after first successful filing
            else:
                print(f"⚠️ Filing endpoint returned HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error fetching filing: {str(e)}")
        
        time.sleep(1)  # Be gentle with the API

print("\n🏁 Processing complete")