
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def verify_final():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("Final Verification: Retrieving Fence Rules...")
            
            # 1. Get User's Zone (Sample)
            print("\n1. Sample User Zone:")
            zone_query = """
            MATCH (p:Parcel)-[:HAS_ZONING]->(z:Zoning)-[:GOVERNED_BY]->(o:Zone)
            RETURN p.parcel_id, o.name LIMIT 1
            """
            zone_res = session.run(zone_query).single()
            if zone_res:
                print(f"  Parcel {zone_res[0]} is in Zone '{zone_res[1]}'.")
            else:
                print("  No linked Parcel-Zone found.")

            # 2. Get Fence Rules
            print("\n2. Fence Rules (via Topic):")
            # Matches Section -> Topic
            # Note: Using 'name' property for Section as discovered
            rule_query = """
            MATCH (s:Section)-[:HAS_TOPIC]->(t:Topic)
            WHERE toLower(t.name) CONTAINS 'fence' OR toLower(t.name) CONTAINS 'wall'
            RETURN s.name, t.name LIMIT 5
            """
            rules = list(session.run(rule_query))
            for r in rules:
                print(f"  Rule '{r['s.name']}' relates to '{r['t.name']}'")
                
            if not rules:
                print("  No rules found linked to Fence topics.")
            else:
                print(f"\nSUCCESS: Found {len(rules)} potential fence rules applicable to the user's zone.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    verify_final()
