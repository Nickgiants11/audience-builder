#!/usr/bin/env python3
"""
BuzzLead Audience Builder - Request Processor
Corrected for AI-Ark exact filter structure
"""

import os
import sys
import json
import csv
import httpx
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

AI_ARC_API_KEY = os.getenv("AI_ARC_API_KEY", "")
AI_ARC_PEOPLE_URL = "https://api.ai-ark.com/api/developer-portal/v1/people"


async def search_ai_arc_people(filters: Dict[str, Any], limit: int = 100) -> List[Dict]:
    if not AI_ARC_API_KEY:
        print("ERROR: AI_ARC_API_KEY not configured")
        return []
    
    headers = {
        "X-TOKEN": AI_ARC_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    contact = {}
    account = {}
    
    # CONTACT FILTERS
    if "seniority" in filters:
        contact["seniority"] = {
            "all": {
                "include": filters["seniority"]
            }
        }
    
    if "department" in filters:
        contact["departmentAndFunction"] = {
            "all": {
                "include": filters["department"]
            }
        }
    
    if "skills" in filters:
        contact["skill"] = {
            "any": {
                "include": filters["skills"]
            }
        }
    
    if "keywords" in filters:
        contact["keyword"] = {
            "any": {
                "include": filters["keywords"]
            }
        }
    
    # ACCOUNT FILTERS
    if "industries" in filters:
        account["industry"] = {
            "any": {
                "include": filters["industries"]
            }
        }
    
    if "company_size" in filters:
        size = filters["company_size"]
        size_mapping = {
            "1-10": {"start": 1, "end": 10},
            "1-50": {"start": 1, "end": 50},
            "1-100": {"start": 1, "end": 100},
            "11-50": {"start": 11, "end": 50},
            "51-200": {"start": 51, "end": 200},
            "201-500": {"start": 201, "end": 500},
            "501-1000": {"start": 501, "end": 1000},
            "1001-5000": {"start": 1001, "end": 5000},
            "5000+": {"start": 5001, "end": 100000}
        }
        if size in size_mapping:
            account["employeeSize"] = {
                "type": "RANGE",
                "range": [size_mapping[size]]
            }
    
    if "location" in filters:
        account["location"] = {
            "country": {
                "any": {
                    "include": [filters["location"]] if isinstance(filters["location"], str) else filters["location"]
                }
            }
        }
    
    if "technologies" in filters:
        account["technology"] = {
            "any": {
                "include": filters["technologies"]
            }
        }
    
    # Build payload
    payload = {
        "page": 0,
        "size": min(limit, 100)
    }
    
    if contact:
        payload["contact"] = contact
    if account:
        payload["account"] = account
    
    print(f"  API URL: {AI_ARC_PEOPLE_URL}")
    print(f"  Request payload: {json.dumps(payload, indent=2)}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(AI_ARC_PEOPLE_URL, headers=headers, json=payload)
            print(f"  Response status: {response.status_code}")
            print(f"  Response preview: {response.text[:1000]}...")
            
            response.raise_for_status()
            data = response.json()
            
            if "content" in data:
                results = data["content"]
                total = data.get("totalElements", len(results))
                print(f"  Total available: {total}, Retrieved: {len(results)}")
                return results
            return []
                
        except httpx.HTTPStatusError as e:
            print(f"  API Error: {e.response.status_code}")
            print(f"  Error body: {e.response.text}")
            return []
        except Exception as e:
            print(f"  Error: {str(e)}")
            return []


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
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
    if not leads:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            f.write("status,message\n")
            f.write("no_results,No leads found.\n")
        return
    
    flat_leads = [flatten_dict(lead) for lead in leads]
    all_fields = set()
    for lead in flat_leads:
        all_fields.update(lead.keys())
    
    priority = ["id", "identifier", "profile_first_name", "profile_last_name", 
                "profile_full_name", "profile_headline", "profile_title",
                "link_linkedin", "location_country", "location_state", "location_city",
                "industry", "company_summary_name", "department_seniority", "skills"]
    
    fieldnames = [f for f in priority if f in all_fields]
    fieldnames += sorted([f for f in all_fields if f not in priority])
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flat_leads)
    
    print(f"  Saved {len(leads)} leads to {output_path}")


async def process_request_file(request_path: str):
    request_file = Path(request_path)
    
    if not request_file.exists() or request_file.name.startswith("_"):
        return
    
    print(f"\n{'='*60}")
    print(f"Processing: {request_file.name}")
    print(f"{'='*60}")
    
    with open(request_file, "r") as f:
        request = json.load(f)
    
    if "processed_at" in request:
        print(f"  Already processed")
        return
    
    filters = request.get("filters", {})
    limit = request.get("limit", 100)
    audience_name = request.get("audience_name", request_file.stem)
    
    print(f"  Filters: {json.dumps(filters)}")
    print(f"  Limit: {limit}")
    
    results = await search_ai_arc_people(filters, limit)
    print(f"  Found {len(results)} leads")
    
    Path("results").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = Path("results") / f"{audience_name}-{timestamp}.csv"
    
    save_to_csv(results, output_path)
    
    request["processed_at"] = datetime.now().isoformat()
    request["result_file"] = str(output_path)
    request["result_count"] = len(results)
    
    with open(request_file, "w") as f:
        json.dump(request, f, indent=2)
    
    print(f"✅ Done! Results: {output_path}")


if __name__ == "__main__":
    import asyncio
    if len(sys.argv) < 2:
        sys.exit(1)
    asyncio.run(process_request_file(sys.argv[1]))
