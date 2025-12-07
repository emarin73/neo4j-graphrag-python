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
    python build_kg_from_pdf.py --pdf path/to/document.pdf --track-schema
"""

import argparse
import asyncio
import logging
import os
import re
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    import warnings
    import logging

    # Suppress python-dotenv parsing warnings for non-standard lines
    # (like separator lines or instructions in template files)
    # These warnings are harmless - dotenv will skip invalid lines and only parse KEY=VALUE format
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Temporarily suppress dotenv logger warnings
        dotenv_logger = logging.getLogger("dotenv")
        original_level = dotenv_logger.level
        dotenv_logger.setLevel(logging.ERROR)
        
        # Load environment variables from .env file if it exists
        # Set override=False so system env vars take precedence
        load_dotenv(override=False)
        
        # Restore original logging level
        dotenv_logger.setLevel(original_level)
except ImportError:
    print(
        "Warning: python-dotenv not installed. Install with: pip install python-dotenv\n"
        "You can still use environment variables set in your system."
    )

import neo4j
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.exceptions import LLMGenerationError, RateLimitError
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.pipeline.pipeline import PipelineResult
from neo4j_graphrag.experimental.pipeline.types.schema import (
    EntityInputType,
    RelationInputType,
)
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.utils.rate_limit import RetryRateLimitHandler, is_rate_limit_error
from tenacity import RetryError

# Import schema manager for automatic schema tracking
try:
    from schema_manager import SchemaManager
    SCHEMA_MANAGER_AVAILABLE = True
except ImportError:
    SCHEMA_MANAGER_AVAILABLE = False

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
# Default to gpt-4o-mini for better rate limits (200k TPM vs 30k TPM) and lower cost
# Override with OPENAI_MODEL environment variable if needed
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Rate Limit Configuration (can be overridden via environment variables)
RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv("RATE_LIMIT_MAX_ATTEMPTS", "5"))
RATE_LIMIT_MIN_WAIT = float(os.getenv("RATE_LIMIT_MIN_WAIT", "2.0"))
RATE_LIMIT_MAX_WAIT = float(os.getenv("RATE_LIMIT_MAX_WAIT", "120.0"))
RATE_LIMIT_MULTIPLIER = float(os.getenv("RATE_LIMIT_MULTIPLIER", "2.0"))

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


def get_current_schema_dict() -> dict:
    """Get current schema as a dictionary for version tracking."""
    return {
        "node_types": DEFAULT_NODE_TYPES,
        "relationship_types": DEFAULT_RELATIONSHIP_TYPES,
        "patterns": DEFAULT_PATTERNS,
    }


def extract_wait_time_from_error(error_message: str) -> float | None:
    """Extract recommended wait time from OpenAI rate limit error message.
    
    Args:
        error_message: The error message string
        
    Returns:
        Wait time in seconds if found, None otherwise
    """
    # Look for patterns like "Please try again in 4.16s" or "try again in 4.16 seconds"
    pattern = r"try again in ([\d.]+)\s*(?:s|seconds?)"
    match = re.search(pattern, error_message, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            pass
    return None


def increment_version(version: str) -> str:
    """Increment a semantic version string.
    
    Args:
        version: Version string in format "X.Y.Z"
        
    Returns:
        Incremented version string (patch version incremented by default)
    """
    try:
        parts = version.split(".")
        if len(parts) == 3:
            major, minor, patch = parts
            patch_num = int(patch) + 1
            return f"{major}.{minor}.{patch_num}"
        else:
            # If format is unexpected, return 1.0.1
            return "1.0.1"
    except (ValueError, IndexError):
        return "1.0.1"


async def track_schema_automatically(
    driver: neo4j.Driver,
    schema: dict,
    version: str | None = None,
    description: str | None = None,
    auto_increment: bool = True,
) -> None:
    """Automatically track schema version after build.
    
    Args:
        driver: Neo4j driver instance
        schema: Schema dictionary to track
        version: Optional version string (auto-incremented if not provided)
        description: Optional description for this version
        auto_increment: If True, auto-increment version when schema changes
    """
    if not SCHEMA_MANAGER_AVAILABLE:
        logger.warning(
            "Schema tracking skipped: schema_manager module not available. "
            "Ensure schema_manager.py is in the same directory."
        )
        return
    
    try:
        manager = SchemaManager(driver, database=NEO4J_DATABASE)
        
        # Get stored schema version
        stored_version = await manager.get_current_schema_version()
        
        if stored_version:
            stored_schema = {
                "node_types": stored_version.node_types,
                "relationship_types": stored_version.relationship_types,
                "patterns": stored_version.patterns,
            }
            
            # Compare schemas
            changes = manager.compare_schemas(stored_schema, schema)
            
            if not changes:
                logger.info(
                    f"✓ Schema unchanged (version {stored_version.version}). "
                    "No update needed."
                )
                return
            
            logger.info(f"Schema changes detected ({len(changes)} changes):")
            for change in changes[:5]:  # Show first 5 changes
                logger.info(
                    f"  - {change.change_type.upper()}: "
                    f"{change.entity_type} '{change.name}'"
                )
            if len(changes) > 5:
                logger.info(f"  ... and {len(changes) - 5} more changes")
            
            # Determine version
            if version:
                new_version = version
            elif auto_increment:
                new_version = increment_version(stored_version.version)
                logger.info(
                    f"Auto-incrementing version: {stored_version.version} → {new_version}"
                )
            else:
                logger.warning(
                    "Schema has changed but no version specified. "
                    "Skipping schema tracking. Use --schema-version to store."
                )
                return
        
        else:
            # No stored schema - this is the first time
            logger.info("No existing schema version found. Storing initial schema.")
            if not version:
                new_version = "1.0.0"
                logger.info(f"Using initial version: {new_version}")
            else:
                new_version = version
        
        # Store the schema version
        if not description:
            description = f"Automatically tracked after build"
        
        success = await manager.store_schema_version(
            schema, version=new_version, description=description
        )
        
        if success:
            logger.info(f"✓ Schema version {new_version} stored successfully")
        else:
            logger.error("Failed to store schema version")
    
    except Exception as e:
        logger.warning(f"Schema tracking failed (non-fatal): {e}")
        logger.debug("Schema tracking error details:", exc_info=True)


# ============================================================================
# MAIN PIPELINE FUNCTION
# ============================================================================


async def build_knowledge_graph_from_pdf(
    pdf_path: str | Path,
    auto_schema: bool = False,
    schema: dict | None = None,
    document_metadata: dict | None = None,
    track_schema: bool = False,
    schema_version: str | None = None,
    schema_description: str | None = None,
) -> PipelineResult:
    """Build a knowledge graph from a PDF file.

    Args:
        pdf_path: Path to the PDF file to process
        auto_schema: If True, let LLM automatically determine schema
        schema: Custom schema dictionary (ignored if auto_schema is True)
        document_metadata: Optional metadata to attach to the document node
        track_schema: If True, automatically track schema version after build
        schema_version: Optional schema version string (e.g., "1.0.0"). If not provided
            and track_schema is True, version will auto-increment when schema changes
        schema_description: Optional description for the schema version

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

        # Initialize LLM with enhanced rate limiting
        logger.info(f"Initializing LLM: {LLM_MODEL}")
        logger.info(
            f"Rate limit configuration: {RATE_LIMIT_MAX_ATTEMPTS} max attempts, "
            f"{RATE_LIMIT_MIN_WAIT}-{RATE_LIMIT_MAX_WAIT}s wait times"
        )
        
        rate_limit_handler = RetryRateLimitHandler(
            max_attempts=RATE_LIMIT_MAX_ATTEMPTS,
            min_wait=RATE_LIMIT_MIN_WAIT,
            max_wait=RATE_LIMIT_MAX_WAIT,
            multiplier=RATE_LIMIT_MULTIPLIER,
            jitter=True,
        )
        
        llm = OpenAILLM(
            model_name=LLM_MODEL,
            model_params={
                "max_tokens": 2000,
                "response_format": {"type": "json_object"},
                "temperature": 0,
            },
            rate_limit_handler=rate_limit_handler,
        )

        # Initialize Embedder with enhanced rate limiting
        logger.info("Initializing embedder...")
        embedder = OpenAIEmbeddings(
            model="text-embedding-3-large",
            rate_limit_handler=rate_limit_handler,
        )

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
        logger.info("")
        logger.info("Note: If you see rate limit warnings (429 errors), don't worry!")
        logger.info("The script will automatically retry with exponential backoff.")
        logger.info("Look for '200 OK' responses to see successful requests.")
        logger.info("=" * 60)

        result = await kg_builder.run_async(
            file_path=str(pdf_path),
            document_metadata=document_metadata,
        )

        logger.info("=" * 60)
        logger.info("✓ Knowledge graph construction completed!")
        logger.info(f"Result: {result}")
        logger.info("=" * 60)

        # Automatic schema tracking (only for predefined schemas, not auto-schema)
        if track_schema and not auto_schema:
            logger.info("")
            logger.info("=" * 60)
            logger.info("Schema Version Tracking")
            logger.info("=" * 60)
            
            schema_to_track = schema or get_current_schema_dict()
            await track_schema_automatically(
                driver=driver,
                schema=schema_to_track,
                version=schema_version,
                description=schema_description,
                auto_increment=(schema_version is None),
            )
        elif track_schema and auto_schema:
            logger.info(
                "Schema tracking skipped: Auto-schema mode generates dynamic schemas "
                "that cannot be automatically tracked. Use manual schema management instead."
            )

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

  # Process PDF with automatic schema version tracking
  python build_kg_from_pdf.py --pdf document.pdf --track-schema

  # Process PDF with explicit schema version
  python build_kg_from_pdf.py --pdf document.pdf --track-schema --schema-version "1.0.0" --schema-description "Initial schema"

Configuration:
  Set environment variables in a .env file or system environment:
  - NEO4J_URI (default: neo4j://localhost:7687)
  - NEO4J_USER (default: neo4j)
  - NEO4J_PASSWORD (required)
  - NEO4J_DATABASE (default: neo4j)
  - OPENAI_API_KEY (required)
  - OPENAI_MODEL (default: gpt-4o)
  
  Rate Limit Configuration (optional):
  - RATE_LIMIT_MAX_ATTEMPTS (default: 5) - Max retry attempts for rate limits
  - RATE_LIMIT_MIN_WAIT (default: 2.0) - Min wait time between retries (seconds)
  - RATE_LIMIT_MAX_WAIT (default: 120.0) - Max wait time between retries (seconds)
  - RATE_LIMIT_MULTIPLIER (default: 2.0) - Exponential backoff multiplier
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

    parser.add_argument(
        "--track-schema",
        action="store_true",
        help="Automatically track schema version after build (compares and stores if changed)",
    )

    parser.add_argument(
        "--schema-version",
        type=str,
        help="Schema version string (e.g., '1.0.0'). If not provided and --track-schema is used, version will auto-increment",
    )

    parser.add_argument(
        "--schema-description",
        type=str,
        help="Optional description for the schema version (used with --track-schema)",
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
            track_schema=getattr(args, "track_schema", False),
            schema_version=getattr(args, "schema_version", None),
            schema_description=getattr(args, "schema_description", None),
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
    except RetryError as e:
        # Handle case where all retry attempts were exhausted
        error_str = str(e)
        error_lower = error_str.lower()
        
        # Extract wait time from error message if available
        wait_time = extract_wait_time_from_error(error_str)
        
        if "ratelimiterror" in error_lower or "rate limit" in error_lower or "429" in error_lower:
            logger.error("=" * 60)
            logger.error("RATE LIMIT ERROR - ALL RETRY ATTEMPTS EXHAUSTED")
            logger.error("=" * 60)
            logger.error("")
            logger.error(f"The script attempted to retry the request {RATE_LIMIT_MAX_ATTEMPTS} times,")
            logger.error("but all attempts failed due to rate limiting.")
            logger.error("")
            
            if wait_time:
                wait_minutes = int(wait_time / 60) + 1
                logger.error(f"OpenAI suggests waiting: {wait_time:.1f} seconds (~{wait_minutes} minute{'s' if wait_minutes > 1 else ''})")
                logger.error("")
            
            logger.error("RECOMMENDED ACTIONS:")
            logger.error("")
            if wait_time:
                recommended_wait = max(5, int(wait_time / 60) + 2)  # Add buffer
                logger.error(f"1. ⏱️  WAIT {recommended_wait}+ MINUTES - Your rate limit needs time to reset")
            else:
                logger.error("1. ⏱️  WAIT 5-10 MINUTES - Your rate limit needs time to reset")
            logger.error("   Then run the script again.")
            logger.error("")
            logger.error("2. 📈 INCREASE RETRY CONFIGURATION in your .env file:")
            logger.error("   RATE_LIMIT_MAX_ATTEMPTS=10")
            logger.error("   RATE_LIMIT_MAX_WAIT=600  # 10 minutes")
            logger.error("")
            logger.error("3. 🔍 CHECK YOUR USAGE:")
            logger.error("   https://platform.openai.com/account/rate-limits")
            logger.error("   Your limit: 30,000 tokens/minute")
            logger.error("")
            logger.error("4. 💡 CONSIDER:")
            logger.error("   - Processing smaller PDFs")
            logger.error("   - Waiting between runs")
            logger.error("   - Upgrading your OpenAI plan for higher limits")
            logger.error("")
            logger.error(f"Current retry configuration: {RATE_LIMIT_MAX_ATTEMPTS} attempts, "
                        f"{RATE_LIMIT_MIN_WAIT}-{RATE_LIMIT_MAX_WAIT}s wait times")
            logger.error("")
            logger.error("=" * 60)
            sys.exit(1)
        else:
            logger.error(f"RetryError: All retry attempts exhausted. Original error: {e}", exc_info=True)
            sys.exit(1)
    except (RateLimitError, LLMGenerationError) as e:
        error_str = str(e).lower()
        if is_rate_limit_error(e) or "429" in error_str or "rate limit" in error_str:
            logger.error("=" * 60)
            logger.error("RATE LIMIT ERROR")
            logger.error("=" * 60)
            logger.error(f"Error: {e}")
            logger.error("")
            logger.error("You've hit OpenAI's rate limit. The script will automatically retry,")
            logger.error(f"but if the error persists, try the following:")
            logger.error("")
            logger.error("1. Wait a few minutes before running again")
            logger.error("2. Increase rate limit retry attempts (set in environment):")
            logger.error("   RATE_LIMIT_MAX_ATTEMPTS=10")
            logger.error("3. Increase maximum wait time:")
            logger.error("   RATE_LIMIT_MAX_WAIT=300  # 5 minutes")
            logger.error("4. Check your OpenAI usage limits:")
            logger.error("   https://platform.openai.com/account/rate-limits")
            logger.error("5. Consider using a lower-tier model or reducing PDF size")
            logger.error("")
            logger.error("The script has been configured with automatic retries.")
            logger.error(f"Current settings: {RATE_LIMIT_MAX_ATTEMPTS} attempts, "
                        f"{RATE_LIMIT_MIN_WAIT}-{RATE_LIMIT_MAX_WAIT}s wait times")
            logger.error("=" * 60)
            sys.exit(1)
        else:
            logger.error(f"LLM Error: {e}", exc_info=True)
            sys.exit(1)
    except Exception as e:
        error_str = str(e).lower()
        # Check if it's a rate limit related error in the exception chain
        if "ratelimiterror" in error_str or "rate limit" in error_str or "429" in error_str or "retryerror" in error_str:
            logger.error("=" * 60)
            logger.error("RATE LIMIT ERROR - ALL RETRY ATTEMPTS EXHAUSTED")
            logger.error("=" * 60)
            logger.error("")
            logger.error("The script attempted multiple retries but all failed.")
            logger.error("")
            logger.error("RECOMMENDED: Wait 5-10 minutes, then run the script again.")
            logger.error("")
            logger.error("To increase retry attempts, add to your .env file:")
            logger.error("  RATE_LIMIT_MAX_ATTEMPTS=10")
            logger.error("  RATE_LIMIT_MAX_WAIT=600")
            logger.error("")
            logger.error(f"Current settings: {RATE_LIMIT_MAX_ATTEMPTS} attempts, "
                        f"{RATE_LIMIT_MIN_WAIT}-{RATE_LIMIT_MAX_WAIT}s wait times")
            logger.error("=" * 60)
            sys.exit(1)
        logger.error(f"Error building knowledge graph: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
