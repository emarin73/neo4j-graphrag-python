"""Schema Management CLI Tool.

This tool helps you manage schema versions, compare schemas, and migrate data.

Usage:
    # Store current schema version
    python manage_schema.py store --version 1.0.0

    # Compare current schema with stored version
    python manage_schema.py compare

    # Check schema compatibility
    python manage_schema.py validate

    # Export schema to file
    python manage_schema.py export --output schema_v1.0.0.json

    # Migrate schema (dry run)
    python manage_schema.py migrate --dry-run
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    import warnings
    import logging
    
    # Suppress python-dotenv parsing warnings for non-standard lines
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dotenv_logger = logging.getLogger("dotenv")
        original_level = dotenv_logger.level
        dotenv_logger.setLevel(logging.ERROR)
        load_dotenv(override=False)
        dotenv_logger.setLevel(original_level)
except ImportError:
    pass

import neo4j

from schema_manager import SchemaManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load configuration from environment
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def get_current_schema() -> dict[str, any]:
    """Load current schema from build_kg_from_pdf.py."""
    # Import the schema from the build script
    import importlib.util
    build_script_path = Path(__file__).parent / "build_kg_from_pdf.py"
    
    spec = importlib.util.spec_from_file_location("build_kg_from_pdf", build_script_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return {
            "node_types": getattr(module, "DEFAULT_NODE_TYPES", []),
            "relationship_types": getattr(module, "DEFAULT_RELATIONSHIP_TYPES", []),
            "patterns": getattr(module, "DEFAULT_PATTERNS", []),
        }
    
    return {"node_types": [], "relationship_types": [], "patterns": []}


async def cmd_store(args):
    """Store current schema version."""
    driver = neo4j.GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        manager = SchemaManager(driver, NEO4J_DATABASE)
        current_schema = get_current_schema()
        
        success = await manager.store_schema_version(
            current_schema,
            version=args.version,
            description=args.description
        )
        
        if success:
            logger.info(f"✓ Schema version {args.version} stored successfully")
        else:
            logger.error("Failed to store schema version")
            sys.exit(1)
            
    finally:
        driver.close()


async def cmd_compare(args):
    """Compare current schema with stored version."""
    driver = neo4j.GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        manager = SchemaManager(driver, NEO4J_DATABASE)
        current_schema = get_current_schema()
        stored_version = await manager.get_current_schema_version()
        
        if not stored_version:
            logger.warning("No stored schema version found")
            return
        
        stored_schema = {
            "node_types": stored_version.node_types,
            "relationship_types": stored_version.relationship_types,
            "patterns": stored_version.patterns,
        }
        
        changes = manager.compare_schemas(stored_schema, current_schema)
        
        if not changes:
            logger.info("✓ No changes detected - schemas are identical")
        else:
            logger.info(f"Found {len(changes)} changes:")
            for change in changes:
                logger.info(f"  - {change.change_type.upper()}: {change.entity_type} '{change.name}'")
                
    finally:
        driver.close()


async def cmd_validate(args):
    """Validate schema compatibility with existing data."""
    driver = neo4j.GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        manager = SchemaManager(driver, NEO4J_DATABASE)
        current_schema = get_current_schema()
        
        is_compatible, warnings = await manager.validate_schema_compatibility(current_schema)
        
        if is_compatible:
            logger.info("✓ Schema is compatible with existing data")
        else:
            logger.warning("Schema compatibility issues found:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
                
    finally:
        driver.close()


async def cmd_export(args):
    """Export schema to file."""
    driver = neo4j.GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        manager = SchemaManager(driver, NEO4J_DATABASE)
        output_path = Path(args.output)
        
        success = await manager.export_schema(output_path)
        
        if success:
            logger.info(f"✓ Schema exported to {output_path}")
        else:
            logger.error("Failed to export schema")
            sys.exit(1)
            
    finally:
        driver.close()


async def cmd_status(args):
    """Show current schema status."""
    driver = neo4j.GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        manager = SchemaManager(driver, NEO4J_DATABASE)
        stored_version = await manager.get_current_schema_version()
        current_schema = get_current_schema()
        
        print("\n" + "=" * 60)
        print("SCHEMA STATUS")
        print("=" * 60)
        
        if stored_version:
            print(f"\nStored Schema Version: {stored_version.version}")
            print(f"Schema Hash: {stored_version.schema_hash}")
            print(f"Created: {stored_version.created_at}")
            if stored_version.description:
                print(f"Description: {stored_version.description}")
            print(f"\nStored Schema:")
            print(f"  - Node Types: {len(stored_version.node_types)}")
            print(f"  - Relationship Types: {len(stored_version.relationship_types)}")
            print(f"  - Patterns: {len(stored_version.patterns)}")
        else:
            print("\n⚠ No schema version stored in database")
        
        print(f"\nCurrent Schema (from build_kg_from_pdf.py):")
        print(f"  - Node Types: {len(current_schema.get('node_types', []))}")
        print(f"  - Relationship Types: {len(current_schema.get('relationship_types', []))}")
        print(f"  - Patterns: {len(current_schema.get('patterns', []))}")
        
        if stored_version:
            stored_schema = {
                "node_types": stored_version.node_types,
                "relationship_types": stored_version.relationship_types,
                "patterns": stored_version.patterns,
            }
            changes = manager.compare_schemas(stored_schema, current_schema)
            if changes:
                print(f"\n⚠ Schema has changed: {len(changes)} differences detected")
                print("   Run 'python manage_schema.py compare' for details")
            else:
                print("\n✓ Current schema matches stored version")
        
        print("=" * 60 + "\n")
                
    finally:
        driver.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage schema versions for Neo4j GraphRAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Store command
    store_parser = subparsers.add_parser("store", help="Store current schema version")
    store_parser.add_argument("--version", required=True, help="Schema version (e.g., 1.0.0)")
    store_parser.add_argument("--description", help="Optional description")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare schemas")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate schema compatibility")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export schema to file")
    export_parser.add_argument("--output", required=True, help="Output file path")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show schema status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if not NEO4J_PASSWORD:
        logger.error("NEO4J_PASSWORD environment variable is required")
        sys.exit(1)
    
    # Execute command
    commands = {
        "store": cmd_store,
        "compare": cmd_compare,
        "validate": cmd_validate,
        "export": cmd_export,
        "status": cmd_status,
    }
    
    asyncio.run(commands[args.command](args))


if __name__ == "__main__":
    main()
