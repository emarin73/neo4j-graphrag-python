
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def create_subdivision_links_batch():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("="*80)
            print("PHASE 1: CREATING PARCEL-SUBDIVISION LINKS (BATCH MODE)")
            print("="*80)
            
            # 1. Create all subdivision nodes first
            print("\n1. Creating Subdivision nodes...")
            query_create_subdivisions = """
            MATCH (p:Parcel)
            WHERE p.parcel_id IS NOT NULL
            WITH DISTINCT substring(p.parcel_id, 0, 8) as subdiv_id
            MERGE (s:Subdivision {subdivision_id: subdiv_id})
            RETURN count(s) as created
            """
            result = session.run(query_create_subdivisions).single()
            print(f"  ✓ Ensured {result['created']} Subdivision nodes exist")
            
            # 2. Create relationships in batches
            print("\n2. Creating BELONGS_TO relationships (batch processing)...")
            batch_size = 10000
            total_created = 0
            
            while True:
                query_batch = """
                MATCH (p:Parcel)
                WHERE p.parcel_id IS NOT NULL 
                  AND NOT exists((p)-[:BELONGS_TO]->(:Subdivision))
                WITH p LIMIT $batch_size
                WITH p, substring(p.parcel_id, 0, 8) as subdiv_id
                MATCH (s:Subdivision {subdivision_id: subdiv_id})
                CREATE (p)-[:BELONGS_TO]->(s)
                RETURN count(p) as created
                """
                result = session.run(query_batch, batch_size=batch_size).single()
                created = result['created']
                total_created += created
                
                if created > 0:
                    print(f"  Processed batch: {created} relationships created (total: {total_created})")
                else:
                    break
            
            print(f"  ✓ Total relationships created: {total_created}")
            
            # 3. Verify results
            print("\n3. Verifying results...")
            query_verify = """
            MATCH (p:Parcel)
            WHERE p.parcel_id IS NOT NULL
            WITH p, exists((p)-[:BELONGS_TO]->(:Subdivision)) as has_link
            RETURN 
                count(p) as total_parcels,
                sum(CASE WHEN has_link THEN 1 ELSE 0 END) as linked_parcels
            """
            verify = session.run(query_verify).single()
            print(f"  Total parcels: {verify['total_parcels']}")
            print(f"  Linked parcels: {verify['linked_parcels']}")
            
            print("\n" + "="*80)
            print("PHASE 1 COMPLETE")
            print("="*80)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    create_subdivision_links_batch()
