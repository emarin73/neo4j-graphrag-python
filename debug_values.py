
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def debug_values(jurisdiction):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print(f"--- Value Analysis for {jurisdiction} ---")
            
            # 1. Get Weston Parcel Zoning Classes
            print("\n1. Top 10 Zoning Classes (from Parcels in Weston):")
            query_parcel = """
            MATCH (p:Parcel)-[:HAS_ADDRESS]->(a:Address)
            WHERE toLower(a.city) CONTAINS toLower($jurisdiction)
            MATCH (p)-[:HAS_ZONING]->(z:Zoning)
            RETURN z.zone_class as cls, count(*) as c
            ORDER BY c DESC LIMIT 10
            """
            res = session.run(query_parcel, jurisdiction=jurisdiction)
            for r in res:
                print(f"  Class: '{r['cls']}' (Count: {r['c']})")

            # 2. Get Actual Zone IDs
            print("\n2. Actual Zone IDs (in Graph):")
            query_zone = """
            MATCH (z:Zone)
            WHERE z.id STARTS WITH 'Weston::'
            RETURN z.id, z.name
            """
            res = session.run(query_zone)
            ids = []
            for r in res:
                ids.append(r['z.id'])
                print(f"  ID: '{r['z.id']}' - Name: '{r['z.name']}'")
            
            if not ids:
                print("  No Weston Zones found.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    debug_values("Weston")
