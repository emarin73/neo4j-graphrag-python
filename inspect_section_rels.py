
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Re-load dotenv (now cleaned)
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def inspect_section_rels():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            # Find Section § 124.33 and show ALL outgoing/incoming relationships
            section_code = '§ 124.33'
            print(f"Inspecting Relationships for Section {section_code}...")
            
            # Note: We match on 'code' property as seen in earlier inspection
            query = """
            MATCH (s {code: $code})-[r]-(n)
            RETURN type(r), startNode(r) = s as is_outgoing, labels(n), n.name, n.id, n.code
            LIMIT 20
            """
            result = list(session.run(query, code=section_code))
            
            if not result:
                print(f"No relationships found for Section with code '{section_code}'.")
                # Try partial match if exact match fails
                print("Trying partial match...")
                partial_query = "MATCH (s:Section) WHERE s.code CONTAINS '124.33' RETURN s.code LIMIT 5"
                partial = list(session.run(partial_query))
                print(f"Found Code Matches: {[r['s.code'] for r in partial]}")
            
            for row in result:
                direction = "->" if row['is_outgoing'] else "<-"
                name = row['n.name'] or row['n.id'] or row['n.code'] or "Unknown"
                print(f"  (s) -[{row['type(r)']}]- {direction} ({list(row['labels(n)'])[0]}) '{name}'")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    inspect_section_rels()
