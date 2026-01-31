import feedparser
import requests
import pandas as pd
import io
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup 
from datetime import datetime, timezone


# --- CONFIGURATION ---
RSS_URL = "https://weworkremotely.com/remote-jobs.rss"
DATA_FILE = "wwr_tech_jobs.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Define what counts as a "Tech Job"
TECH_KEYWORDS = [
    "engineer", "developer", "programmer", "software", "data", 
    "devops", "sre", "cloud", "backend", "frontend", "full stack",
    "machine learning", "ai", "product manager", "qa", "security"
]

NON_TECH_KEYWORDS = [
    "sales", "marketing", "customer support", "hr", "writer", 
    "executive assistant", "finance", "legal", "account executive"
]

def clean_html(html_text):
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator=" ").strip()

def is_tech_job(title, category):
    title_lower = title.lower()
    category_lower = category.lower()
    
    if any(word in title_lower for word in NON_TECH_KEYWORDS):
        return False
        
    if "programming" in category_lower or "devops" in category_lower or "design" in category_lower:
        return True
        
    if any(word in title_lower for word in TECH_KEYWORDS):
        return True
        
    return False

def fetch_with_retry(url, retries=3, backoff=5):
    """
    Tries to download the URL up to 'retries' times.
    Waits 'backoff' seconds between failures.
    """
    for attempt in range(retries):
        try:
            # INCREASED TIMEOUT TO 30 SECONDS
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status() # Check for HTTP errors (404, 500)
            return response
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print(f"   Retrying in {backoff} seconds...")
                time.sleep(backoff)
            else:
                raise e # If all retries fail, crash the program

def fetch_and_save():
    print(f"[{datetime.now()}] Fetching and Filtering Tech jobs...")
    
    try:
        # USE THE NEW RETRY FUNCTION
        response = fetch_with_retry(RSS_URL)
        feed = feedparser.parse(io.BytesIO(response.content))
        
        new_jobs = []
        for entry in feed.entries:
            # Clean Title
            raw_title = entry.title
            company = entry.get("author")
            if (not company or company == "Unknown") and ":" in raw_title:
                parts = raw_title.split(":", 1)
                company = parts[0].strip()
                title = parts[1].strip()
            else:
                title = raw_title
                company = company if company else "Unknown"
            
            # Get Category
            category = entry.get("category", "Uncategorized")
            
            # --- FILTER LOGIC ---
            if is_tech_job(title, category):
                raw_desc = entry.get("summary", "")
                clean_desc = clean_html(raw_desc)
                
                job_data = {
                    "job_id": entry.id,
                    "title": title,
                    "company": company,
                    "category": category,
                    "full_description": clean_desc,
                    "published_date": entry.published,
                    "link": entry.link,
                    "fetched_at": datetime.now().isoformat()
                }
                new_jobs.append(job_data)
            
        print(f"-> Parsed {len(new_jobs)} TECH jobs (Filtered out non-tech).")

        # Database Logic
        if os.path.exists(DATA_FILE):
            existing_df = pd.read_csv(DATA_FILE)
            existing_ids = set(existing_df['job_id'].astype(str))
        else:
            existing_df = pd.DataFrame()
            existing_ids = set()

        unique_jobs = [job for job in new_jobs if str(job['job_id']) not in existing_ids]

        if unique_jobs:
            new_df = pd.DataFrame(unique_jobs)
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)

            # Dataset-level last updated timestamp (UTC)
            updated_df["dataset_last_updated_utc"] = datetime.now(timezone.utc).isoformat()

            updated_df.to_csv(DATA_FILE, index=False)

            print(f"✅ SUCCESS: Added {len(unique_jobs)} new TECH jobs.")
        else:
            # Still update dataset timestamp even if no new jobs
            existing_df["dataset_last_updated_utc"] = datetime.now(timezone.utc).isoformat()
            existing_df.to_csv(DATA_FILE, index=False)
            print("✅ No new tech jobs found, timestamp updated.")


    except Exception as e:
        print(f"❌ CRITICAL ERROR: Could not fetch data after 3 attempts. \nDetails: {e}")


if __name__ == "__main__":
    fetch_and_save()