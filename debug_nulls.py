
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def unique_check():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("--- Forensic Check II ---")
            
            # 1. Check for Null IDs in Zones
            query = "MATCH (z:Zone) WHERE z.id IS NULL RETURN count(z) as c"
            nulls = session.run(query).single()["c"]
            print(f"Zones with NULL IDs: {nulls}")
            
            # 2. Check for Non-Null but no prefix
            query = "MATCH (z:Zone) WHERE z.id IS NOT NULL AND NOT z.id STARTS WITH 'Weston::' RETURN count(z) as c"
            others = session.run(query).single()["c"]
            print(f"Zones with Non-Null IDs (no prefix): {others}")

            # 3. Check for Addresses in Weston
            print("\nChecking Addresses...")
            query = "MATCH (a:Address) WHERE toLower(a.city) CONTAINS 'weston' RETURN count(a) as c"
            weston_count = session.run(query).single()["c"]
            print(f"Addresses with city 'Weston': {weston_count}")
            
            if weston_count > 0:
                print("  Sample Weston Address:")
                res = session.run("MATCH (a:Address) WHERE toLower(a.city) CONTAINS 'weston' RETURN a.street, a.city LIMIT 1").single()
                print(f"  {res['a.street']}, {res['a.city']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    unique_check()
