# Next Steps - Getting Started with Neo4j GraphRAG from PDF

## Quick Start Checklist

### ✅ Step 1: Install Dependencies

Make sure you have the required packages installed:

```bash
# Install neo4j-graphrag with OpenAI support
pip install "neo4j-graphrag[openai]"

# Install python-dotenv for .env file support
pip install python-dotenv
```

### ✅ Step 2: Set Up Neo4j Database

Choose one option:

**Option A: Neo4j Desktop (Recommended for Development)**
1. Download and install [Neo4j Desktop](https://neo4j.com/download/)
2. Create a new database
3. Start the database
4. Note your password (set during database creation)
5. Make sure APOC plugin is installed (usually automatic)

**Option B: Neo4j AuraDB (Cloud)**
1. Sign up at [Neo4j AuraDB](https://neo4j.com/cloud/aura/)
2. Create a free database instance
3. Copy your connection URI and password from the dashboard

### ✅ Step 3: Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (you'll only see it once)

### ✅ Step 4: Create Your .env File

1. Copy `ENV_TEMPLATE.txt` to create `.env` file in the project root:

```bash
# Windows PowerShell
Copy-Item ENV_TEMPLATE.txt .env

# Windows CMD
copy ENV_TEMPLATE.txt .env

# Linux/Mac
cp ENV_TEMPLATE.txt .env
```

2. Edit `.env` file and replace placeholders with your actual values:

```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_actual_password
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=your_actual_openai_key
```

**Important:** Never commit your `.env` file to git! (It's already in .gitignore)

### ✅ Step 5: Prepare Your PDF

Place your PDF file somewhere accessible, or note its full path.

### ✅ Step 6: Build Your Knowledge Graph

Run the script with your PDF:

```bash
# Basic usage with default schema
python build_kg_from_pdf.py --pdf path/to/your/document.pdf

# With automatic schema extraction (LLM determines entities/relationships)
python build_kg_from_pdf.py --pdf path/to/your/document.pdf --auto-schema

# With document metadata
python build_kg_from_pdf.py --pdf document.pdf --metadata author "John Doe" --metadata source "Internal"

# Verbose logging for debugging
python build_kg_from_pdf.py --pdf document.pdf --verbose
```

### ✅ Step 7: Explore Your Knowledge Graph

Once the script completes:

1. **Open Neo4j Browser:**
   - If using Neo4j Desktop: Click "Open" button next to your database
   - If using AuraDB: Click "Open" in the dashboard

2. **Run a simple query to see your graph:**
   ```cypher
   MATCH (n) RETURN n LIMIT 25
   ```

3. **Explore entities:**
   ```cypher
   MATCH (n) RETURN labels(n) as NodeType, count(*) as Count
   ORDER BY Count DESC
   ```

4. **See relationships:**
   ```cypher
   MATCH ()-[r]->() RETURN type(r) as RelationshipType, count(*) as Count
   ORDER BY Count DESC
   ```

## Troubleshooting

### Connection Issues
- **Problem:** Can't connect to Neo4j
- **Solution:** 
  - Verify Neo4j is running
  - Check your URI format (neo4j://localhost:7687)
  - Verify username and password in .env file

### Missing API Key
- **Problem:** Error about missing OPENAI_API_KEY
- **Solution:** 
  - Check that .env file exists in project root
  - Verify OPENAI_API_KEY is set in .env file
  - Restart your terminal/IDE after creating .env

### PDF Processing Errors
- **Problem:** PDF can't be read
- **Solution:**
  - Verify PDF file path is correct
  - Check file permissions
  - Ensure file is a valid PDF

### APOC Not Installed
- **Problem:** Error about APOC library
- **Solution:**
  - In Neo4j Desktop: Go to database → Plugins → Install APOC
  - Restart your database

## What's Next After Building Your Graph?

1. **Query Your Graph** - Use Cypher queries to explore relationships
2. **Build RAG Applications** - Use the retrievers to build question-answering systems
3. **Customize Schema** - Edit the schema in `build_kg_from_pdf.py` to extract specific entities
4. **Process Multiple PDFs** - Run the script multiple times to build a larger knowledge base

## Need Help?

- Check `GETTING_STARTED.md` for detailed documentation
- Review examples in `examples/` directory
- Visit [Neo4j Community](https://community.neo4j.com/) for support
