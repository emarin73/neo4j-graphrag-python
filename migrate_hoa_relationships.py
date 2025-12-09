
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def migrate_hoa_relationships():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("="*80)
            print("PHASE 3: MIGRATING HOA RELATIONSHIPS")
            print("="*80)
            
            # 1. Verify new structure exists
            print("\n1. Verifying new structure...")
            query_verify = """
            MATCH path = (p:Parcel)-[:BELONGS_TO]->(s:Subdivision)-[:MANAGED_BY]->(hoa:HOA)
            RETURN count(DISTINCT p) as parcels_with_path,
                   count(DISTINCT s) as subdivisions_with_hoa,
                   count(DISTINCT hoa) as hoas
            """
            verify = session.run(query_verify).single()
            print(f"  Parcels reachable via new path: {verify['parcels_with_path']}")
            print(f"  Subdivisions with HOA: {verify['subdivisions_with_hoa']}")
            print(f"  HOAs: {verify['hoas']}")
            
            # 2. Check old direct links
            print("\n2. Checking old direct Parcel->HOA links...")
            query_old = """
            MATCH (p:Parcel)-[r:IN_HOA]->(hoa:HOA)
            RETURN count(r) as old_links
            """
            old_links = session.run(query_old).single()
            print(f"  Old IN_HOA relationships: {old_links['old_links']}")
            
            if old_links['old_links'] == 0:
                print("  ✓ No old links to remove")
            else:
                # 3. Remove old direct links
                print("\n3. Removing old direct Parcel->HOA links...")
                query_remove = """
                MATCH (p:Parcel)-[r:IN_HOA]->(hoa:HOA)
                DELETE r
                RETURN count(r) as deleted
                """
                deleted = session.run(query_remove).single()
                print(f"  ✓ Deleted {deleted['deleted']} old IN_HOA relationships")
            
            # 4. Final verification
            print("\n4. Final verification...")
            final_verify = session.run(query_verify).single()
            print(f"  Parcels with HOA access: {final_verify['parcels_with_path']}")
            
            final_old = session.run(query_old).single()
            print(f"  Remaining old links: {final_old['old_links']}")
            
            print("\n" + "="*80)
            print("PHASE 3 COMPLETE")
            print("="*80)
            print("\nNew structure: (Parcel)-[:BELONGS_TO]->(Subdivision)-[:MANAGED_BY]->(HOA)")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    migrate_hoa_relationships()
