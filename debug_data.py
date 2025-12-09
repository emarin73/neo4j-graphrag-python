
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def inspect_debug():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("--- Forensic Inspection ---")
            
            # 1. Check what Zones exist and their IDs
            print("\n1. Existing Zones (Limit 10):")
            res = session.run("MATCH (z:Zone) RETURN z.id, z.name LIMIT 10")
            count = 0
            for r in res:
                print(f"  Zone ID: '{r['z.id']}' - Name: '{r['z.name']}'")
                count += 1
            if count == 0:
                print("  No Zone nodes found at all.")

            # 2. Check Parcel Address Structure
            print("\n2. Parcel Address Data:")
            # Guessing relationship HAS_ADDRESS or similar
            query = """
            MATCH (p:Parcel)
            OPTIONAL MATCH (p)-[:HAS_ADDRESS]->(a:Address)
            RETURN p.parcel_id, properties(p) as p_props, properties(a) as a_props LIMIT 1
            """
            res = session.run(query).single()
            if res:
                print(f"  Parcel ID: {res['p.parcel_id']}")
                print(f"  Parcel Properties: {res['p_props']}")
                print(f"  Address Properties: {res['a_props']}")
            else:
                print("  No Parcels found.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    inspect_debug()
