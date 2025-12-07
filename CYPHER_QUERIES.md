# Cypher Queries for Exploring Your Knowledge Graph

This guide provides ready-to-use Cypher queries for exploring the knowledge graph created from your Weston, FL Code of Ordinances PDF.

## 📊 Overview Queries

### See All Node Types and Counts
```cypher
MATCH (n)
RETURN labels(n)[0] as NodeType, count(*) as Count
ORDER BY Count DESC
```

### See All Relationship Types and Counts
```cypher
MATCH ()-[r]->()
RETURN type(r) as RelationshipType, count(*) as Count
ORDER BY Count DESC
```

### Get Total Statistics
```cypher
MATCH (n)
WITH count(n) as totalNodes
MATCH ()-[r]->()
WITH totalNodes, count(r) as totalRelationships
RETURN totalNodes, totalRelationships
```

## 🏛️ Ordinance & Section Queries

### View All Ordinances
```cypher
MATCH (o:Ordinance)
RETURN o
LIMIT 25
```

### Find Specific Ordinance
```cypher
MATCH (o:Ordinance)
WHERE o.name CONTAINS '2024' OR o.id CONTAINS '2024'
RETURN o
LIMIT 10
```

### See Sections Enacted by Ordinances
```cypher
MATCH (o:Ordinance)-[:ENACTS]->(s:Section)
RETURN o, s
LIMIT 25
```

### View Section Hierarchy (Title → Chapter → Section)
```cypher
MATCH (t:Title)-[:PART_OF*0..]-(c:Chapter)-[:PART_OF*0..]-(s:Section)
RETURN t, c, s
LIMIT 25
```

### Find Sections by Number
```cypher
MATCH (s:Section)
WHERE s.name CONTAINS '12-3' OR s.id CONTAINS '12-3'
RETURN s
LIMIT 10
```

## 🔗 Relationship Exploration

### See All Relationships from a Section
```cypher
MATCH (s:Section)-[r]->(target)
RETURN s, type(r) as RelationshipType, target
LIMIT 25
```

### Find Sections That Reference Other Sections
```cypher
MATCH (s1:Section)-[:REFERS_TO]->(s2:Section)
RETURN s1, s2
LIMIT 25
```

### Find Sections That Apply to Specific Zones
```cypher
MATCH (s:Section)-[:APPLIES_TO]->(z:Zone)
RETURN s, z
LIMIT 25
```

### See Topics Covered by Sections
```cypher
MATCH (s:Section)-[:HAS_TOPIC]->(t:Topic)
RETURN s, t
LIMIT 25
```

## 🚧 Fencing-Specific Queries

### Find All Fencing-Related Content
```cypher
MATCH (n)
WHERE toLower(toString(n.name)) CONTAINS 'fence' 
   OR toLower(toString(n.description)) CONTAINS 'fence'
   OR toLower(toString(n.name)) CONTAINS 'fencing'
   OR toLower(toString(n.description)) CONTAINS 'fencing'
RETURN labels(n)[0] as NodeType, n
LIMIT 50
```

### Find Sections About Fencing
```cypher
MATCH (s:Section)-[:HAS_TOPIC]->(t:Topic)
WHERE toLower(t.name) CONTAINS 'fence' OR toLower(t.name) CONTAINS 'fencing'
RETURN s, t
```

### Find Obligations Related to Fencing
```cypher
MATCH (o:Obligation)-[:IMPOSED_BY]->(s:Section)
WHERE toLower(toString(o.name)) CONTAINS 'fence'
   OR toLower(toString(o.description)) CONTAINS 'fence'
RETURN o, s
```

### Find Prohibitions Related to Fencing
```cypher
MATCH (p:Prohibition)-[:IMPOSED_BY]->(s:Section)
WHERE toLower(toString(p.name)) CONTAINS 'fence'
   OR toLower(toString(p.description)) CONTAINS 'fence'
RETURN p, s
```

## 📋 Rules & Requirements Queries

### View All Obligations
```cypher
MATCH (o:Obligation)-[:IMPOSED_BY]->(s:Section)
RETURN o, s
LIMIT 25
```

### View All Prohibitions
```cypher
MATCH (p:Prohibition)-[:IMPOSED_BY]->(s:Section)
RETURN p, s
LIMIT 25
```

### Find Penalties for Violations
```cypher
MATCH (pen:Penalty)-[:FOR_VIOLATION_OF]->(target)
RETURN pen, target, labels(target)[0] as ViolationType
LIMIT 25
```

### See Which Actors Enforce Sections
```cypher
MATCH (a:Actor)-[:ENFORCES]->(s:Section)
RETURN a, s
LIMIT 25
```

## 🔍 Search & Filter Queries

### Search for Any Node by Text
```cypher
MATCH (n)
WHERE toLower(toString(n.name)) CONTAINS 'fence'
   OR toLower(toString(n.description)) CONTAINS 'fence'
   OR toLower(toString(n.text)) CONTAINS 'fence'
RETURN labels(n)[0] as NodeType, n
LIMIT 25
```

### Find Terms Defined in Sections
```cypher
MATCH (s:Section)-[:DEFINES]->(t:Term)
RETURN s, t
LIMIT 25
```

### Find All Zones
```cypher
MATCH (z:Zone)
RETURN z
ORDER BY z.name
```

## 🌐 Graph Visualization Queries

### View a Complete Section with All Connections
```cypher
MATCH (s:Section)
WHERE s.name CONTAINS '12-3' OR s.id CONTAINS '12-3'
MATCH path = (s)-[*1..2]-(connected)
RETURN path
LIMIT 1
```

### View Ordinance Network
```cypher
MATCH path = (o:Ordinance)-[*1..3]-(connected)
WHERE o.name IS NOT NULL
RETURN path
LIMIT 5
```

### View Topic Network (Sections Related to Same Topic)
```cypher
MATCH (t:Topic)<-[:HAS_TOPIC]-(s:Section)
WITH t, collect(s) as sections
WHERE size(sections) > 1
MATCH path = (t)<-[:HAS_TOPIC]-(s:Section)
RETURN path
LIMIT 10
```

## 📈 Analysis Queries

### Count Sections by Topic
```cypher
MATCH (s:Section)-[:HAS_TOPIC]->(t:Topic)
RETURN t.name as Topic, count(s) as SectionCount
ORDER BY SectionCount DESC
```

### Count Obligations by Section
```cypher
MATCH (o:Obligation)-[:IMPOSED_BY]->(s:Section)
RETURN s.name as Section, count(o) as ObligationCount
ORDER BY ObligationCount DESC
LIMIT 20
```

### Find Most Referenced Sections
```cypher
MATCH (s:Section)<-[:REFERS_TO]-(referrer)
RETURN s.name as Section, count(referrer) as ReferenceCount
ORDER BY ReferenceCount DESC
LIMIT 20
```

### Find Sections with Most Relationships
```cypher
MATCH (s:Section)-[r]->()
WITH s, count(r) as relCount
WHERE relCount > 2
RETURN s.name as Section, relCount
ORDER BY relCount DESC
LIMIT 20
```

## 🎯 Specific Use Case: Find Fencing Requirements

### Complete Fencing Requirements Query
```cypher
// Find all fencing-related content with full context
MATCH path = (n)-[*0..2]-(related)
WHERE toLower(toString(n.name)) CONTAINS 'fence'
   OR toLower(toString(n.description)) CONTAINS 'fence'
   OR toLower(toString(n.text)) CONTAINS 'fence'
   OR (labels(n)[0] = 'Topic' AND toLower(n.name) CONTAINS 'fence')
RETURN path
LIMIT 10
```

### Fencing Rules with Penalties
```cypher
MATCH (s:Section)-[:HAS_TOPIC]->(t:Topic)
WHERE toLower(t.name) CONTAINS 'fence'
MATCH (s)-[:IMPOSED_BY]-(rule)
OPTIONAL MATCH (pen:Penalty)-[:FOR_VIOLATION_OF]->(rule)
RETURN s, t, rule, pen
```

## 💡 Tips for Using These Queries

1. **Start Simple**: Begin with overview queries to understand your graph structure
2. **Use LIMIT**: Always use `LIMIT` when exploring to avoid overwhelming results
3. **Visualize**: In Neo4j Browser, these queries will show graph visualizations
4. **Modify**: Adjust the `CONTAINS` clauses to search for different terms
5. **Combine**: You can combine multiple patterns in one query

## 🔧 Customizing Queries

### Change Search Term
Replace `'fence'` with any term you want to search for:
```cypher
MATCH (n)
WHERE toLower(toString(n.name)) CONTAINS 'YOUR_TERM_HERE'
RETURN n
```

### Change Node Type
Replace `Section` with any node type:
```cypher
MATCH (n:YOUR_NODE_TYPE)
RETURN n
LIMIT 25
```

### Change Relationship Type
Replace `HAS_TOPIC` with any relationship type:
```cypher
MATCH (a)-[:YOUR_REL_TYPE]->(b)
RETURN a, b
LIMIT 25
```

## 📝 Quick Reference

| Query Type | Use Case |
|------------|----------|
| Overview queries | Get general statistics |
| Ordinance & Section | Navigate legal structure |
| Relationship Exploration | Understand connections |
| Fencing-Specific | Find fence-related content |
| Rules & Requirements | Find obligations/prohibitions |
| Search & Filter | Find specific content |
| Graph Visualization | Visual exploration |
| Analysis | Statistical insights |

---

**Note**: These queries are optimized for the schema created from your Weston, FL Code of Ordinances. Adjust node labels and relationship types if your schema differs.
