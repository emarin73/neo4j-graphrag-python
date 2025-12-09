
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def inspect_graph():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("--- Node Inspection ---")
        
        with driver.session() as session:
            # 1. Check for Jurisdiction Nodes
            print("\n1. Jurisdiction Nodes:")
            res = session.run("MATCH (j:Jurisdiction) RETURN j.name, j.id")
            jurisdictions = list(res)
            for r in jurisdictions:
                print(f"  Jurisdiction: {r['j.name']} (ID: {r['j.id']})")
            if not jurisdictions: 
                print("  No Jurisdiction nodes found.")

            # 2. Check for Zones (Any ID)
            print("\n2. Recently Created Zones (Limit 10):")
            # We assume new nodes have higher Element IDs, but let's just grab any
            res = session.run("MATCH (z:Zone) RETURN z.id, z.name LIMIT 10")
            for r in res:
                print(f"  Zone: {r['z.name']} (ID: {r['z.id']})")

            # 3. Check for Ordinances
            print("\n3. Ordinances:")
            res = session.run("MATCH (o:Ordinance) RETURN o.id, o.name LIMIT 5")
            for r in res:
                print(f"  Ordinance: {r['o.name']} (ID: {r['o.id']})")

            # 4. Check Schema Version
            print("\n4. Schema Version:")
            res = session.run("MATCH (v:SchemaVersion) RETURN v.version, v.created_at, v.hash")
            for r in res:
                print(f"  Version: {r['v.version']} - Hash: {r['v.hash']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    inspect_graph()
