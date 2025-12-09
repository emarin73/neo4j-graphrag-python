
import os
import argparse
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def link_parcels(jurisdiction: str):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print(f"Linking Parcels for Jurisdiction: {jurisdiction}")
        
        prefix = f"{jurisdiction}::"
        
        with driver.session() as session:
            # 1. Check for target Zones
            print(f"Checking for Zones with prefix '{prefix}'...")
            query = "MATCH (z:Zone) WHERE z.id STARTS WITH $prefix RETURN count(z) as c"
            count = session.run(query, prefix=prefix).single()["c"]
            print(f"  Found {count} namespace zones.")
            
            if count == 0:
                print("  WARNING: No namespaced zones found. Did you build with --jurisdiction?")

            # 2. Perform the Link with City Filter
            print(f"\nExecuting Link Query for jurisdiction '{jurisdiction}'...")
            
            link_query = """
            MATCH (p:Parcel)-[:HAS_ADDRESS]->(a:Address)
            WHERE toLower(a.city) = toLower($jurisdiction)
            
            MATCH (p)-[:HAS_ZONING]->(z:Zoning)
            
            // Handle inconsistent property keys (zone_class, code, zoneclass)
            WITH z, coalesce(z.zone_class, z.code, z.zoneclass) as z_code
            WHERE z_code IS NOT NULL
            
            // Match against Code OR ID
            MATCH (o:Zone)
            WHERE o.id STARTS WITH $prefix 
              AND (
                 o.code = z_code
                 OR o.id = $prefix + z_code
                 OR o.name = z_code
              )
            
            MERGE (z)-[r:GOVERNED_BY]->(o)
            RETURN count(r) as links_created
            """
            
            result = session.run(link_query, prefix=prefix, jurisdiction=jurisdiction)
            links = result.single()["links_created"]
            print(f"Links created: {links}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Link Parcels to Multi-City Zones")
    parser.add_argument("--jurisdiction", type=str, required=True, help="Name of the jurisdiction (e.g. Weston)")
    args = parser.parse_args()
    link_parcels(args.jurisdiction)
