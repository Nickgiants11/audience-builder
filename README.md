# audience-builder
Pull target audience lists from AI Arc, Clay, and other data sources - directly from Claude.ai.
# BuzzLead Audience Builder

Pull target audience lists from AI Arc, Clay, and other data sources - directly from Claude.ai.

## How It Works

1. **You ask Claude** for an audience (e.g., "Get me 500 fintech CEOs in California")
2. **Claude creates a request file** and commits it to this repo
3. **GitHub Action runs automatically** and calls the APIs
4. **Results appear in the `results/` folder** as a CSV within 2-3 minutes

---

## For List Building Team: How to Use

### Step 1: Ask Claude for an Audience

In Claude.ai, say something like:

> "I need to pull a list from AI Arc. Create a request file for 500 CEOs at fintech companies with 50-200 employees in the United States."

Or:

> "Create an audience request for VP of Sales at SaaS companies in California, limit 300."

### Step 2: Claude Will Create a Request File

Claude will generate a JSON file and commit it to the `requests/` folder. The file looks like this:

```json
{
  "source": "ai_arc",
  "audience_name": "fintech-ceos-us",
  "filters": {
    "job_titles": ["CEO", "Chief Executive Officer", "Founder"],
    "industries": ["Fintech", "Financial Services", "Financial Technology"],
    "company_size": "51-200",
    "location": "United States"
  },
  "limit": 500,
  "requested_by": "Troy",
  "notes": "For Q1 fintech campaign"
}
```

### Step 3: Wait 2-3 Minutes

The GitHub Action will:
- Detect the new request file
- Call the AI Arc API
- Save results to `results/[audience-name].csv`

### Step 4: Download Your List

Go to the `results/` folder in this repo and download your CSV.

---

## Request Templates

### Basic AI Arc Request
```json
{
  "source": "ai_arc",
  "audience_name": "descriptive-name-here",
  "filters": {
    "job_titles": ["CEO", "CTO", "VP of Sales"],
    "industries": ["SaaS", "Technology"],
    "company_size": "51-200",
    "location": "United States"
  },
  "limit": 500
}
```

### Available Filters

| Filter | Options | Example |
|--------|---------|---------|
| `job_titles` | Any job titles | `["CEO", "Founder", "VP Sales"]` |
| `industries` | Any industries | `["Fintech", "Healthcare", "SaaS"]` |
| `company_size` | `"1-10"`, `"11-50"`, `"51-200"`, `"201-500"`, `"500+"` | `"51-200"` |
| `location` | Country, state, or city | `"California"` or `"United States"` |
| `limit` | 1-1000 | `500` |

### Available Sources

| Source | What It Does |
|--------|-------------|
| `ai_arc` | Pull leads from AI Arc database |
| `clay` | Enrich companies via Clay |
| `serper` | Search Google for company info |

---

## Folder Structure

```
audience-builder/
├── requests/           # Put new request files here
│   └── example.json
├── results/            # Completed lists appear here
│   └── example.csv
├── scripts/            # API processing scripts
│   └── process_request.py
├── .github/
│   └── workflows/
│       └── process-audience.yml
└── README.md
```

---

## For Admins: Setup Instructions

See [SETUP.md](SETUP.md) for how to configure API keys and deploy this repo.
