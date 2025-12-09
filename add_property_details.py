
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def add_property_details(parcel_id, property_data):
    """
    Add detailed property attributes to a parcel node.
    
    property_data should be a dict with keys like:
    - property_type: str
    - lot_type: str
    - is_corner_lot: bool
    - has_pool: bool
    - fence_linear_feet: int
    - hoa_id: str (optional, will create relationship to HOA)
    - hoa_name: str (optional)
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print(f"Adding property details to Parcel {parcel_id}...")
            
            # 1. Update parcel properties
            query_update = """
            MATCH (p:Parcel {parcel_id: $pid})
            SET p.property_type = $property_type,
                p.lot_type = $lot_type,
                p.is_corner_lot = $is_corner_lot,
                p.has_pool = $has_pool,
                p.fence_linear_feet = $fence_linear_feet,
                p.requires_fence_permit = $requires_permit
            RETURN p.parcel_id as id
            """
            
            result = session.run(query_update, 
                pid=parcel_id,
                property_type=property_data.get('property_type'),
                lot_type=property_data.get('lot_type'),
                is_corner_lot=property_data.get('is_corner_lot', False),
                has_pool=property_data.get('has_pool', False),
                fence_linear_feet=property_data.get('fence_linear_feet'),
                requires_permit=property_data.get('requires_fence_permit', True)
            ).single()
            
            if result:
                print(f"✓ Updated parcel {result['id']}")
            else:
                print(f"✗ Parcel {parcel_id} not found")
                return
            
            # 2. Create/link HOA if provided
            if property_data.get('hoa_id'):
                query_hoa = """
                MATCH (p:Parcel {parcel_id: $pid})
                MERGE (hoa:HOA {hoa_id: $hoa_id})
                ON CREATE SET hoa.name = $hoa_name
                MERGE (p)-[:IN_HOA]->(hoa)
                RETURN hoa.name as name
                """
                
                hoa_result = session.run(query_hoa,
                    pid=parcel_id,
                    hoa_id=property_data.get('hoa_id'),
                    hoa_name=property_data.get('hoa_name', 'Unknown HOA')
                ).single()
                
                if hoa_result:
                    print(f"✓ Linked to HOA: {hoa_result['name']}")
            
            print("\nProperty details added successfully!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    # Example usage for parcel 503911073240
    parcel_data = {
        'property_type': 'Residential, single-family',
        'lot_type': 'Dry interior lot (not a corner, not waterfront, no pool)',
        'is_corner_lot': False,
        'has_pool': False,
        'fence_linear_feet': 234,
        'requires_fence_permit': True,
        'hoa_id': 'HOA-WESTON-001',
        'hoa_name': 'Weston Hills HOA'
    }
    
    add_property_details('503911073240', parcel_data)
