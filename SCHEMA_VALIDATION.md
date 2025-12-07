# Schema Validation Guide: Can Your Schema Answer Parcel-Specific Questions?

This guide helps you verify if your knowledge graph schema can answer questions like:
- **"What fence rules apply to my parcel?"**
- **"What are the fencing requirements for zone R-1?"**
- **"What obligations apply to my property's zone?"**

## 🎯 The Question Breakdown

To answer **"What fence rules apply to my parcel?"**, your schema needs to support:

1. ✅ **Parcel/Property** → Know which property you're asking about
2. ✅ **Zone Assignment** → Know which zone the parcel is in
3. ✅ **Section → Zone** → Which sections apply to that zone
4. ✅ **Section → Topic** → Which sections are about fencing
5. ✅ **Section → Obligation** → What are the specific requirements
6. ✅ **Section → Prohibition** → What's not allowed

## 🔍 Current Schema Analysis

### What You Have ✅

Your current schema includes:
- **Zone** node type - Zoning districts (R-1, R-2, C-1, etc.)
- **Section** node type - Code sections
- **Topic** node type - Legal topics (includes fencing)
- **Obligation** node type - Requirements that must be followed
- **Prohibition** node type - Activities that are forbidden
- **APPLIES_TO** relationship - Section → Zone
- **HAS_TOPIC** relationship - Section → Topic
- **IMPOSED_BY** relationship - Obligation/Prohibition → Section

### What Might Be Missing ⚠️

1. **Parcel/Property** node type - To represent specific properties
2. **Property → Zone** relationship - To link properties to their zones
3. **Property-specific attributes** - Address, parcel ID, lot number, etc.

## ✅ Validation Queries

Run these queries to test your schema's capability:

### Test 1: Can You Find Fence Rules by Zone?

```cypher
// Find all fencing rules for a specific zone (e.g., R-1)
MATCH (z:Zone)
WHERE toLower(z.name) CONTAINS 'r-1' OR z.name = 'R-1'
MATCH (s:Section)-[:APPLIES_TO]->(z)
MATCH (s)-[:HAS_TOPIC]->(t:Topic)
WHERE toLower(t.name) CONTAINS 'fence'
OPTIONAL MATCH (s)-[:IMPOSED_BY]-(o:Obligation)
OPTIONAL MATCH (s)-[:IMPOSED_BY]-(p:Prohibition)
RETURN 
    z.name as Zone,
    s.name as Section,
    t.name as Topic,
    collect(DISTINCT o.name) as Obligations,
    collect(DISTINCT p.name) as Prohibitions
```

**Expected Result**: You should see fence-related sections that apply to the zone.

### Test 2: Can You Find All Zone-Specific Fencing Requirements?

```cypher
// Get all zones with fencing rules
MATCH (z:Zone)
MATCH (s:Section)-[:APPLIES_TO]->(z)
MATCH (s)-[:HAS_TOPIC]->(t:Topic)
WHERE toLower(t.name) CONTAINS 'fence'
WITH z, count(DISTINCT s) as fenceSections
WHERE fenceSections > 0
RETURN z.name as Zone, fenceSections as NumberOfFenceSections
ORDER BY fenceSections DESC
```

**Expected Result**: List of zones with fencing regulations and how many sections each has.

### Test 3: Can You Get Complete Fence Requirements for a Zone?

```cypher
// Complete fence requirements for a zone (replace 'R-1' with your zone)
MATCH (z:Zone {name: 'R-1'})
MATCH (s:Section)-[:APPLIES_TO]->(z)
MATCH (s)-[:HAS_TOPIC]->(t:Topic)
WHERE toLower(t.name) CONTAINS 'fence'
OPTIONAL MATCH (o:Obligation)-[:IMPOSED_BY]->(s)
OPTIONAL MATCH (pr:Prohibition)-[:IMPOSED_BY]->(s)
OPTIONAL MATCH (pen:Penalty)-[:FOR_VIOLATION_OF]->(o)
OPTIONAL MATCH (pen)-[:FOR_VIOLATION_OF]->(pr)
OPTIONAL MATCH (a:Actor)-[:ENFORCES]->(s)
RETURN 
    z.name as Zone,
    s.name as Section,
    t.name as Topic,
    collect(DISTINCT o.name) as Obligations,
    collect(DISTINCT pr.name) as Prohibitions,
    collect(DISTINCT pen.name) as Penalties,
    collect(DISTINCT a.name) as EnforcingActors
```

**Expected Result**: Complete list of all fencing requirements, prohibitions, penalties, and who enforces them.

### Test 4: Schema Completeness Check

```cypher
// Check if you have the necessary relationships
MATCH (s:Section)-[r1:APPLIES_TO]->(z:Zone)
MATCH (s)-[r2:HAS_TOPIC]->(t:Topic)
WHERE toLower(t.name) CONTAINS 'fence'
RETURN 
    count(DISTINCT z) as ZonesWithFenceRules,
    count(DISTINCT s) as FenceSections,
    count(DISTINCT t) as FenceTopics
```

**Expected Result**: Should return counts > 0 if the schema is working.

## 🚨 Gap Analysis

### Scenario 1: You Know Your Zone

**Question**: "What fence rules apply to my parcel in zone R-1?"

**Answer**: ✅ **YES, your schema can answer this!**

Use Test 3 query above with your zone name.

### Scenario 2: You Only Know Your Address/Parcel ID

**Question**: "What fence rules apply to my parcel at 123 Main St?"

**Answer**: ⚠️ **PARTIALLY** - You need to:
1. Know which zone your address is in (external knowledge)
2. Then use the query from Scenario 1

### Scenario 3: You Want to Query by Property Attributes

**Question**: "What fence rules apply to my property based on my lot size/type?"

**Answer**: ❌ **NO** - This requires additional schema elements:
- Property node type
- Property attributes (lot size, property type, etc.)
- Property → Zone relationship

## 🔧 Schema Enhancement Recommendations

If you need to answer parcel-specific questions without knowing the zone, consider adding:

### Option 1: Add Property/Parcel Node Type (Recommended)

Add to your `build_kg_from_pdf.py` schema:

```python
DEFAULT_NODE_TYPES: list[EntityInputType] = [
    # ... existing node types ...
    {
        "label": "Property",
        "description": "A specific property, parcel, or lot with an address, parcel ID, or lot number",
        "properties": [
            {"name": "address", "type": "STRING"},
            {"name": "parcel_id", "type": "STRING"},
            {"name": "lot_number", "type": "STRING"},
            {"name": "property_type", "type": "STRING"},
        ]
    },
]

DEFAULT_RELATIONSHIP_TYPES: list[RelationInputType] = [
    # ... existing relationship types ...
    {
        "label": "LOCATED_IN",
        "description": "Property is located in a specific zone",
    },
]

DEFAULT_PATTERNS: list[tuple[str, str, str]] = [
    # ... existing patterns ...
    ("Property", "LOCATED_IN", "Zone"),
]
```

### Option 2: Add Zone Attributes to Sections

Enhance sections with zone information as properties:

```python
{
    "label": "Section",
    "description": "A codified section (e.g. §12-3-105)",
    "properties": [
        {"name": "applicable_zones", "type": "LIST"},
        {"name": "zone_specific", "type": "BOOLEAN"},
    ]
}
```

### Option 3: Use External Zone Lookup

Keep current schema, but maintain a separate mapping:
- Address → Zone (external database or file)
- Use that to query the graph

## 📊 Validation Checklist

Use this checklist to verify your schema:

- [ ] **Can find sections by zone**: Run Test 1 ✅
- [ ] **Can find fencing topics**: Run Test 2 ✅
- [ ] **Can get complete requirements**: Run Test 3 ✅
- [ ] **Has APPLIES_TO relationships**: Check with Test 4 ✅
- [ ] **Has HAS_TOPIC relationships**: Check with Test 4 ✅
- [ ] **Has Obligations linked**: Check if Obligations exist
- [ ] **Has Prohibitions linked**: Check if Prohibitions exist
- [ ] **Can query by address**: ⚠️ Requires Property node or external lookup
- [ ] **Can query by parcel ID**: ⚠️ Requires Property node or external lookup

## 🎯 Practical Workflow

### Current Workflow (Zone Known)

1. **Identify your zone** (check with city/county, property records)
2. **Run query**:
   ```cypher
   MATCH (z:Zone {name: 'YOUR_ZONE'})
   MATCH (s:Section)-[:APPLIES_TO]->(z)
   MATCH (s)-[:HAS_TOPIC]->(t:Topic)
   WHERE toLower(t.name) CONTAINS 'fence'
   RETURN s, t
   ```
3. **Get complete requirements** using Test 3 query

### Enhanced Workflow (After Adding Property Node)

1. **Add your property**:
   ```cypher
   CREATE (p:Property {
       address: '123 Main St',
       parcel_id: 'PARCEL-123',
       zone: 'R-1'
   })-[:LOCATED_IN]->(z:Zone {name: 'R-1'})
   ```

2. **Query by address**:
   ```cypher
   MATCH (p:Property {address: '123 Main St'})-[:LOCATED_IN]->(z:Zone)
   MATCH (s:Section)-[:APPLIES_TO]->(z)
   MATCH (s)-[:HAS_TOPIC]->(t:Topic)
   WHERE toLower(t.name) CONTAINS 'fence'
   RETURN s, t
   ```

## ✅ Conclusion

**Your current schema CAN answer "What fence rules apply to my parcel?" IF:**
- You know the zone your parcel is in, OR
- You can look up the zone first

**To answer directly by address/parcel ID, you need to:**
- Add a Property node type, OR
- Maintain an external Address → Zone mapping

## 🚀 Next Steps

1. **Run the validation queries** above to test your current schema
2. **Check if you have zone data** in your graph:
   ```cypher
   MATCH (z:Zone)
   RETURN z.name, count{(z)<-[:APPLIES_TO]-()} as sections
   ```
3. **Test a real query** with your actual zone
4. **Decide if you need Property nodes** based on your use case
5. **If needed, update schema** and reprocess your PDF

---

**Bottom Line**: Your schema is well-designed for zone-based queries! For address-based queries, consider adding Property nodes or using external zone lookup.
