# Getting Started with Neo4j GraphRAG - Knowledge Database Creation

This guide will help you create a knowledge database using Neo4j GraphRAG for Python.

## Prerequisites

Before you begin, ensure you have the following:

### 1. Neo4j Database

You need a running Neo4j instance. You have two options:

**Option A: Neo4j Desktop (Recommended for Development)**
- Download and install [Neo4j Desktop](https://neo4j.com/download/)
- Create a new database and start it
- Note your connection details (URI, username, password)

**Option B: Neo4j AuraDB (Cloud)**
- Sign up for free at [Neo4j AuraDB](https://neo4j.com/cloud/aura/)
- Create a new database instance
- Note your connection URI, username, and password

**Important:** The [APOC core library](https://neo4j.com/labs/apoc/) must be installed in your Neo4j instance. This is usually installed by default in Neo4j Desktop, but check if you're using a custom setup.

### 2. Python Environment

- Python 3.9 or higher (3.10+ recommended)
- pip or poetry for package management

### 3. API Keys

You'll need API keys for LLM and embedding services. At minimum, you need:

- **OpenAI API Key** (for LLM and embeddings) - Get one at [platform.openai.com](https://platform.openai.com)
- OR alternative LLM providers (Anthropic, Cohere, MistralAI, Vertex AI, Ollama)

### 4. Install the Package

Install the neo4j-graphrag package with your preferred LLM provider:

```bash
# For OpenAI
pip install "neo4j-graphrag[openai]"

# For other providers, see below:
# pip install "neo4j-graphrag[anthropic]"  # For Anthropic Claude
# pip install "neo4j-graphrag[cohere]"     # For Cohere
# pip install "neo4j-graphrag[mistralai]"  # For MistralAI
# pip install "neo4j-graphrag[google]"     # For Vertex AI
# pip install "neo4j-graphrag[ollama]"     # For Ollama (local)
```

For development from source (this repository):

```bash
poetry install --with dev
# or with OpenAI support
poetry install --with dev --extras openai
```

## Quick Start

### Step 1: Set Up Credentials

You need to configure your Neo4j connection and API keys. There are three ways to do this:

#### Option 1: Using a `.env` File (Recommended)

Create a `.env` file in your project root directory:

```env
# Neo4j Connection
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# OpenAI API Key (for LLM and embeddings)
OPENAI_API_KEY=your_openai_api_key
```

**For Neo4j AuraDB (Cloud):**
```env
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_aura_password
```

The `.env` file is already in `.gitignore`, so your credentials won't be committed to git.

**To use .env files, install python-dotenv:**
```bash
pip install python-dotenv
```

#### Option 2: System Environment Variables

Set these in your system before running scripts:

**Windows PowerShell:**
```powershell
$env:NEO4J_URI="neo4j://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="your_password"
$env:OPENAI_API_KEY="your_openai_api_key"
```

**Windows CMD:**
```cmd
set NEO4J_URI=neo4j://localhost:7687
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=your_password
set OPENAI_API_KEY=your_openai_api_key
```

**Linux/Mac:**
```bash
export NEO4J_URI="neo4j://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
export OPENAI_API_KEY="your_openai_api_key"
```

#### Option 3: Hardcode in Script (Not Recommended)

You can edit scripts directly, but this is only for quick testing. **Never commit credentials to git.**

### Step 2: Choose Your Approach

You have two main approaches for building a knowledge graph:

1. **SimpleKGPipeline** (Recommended for beginners)
   - Easy to use, streamlined interface
   - Good for most use cases
   - Can work with text or PDF files

2. **Pipeline** (Advanced)
   - Full control over each component
   - More customization options
   - Better for complex requirements

### Step 3: Define Your Schema

Before building your knowledge graph, decide what entities and relationships you want to extract:

- **Node Types (Entities)**: e.g., Person, Company, Location, Product
- **Relationship Types**: e.g., WORKS_FOR, LOCATED_IN, CREATED_BY
- **Patterns**: Valid combinations of relationships, e.g., (Person)-[WORKS_FOR]->(Company)

### Step 4: Run the Pipeline

#### Quick Start: Build from PDF

Use the ready-to-use script for PDF processing:

```bash
# Process a PDF with default schema
python build_kg_from_pdf.py --pdf path/to/your/document.pdf

# Process a PDF with automatic schema extraction
python build_kg_from_pdf.py --pdf path/to/your/document.pdf --auto-schema

# Add document metadata
python build_kg_from_pdf.py --pdf document.pdf --metadata author "John Doe" --metadata source "Internal"
```

#### Other Starter Scripts

You can also use these scripts from the examples:
- `examples/build_graph/simple_kg_builder_from_text.py` - For text input
- `examples/build_graph/simple_kg_builder_from_pdf.py` - For PDF files
- `examples/build_graph/automatic_schema_extraction/` - Automatic schema extraction

## Example Use Cases

### Example 1: Build from Text

```python
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM

# Define your schema
node_types = ["Person", "Company", "Location"]
relationship_types = ["WORKS_FOR", "LOCATED_IN"]
patterns = [
    ("Person", "WORKS_FOR", "Company"),
    ("Company", "LOCATED_IN", "Location"),
]

# Create pipeline and run
kg_builder = SimpleKGPipeline(
    llm=llm,
    driver=driver,
    embedder=embedder,
    schema={"node_types": node_types, "relationship_types": relationship_types, "patterns": patterns},
    from_pdf=False,
)
await kg_builder.run_async(text="Your text here...")
```

### Example 2: Build from PDF

```python
# Same setup as above, but:
kg_builder = SimpleKGPipeline(
    llm=llm,
    driver=driver,
    embedder=embedder,
    schema=...,
    from_pdf=True,  # Enable PDF processing
)
await kg_builder.run_async(file_path="path/to/document.pdf")
```

### Example 3: Automatic Schema Extraction

If you don't know what schema to use, you can let the LLM automatically extract it:

```python
# Don't provide a schema parameter
kg_builder = SimpleKGPipeline(
    llm=llm,
    driver=driver,
    embedder=embedder,
    from_pdf=False,
)
await kg_builder.run_async(text="Your text here...")
```

## Next Steps

1. **Explore Examples**: Check the `examples/` directory for more advanced use cases
2. **Customize Components**: See `examples/customize/` for customization options
3. **Query Your Graph**: After building, use retrievers to query your knowledge graph
4. **Build RAG Application**: Use GraphRAG for question-answering over your knowledge graph

## Common Issues

### APOC Not Installed
If you get errors about APOC, make sure it's installed in your Neo4j instance. In Neo4j Desktop, go to your database → Plugins → Install APOC.

### Connection Issues

**Missing Credentials:**
- Make sure you've set `NEO4J_PASSWORD` (required)
- Verify `NEO4J_URI` is set correctly
- Check that your `.env` file is in the project root directory
- If using system environment variables, ensure they're set in the same terminal session

**Connection Failed:**
- Verify your Neo4j URI format:
  - Local: `neo4j://localhost:7687` or `bolt://localhost:7687`
  - AuraDB: `neo4j+s://xxxxx.databases.neo4j.io`
- Check if your Neo4j database is running
- Verify credentials are correct (username and password)
- For AuraDB, ensure you're using the correct connection string from the dashboard
- Check firewall settings if connecting to a remote instance

**Common URI Formats:**
- Local Neo4j Desktop: `neo4j://localhost:7687`
- Local Docker: `neo4j://localhost:7687`
- Neo4j AuraDB Free: `neo4j+s://xxxxx.databases.neo4j.io`
- Neo4j AuraDB Enterprise: `neo4j+s://xxxxx.databases.neo4j.io`

### API Key Issues

**Missing API Key:**
- Set `OPENAI_API_KEY` in your `.env` file or as a system environment variable
- Verify the variable name is exactly `OPENAI_API_KEY` (case-sensitive)

**Invalid API Key:**
- Check that your API key is correct and hasn't expired
- Verify you have sufficient credits/quota in your OpenAI account
- Test your API key by making a simple API call outside of this project

**For Other LLM Providers:**
- Anthropic: Set `ANTHROPIC_API_KEY`
- Cohere: Set `COHERE_API_KEY`
- MistralAI: Set `MISTRAL_API_KEY`
- See examples in the `examples/customize/llms/` directory for configuration

## Resources

- [Official Documentation](https://neo4j.com/docs/neo4j-graphrag-python/)
- [Neo4j GraphRAG Blog Posts](https://neo4j.com/blog/graphrag-manifesto/)
- [Example Code](examples/)
- [Neo4j Community Forum](https://community.neo4j.com/)

## Support

- Check existing issues: [GitHub Issues](https://github.com/neo4j/neo4j-graphrag-python/issues)
- Ask questions: [Neo4j Community](https://community.neo4j.com/)
- Enterprise support: [Neo4j Support](http://support.neo4j.com/)
