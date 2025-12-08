#!/usr/bin/env python3
"""
BuzzLead Audience Builder - Request Processor
"""

import os
import sys
import json
import csv
import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

AI_ARC_API_KEY = os.getenv("AI_ARC_API_KEY", "")
AI_ARC_PEOPLE_URL = "https://api.ai-ark.com/api/developer-portal/v1/people"


async def search_ai_arc_people(filters: Dict[str, Any], limit: int = 100) -> List[Dict]:
    if not AI_ARC_API_KEY:
        print("ERROR: AI_ARC_API_KEY not configured")
        return []

    headers = {
        "X-TOKEN": AI_ARC_API_KEY,
        "Content-Type": "application/json"
    }

    contact_filters = {}
    account_filters = {}

    if "job_titles" in filters:
        contact_filters["current_title"] = filters["job_titles"]

    if "industries" in filters:
        account_filters["industry"] = filters["industries"]

    if "company_size" in filters:
        size = filters["company_size"]
        size_mapping = {
            "1-10": {"min": 1, "max": 10},
            "11-50": {"min": 11, "max": 50},
            "51-200": {"min": 51, "max": 200},
            "201-500": {"min": 201, "max": 500},
            "500+": {"min": 500, "max": 10000}
        }
        if size in size_mapping:
            account_filters["employee_size"] = size_mapping[size]

    if "location" in filters:
        contact_filters["location"] = filters["location"]
        account_filters["location"] = filters["location"]

    payload = {
        "page_size": min(limit, 100),
        "page": 1
    }

    if contact_filters:
        payload["contact_filters"] = contact_filters
    if account_filters:
        payload["account_filters"] = account_filters

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
            print(f"  Response preview: {response_text[:500]}")
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                return data
            elif "data" in data:
                return data["data"]
            elif "results" in data:
                return data["results"]
            elif "people" in data:
                return data["people"]
            else:
                return [data] if data else []

        except httpx.HTTPStatusError as e:
            print(f"  API Error: {e.response.status_code}")
            print(f"  Error body: {e.response.text}")
            return []
        except Exception as e:
            print(f"  Error: {str(e)}")
            return []


def save_to_csv(leads: List[Dict], output_path: Path):
    if not leads:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            f.write("status,message\n")
            f.write("no_results,No leads found. Check Actions logs.\n")
        print(f"  Created empty results file: {output_path}")
        return

    all_fields = set()
    for lead in leads:
        if isinstance(lead, dict):
            all_fields.update(lead.keys())

    priority_fields = [
        "first_name", "last_name", "full_name", "name",
        "email", "work_email", "personal_email",
        "phone", "mobile_phone", "direct_phone",
        "title", "job_title", "current_title",
        "company", "company_name", "organization",
        "industry", "employee_count", "company_size",
        "location", "city", "state", "country",
        "linkedin", "linkedin_url", "website", "domain"
    ]

    fieldnames = [f for f in priority_fields if f in all_fields]
    fieldnames += sorted([f for f in all_fields if f not in priority_fields])

    if not fieldnames:
        fieldnames = ["raw_data"]
        leads = [{"raw_data": json.dumps(lead)} for lead in leads]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            if isinstance(lead, dict):
                writer.writerow(lead)

    print(f"  Saved {len(leads)} leads to {output_path}")


async def process_request_file(request_path: str):
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
    print(f"  Limit: {limit}")

    results = []
    if source == "ai_arc":
        results = await search_ai_arc_people(filters, limit)

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
