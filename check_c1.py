
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def check_c1():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("Checking for 'C-1' Zones...")
            # Check ID or Name containing 'C-1'
            query = """
            MATCH (z:Zone)
            WHERE z.id CONTAINS 'C-1' OR z.name CONTAINS 'C-1'
            RETURN z.id, z.name
            """
            res = list(session.run(query))
            for r in res:
                print(f"Found: ID='{r['z.id']}' Name='{r['z.name']}'")
            
            if not res:
                print("No Zone found containing 'C-1'.")
                
            # List ALL zones again just to be sure
            print("\nList distinct Zone IDs:")
            res = session.run("MATCH (z:Zone) RETURN distinct z.id")
            for r in res:
                print(f"  {r['z.id']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    check_c1()
