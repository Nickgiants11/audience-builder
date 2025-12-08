#!/usr/bin/env python3
"""
BuzzLead Audience Builder - Request Processor
Fixed for AI-Ark People Search API
"""

import os
import sys
import json
import csv
import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# API Keys from environment
AI_ARC_API_KEY = os.getenv("AI_ARC_API_KEY", "")

# AI-Ark API endpoints
AI_ARC_PEOPLE_URL = "https://api.ai-ark.com/api/developer-portal/v1/people"


async def search_ai_arc_people(filters: Dict[str, Any], limit: int = 100) -> List[Dict]:
    """Search AI-Ark for people/contacts."""
    
    if not AI_ARC_API_KEY:
        print("ERROR: AI_ARC_API_KEY not configured")
        return []
    
    headers = {
        "X-TOKEN": AI_ARC_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    # Build AI-Ark format request body
    contact = {}
    account = {}
    
    # Contact filters
    if "job_titles" in filters:
        contact["current_title"] = filters["job_titles"]
    
    if "seniority" in filters:
        contact["seniority"] = filters["seniority"]
    
    if "location" in filters:
        contact["location"] = {"country": filters["location"]}
    
    # Account filters
    if "industries" in filters:
        account["industry"] = filters["industries"]
    
    if "company_size" in filters:
        size = filters["company_size"]
        size_mapping = {
            "1-10": {"start": 1, "end": 10},
            "11-50": {"start": 11, "end": 50},
            "51-200": {"start": 51, "end": 200},
            "201-500": {"start": 201, "end": 500},
            "501-1000": {"start": 501, "end": 1000},
            "1001-5000": {"start": 1001, "end": 5000},
            "5000+": {"start": 5001, "end": 100000}
        }
        if size in size_mapping:
            account["staff"] = size_mapping[size]
    
    # Build payload - use correct AI-Ark format
    payload = {
        "page": 0,
        "size": min(limit, 100)
    }
    
    # Only add contact/account if they have values
    if contact:
        payload["contact"] = contact
    if account:
        payload["account"] = account
    
    print(f"  API URL: {AI_ARC_PEOPLE_URL}")
    print(f"  Request payload: {json.dumps(payload, indent=2)}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                AI_ARC_PEOPLE_URL,
                headers=headers,
                json=payload
            )
            
            print(f"  Response status: {response.status_code}")
            
            response_text = response.text
            print(f"  Response preview: {response_text[:1000]}...")
            
            response.raise_for_status()
            data = response.json()
            
            # AI-Ark returns data in "content" array
            if "content" in data:
                results = data["content"]
                total = data.get("totalElements", len(results))
                pages = data.get("totalPages", 1)
                print(f"  Total available: {total}, Pages: {pages}, Retrieved: {len(results)}")
                return results
            else:
                print(f"  Unknown response structure. Keys: {data.keys()}")
                return []
                
        except httpx.HTTPStatusError as e:
            print(f"  API Error: {e.response.status_code}")
            print(f"  Error body: {e.response.text}")
            return []
        except Exception as e:
            print(f"  Error: {str(e)}")
            return []


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Flatten nested dictionaries for CSV export."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            if v and isinstance(v[0], dict):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, ", ".join(str(x) for x in v)))
        else:
            items.append((new_key, v))
    return dict(items)


def save_to_csv(leads: List[Dict], output_path: Path):
    """Save leads to CSV."""
    
    if not leads:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            f.write("status,message\n")
            f.write("no_results,No leads found matching your criteria.\n")
        print(f"  Created empty results file: {output_path}")
        return
    
    # Flatten nested data
    flat_leads = [flatten_dict(lead) for lead in leads]
    
    all_fields = set()
    for lead in flat_leads:
        all_fields.update(lead.keys())
    
    # Priority fields based on AI-Ark response structure
    priority_fields = [
        "id", "identifier",
        "profile_first_name", "profile_last_name", "profile_full_name",
        "profile_headline", "profile_title",
        "link_linkedin",
        "location_country", "location_state", "location_city", "location_default",
        "industry",
        "company_summary_name", "company_link_domain", "company_link_website",
        "department_seniority", "department_functions",
        "skills"
    ]
    
    fieldnames = [f for f in priority_fields if f in all_fields]
    fieldnames += sorted([f for f in all_fields if f not in priority_fields])
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for lead in flat_leads:
            writer.writerow(lead)
    
    print(f"  Saved {len(leads)} leads to {output_path}")


async def process_request_file(request_path: str):
    """Process a request file."""
    
    request_file = Path(request_path)
    
    if not request_file.exists():
        print(f"ERROR: File not found: {request_path}")
        return
    
    if request_file.name.startswith("_"):
        print(f"Skipping template file: {request_file.name}")
        return
    
    print(f"\n{'='*60}")
    print(f"Processing: {request_file.name}")
    print(f"{'='*60}")
    
    with open(request_file, "r", encoding="utf-8") as f:
        request = json.load(f)
    
    if "processed_at" in request:
        print(f"  Already processed at {request['processed_at']}")
        return
    
    source = request.get("source", "ai_arc")
    audience_name = request.get("audience_name", request_file.stem)
    filters = request.get("filters", {})
    limit = request.get("limit", 100)
    
    print(f"  Source: {source}")
    print(f"  Audience: {audience_name}")
    print(f"  Filters: {json.dumps(filters)}")
    print(f"  Limit: {limit}")
    
    results = []
    
    if source == "ai_arc":
        results = await search_ai_arc_people(filters, limit)
    else:
        print(f"  Unknown source: {source}")
        return
    
    print(f"  Found {len(results)} leads")
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = results_dir / f"{audience_name}-{timestamp}.csv"
    
    save_to_csv(results, output_path)
    
    processed = {
        **request,
        "processed_at": datetime.now().isoformat(),
        "result_file": str(output_path),
        "result_count": len(results)
    }
    
    with open(request_file, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)
    
    print(f"\n✅ Done! Results: {output_path}")


if __name__ == "__main__":
    import asyncio
    
    if len(sys.argv) < 2:
        print("Usage: python process_request.py <request_file.json>")
        sys.exit(1)
    
    asyncio.run(process_request_file(sys.argv[1]))
