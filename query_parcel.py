
import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def query_parcel(parcel_id):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print(f"Querying Parcel ID: {parcel_id}...")
            
            # 1. Get Parcel Info & Linked Zone
            query_info = """
            MATCH (p:Parcel {parcel_id: $pid})
            OPTIONAL MATCH (p)-[:HAS_ADDRESS]->(a:Address)
            OPTIONAL MATCH (p)-[:HAS_ZONING]->(z:Zoning)
            OPTIONAL MATCH (z)-[:GOVERNED_BY]->(oz:Zone)
            RETURN p, a, z, oz LIMIT 1
            """
            # Use list + index 0 to avoid warning
            results = list(session.run(query_info, pid=parcel_id))
            
            if not results:
                print(f"Parcel {parcel_id} not found.")
                return

            result = results[0]
            addr = result['a']
            zoning = result['z']
            ord_zone = result['oz']
            
            print("\n--- Property Details ---")
            if addr:
                print(f"Address: {addr.get('street', 'N/A')}, {addr.get('city', 'N/A')}")
            if zoning:
                # Handle inconsistent keys again just in case
                code = zoning.get('zone_class') or zoning.get('code') or zoning.get('zoneclass')
                print(f"Zoning Code (Parcel Data): {code}")
            
            if ord_zone:
                print(f"Mapped to Ordinance Zone: {ord_zone.get('name')} (ID: {ord_zone.get('id')})")
            else:
                print("WARNING: This Parcel is NOT linked to an Ordinance Zone.")
                print("Cannot retrieve specific rules.")
                return

            # 2. Get Applicable Fence Rules
            print("\n--- Applicable Fence Rules ---")
            
            # First try zone-specific rules
            query_zone_rules = """
            MATCH (oz:Zone {id: $zid})<-[:APPLIES_TO]-(s:Section)
            WHERE toLower(s.text) CONTAINS 'fence' 
               OR toLower(s.title) CONTAINS 'fence'
            RETURN s.name, s.title, s.text
            ORDER BY s.name
            """
            zone_rules = list(session.run(query_zone_rules, zid=ord_zone.get('id')))
            
            if zone_rules:
                print(f"Found {len(zone_rules)} zone-specific fence rule(s):\n")
                for r in zone_rules:
                    print(f"{'='*80}")
                    print(f"Section {r['s.name']}: {r['s.title'] or 'Fence Regulations'}")
                    print(f"{'='*80}")
                    print(f"{r['s.text']}\n")
            else:
                # Show general city-wide fence rules
                print("No zone-specific fence rules found.")
                print("Displaying general Weston fence regulations:\n")
                
                query_general = """
                MATCH (s:Section)
                WHERE s.id STARTS WITH 'Weston::' 
                  AND toLower(s.text) CONTAINS 'fence'
                RETURN s.name, s.text
                ORDER BY s.name
                """
                general_rules = list(session.run(query_general))
                
                if general_rules:
                    print(f"Found {len(general_rules)} general fence regulation(s):\n")
                    for r in general_rules:
                        print(f"{'='*80}")
                        print(f"Section {r['s.name']}")
                        print(f"{'='*80}")
                        print(f"{r['s.text']}\n")
                else:
                    print("No fence regulations found in the knowledge graph.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    pid_arg = sys.argv[1] if len(sys.argv) > 1 else "503911073240"
    query_parcel(pid_arg)
