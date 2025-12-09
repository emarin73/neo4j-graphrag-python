
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Define your HOA-Subdivision mappings here
# Format: {"HOA_name": ["subdivision_id1", "subdivision_id2", ...]}
HOA_MAPPINGS = {
    "Savanna Maintenance Association": [
        # Add subdivision IDs here (first 8 chars of parcel IDs)
        # Example: "49423401", "50391107", etc.
    ],
    # Add more HOAs as needed
    # "North Lakes": ["12345678", "23456789"],
}

def add_hoa_mappings():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("="*80)
            print("ADDING CUSTOM HOA-SUBDIVISION MAPPINGS")
            print("="*80)
            
            total_created = 0
            
            for hoa_name, subdivision_ids in HOA_MAPPINGS.items():
                if not subdivision_ids:
                    print(f"\nSkipping {hoa_name} - no subdivisions defined")
                    continue
                
                print(f"\n{hoa_name}:")
                print(f"  Mapping {len(subdivision_ids)} subdivisions...")
                
                for subdiv_id in subdivision_ids:
                    # Find or create HOA
                    query_create = """
                    MERGE (hoa:HOA {name: $hoa_name})
                    WITH hoa
                    MATCH (s:Subdivision {subdivision_id: $subdiv_id})
                    MERGE (s)-[:MANAGED_BY]->(hoa)
                    RETURN s.subdivision_id as subdiv, hoa.name as hoa
                    """
                    
                    try:
                        result = session.run(query_create, hoa_name=hoa_name, subdiv_id=subdiv_id).single()
                        if result:
                            print(f"    ✓ {result['subdiv']} -> {result['hoa']}")
                            total_created += 1
                        else:
                            print(f"    ✗ Subdivision {subdiv_id} not found")
                    except Exception as e:
                        print(f"    ✗ Error mapping {subdiv_id}: {e}")
            
            print(f"\n{'='*80}")
            print(f"COMPLETE: Created {total_created} HOA-Subdivision mappings")
            print("="*80)
            
            # Show summary
            print("\nCurrent HOA-Subdivision Summary:")
            query_summary = """
            MATCH (s:Subdivision)-[:MANAGED_BY]->(hoa:HOA)
            RETURN hoa.name as hoa_name, count(s) as subdivision_count
            ORDER BY subdivision_count DESC
            """
            summary = list(session.run(query_summary))
            for item in summary:
                print(f"  {item['hoa_name']}: {item['subdivision_count']} subdivisions")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    print("\nINSTRUCTIONS:")
    print("1. Edit this file and add subdivision IDs to the HOA_MAPPINGS dictionary")
    print("2. Subdivision IDs are the first 8 characters of parcel IDs")
    print("3. Run this script to create the mappings\n")
    
    if not any(HOA_MAPPINGS.values()):
        print("⚠️  No mappings defined yet. Please edit the HOA_MAPPINGS dictionary.")
    else:
        add_hoa_mappings()
