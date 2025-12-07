"""Schema Versioning and Migration Management for Neo4j GraphRAG.

This module provides utilities to:
1. Version control your schema
2. Store schema metadata in Neo4j
3. Compare schema versions
4. Migrate existing data when schema changes
5. Validate schema compatibility

Usage:
    from schema_manager import SchemaManager
    
    manager = SchemaManager(driver, database="neo4j")
    
    # Store current schema version
    await manager.store_schema_version(schema_dict, version="1.0.0")
    
    # Check for schema changes
    changes = await manager.compare_schemas(old_schema, new_schema)
    
    # Migrate data
    await manager.migrate_schema(from_version="1.0.0", to_version="1.1.0")
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import neo4j
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ============================================================================
# SCHEMA METADATA MODELS
# ============================================================================


class SchemaVersion(BaseModel):
    """Schema version metadata."""

    version: str
    schema_hash: str
    node_types: list[dict[str, Any]]
    relationship_types: list[dict[str, Any]]
    patterns: list[tuple[str, str, str]]
    created_at: str
    description: Optional[str] = None


class SchemaChange(BaseModel):
    """Represents a change between schema versions."""

    change_type: str  # "added", "removed", "modified"
    entity_type: str  # "node_type", "relationship_type", "pattern"
    name: str
    details: dict[str, Any]


# ============================================================================
# SCHEMA MANAGER
# ============================================================================


class SchemaManager:
    """Manages schema versioning and migration for Neo4j knowledge graphs."""

    SCHEMA_METADATA_LABEL = "SchemaMetadata"
    SCHEMA_VERSION_PROPERTY = "schema_version"
    SCHEMA_HASH_PROPERTY = "schema_hash"

    def __init__(self, driver: neo4j.Driver, database: Optional[str] = None):
        """Initialize the SchemaManager.

        Args:
            driver: Neo4j driver instance
            database: Neo4j database name (optional)
        """
        self.driver = driver
        self.database = database or "neo4j"

    def _calculate_schema_hash(self, schema: dict[str, Any]) -> str:
        """Calculate a hash for the schema to detect changes."""
        schema_json = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(schema_json.encode()).hexdigest()[:16]

    async def store_schema_version(
        self,
        schema: dict[str, Any],
        version: str,
        description: Optional[str] = None,
    ) -> bool:
        """Store schema version metadata in Neo4j.

        Args:
            schema: Schema dictionary with node_types, relationship_types, patterns
            version: Schema version string (e.g., "1.0.0")
            description: Optional description of this version

        Returns:
            True if stored successfully
        """
        schema_hash = self._calculate_schema_hash(schema)

        query = """
        MERGE (s:SchemaMetadata {version: $version})
        SET s.schema_hash = $schema_hash,
            s.node_types = $node_types,
            s.relationship_types = $relationship_types,
            s.patterns = $patterns,
            s.created_at = datetime(),
            s.description = $description
        RETURN s
        """

        # Serialize nested structures to JSON strings for Neo4j storage
        # Neo4j can only store primitive types, not nested objects
        node_types = schema.get("node_types", [])
        relationship_types = schema.get("relationship_types", [])
        patterns = schema.get("patterns", [])
        
        # Convert to JSON strings for storage
        node_types_json = json.dumps(node_types) if node_types else "[]"
        relationship_types_json = json.dumps(relationship_types) if relationship_types else "[]"
        patterns_json = json.dumps(patterns) if patterns else "[]"

        try:
            result = self.driver.execute_query(
                query,
                {
                    "version": version,
                    "schema_hash": schema_hash,
                    "node_types": node_types_json,
                    "relationship_types": relationship_types_json,
                    "patterns": patterns_json,
                    "description": description or "",
                },
                database_=self.database,
            )

            logger.info(f"Stored schema version {version} (hash: {schema_hash})")
            return True

        except Exception as e:
            logger.error(f"Failed to store schema version: {e}")
            return False

    async def get_current_schema_version(self) -> Optional[SchemaVersion]:
        """Get the current/latest schema version from Neo4j.

        Returns:
            SchemaVersion object or None if no schema exists
        """
        query = """
        MATCH (s:SchemaMetadata)
        RETURN s
        ORDER BY s.created_at DESC
        LIMIT 1
        """

        try:
            result = self.driver.execute_query(
                query, database_=self.database, result_transformer_=neo4j.Result.single
            )

            if not result:
                return None

            record = result
            node_data = record.get("s", {})
            
            # Deserialize JSON strings back to objects
            node_types = json.loads(node_data.get("node_types", "[]"))
            relationship_types = json.loads(node_data.get("relationship_types", "[]"))
            patterns = json.loads(node_data.get("patterns", "[]"))
            
            return SchemaVersion(
                version=node_data.get("version", ""),
                schema_hash=node_data.get("schema_hash", ""),
                node_types=node_types,
                relationship_types=relationship_types,
                patterns=patterns,
                created_at=node_data.get("created_at", ""),
                description=node_data.get("description"),
            )

        except Exception as e:
            logger.error(f"Failed to get current schema version: {e}")
            return None

    def compare_schemas(
        self, old_schema: dict[str, Any], new_schema: dict[str, Any]
    ) -> list[SchemaChange]:
        """Compare two schemas and return a list of changes.

        Args:
            old_schema: Previous schema version
            new_schema: New schema version

        Returns:
            List of SchemaChange objects
        """
        changes: list[SchemaChange] = []

        # Compare node types
        old_nodes = {
            self._get_label(nt): nt for nt in old_schema.get("node_types", [])
        }
        new_nodes = {
            self._get_label(nt): nt for nt in new_schema.get("node_types", [])
        }

        for label, node_type in new_nodes.items():
            if label not in old_nodes:
                changes.append(
                    SchemaChange(
                        change_type="added",
                        entity_type="node_type",
                        name=label,
                        details={"node_type": node_type},
                    )
                )
            elif old_nodes[label] != node_type:
                changes.append(
                    SchemaChange(
                        change_type="modified",
                        entity_type="node_type",
                        name=label,
                        details={"old": old_nodes[label], "new": node_type},
                    )
                )

        for label in old_nodes:
            if label not in new_nodes:
                changes.append(
                    SchemaChange(
                        change_type="removed",
                        entity_type="node_type",
                        name=label,
                        details={},
                    )
                )

        # Compare relationship types
        old_rels = set(old_schema.get("relationship_types", []))
        new_rels = set(new_schema.get("relationship_types", []))

        for rel in new_rels:
            if rel not in old_rels:
                changes.append(
                    SchemaChange(
                        change_type="added",
                        entity_type="relationship_type",
                        name=rel if isinstance(rel, str) else rel.get("label", ""),
                        details={},
                    )
                )

        for rel in old_rels:
            if rel not in new_rels:
                changes.append(
                    SchemaChange(
                        change_type="removed",
                        entity_type="relationship_type",
                        name=rel if isinstance(rel, str) else rel.get("label", ""),
                        details={},
                    )
                )

        # Compare patterns
        old_patterns = set(old_schema.get("patterns", []))
        new_patterns = set(new_schema.get("patterns", []))

        for pattern in new_patterns:
            if pattern not in old_patterns:
                changes.append(
                    SchemaChange(
                        change_type="added",
                        entity_type="pattern",
                        name=f"{pattern[0]}-{pattern[1]}-{pattern[2]}",
                        details={"pattern": pattern},
                    )
                )

        for pattern in old_patterns:
            if pattern not in new_patterns:
                changes.append(
                    SchemaChange(
                        change_type="removed",
                        entity_type="pattern",
                        name=f"{pattern[0]}-{pattern[1]}-{pattern[2]}",
                        details={},
                    )
                )

        return changes

    def _get_label(self, node_type: Any) -> str:
        """Extract label from a node type definition."""
        if isinstance(node_type, str):
            return node_type
        elif isinstance(node_type, dict):
            return node_type.get("label", "")
        return ""

    async def validate_schema_compatibility(
        self, new_schema: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate that new schema is compatible with existing data.

        Args:
            new_schema: New schema to validate

        Returns:
            Tuple of (is_compatible, list of warnings)
        """
        warnings: list[str] = []

        # Get existing node labels in the graph
        query = """
        CALL db.labels() YIELD label
        RETURN collect(label) as labels
        """
        result = self.driver.execute_query(
            query, database_=self.database, result_transformer_=neo4j.Result.single
        )

        existing_labels = set(result.get("labels", []) if result else [])

        # Check if any existing labels are not in new schema
        new_node_labels = {
            self._get_label(nt) for nt in new_schema.get("node_types", [])
        }

        removed_labels = existing_labels - new_node_labels - {
            "Document",
            "Chunk",
            self.SCHEMA_METADATA_LABEL,
        }

        if removed_labels:
            warnings.append(
                f"Warning: Existing node labels not in new schema: {removed_labels}. "
                "These nodes will not be validated against the new schema."
            )

        # Check relationship types
        query = """
        CALL db.relationshipTypes() YIELD relationshipType
        RETURN collect(relationshipType) as rel_types
        """
        result = self.driver.execute_query(
            query, database_=self.database, result_transformer_=neo4j.Result.single
        )

        existing_rel_types = set(result.get("rel_types", []) if result else [])

        new_rel_labels = set()
        for rel in new_schema.get("relationship_types", []):
            if isinstance(rel, str):
                new_rel_labels.add(rel)
            elif isinstance(rel, dict):
                new_rel_labels.add(rel.get("label", ""))

        removed_rel_types = existing_rel_types - new_rel_labels

        if removed_rel_types:
            warnings.append(
                f"Warning: Existing relationship types not in new schema: {removed_rel_types}"
            )

        return len(warnings) == 0, warnings

    async def export_schema(self, file_path: Path, version: Optional[str] = None) -> bool:
        """Export schema to a JSON file.

        Args:
            file_path: Path to save the schema file
            version: Optional version to export (defaults to latest)

        Returns:
            True if exported successfully
        """
        schema_version = await self.get_current_schema_version()

        if not schema_version:
            logger.error("No schema version found to export")
            return False

        schema_dict = {
            "version": schema_version.version,
            "schema_hash": schema_version.schema_hash,
            "node_types": schema_version.node_types,
            "relationship_types": schema_version.relationship_types,
            "patterns": schema_version.patterns,
            "created_at": schema_version.created_at,
            "description": schema_version.description,
        }

        try:
            with open(file_path, "w") as f:
                json.dump(schema_dict, f, indent=2)
            logger.info(f"Exported schema version {schema_version.version} to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export schema: {e}")
            return False

    async def load_schema_from_file(self, file_path: Path) -> Optional[dict[str, Any]]:
        """Load schema from a JSON file.

        Args:
            file_path: Path to the schema file

        Returns:
            Schema dictionary or None if failed
        """
        try:
            with open(file_path, "r") as f:
                schema_dict = json.load(f)
            return schema_dict
        except Exception as e:
            logger.error(f"Failed to load schema from file: {e}")
            return None
