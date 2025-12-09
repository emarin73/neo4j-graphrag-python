
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def inspect_r2():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("--- Inspecting 'R-2' Zones ---")
            query = """
            MATCH (z:Zone)
            WHERE z.id CONTAINS 'R-2' OR z.code = 'R-2' OR z.name CONTAINS 'R-2'
            RETURN z.id, z.name, z.code, z.type
            """
            res = list(session.run(query))
            for r in res:
                print(f"Found R-2 match: ID='{r['z.id']}', Name='{r['z.name']}', Code='{r['z.code']}'")
            
            print("\n--- Inspecting 'Single Family' Zones ---")
            query_sf = """
            MATCH (z:Zone)
            WHERE toLower(z.name) CONTAINS 'single family'
            RETURN z.id, z.name, z.code
            """
            res_sf = list(session.run(query_sf))
            for r in res_sf:
                print(f"Found SF match: ID='{r['z.id']}', Name='{r['z.name']}', Code='{r['z.code']}'")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    inspect_r2()
