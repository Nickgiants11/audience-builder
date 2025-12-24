#!/usr/bin/env python3
"""
Lookalike Finder
DiscoLike company discovery → AI Ark people enrichment → CSV for Clay
"""

import requests
import csv
import sys
import os
from datetime import datetime
from typing import List, Dict
from time import sleep

# =============================================================================
# CONFIGURATION
# =============================================================================

# API Keys from environment variables
DISCOLIKE_API_KEY = os.environ.get("DISCOLIKE_API_KEY", "")
AIARK_API_KEY = os.environ.get("AIARK_API_KEY", "")

DISCOLIKE_BASE_URL = "https://api.discolike.com/v1"
AIARK_BASE_URL = "https://api.ai-ark.com/api/developer-portal/v1"

# Company Filters
FILTERS = {
    "country": "US",
    "employee_min": 5,
    "employee_max": 100,
}

# Target Titles for People Search
TARGET_SENIORITIES = ["C-Level", "VP", "Director", "Owner", "Founder"]
TARGET_DEPARTMENTS = ["Executive", "Sales", "Business Development", "Marketing", "Management"]

DEFAULT_COMPANY_LIMIT = 100
RATE_LIMIT_DELAY = 0.2


# =============================================================================
# DISCOLIKE API
# =============================================================================

def discolike_headers():
    return {"x-discolike-key": DISCOLIKE_API_KEY}


def find_companies_by_icp(icp_text: str, limit: int = DEFAULT_COMPANY_LIMIT) -> List[Dict]:
    """Find companies using ICP text description."""
    endpoint = f"{DISCOLIKE_BASE_URL}/discover"
    
    params = {
        "country": FILTERS["country"],
        "min_similarity": 50,
        "max_records": limit,
        "redirect": 1,
        "icp_text": icp_text,
    }
    
    try:
        print(f"Calling DiscoLike API...")
        print(f"ICP: {icp_text[:80]}...")
        response = requests.get(endpoint, headers=discolike_headers(), params=params, timeout=120)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            companies = data if isinstance(data, list) else []
            if companies:
                print(f"Found {len(companies)} companies!")
                return companies[:limit]
            else:
                print("No companies returned")
        elif response.status_code == 401:
            print("Authentication failed - check DISCOLIKE_API_KEY")
        else:
            print(f"Error: {response.status_code} - {response.text[:300]}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    return []


# =============================================================================
# AI ARK API
# =============================================================================

def aiark_headers():
    return {
        "Content-Type": "application/json",
        "x-api-key": AIARK_API_KEY,
    }


def find_people_at_company(domain: str) -> List[Dict]:
    """Find decision-makers at a company."""
    endpoint = f"{AIARK_BASE_URL}/people"
    
    payload = {
        "account_filter": {"domain": domain},
        "contact_filter": {
            "seniority": TARGET_SENIORITIES,
            "department": TARGET_DEPARTMENTS,
        },
        "page_size": 20,
        "page": 1
    }
    
    try:
        response = requests.post(endpoint, headers=aiark_headers(), json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("results", data.get("people", data.get("data", [])))
    except:
        pass
    return []


# =============================================================================
# DATA EXTRACTION
# =============================================================================

def extract_company(company: Dict) -> Dict:
    """Extract company info from DiscoLike response."""
    address = company.get("address", {}) or {}
    
    linkedin = ""
    social_urls = company.get("social_urls", []) or []
    if isinstance(social_urls, list):
        for url in social_urls:
            if url and "linkedin.com" in str(url).lower():
                linkedin = url
                break
    
    return {
        "company_name": company.get("name", ""),
        "company_domain": company.get("domain", ""),
        "company_linkedin": linkedin,
        "employees": company.get("employees", ""),
        "city": address.get("city", ""),
        "state": address.get("state", ""),
    }


def extract_person(person: Dict) -> Dict:
    """Extract person info from AI Ark response."""
    full_name = person.get("name", person.get("full_name", ""))
    first_name = person.get("first_name", "")
    last_name = person.get("last_name", "")
    
    if full_name and not first_name:
        parts = full_name.split(" ", 1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""
    
    return {
        "first_name": first_name,
        "last_name": last_name,
        "title": person.get("title", person.get("job_title", "")),
        "person_linkedin": person.get("linkedin_url", person.get("linkedin", "")),
    }


# =============================================================================
# MAIN WORKFLOW
# =============================================================================

def run_search(icp_text: str, limit: int = DEFAULT_COMPANY_LIMIT, skip_people: bool = False) -> str:
    """Main workflow."""
    print("=" * 60)
    print("LOOKALIKE FINDER")
    print("=" * 60)
    print(f"ICP: {icp_text}")
    print(f"Limit: {limit}")
    print(f"People enrichment: {'Disabled' if skip_people else 'Enabled'}")
    print()
    
    # Step 1: Find companies
    companies = find_companies_by_icp(icp_text, limit)
    
    if not companies:
        print("No companies found.")
        return ""
    
    # Step 2: Process and optionally enrich
    results = []
    total = len(companies)
    
    if skip_people:
        print(f"Processing {total} companies (no enrichment)...")
        for company in companies:
            info = extract_company(company)
            results.append({
                **info,
                "first_name": "",
                "last_name": "",
                "title": "",
                "person_linkedin": "",
            })
    else:
        print(f"Finding decision-makers at {total} companies...")
        for i, company in enumerate(companies):
            info = extract_company(company)
            domain = info["company_domain"]
            
            if not domain:
                continue
            
            if (i + 1) % 25 == 0 or i == 0:
                print(f"Processing {i + 1}/{total}...")
            
            people = find_people_at_company(domain)
            
            if people:
                for person in people:
                    person_info = extract_person(person)
                    results.append({**info, **person_info})
            else:
                results.append({
                    **info,
                    "first_name": "",
                    "last_name": "",
                    "title": "",
                    "person_linkedin": "",
                })
            
            sleep(RATE_LIMIT_DELAY)
    
    # Step 3: Export CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lookalikes_{timestamp}.csv"
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "company_name", "company_domain", "company_linkedin",
            "employees", "city", "state",
            "first_name", "last_name", "title", "person_linkedin"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({k: v for k, v in row.items() if k in fieldnames})
    
    print()
    print("=" * 60)
    print("SUCCESS!")
    print(f"Companies: {len(companies)}")
    print(f"Total rows: {len(results)}")
    print(f"CSV: {filename}")
    print("=" * 60)
    
    return filename


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lookalike_finder.py <icp_text> --icp [--limit N] [--skip-people]")
        sys.exit(1)
    
    icp_text = sys.argv[1]
    limit = DEFAULT_COMPANY_LIMIT
    skip_people = "--skip-people" in sys.argv
    
    if "--limit" in sys.argv:
        try:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        except:
            pass
    
    if not DISCOLIKE_API_KEY:
        print("Error: DISCOLIKE_API_KEY environment variable not set")
        sys.exit(1)
    
    run_search(icp_text, limit, skip_people)
