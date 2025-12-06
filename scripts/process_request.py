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

# API Keys from environment
AI_ARC_API_KEY = os.getenv("AI_ARC_API_KEY", "")
AI_ARC_BASE_URL = os.getenv("AI_ARC_BASE_URL", "https://api.ai-ark.com/v1")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
CLAY_API_KEY = os.getenv("CLAY_API_KEY", "")
CLAY_BASE_URL = os.getenv("CLAY_BASE_URL", "https://api.clay.com/v1")


async def search_ai_arc(filters: Dict[str, Any], limit: int = 100) -> List[Dict]:
    """Search AI Arc for leads."""
    
    if not AI_ARC_API_KEY:
        print("ERROR: AI_ARC_API_KEY not configured")
        return []
    
    headers = {
        "Authorization": f"Bearer {AI_ARC_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {**filters, "limit": limit}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{AI_ARC_BASE_URL}/leads/search",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("leads", data.get("results", []))
        except Exception as e:
            print(f"AI Arc Error: {str(e)}")
            return []


def save_to_csv(leads: List[Dict], output_path: Path):
    """Save leads to CSV."""
    
    if not leads:
        print("No leads to save")
        return
    
    all_fields = set()
    for lead in leads:
        all_fields.update(lead.keys())
    
    priority_fields = [
        "first_name", "last_name", "email", "phone",
        "job_title", "company_name", "industry",
        "company_size", "location", "linkedin_url",
        "company_website", "revenue"
    ]
    
    fieldnames = [f for f in priority_fields if f in all_fields]
    fieldnames += sorted([f for f in all_fields if f not in priority_fields])
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)
    
    print(f"Saved {len(leads)} leads to {output_path}")


async def process_request_file(request_path: str):
    """Process a request file."""
    
    request_file = Path(request_path)
    
    if not request_file.exists():
        print(f"ERROR: File not found: {request_path}")
        return
    
    print(f"\nProcessing: {request_file.name}")
    
    with open(request_file, "r", encoding="utf-8") as f:
        request = json.load(f)
    
    source = request.get("source", "ai_arc")
    audience_name = request.get("audience_name", request_file.stem)
    filters = request.get("filters", {})
    limit = request.get("limit", 100)
    
    print(f"Source: {source}")
    print(f"Audience: {audience_name}")
    print(f"Limit: {limit}")
    
    results = []
    
    if source == "ai_arc":
        results = await search_ai_arc(filters, limit)
    else:
        print(f"Unknown source: {source}")
        return
    
    print(f"Found {len(results)} leads")
    
    # Save results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = results_dir / f"{audience_name}-{timestamp}.csv"
    
    save_to_csv(results, output_path)
    
    # Mark request as processed
    processed = {
        **request,
        "processed_at": datetime.now().isoformat(),
        "result_file": str(output_path),
        "result_count": len(results)
    }
    
    with open(request_file, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)
    
    print(f"✅ Done! Results: {output_path}")


if __name__ == "__main__":
    import asyncio
    
    if len(sys.argv) < 2:
        print("Usage: python process_request.py <request_file.json>")
        sys.exit(1)
    
    asyncio.run(process_request_file(sys.argv[1]))
