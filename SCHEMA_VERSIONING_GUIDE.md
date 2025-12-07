# Schema Versioning and Change Management Guide

## Overview

Your knowledge graph schema is now **change-proof** with automatic version tracking, comparison, and migration capabilities. This ensures that when you update your schema in `build_kg_from_pdf.py`, you can:

1. **Track changes** - See exactly what changed between versions
2. **Validate compatibility** - Check if new schema works with existing data
3. **Migrate data** - Automatically update existing nodes/relationships when schema changes
4. **Maintain history** - Keep a record of all schema versions

## Components

### 1. `schema_manager.py`
Core schema versioning system that:
- Stores schema versions in Neo4j
- Compares schema versions
- Validates schema compatibility
- Exports/imports schemas

### 2. `schema_migration.py`
Migration utilities for:
- Renaming node types
- Renaming relationship types
- Handling schema changes

### 3. `manage_schema.py` (CLI Tool)
Command-line interface for schema management

## Quick Start

### Step 1: Store Your Initial Schema Version

After building your first knowledge graph, store the schema:

```bash
python manage_schema.py store --version 1.0.0 --description "Initial legal document schema"
```

### Step 2: Check Schema Status

See current schema status:

```bash
python manage_schema.py status
```

This shows:
- Currently stored schema version
- Current schema from `build_kg_from_pdf.py`
- Any differences between them

### Step 3: When You Update Your Schema

1. **Edit the schema** in `build_kg_from_pdf.py` (lines 94-169)

2. **Compare schemas** to see what changed:
   ```bash
   python manage_schema.py compare
   ```

3. **Validate compatibility** with existing data:
   ```bash
   python manage_schema.py validate
   ```

4. **Store new version** after updating:
   ```bash
   python manage_schema.py store --version 1.1.0 --description "Added new node types"
   ```

## Schema Management Commands

### Store Schema Version
```bash
python manage_schema.py store --version 1.0.0 --description "Description of changes"
```

### Compare Schemas
```bash
python manage_schema.py compare
```
Shows differences between stored schema and current schema in code.

### Validate Compatibility
```bash
python manage_schema.py validate
```
Checks if new schema is compatible with existing graph data.

### Export Schema
```bash
python manage_schema.py export --output schema_v1.0.0.json
```
Saves schema to a JSON file for backup or sharing.

### Check Status
```bash
python manage_schema.py status
```
Shows comprehensive schema status information.

## Automatic Schema Tracking (Recommended)

To automatically track schema versions when building graphs, you can integrate schema versioning into your build script. The schema will be automatically stored after each build.

## Migration Workflow

When you need to migrate existing data after schema changes:

### Example: Renaming a Node Type

If you change `"Section"` to `"CodeSection"`:

1. Update schema in `build_kg_from_pdf.py`
2. Run comparison:
   ```bash
   python manage_schema.py compare
   ```
3. Use migration utilities (see `schema_migration.py`) to rename nodes:
   ```python
   from schema_migration import SchemaMigrator
   
   migrator = SchemaMigrator(driver)
   nodes_updated, rels_updated = await migrator.migrate_node_type_rename(
       "Section", "CodeSection"
   )
   ```

## Best Practices

1. **Version Naming**: Use semantic versioning (1.0.0, 1.1.0, 2.0.0)
   - Major (2.0.0): Breaking changes
   - Minor (1.1.0): New features, backward compatible
   - Patch (1.0.1): Bug fixes

2. **Store Versions Regularly**: Store a new version after each schema change

3. **Document Changes**: Always add a description when storing versions

4. **Validate Before Deploying**: Always validate schema compatibility before processing new documents

5. **Export Backups**: Export schemas to JSON files for backup:
   ```bash
   python manage_schema.py export --output schemas/schema_v1.0.0.json
   ```

## Schema Change Types

### Safe Changes (No Migration Needed)
- Adding new node types
- Adding new relationship types
- Adding new patterns
- Modifying descriptions

### Changes Requiring Migration
- Renaming node types
- Renaming relationship types
- Removing node types (data cleanup needed)
- Removing relationship types

## Integration with Build Script

You can integrate automatic schema tracking into `build_kg_from_pdf.py` by adding schema version storage after successful builds. This ensures your schema is always tracked.

## Troubleshooting

### "No schema version stored"
Run `python manage_schema.py store --version 1.0.0` to create initial version.

### Schema comparison shows differences but code looks same
Check for whitespace, ordering, or format differences. The comparison is exact.

### Migration fails
- Ensure APOC is installed for relationship migrations
- Check Neo4j connection
- Review error messages for specific issues

## Next Steps

1. **Store your current schema**: `python manage_schema.py store --version 1.0.0`
2. **Check status**: `python manage_schema.py status`
3. **Update schema as needed** in `build_kg_from_pdf.py`
4. **Track changes** using the compare command
5. **Migrate data** when needed using migration utilities

For detailed API documentation, see the docstrings in `schema_manager.py` and `schema_migration.py`.
