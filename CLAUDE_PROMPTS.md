# Claude Prompts for Audience Builder

Use these prompts in Claude.ai to generate request files for the audience builder.

---

## Basic Lead List Request

**Prompt:**
```
Create a JSON request file for the BuzzLead audience-builder GitHub repo.

Audience: [DESCRIBE YOUR AUDIENCE]
Limit: [NUMBER OF LEADS]
Requested by: [YOUR NAME]

Use the ai_arc source and format it as a valid JSON file I can commit to the requests/ folder.
```

**Example:**
```
Create a JSON request file for the BuzzLead audience-builder GitHub repo.

Audience: CEOs and Founders at fintech companies with 50-200 employees in California
Limit: 500
Requested by: Sarah

Use the ai_arc source and format it as a valid JSON file I can commit to the requests/ folder.
```

**Claude will output:**
```json
{
  "source": "ai_arc",
  "audience_name": "fintech-ceos-california",
  "filters": {
    "job_titles": ["CEO", "Chief Executive Officer", "Founder", "Co-Founder"],
    "industries": ["Fintech", "Financial Technology", "Financial Services"],
    "company_size": "51-200",
    "location": "California"
  },
  "limit": 500,
  "requested_by": "Sarah",
  "notes": "Fintech CEOs and Founders in California for outbound campaign"
}
```

---

## VP of Sales Request

**Prompt:**
```
Create a JSON request file for BuzzLead audience-builder.

I need VP of Sales and Sales Directors at B2B SaaS companies, 100-500 employees, United States. Get me 300 leads.

My name is [YOUR NAME].
```

---

## Marketing Leaders Request

**Prompt:**
```
Create a JSON request file for BuzzLead audience-builder.

Target: CMOs, VP of Marketing, and Marketing Directors
Industry: E-commerce and DTC brands
Company size: 50-200 employees
Location: United States
Limit: 400
Requested by: [YOUR NAME]
```

---

## After Claude Generates the JSON

1. Copy the JSON output
2. Go to: https://github.com/[your-org]/audience-builder/tree/main/requests
3. Click **Add file** → **Create new file**
4. Name it something descriptive: `fintech-ceos-california-dec2024.json`
5. Paste the JSON
6. Click **Commit new file**
7. Wait 2-3 minutes
8. Check the `results/` folder for your CSV

---

## Quick Reference: Available Filters

| Filter | What to Say | Example Values |
|--------|-------------|----------------|
| Job Titles | "targeting CEOs, CTOs, and VPs" | CEO, CTO, VP of Sales, Founder |
| Industries | "at SaaS and fintech companies" | SaaS, Fintech, Healthcare, E-commerce |
| Company Size | "with 50-200 employees" | 1-10, 11-50, 51-200, 201-500, 500+ |
| Location | "in California" or "in the United States" | Any country, state, or city |
| Limit | "get me 500 leads" | 1-1000 |
