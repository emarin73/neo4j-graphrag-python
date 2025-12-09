
import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def query_zone_rules(zone_code, jurisdiction="Weston"):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print(f"Querying rules for Zone: {zone_code} in {jurisdiction}...")
            
            # 1. Find the Zone node
            query_zone = """
            MATCH (z:Zone)
            WHERE z.code = $code AND z.id STARTS WITH $prefix
            RETURN z.id, z.name, z.code
            LIMIT 1
            """
            results = list(session.run(query_zone, code=zone_code, prefix=f"{jurisdiction}::"))
            
            if not results:
                print(f"Zone '{zone_code}' not found in {jurisdiction} jurisdiction.")
                return
            
            zone = results[0]
            print(f"\n--- Zone Details ---")
            print(f"Code: {zone['z.code']}")
            print(f"Name: {zone['z.name']}")
            print(f"ID: {zone['z.id']}")
            
            # 2. Get all sections that apply to this zone
            print(f"\n--- All Rules Applicable to {zone_code} ---")
            
            query_rules = """
            MATCH (z:Zone {id: $zid})<-[:APPLIES_TO]-(s:Section)
            RETURN s.name, s.title, s.text
            ORDER BY s.name
            """
            rules = list(session.run(query_rules, zid=zone['z.id']))
            
            if rules:
                print(f"Found {len(rules)} zone-specific rule(s):\n")
                for r in rules:
                    print(f"{'='*80}")
                    print(f"Section {r['s.name']}: {r['s.title'] or 'Regulation'}")
                    print(f"{'='*80}")
                    print(f"{r['s.text']}\n")
            else:
                print(f"No specific rules explicitly linked to zone {zone_code}.")
                print("\nNote: General city-wide regulations may still apply.")
                print("Use query_parcel.py to see all applicable fence rules for a specific parcel.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    zone_arg = sys.argv[1] if len(sys.argv) > 1 else "R-2"
    jurisdiction_arg = sys.argv[2] if len(sys.argv) > 2 else "Weston"
    query_zone_rules(zone_arg, jurisdiction_arg)
