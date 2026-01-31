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
    "software engineer",
    "backend",
    "frontend",
    "full stack",
    "python",
    "java",
    "golang",
    "node",
    "django",
    "flask",
    "fastapi",
    "devops",
    "sre",
    "kubernetes",
    "docker",
    "terraform",
    "aws",
    "gcp",
    "azure",
    "machine learning",
    "ml",
    "ai"
]


NON_TECH_KEYWORDS = [
    "support",
    "customer",
    "sales",
    "marketing",
    "recruiter",
    "designer",
    "content",
    "writer",
    "hr",
    "finance",
    "legal",
    "assistant"
]
ALLOWED_CATEGORIES = [
    # Core SWE
    "Back-End Programming",
    "Front-End Programming",
    "Full-Stack Programming",
    "Software Engineering",
    "Web Development",
    "Application Development",

    # DevOps / Cloud
    "DevOps and Sysadmin",
    "Cloud Infrastructure",
    "Site Reliability Engineering",
    "Platform Engineering",
    "Infrastructure Engineering",

    # Data / AI
    "AI / Machine Learning",
    "Data Engineering",
    "Data Science",
    "Applied Machine Learning",
    "MLOps",

    # QA / Testing
    "Quality Assurance",
    "Test Automation",
    "Software Testing",

    # Mobile
    "Mobile Development",
    "iOS Development",
    "Android Development",
    "Cross-Platform Development",

    # Security
    "Security Engineering",
    "Application Security",
    "Cloud Security",
    "DevSecOps",

    # Systems
    "Systems Programming",
    "Embedded Systems",
    "Firmware Development",
    "Operating Systems",

    # Distributed
    "Distributed Systems",
    "Microservices"
]

def clean_html(html_text):
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator=" ").strip()

def is_tech_job(title, category, description=""):
    text = f"{title} {description}".lower()

    # 1. Hard reject non-tech roles
    if any(word in text for word in NON_TECH_KEYWORDS):
        return False

    # 2. Category must be allowed OR strong keyword match
    category_ok = category in ALLOWED_CATEGORIES
    keyword_ok = any(word in text for word in TECH_KEYWORDS)

    return category_ok and keyword_ok



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
            raw_desc = entry.get("summary", "")
            clean_desc = clean_html(raw_desc)
            if is_tech_job(title, category, clean_desc):
                
                job_data = {
                    "job_id": entry.id,
                    "title": title,
                    "company": company,
                    "category": category,
                    "full_description": clean_desc,
                    "published_date": pd.to_datetime(entry.published, errors="coerce"),
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