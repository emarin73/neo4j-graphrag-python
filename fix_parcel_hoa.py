
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def fix_parcel_and_hoa():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("="*80)
            print("FIXING PARCEL 503911073240 AND SAVANNA HOA MAPPING")
            print("="*80)
            
            # 1. Fix the subdivision link for this parcel
            print("\n1. Fixing Parcel->Subdivision link...")
            query_fix_parcel = """
            MATCH (p:Parcel {parcel_id: '503911073240'})
            MERGE (s:Subdivision {subdivision_id: '50391107'})
            MERGE (p)-[:BELONGS_TO]->(s)
            RETURN p.parcel_id as parcel, s.subdivision_id as subdiv
            """
            result = session.run(query_fix_parcel).single()
            print(f"  ✓ Linked Parcel {result['parcel']} to Subdivision {result['subdiv']}")
            
            # 2. Remove old Weston Hills HOA mapping from this subdivision
            print("\n2. Removing old HOA mapping...")
            query_remove_old = """
            MATCH (s:Subdivision {subdivision_id: '50391107'})-[r:MANAGED_BY]->(hoa:HOA {name: 'Weston Hills HOA'})
            DELETE r
            RETURN count(r) as deleted
            """
            deleted = session.run(query_remove_old).single()
            print(f"  ✓ Removed {deleted['deleted']} old mapping(s)")
            
            # 3. Create Savanna HOA and link to subdivision
            print("\n3. Creating Savanna HOA mapping...")
            query_create_savanna = """
            MERGE (hoa:HOA {name: 'Savanna Maintenance Association'})
            ON CREATE SET hoa.hoa_id = 'HOA-SAVANNA-001'
            WITH hoa
            MATCH (s:Subdivision {subdivision_id: '50391107'})
            MERGE (s)-[:MANAGED_BY]->(hoa)
            RETURN s.subdivision_id as subdiv, hoa.name as hoa_name
            """
            savanna = session.run(query_create_savanna).single()
            print(f"  ✓ Linked Subdivision {savanna['subdiv']} to {savanna['hoa_name']}")
            
            # 4. Verify the fix
            print("\n4. Verifying fix...")
            query_verify = """
            MATCH (p:Parcel {parcel_id: '503911073240'})-[:BELONGS_TO]->(s:Subdivision)-[:MANAGED_BY]->(hoa:HOA)
            RETURN p.parcel_id as parcel, s.subdivision_id as subdiv, hoa.name as hoa
            """
            verify = session.run(query_verify).single()
            print(f"  Parcel: {verify['parcel']}")
            print(f"  Subdivision: {verify['subdiv']}")
            print(f"  HOA: {verify['hoa']}")
            
            print("\n" + "="*80)
            print("FIX COMPLETE")
            print("="*80)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    fix_parcel_and_hoa()
