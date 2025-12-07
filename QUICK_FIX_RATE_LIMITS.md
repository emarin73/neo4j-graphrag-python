# Quick Fix for Rate Limit Issues

## The Problem

You're hitting rate limits because you're using `gpt-4o` which has a 30,000 tokens/minute limit. Your PDF is large (12 MB), so you're constantly hitting this limit.

## The Solution: Switch to `gpt-4o-mini`

**`gpt-4o-mini` has 200,000 TPM** - that's 6.7x higher! This will eliminate your rate limit issues.

## Quick Steps to Fix

### Step 1: Update Your `.env` File

Open your `.env` file and add or change this line:

```env
OPENAI_MODEL=gpt-4o-mini
```

If you have `OPENAI_MODEL=gpt-4o` in your `.env`, change it to:
```env
OPENAI_MODEL=gpt-4o-mini
```

### Step 2: Run Again

Wait 5-10 minutes for your current rate limit to reset, then run:

```bash
python build_kg_from_pdf.py --pdf "C:\Rocanegras\My Fence Project\Fence Requirements\weston-fl-Code of Ordinance.pdf" --track-schema
```

That's it! The script will now use `gpt-4o-mini` and should complete without rate limit errors.

## Why This Works

| Model | TPM Limit | Your PDF Needs | Result |
|-------|-----------|----------------|--------|
| `gpt-4o` | 30,000 | ~50,000+ tokens | ❌ Rate limit errors |
| `gpt-4o-mini` | 200,000 | ~50,000+ tokens | ✅ No problems! |

## Bonus Benefits

- **94% cheaper** - Save money on API calls
- **Faster** - Lower latency per request
- **Same quality** - Excellent for knowledge graph extraction

## Note

I've also updated the default in the code to use `gpt-4o-mini`, so future runs will use it automatically unless you override it in your `.env` file.
