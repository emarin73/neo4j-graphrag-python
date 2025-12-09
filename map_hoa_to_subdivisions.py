
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def map_hoa_to_subdivisions():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("="*80)
            print("PHASE 2: MAPPING HOAs TO SUBDIVISIONS")
            print("="*80)
            
            # 1. Find existing Parcel->HOA links and infer Subdivision->HOA mappings
            print("\n1. Analyzing existing Parcel->HOA relationships...")
            query_analyze = """
            MATCH (p:Parcel)-[:IN_HOA]->(hoa:HOA)
            MATCH (p)-[:BELONGS_TO]->(s:Subdivision)
            RETURN s.subdivision_id as subdiv_id, hoa.name as hoa_name, hoa.hoa_id as hoa_id, count(p) as parcel_count
            ORDER BY parcel_count DESC
            """
            mappings = list(session.run(query_analyze))
            
            if not mappings:
                print("  No existing Parcel->HOA relationships found.")
                print("  Skipping HOA mapping (no data to infer from)")
                return
            
            print(f"  Found {len(mappings)} Subdivision->HOA mappings to create:")
            for m in mappings:
                print(f"    Subdivision {m['subdiv_id']} -> {m['hoa_name']} ({m['parcel_count']} parcels)")
            
            # 2. Create MANAGED_BY relationships
            print("\n2. Creating MANAGED_BY relationships...")
            query_create = """
            MATCH (p:Parcel)-[:IN_HOA]->(hoa:HOA)
            MATCH (p)-[:BELONGS_TO]->(s:Subdivision)
            WITH s, hoa
            MERGE (s)-[:MANAGED_BY]->(hoa)
            RETURN count(DISTINCT s) as subdivisions_linked
            """
            result = session.run(query_create).single()
            print(f"  ✓ Created MANAGED_BY links for {result['subdivisions_linked']} subdivisions")
            
            # 3. Verify results
            print("\n3. Verifying MANAGED_BY relationships...")
            query_verify = """
            MATCH (s:Subdivision)-[:MANAGED_BY]->(hoa:HOA)
            RETURN count(s) as total_managed_subdivisions
            """
            verify = session.run(query_verify).single()
            print(f"  Total subdivisions with HOA: {verify['total_managed_subdivisions']}")
            
            print("\n" + "="*80)
            print("PHASE 2 COMPLETE")
            print("="*80)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    map_hoa_to_subdivisions()
