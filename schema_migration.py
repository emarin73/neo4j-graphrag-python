"""Schema Migration Utilities.

Provides functions to migrate data when schema changes occur.
"""

import logging
from typing import Any, Optional

import neo4j

from schema_manager import SchemaChange, SchemaManager

logger = logging.getLogger(__name__)


class SchemaMigrator:
    """Handles data migration when schema changes."""

    def __init__(self, driver: neo4j.Driver, database: Optional[str] = None):
        """Initialize the SchemaMigrator.

        Args:
            driver: Neo4j driver instance
            database: Neo4j database name (optional)
        """
        self.driver = driver
        self.database = database or "neo4j"
        self.schema_manager = SchemaManager(driver, database)

    async def migrate_node_type_rename(
        self, old_label: str, new_label: str
    ) -> tuple[int, int]:
        """Rename a node type (label) in the graph.

        Args:
            old_label: Old node label
            new_label: New node label

        Returns:
            Tuple of (nodes_updated, relationships_updated)
        """
        # Update node labels
        query = f"""
        MATCH (n:{old_label})
        SET n:{new_label}
        REMOVE n:{old_label}
        RETURN count(n) as count
        """

        try:
            result = self.driver.execute_query(
                query, database_=self.database, result_transformer_=neo4j.Result.single
            )
            nodes_updated = result.get("count", 0) if result else 0

            logger.info(f"Renamed {nodes_updated} nodes from {old_label} to {new_label}")
            return nodes_updated, 0

        except Exception as e:
            logger.error(f"Failed to rename node type: {e}")
            return 0, 0

    async def migrate_relationship_type_rename(
        self, old_type: str, new_type: str
    ) -> int:
        """Rename a relationship type in the graph.

        Args:
            old_type: Old relationship type
            new_type: New relationship type

        Returns:
            Number of relationships updated
        """
        query = f"""
        MATCH ()-[r:{old_type}]->()
        CALL apoc.refactor.setType(r, '{new_type}')
        YIELD input, output
        RETURN count(output) as count
        """

        try:
            result = self.driver.execute_query(
                query, database_=self.database, result_transformer_=neo4j.Result.single
            )
            rels_updated = result.get("count", 0) if result else 0

            logger.info(f"Renamed {rels_updated} relationships from {old_type} to {new_type}")
            return rels_updated

        except Exception as e:
            logger.error(f"Failed to rename relationship type: {e}")
            logger.warning("APOC may not be installed. Relationship migration requires APOC.")
            return 0

    async def migrate_schema_changes(
        self, changes: list[SchemaChange], dry_run: bool = False
    ) -> dict[str, Any]:
        """Migrate data based on schema changes.

        Args:
            changes: List of schema changes to apply
            dry_run: If True, only report what would be changed

        Returns:
            Dictionary with migration statistics
        """
        stats = {
            "nodes_updated": 0,
            "relationships_updated": 0,
            "nodes_removed": 0,
            "relationships_removed": 0,
            "warnings": [],
        }

        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")

        for change in changes:
            if change.change_type == "removed":
                if change.entity_type == "node_type":
                    # Optionally remove nodes of this type
                    # WARNING: This is destructive!
                    stats["warnings"].append(
                        f"Node type {change.name} was removed from schema. "
                        "Consider manual cleanup or data migration."
                    )

                elif change.entity_type == "relationship_type":
                    stats["warnings"].append(
                        f"Relationship type {change.name} was removed from schema. "
                        "Consider manual cleanup or data migration."
                    )

            elif change.change_type == "modified":
                if change.entity_type == "node_type":
                    # Check if label changed
                    old_label = change.details.get("old", {}).get("label")
                    new_label = change.details.get("new", {}).get("label")

                    if old_label and new_label and old_label != new_label:
                        if not dry_run:
                            nodes, rels = await self.migrate_node_type_rename(
                                old_label, new_label
                            )
                            stats["nodes_updated"] += nodes
                            stats["relationships_updated"] += rels
                        else:
                            logger.info(
                                f"Would rename node type: {old_label} -> {new_label}"
                            )

        return stats
