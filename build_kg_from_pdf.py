"""Build a Knowledge Graph from PDF using Neo4j GraphRAG.

This script processes a PDF file and creates a knowledge graph in Neo4j by extracting
entities and relationships using LLM-powered extraction.

Prerequisites:
1. Neo4j database running (local or cloud)
2. OPENAI_API_KEY environment variable set (or in .env file)
3. Neo4j connection credentials (set via environment variables or .env file)

Configuration:
- Create a .env file in the project root with:
  NEO4J_URI=neo4j://localhost:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=your_password
  OPENAI_API_KEY=your_openai_api_key

Usage:
    python build_kg_from_pdf.py --pdf path/to/document.pdf
    python build_kg_from_pdf.py --pdf path/to/document.pdf --auto-schema
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    # Load environment variables from .env file if it exists
    load_dotenv()
except ImportError:
    print(
        "Warning: python-dotenv not installed. Install with: pip install python-dotenv\n"
        "You can still use environment variables set in your system."
    )

import neo4j
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.pipeline.pipeline import PipelineResult
from neo4j_graphrag.experimental.pipeline.types.schema import (
    EntityInputType,
    RelationInputType,
)
from neo4j_graphrag.llm import OpenAILLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION - Load from environment variables
# ============================================================================

# Neo4j connection settings (from environment variables)
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# LLM Configuration
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ============================================================================
# SCHEMA DEFINITION - Customize based on your document type
# ============================================================================
#
# This schema defines what entities and relationships the LLM will extract
# from your PDF documents. You can customize:
#
# 1. DEFAULT_NODE_TYPES - The types of entities (nodes) to extract
# 2. DEFAULT_RELATIONSHIP_TYPES - The types of relationships (edges) to extract
# 3. DEFAULT_PATTERNS - Valid combinations of relationships
#
# Each node type can be:
#   - Simple string: "Ordinance"
#   - Dict with description: {"label": "Section", "description": "..."}
#   - Dict with properties: {"label": "Section", "properties": [...]}
#
# Schema location: Lines 79-134 in this file
#
# Alternative: Use --auto-schema flag to let LLM automatically determine schema
#
# ============================================================================

DEFAULT_NODE_TYPES: list[EntityInputType] = [
    {
        "label": "Ordinance",
        "description": "A specific adopted ordinance (e.g. Ord 2024-15)",
    },
    {
        "label": "Section",
        "description": "A codified section (e.g. §12-3-105)",
    },
    {
        "label": "Chapter",
        "description": "A chapter in the code, part of the hierarchy",
    },
    {
        "label": "Title",
        "description": "A title in the code, part of the hierarchy",
    },
    {
        "label": "Topic",
        "description": "Legal topics such as zoning, fencing, noise, signs, etc.",
    },
    {
        "label": "Zone",
        "description": "Zoning districts (R-1, R-2, C-1, etc.)",
    },
    {
        "label": "Actor",
        "description": "Departments, boards, officials (e.g. Planning Dept, Code Enforcement Office)",
    },
    {
        "label": "Obligation",
        "description": "Normalized rules or requirements that must be followed",
    },
    {
        "label": "Prohibition",
        "description": "Normalized rules or activities that are forbidden",
    },
    {
        "label": "Penalty",
        "description": "Fines, imprisonment, remedies for violations",
    },
    {
        "label": "Term",
        "description": "Defined legal terms (e.g. Accessory Structure, Short-term rental)",
    },
]

DEFAULT_RELATIONSHIP_TYPES: list[RelationInputType] = [
    "ENACTS",
    "AMENDS",
    "REPEALS",
    "PART_OF",
    "REFERS_TO",
    "APPLIES_TO",
    "HAS_TOPIC",
    "DEFINES",
    "IMPOSED_BY",
    "FOR_VIOLATION_OF",
    "ENFORCES",
]

DEFAULT_PATTERNS = [
    ("Ordinance", "ENACTS", "Section"),
    ("Ordinance", "AMENDS", "Section"),
    ("Ordinance", "REPEALS", "Section"),
    ("Section", "PART_OF", "Chapter"),
    ("Chapter", "PART_OF", "Title"),
    ("Section", "REFERS_TO", "Section"),
    ("Section", "APPLIES_TO", "Zone"),
    ("Section", "HAS_TOPIC", "Topic"),
    ("Section", "DEFINES", "Term"),
    ("Obligation", "IMPOSED_BY", "Section"),
    ("Penalty", "FOR_VIOLATION_OF", "Section"),
    ("Penalty", "FOR_VIOLATION_OF", "Obligation"),
    ("Actor", "ENFORCES", "Section"),
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def validate_credentials() -> tuple[bool, str]:
    """Validate that required credentials are available."""
    missing = []

    if not NEO4J_PASSWORD:
        missing.append("NEO4J_PASSWORD")

    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if missing:
        return (
            False,
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set them in a .env file or as system environment variables.\n"
            f"See GETTING_STARTED.md for configuration instructions.",
        )

    return True, ""


def verify_neo4j_connection() -> tuple[bool, str]:
    """Verify Neo4j connection before processing."""
    try:
        driver = neo4j.GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        driver.close()
        return True, ""
    except Exception as e:
        return (
            False,
            f"Failed to connect to Neo4j at {NEO4J_URI}: {str(e)}\n"
            f"Please check:\n"
            f"  1. Neo4j database is running\n"
            f"  2. NEO4J_URI is correct (e.g., neo4j://localhost:7687)\n"
            f"  3. NEO4J_USER and NEO4J_PASSWORD are correct",
        )


def check_pdf_exists(pdf_path: str | Path) -> tuple[bool, str]:
    """Check if PDF file exists and is readable."""
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        return False, f"PDF file not found: {pdf_path}\nPlease provide a valid PDF file path."

    if not pdf_path.is_file():
        return False, f"Path is not a file: {pdf_path}"

    if pdf_path.suffix.lower() != ".pdf":
        return (
            False,
            f"File does not have .pdf extension: {pdf_path}\nPlease provide a PDF file.",
        )

    try:
        # Try to read the file to check permissions
        with open(pdf_path, "rb") as f:
            f.read(1)
    except Exception as e:
        return False, f"Cannot read PDF file: {pdf_path}\nError: {str(e)}"

    return True, ""


# ============================================================================
# MAIN PIPELINE FUNCTION
# ============================================================================


async def build_knowledge_graph_from_pdf(
    pdf_path: str | Path,
    auto_schema: bool = False,
    schema: dict | None = None,
    document_metadata: dict | None = None,
) -> PipelineResult:
    """Build a knowledge graph from a PDF file.

    Args:
        pdf_path: Path to the PDF file to process
        auto_schema: If True, let LLM automatically determine schema
        schema: Custom schema dictionary (ignored if auto_schema is True)
        document_metadata: Optional metadata to attach to the document node

    Returns:
        PipelineResult with information about the graph construction
    """
    pdf_path = Path(pdf_path)
    logger.info(f"Processing PDF: {pdf_path}")
    logger.info(f"File size: {pdf_path.stat().st_size / 1024:.2f} KB")

    driver = None
    llm = None

    try:
        # Initialize Neo4j driver
        logger.info(f"Connecting to Neo4j at {NEO4J_URI}...")
        driver = neo4j.GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

        # Verify connection
        driver.verify_connectivity()
        logger.info("✓ Successfully connected to Neo4j")

        # Initialize LLM
        logger.info(f"Initializing LLM: {LLM_MODEL}")
        llm = OpenAILLM(
            model_name=LLM_MODEL,
            model_params={
                "max_tokens": 2000,
                "response_format": {"type": "json_object"},
                "temperature": 0,
            },
        )

        # Initialize Embedder
        logger.info("Initializing embedder...")
        embedder = OpenAIEmbeddings(model="text-embedding-3-large")

        # Create the knowledge graph pipeline
        if auto_schema:
            logger.info("Creating pipeline with automatic schema extraction...")
            logger.info("The LLM will automatically determine entities and relationships.")
            kg_builder = SimpleKGPipeline(
                llm=llm,
                driver=driver,
                embedder=embedder,
                from_pdf=True,
                neo4j_database=NEO4J_DATABASE,
            )
        else:
            schema_to_use = schema or {
                "node_types": DEFAULT_NODE_TYPES,
                "relationship_types": DEFAULT_RELATIONSHIP_TYPES,
                "patterns": DEFAULT_PATTERNS,
            }
            logger.info("Creating pipeline with predefined schema...")
            logger.info(f"  Node types: {len(schema_to_use.get('node_types', []))}")
            logger.info(
                f"  Relationship types: {len(schema_to_use.get('relationship_types', []))}"
            )
            logger.info(f"  Patterns: {len(schema_to_use.get('patterns', []))}")

            kg_builder = SimpleKGPipeline(
                llm=llm,
                driver=driver,
                embedder=embedder,
                schema=schema_to_use,
                from_pdf=True,
                neo4j_database=NEO4J_DATABASE,
            )

        # Run the pipeline
        logger.info("=" * 60)
        logger.info("Starting knowledge graph construction...")
        logger.info("This may take a while depending on PDF size...")
        logger.info("=" * 60)

        result = await kg_builder.run_async(
            file_path=str(pdf_path),
            document_metadata=document_metadata,
        )

        logger.info("=" * 60)
        logger.info("✓ Knowledge graph construction completed!")
        logger.info(f"Result: {result}")
        logger.info("=" * 60)

        return result

    finally:
        # Clean up
        if llm:
            await llm.async_client.close()
        if driver:
            driver.close()
        logger.info("Connections closed.")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Build a Knowledge Graph from PDF using Neo4j GraphRAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process PDF with default schema
  python build_kg_from_pdf.py --pdf document.pdf

  # Process PDF with automatic schema extraction
  python build_kg_from_pdf.py --pdf document.pdf --auto-schema

  # Process PDF with custom metadata
  python build_kg_from_pdf.py --pdf document.pdf --metadata author "John Doe" --metadata source "Internal"

Configuration:
  Set environment variables in a .env file or system environment:
  - NEO4J_URI (default: neo4j://localhost:7687)
  - NEO4J_USER (default: neo4j)
  - NEO4J_PASSWORD (required)
  - NEO4J_DATABASE (default: neo4j)
  - OPENAI_API_KEY (required)
  - OPENAI_MODEL (default: gpt-4o)
        """,
    )

    parser.add_argument(
        "--pdf",
        type=str,
        required=True,
        help="Path to the PDF file to process",
    )

    parser.add_argument(
        "--auto-schema",
        action="store_true",
        help="Let the LLM automatically determine the schema (entities and relationships)",
    )

    parser.add_argument(
        "--metadata",
        nargs=2,
        action="append",
        metavar=("KEY", "VALUE"),
        help="Add metadata to the document node (can be used multiple times)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_arguments()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("neo4j_graphrag").setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("Neo4j GraphRAG - Knowledge Graph Builder (PDF)")
    logger.info("=" * 60)

    try:
        # Validate credentials
        is_valid, error_msg = validate_credentials()
        if not is_valid:
            logger.error(error_msg)
            sys.exit(1)

        # Check PDF file
        is_valid, error_msg = check_pdf_exists(args.pdf)
        if not is_valid:
            logger.error(error_msg)
            sys.exit(1)

        # Verify Neo4j connection
        logger.info("Verifying Neo4j connection...")
        is_valid, error_msg = verify_neo4j_connection()
        if not is_valid:
            logger.error(error_msg)
            sys.exit(1)

        # Parse metadata
        document_metadata = None
        if args.metadata:
            document_metadata = {key: value for key, value in args.metadata}

        # Build knowledge graph
        result = await build_knowledge_graph_from_pdf(
            pdf_path=args.pdf,
            auto_schema=args.auto_schema,
            document_metadata=document_metadata,
        )

        logger.info("")
        logger.info("=" * 60)
        logger.info("SUCCESS! Your knowledge graph has been created.")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Open Neo4j Browser to visualize your graph")
        logger.info("   - Connect to: " + NEO4J_URI)
        logger.info("   - Try query: MATCH (n) RETURN n LIMIT 25")
        logger.info("2. Query your graph using Cypher")
        logger.info("3. Use retrievers to search your knowledge graph")
        logger.info("4. Build a RAG application using GraphRAG")
        logger.info("")

    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error building knowledge graph: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
