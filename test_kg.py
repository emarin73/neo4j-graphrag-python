
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def test_weston_kg():
    print("Testing 'Weston' Knowledge Graph...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            # 1. Verify Jurisdiction
            print("\n1. Checking Jurisdiction Node:")
            res = session.run("MATCH (j:Jurisdiction {name: 'Weston'}) RETURN j.id, j.name").single()
            if res:
                print(f"  ✓ Found Jurisdiction: {res['j.name']}")
            else:
                print("  X Jurisdiction 'Weston' not found.")

            # 2. Check for Namespaced Zones
            print("\n2. Checking for Namespaced Zones (Weston::...):")
            res = session.run("MATCH (z:Zone) WHERE z.id STARTS WITH 'Weston::' RETURN count(z) as c").single()
            count = res['c']
            print(f"  Found {count} zones with 'Weston::' prefix.")
            
            # 3. Check for Linked Parcels
            print("\n3. Checking Parcel -> Zone Links:")
            query = """
            MATCH (p:Parcel)-[:HAS_ZONING]->(:Zoning)-[:GOVERNED_BY]->(z:Zone)
            WHERE z.id STARTS WITH 'Weston::'
            RETURN count(p) as c
            """
            res = session.run(query).single()
            links = res['c']
            print(f"  Found {links} Parcels linked to Weston Zones.")
            
            # 4. Query All Fence Rules
            print("\n4. Query: 'What are the fence rules?' (All matches)")
            query = """
            MATCH (s:Section)
            WHERE toLower(s.text) CONTAINS 'fence'
            AND s.id STARTS WITH 'Weston::'
            RETURN s.name, s.text
            ORDER BY s.name
            """
            rules = list(session.run(query))
            print(f"  Found {len(rules)} related sections:")
            for r in rules:
                print(f"\n--- {r['s.name']} ---\n{r['s.text']}\n")
                
            if not rules:
                print("  No fence rules found under Weston jurisdiction.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    test_weston_kg()
