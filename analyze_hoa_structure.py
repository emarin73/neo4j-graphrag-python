
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def analyze_hoa_structure():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("="*80)
            print("CURRENT HOA-PARCEL RELATIONSHIP ANALYSIS")
            print("="*80)
            
            # 1. Check existing HOA nodes
            print("\n1. HOA Nodes:")
            print("-"*80)
            query_hoa = """
            MATCH (hoa:HOA)
            RETURN hoa.hoa_id as id, hoa.name as name, count{(hoa)<-[:IN_HOA]-()} as parcel_count
            ORDER BY parcel_count DESC
            LIMIT 10
            """
            hoas = list(session.run(query_hoa))
            for h in hoas:
                print(f"  HOA: {h['name']} (ID: {h['id']}) - {h['parcel_count']} parcels")
            
            # 2. Check for existing Subdivision nodes
            print("\n2. Existing Subdivision Nodes:")
            print("-"*80)
            query_subdiv = """
            MATCH (s:Subdivision)
            RETURN count(s) as count
            """
            subdiv_count = session.run(query_subdiv).single()
            print(f"  Found {subdiv_count['count']} Subdivision nodes")
            
            # 3. Analyze parcel ID patterns (first 8 characters)
            print("\n3. Parcel ID Subdivision Patterns (first 8 chars):")
            print("-"*80)
            query_patterns = """
            MATCH (p:Parcel)
            WHERE p.parcel_id IS NOT NULL
            WITH substring(p.parcel_id, 0, 8) as subdiv_id, count(p) as parcel_count
            ORDER BY parcel_count DESC
            LIMIT 10
            RETURN subdiv_id, parcel_count
            """
            patterns = list(session.run(query_patterns))
            for pat in patterns:
                print(f"  Subdivision ID: {pat['subdiv_id']} - {pat['parcel_count']} parcels")
            
            # 4. Sample parcels with HOA relationships
            print("\n4. Sample Parcels with HOA Relationships:")
            print("-"*80)
            query_sample = """
            MATCH (p:Parcel)-[:IN_HOA]->(hoa:HOA)
            RETURN p.parcel_id as parcel_id, 
                   substring(p.parcel_id, 0, 8) as subdiv_id,
                   hoa.name as hoa_name
            LIMIT 5
            """
            samples = list(session.run(query_sample))
            for s in samples:
                print(f"  Parcel: {s['parcel_id']} (Subdiv: {s['subdiv_id']}) -> HOA: {s['hoa_name']}")
            
            # 5. Check relationship types
            print("\n5. Relationship Analysis:")
            print("-"*80)
            query_rels = """
            MATCH ()-[r:IN_HOA]->()
            RETURN count(r) as total_hoa_links
            """
            rels = session.run(query_rels).single()
            print(f"  Total IN_HOA relationships: {rels['total_hoa_links']}")
            
            # 6. Check if subdivisions already have relationships
            print("\n6. Existing Subdivision Relationships:")
            print("-"*80)
            query_subdiv_rels = """
            MATCH (p:Parcel)-[r]-(s:Subdivision)
            RETURN type(r) as rel_type, count(r) as count
            """
            subdiv_rels = list(session.run(query_subdiv_rels))
            if subdiv_rels:
                for sr in subdiv_rels:
                    print(f"  {sr['rel_type']}: {sr['count']} relationships")
            else:
                print("  No Parcel-Subdivision relationships found")
            
            print("\n" + "="*80)
            print("ANALYSIS COMPLETE")
            print("="*80)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    analyze_hoa_structure()
