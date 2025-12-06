# Admin Setup Guide

This guide explains how to set up the BuzzLead Audience Builder repository.

## Step 1: Create the GitHub Repository

1. Go to https://github.com/new
2. Name it `audience-builder` (or whatever you prefer)
3. Set it to **Private** (important - contains API workflows)
4. Create the repository

## Step 2: Upload These Files

Upload all the files from this folder to your new repo:
- `README.md`
- `SETUP.md` (this file)
- `.gitignore`
- `scripts/process_request.py`
- `requests/_example-request.json`
- `requests/_template-vp-sales.json`
- `.github/workflows/process-audience.yml`

You can do this via the GitHub web interface or by cloning and pushing.

## Step 3: Configure GitHub Secrets

This is the most important step. Your API keys are stored securely in GitHub Secrets.

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** for each of these:

| Secret Name | Value |
|-------------|-------|
| `AI_ARC_API_KEY` | `b51be034b8b4417ba755814fb6d5bc64` |
| `AI_ARC_BASE_URL` | `https://api.ai-ark.com/v1` |
| `SERPER_API_KEY` | `687524857dd97ed5a13d7bcbf80b7a5986d3ccc7` |
| `CLAY_API_KEY` | `816653070f1038edd1ca` |
| `CLAY_BASE_URL` | `https://api.clay.com/v1` |
| `OPENROUTER_API_KEY` | `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` |
| `LEADMAGIC_API_KEY` | `3CJPXMhKXkrTJ7GmXSAUgBnws6Aqrqcf` |
| `FINDYMAIL_API_KEY` | `aGCPIiNT6luxnCPjCToZVYQ2FJhqOQ5gcDSj6qrM24fce8e5` |

## Step 4: Enable GitHub Actions

1. Go to your repo → **Actions** tab
2. If prompted, click **I understand my workflows, go ahead and enable them**

## Step 5: Create Results Folder

Create an empty `results/` folder with a `.gitkeep` file:

1. In your repo, click **Add file** → **Create new file**
2. Name it `results/.gitkeep`
3. Commit it

## Step 6: Test It

1. Create a test request file in `requests/` folder:
   - Click **Add file** → **Create new file**
   - Name it `requests/test-request.json`
   - Paste this content:

```json
{
  "source": "ai_arc",
  "audience_name": "test-ceos",
  "filters": {
    "job_titles": ["CEO"],
    "industries": ["Technology"],
    "location": "United States"
  },
  "limit": 10,
  "requested_by": "Admin Test"
}
```

2. Commit the file
3. Go to **Actions** tab and watch the workflow run
4. After 1-2 minutes, check the `results/` folder for your CSV

## Step 7: Grant Team Access

1. Go to **Settings** → **Collaborators and teams**
2. Add your team members with **Write** access (so they can create request files)

---

## How Team Members Use It

Once set up, team members can:

### Option A: Create Request Files Manually

1. Go to `requests/` folder
2. Click **Add file** → **Create new file**
3. Paste their request JSON
4. Commit → Action runs → Results appear

### Option B: Ask Claude to Create the Request

In Claude.ai, they can say:

> "Create a GitHub request file for the BuzzLead audience-builder repo. I need 500 CEOs at healthcare companies with 100-500 employees in Texas."

Claude will generate the JSON they can paste into the repo.

---

## Troubleshooting

### Action failed with "API key not configured"
- Check that all secrets are added correctly in Settings → Secrets
- Secret names must match exactly (case-sensitive)

### Action didn't trigger
- Make sure the file is in the `requests/` folder
- File must end in `.json`
- Check the Actions tab for any errors

### Results file is empty
- Check the Action logs for API errors
- Verify the API key is correct
- Check if you've hit rate limits

---

## Costs

Each API call has a cost. Here's a rough estimate per 1,000 contacts:

| API | Cost |
|-----|------|
| AI Arc | ~$5-10 |
| Serper | ~$1-2 |
| Clay | ~$10-20 |

Monitor your usage in each platform's dashboard.
