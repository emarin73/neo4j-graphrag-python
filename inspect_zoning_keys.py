
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def inspect_keys():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("--- Inspecting Zoning Node Keys ---")
            query = """
            MATCH (z:Zoning)
            RETURN keys(z) as k, count(*) as c
            ORDER BY c DESC LIMIT 5
            """
            res = session.run(query)
            for r in res:
                print(f"Keys: {r['k']} (Count: {r['c']})")

            print("\nSample Zoning Properties:")
            res = session.run("MATCH (z:Zoning) RETURN properties(z) LIMIT 1")
            for r in res:
                print(f"{r['properties(z)']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    inspect_keys()
