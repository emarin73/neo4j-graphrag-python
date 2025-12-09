
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def debug_links():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            # 1. Check created links
            print("1. Inspecting Linked Zones:")
            result = session.run("MATCH (z:Zoning)-[:GOVERNED_BY]->(o:Zone) RETURN z.zone_class, o.name, o.id LIMIT 10")
            linked = list(result)
            for r in linked:
                print(f"  Zoning '{r[0]}' -> Ordinance Zone '{r[1]}' (ID: {r[2]})")

            if not linked:
                print("  No links found.")

            # 2. Check Fence Topics
            print("\n2. Checking Fence Topics:")
            result = session.run("MATCH (t:Topic) WHERE toLower(t.id) CONTAINS 'fence' OR toLower(t.description) CONTAINS 'fence' RETURN t.id, t.description LIMIT 5")
            topics = list(result)
            for r in topics:
                print(f"  Topic: {r[0]} ({r[1]})")

            # 3. Check Zones with Fence Rules
            print("\n3. Zones with Fence Rules:")
            # Path: (Topic)<-[:HAS_TOPIC]-(Section)-[:APPLIES_TO]->(Zone)
            query = """
            MATCH (t:Topic)<-[:HAS_TOPIC]-(s:Section)-[:APPLIES_TO]->(z:Zone)
            WHERE toLower(t.id) CONTAINS 'fence'
            RETURN DISTINCT z.name, z.id LIMIT 10
            """
            result = session.run(query)
            zones = list(result)
            for r in zones:
                print(f"  Zone with Fence Rules: {r[0]} (ID: {r[1]})")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    debug_links()
