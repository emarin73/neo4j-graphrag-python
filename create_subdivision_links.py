
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def create_subdivision_links():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("="*80)
            print("PHASE 1: CREATING PARCEL-SUBDIVISION LINKS")
            print("="*80)
            
            # 1. Count parcels without subdivision links
            print("\n1. Checking current state...")
            query_check = """
            MATCH (p:Parcel)
            WHERE p.parcel_id IS NOT NULL
            WITH p, exists((p)-[:BELONGS_TO]->(:Subdivision)) as has_link
            RETURN 
                count(p) as total_parcels,
                sum(CASE WHEN has_link THEN 1 ELSE 0 END) as linked_parcels,
                sum(CASE WHEN has_link THEN 0 ELSE 1 END) as unlinked_parcels
            """
            stats = session.run(query_check).single()
            print(f"  Total parcels: {stats['total_parcels']}")
            print(f"  Already linked: {stats['linked_parcels']}")
            print(f"  Need linking: {stats['unlinked_parcels']}")
            
            # 2. Create Subdivision nodes and links for all parcels
            print("\n2. Creating Subdivision nodes and BELONGS_TO relationships...")
            print("  (This may take a few minutes for large datasets)")
            
            query_create = """
            MATCH (p:Parcel)
            WHERE p.parcel_id IS NOT NULL
            WITH p, substring(p.parcel_id, 0, 8) as subdiv_id
            MERGE (s:Subdivision {subdivision_id: subdiv_id})
            MERGE (p)-[:BELONGS_TO]->(s)
            RETURN count(p) as processed
            """
            result = session.run(query_create).single()
            print(f"  ✓ Processed {result['processed']} parcels")
            
            # 3. Verify results
            print("\n3. Verifying results...")
            verify_stats = session.run(query_check).single()
            print(f"  Total parcels: {verify_stats['total_parcels']}")
            print(f"  Linked parcels: {verify_stats['linked_parcels']}")
            print(f"  Unlinked parcels: {verify_stats['unlinked_parcels']}")
            
            # 4. Count unique subdivisions
            query_subdiv_count = """
            MATCH (s:Subdivision)
            RETURN count(s) as total_subdivisions
            """
            subdiv_count = session.run(query_subdiv_count).single()
            print(f"  Total subdivisions: {subdiv_count['total_subdivisions']}")
            
            print("\n" + "="*80)
            print("PHASE 1 COMPLETE")
            print("="*80)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    create_subdivision_links()
