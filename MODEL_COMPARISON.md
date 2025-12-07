# OpenAI Model Comparison for Knowledge Graph Building

## Quick Answer: Should You Use `gpt-4o-mini`?

**Yes!** If you're hitting rate limits with `gpt-4o`, switching to `gpt-4o-mini` is highly recommended.

## Model Comparison

| Feature | gpt-4o | gpt-4o-mini | Winner |
|---------|--------|-------------|--------|
| **Rate Limit (TPM)** | 30,000 tokens/min | 200,000 tokens/min | ✅ gpt-4o-mini (6.7x higher) |
| **Rate Limit (RPM)** | ~50-100 requests/min | 500 requests/min | ✅ gpt-4o-mini (5-10x higher) |
| **Cost** | ~$2.50 per 1M tokens | ~$0.15 per 1M tokens | ✅ gpt-4o-mini (60x cheaper) |
| **Quality** | Excellent | Very Good | gpt-4o (slightly better) |
| **Speed** | Fast | Very Fast | ✅ gpt-4o-mini (faster) |
| **Best For** | Complex reasoning tasks | Knowledge extraction, structured tasks | Depends on use case |

## For Knowledge Graph Extraction

### ✅ **gpt-4o-mini is Recommended**

**Why?**
- **Much higher rate limits** - Won't hit 429 errors
- **Much cheaper** - Process more documents for less cost
- **Excellent quality** for structured extraction tasks
- **Faster processing** - Lower latency

**When to use gpt-4o?**
- Very complex legal/technical documents requiring deep reasoning
- When you need maximum accuracy and cost isn't a concern
- When processing small documents (rate limits won't matter)

## How to Switch Models

### Option 1: Using Environment Variable (Recommended)

Add to your `.env` file:

```env
OPENAI_MODEL=gpt-4o-mini
```

### Option 2: Command Line (if script supports it)

Currently the script uses environment variables. You can modify `OPENAI_MODEL` in your `.env` file.

## Rate Limit Comparison

### With gpt-4o (30k TPM)
- **Problem**: Processing a 100-page PDF = ~50,000 tokens
- **Result**: Hit rate limit after ~1 minute, need to wait or retry
- **Time**: Much longer due to rate limit delays

### With gpt-4o-mini (200k TPM)
- **Problem**: Same 100-page PDF = ~50,000 tokens
- **Result**: Well under limit, can process continuously
- **Time**: Much faster, no rate limit delays

## Cost Comparison Example

Processing a 500-page legal document:

| Model | Tokens | Cost (approx) | Rate Limit Issues? |
|-------|--------|---------------|-------------------|
| gpt-4o | ~250k tokens | $0.63 | ❌ Yes (multiple) |
| gpt-4o-mini | ~250k tokens | $0.04 | ✅ No issues |

**Savings: 94% cheaper with gpt-4o-mini!**

## Quality Comparison

For knowledge graph extraction (entities, relationships, patterns):

- **gpt-4o**: Excellent - Very accurate, handles complex nuances
- **gpt-4o-mini**: Very Good - Still very accurate for structured tasks

**Real-world experience**: For most legal documents and structured text, you'll see minimal quality difference between the two models for entity/relationship extraction.

## Recommendation

### Start with `gpt-4o-mini` because:
1. ✅ **Solves rate limit problems** - 200k TPM is plenty
2. ✅ **Much cheaper** - Process 60x more for the same cost
3. ✅ **Fast enough** - Quality is excellent for extraction tasks
4. ✅ **Production ready** - Used by many companies at scale

### Switch to `gpt-4o` if:
- You notice extraction quality issues
- You're processing very complex/ambiguous text
- Rate limits aren't a concern (small documents)
- Cost isn't a limiting factor

## Current Configuration

Your script defaults to `gpt-4o`. To switch:

1. Open your `.env` file
2. Add or modify:
   ```env
   OPENAI_MODEL=gpt-4o-mini
   ```
3. Run your script again - it will use the new model!

## Testing Both Models

You can test both models on the same PDF to compare:

```bash
# Test with gpt-4o-mini
OPENAI_MODEL=gpt-4o-mini python build_kg_from_pdf.py --pdf document.pdf

# Test with gpt-4o (if you want to compare)
OPENAI_MODEL=gpt-4o python build_kg_from_pdf.py --pdf document.pdf
```

Then compare the extracted entities and relationships in Neo4j to see if quality meets your needs.

## Summary

**For your use case (legal documents → knowledge graph):**

🎯 **Use `gpt-4o-mini`** - It will:
- Eliminate rate limit errors
- Process documents faster
- Cost 94% less
- Still provide excellent extraction quality

The higher rate limits (200k TPM) will let you process large PDFs without hitting limits!
