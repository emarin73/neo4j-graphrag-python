
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def investigate_and_fix():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("="*80)
            print("INVESTIGATING PARCEL 503911073240")
            print("="*80)
            
            # 1. Check all BELONGS_TO relationships
            print("\n1. All BELONGS_TO relationships for this parcel:")
            query_all_belongs = """
            MATCH (p:Parcel {parcel_id: '503911073240'})-[r:BELONGS_TO]->(s:Subdivision)
            RETURN s.subdivision_id as subdiv_id, id(r) as rel_id, id(s) as node_id
            """
            belongs_to = list(session.run(query_all_belongs))
            for b in belongs_to:
                print(f"  -> Subdivision: {b['subdiv_id']} (rel_id: {b['rel_id']}, node_id: {b['node_id']})")
            
            # 2. Check all subdivisions and their HOAs
            print("\n2. All Subdivision->HOA mappings:")
            query_all_hoas = """
            MATCH (p:Parcel {parcel_id: '503911073240'})-[:BELONGS_TO]->(s:Subdivision)
            OPTIONAL MATCH (s)-[:MANAGED_BY]->(hoa:HOA)
            RETURN s.subdivision_id as subdiv, hoa.name as hoa_name
            """
            hoas = list(session.run(query_all_hoas))
            for h in hoas:
                print(f"  Subdivision {h['subdiv']} -> HOA: {h['hoa_name']}")
            
            # 3. Delete ALL old BELONGS_TO relationships
            print("\n3. Removing ALL old BELONGS_TO relationships...")
            query_delete_all = """
            MATCH (p:Parcel {parcel_id: '503911073240'})-[r:BELONGS_TO]->()
            DELETE r
            RETURN count(r) as deleted
            """
            deleted = session.run(query_delete_all).single()
            print(f"  ✓ Deleted {deleted['deleted']} relationships")
            
            # 4. Create the correct single relationship
            print("\n4. Creating correct Parcel->Subdivision link...")
            query_create_correct = """
            MATCH (p:Parcel {parcel_id: '503911073240'})
            MERGE (s:Subdivision {subdivision_id: '50391107'})
            CREATE (p)-[:BELONGS_TO]->(s)
            RETURN p.parcel_id as parcel, s.subdivision_id as subdiv
            """
            created = session.run(query_create_correct).single()
            print(f"  ✓ Created: Parcel {created['parcel']} -> Subdivision {created['subdiv']}")
            
            # 5. Ensure Savanna HOA mapping exists
            print("\n5. Ensuring Savanna HOA mapping...")
            query_savanna = """
            MATCH (s:Subdivision {subdivision_id: '50391107'})
            OPTIONAL MATCH (s)-[old:MANAGED_BY]->(:HOA)
            DELETE old
            WITH s
            MERGE (hoa:HOA {name: 'Savanna Maintenance Association'})
            ON CREATE SET hoa.hoa_id = 'HOA-SAVANNA-001'
            CREATE (s)-[:MANAGED_BY]->(hoa)
            RETURN s.subdivision_id as subdiv, hoa.name as hoa_name
            """
            savanna = session.run(query_savanna).single()
            print(f"  ✓ Mapped: Subdivision {savanna['subdiv']} -> {savanna['hoa_name']}")
            
            # 6. Final verification
            print("\n6. Final verification:")
            query_final = """
            MATCH (p:Parcel {parcel_id: '503911073240'})-[:BELONGS_TO]->(s:Subdivision)-[:MANAGED_BY]->(hoa:HOA)
            RETURN p.parcel_id as parcel, s.subdivision_id as subdiv, hoa.name as hoa
            """
            final = session.run(query_final).single()
            print(f"  Parcel: {final['parcel']}")
            print(f"  Subdivision: {final['subdiv']}")
            print(f"  HOA: {final['hoa']}")
            
            print("\n" + "="*80)
            print("FIX COMPLETE")
            print("="*80)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()

if __name__ == "__main__":
    investigate_and_fix()
