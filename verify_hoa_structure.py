
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def verify_hoa_structure():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("="*80)
            print("HOA STRUCTURE VERIFICATION")
            print("="*80)
            
            # 1. Overall structure
            print("\n1. Overall Structure:")
            print("-"*80)
            query_overall = """
            MATCH (p:Parcel)
            WHERE p.parcel_id IS NOT NULL
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(s:Subdivision)
            OPTIONAL MATCH (s)-[:MANAGED_BY]->(hoa:HOA)
            RETURN 
                count(DISTINCT p) as total_parcels,
                count(DISTINCT s) as total_subdivisions,
                count(DISTINCT hoa) as total_hoas,
                sum(CASE WHEN s IS NOT NULL THEN 1 ELSE 0 END) as parcels_with_subdivision,
                sum(CASE WHEN hoa IS NOT NULL THEN 1 ELSE 0 END) as parcels_with_hoa
            """
            stats = session.run(query_overall).single()
            print(f"  Total Parcels: {stats['total_parcels']}")
            print(f"  Total Subdivisions: {stats['total_subdivisions']}")
            print(f"  Total HOAs: {stats['total_hoas']}")
            print(f"  Parcels with Subdivision link: {stats['parcels_with_subdivision']}")
            print(f"  Parcels with HOA access: {stats['parcels_with_hoa']}")
            
            # 2. Verify no old direct links
            print("\n2. Old Direct Links Check:")
            print("-"*80)
            query_old = """
            MATCH (p:Parcel)-[r:IN_HOA]->(hoa:HOA)
            RETURN count(r) as old_links
            """
            old = session.run(query_old).single()
            if old['old_links'] == 0:
                print("  ✓ No old Parcel->HOA links found (correct)")
            else:
                print(f"  ✗ WARNING: {old['old_links']} old Parcel->HOA links still exist!")
            
            # 3. HOA breakdown
            print("\n3. HOA Breakdown:")
            print("-"*80)
            query_hoas = """
            MATCH (hoa:HOA)<-[:MANAGED_BY]-(s:Subdivision)<-[:BELONGS_TO]-(p:Parcel)
            RETURN hoa.name as hoa_name, 
                   count(DISTINCT s) as subdivisions,
                   count(DISTINCT p) as parcels
            ORDER BY parcels DESC
            """
            hoas = list(session.run(query_hoas))
            if hoas:
                for h in hoas:
                    print(f"  {h['hoa_name']}: {h['subdivisions']} subdivisions, {h['parcels']} parcels")
            else:
                print("  No HOAs with mapped subdivisions")
            
            # 4. Sample parcel test
            print("\n4. Sample Parcel Test (503911073240):")
            print("-"*80)
            query_sample = """
            MATCH (p:Parcel {parcel_id: '503911073240'})
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(s:Subdivision)
            OPTIONAL MATCH (s)-[:MANAGED_BY]->(hoa:HOA)
            RETURN p.parcel_id as parcel,
                   s.subdivision_id as subdivision,
                   hoa.name as hoa_name
            """
            sample = session.run(query_sample).single()
            if sample:
                print(f"  Parcel: {sample['parcel']}")
                print(f"  Subdivision: {sample['subdivision'] or 'None'}")
                print(f"  HOA: {sample['hoa_name'] or 'None'}")
            else:
                print("  Sample parcel not found")
            
            print("\n" + "="*80)
            print("VERIFICATION COMPLETE")
            print("="*80)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    verify_hoa_structure()
