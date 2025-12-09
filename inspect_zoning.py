
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def inspect_zoning():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("--- Inspecting Zoning Nodes ---")
            query = """
            MATCH (p:Parcel)-[:HAS_ADDRESS]->(a:Address)
            WHERE toLower(a.city) CONTAINS 'weston'
            MATCH (p)-[:HAS_ZONING]->(z:Zoning)
            RETURN properties(z) as props LIMIT 5
            """
            res = session.run(query)
            for r in res:
                print(f"Props: {r['props']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    inspect_zoning()
