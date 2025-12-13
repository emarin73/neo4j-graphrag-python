"""
Create HOA-Subdivision Relationships
=====================================

This script creates HOA nodes and establishes MANAGED_BY relationships
between Subdivisions and their HOAs.

Usage:
    python create_hoa_relationships.py
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")


class HOARelationshipManager:
    """Manage HOA nodes and their relationships with Subdivisions."""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def create_hoa_and_link_subdivisions(self, hoa_name, subdivision_ids, hoa_properties=None):
        """
        Create an HOA node and link it to subdivisions.
        
        Args:
            hoa_name: Name of the HOA
            subdivision_ids: List of FOLIO8 IDs (subdivision_id values)
            hoa_properties: Optional dictionary of additional HOA properties
        
        Returns:
            dict: Statistics about the operation
        """
        with self.driver.session() as session:
            # Create HOA node
            hoa_props = hoa_properties or {}
            hoa_props['name'] = hoa_name
            hoa_props['hoa_id'] = hoa_name.lower().replace(' ', '-')
            
            create_hoa_query = """
            MERGE (hoa:HOA {hoa_id: $hoa_id})
            ON CREATE SET 
                hoa.name = $name,
                hoa.created = datetime()
            ON MATCH SET
                hoa.name = $name,
                hoa.updated = datetime()
            """
            
            for key, value in hoa_props.items():
                if key not in ['hoa_id', 'name']:
                    create_hoa_query += f"\nSET hoa.{key} = ${key}"
            
            create_hoa_query += "\nRETURN hoa"
            
            result = session.run(create_hoa_query, **hoa_props)
            hoa_node = result.single()
            
            if not hoa_node:
                print(f"✗ Failed to create HOA: {hoa_name}")
                return None
            
            print(f"✓ HOA node created/updated: {hoa_name}")
            
            # Link subdivisions to HOA
            link_query = """
            UNWIND $subdivision_ids as sub_id
            MATCH (s:Subdivision {subdivision_id: sub_id})
            MATCH (hoa:HOA {hoa_id: $hoa_id})
            MERGE (s)-[r:MANAGED_BY]->(hoa)
            ON CREATE SET r.created = datetime()
            RETURN count(r) as relationships_created
            """
            
            result = session.run(
                link_query, 
                subdivision_ids=subdivision_ids,
                hoa_id=hoa_props['hoa_id']
            )
            
            record = result.single()
            relationships_created = record['relationships_created'] if record else 0
            
            print(f"✓ Created {relationships_created} MANAGED_BY relationships")
            
            # Get statistics
            stats_query = """
            MATCH (hoa:HOA {hoa_id: $hoa_id})<-[:MANAGED_BY]-(s:Subdivision)
            RETURN 
                hoa.name as hoa_name,
                count(s) as subdivision_count,
                sum(s.unit_count) as total_units,
                collect(s.subdivision_id) as subdivision_ids
            """
            
            result = session.run(stats_query, hoa_id=hoa_props['hoa_id'])
            stats = result.single()
            
            return {
                'hoa_name': stats['hoa_name'],
                'subdivision_count': stats['subdivision_count'],
                'total_units': stats['total_units'],
                'subdivision_ids': stats['subdivision_ids']
            }
    
    def verify_hoa_relationships(self, hoa_name=None):
        """
        Verify HOA relationships.
        
        Args:
            hoa_name: Optional HOA name to filter by
        """
        with self.driver.session() as session:
            if hoa_name:
                query = """
                MATCH (hoa:HOA {name: $hoa_name})<-[:MANAGED_BY]-(s:Subdivision)
                RETURN 
                    hoa.name as hoa_name,
                    hoa.hoa_id as hoa_id,
                    s.subdivision_id as subdivision_id,
                    s.unit_count as unit_count,
                    s.legal_line as legal_line,
                    s.situs_city as city,
                    s.situs_zip_code as zip
                ORDER BY s.subdivision_id
                """
                results = session.run(query, hoa_name=hoa_name)
            else:
                query = """
                MATCH (hoa:HOA)<-[:MANAGED_BY]-(s:Subdivision)
                RETURN 
                    hoa.name as hoa_name,
                    hoa.hoa_id as hoa_id,
                    count(s) as subdivision_count,
                    sum(s.unit_count) as total_units
                ORDER BY hoa.name
                """
                results = session.run(query)
            
            return list(results)


def main():
    """Main entry point."""
    
    manager = HOARelationshipManager()
    
    try:
        print("=" * 80)
        print("HOA-SUBDIVISION RELATIONSHIP MANAGER")
        print("=" * 80)
        print(f"Neo4j URI: {NEO4J_URI}\n")
        
        # Create Savanna HOA and link its subdivisions
        print("Creating Savanna HOA and linking subdivisions...")
        print("-" * 80)
        
        savanna_subdivisions = ['50390201', '50391106', '50391107']
        
        savanna_properties = {
            'website': None,  # Add if known
            'management_company': None,  # Add if known
            'location': 'Weston, FL',
            'zip_code': '33327'
        }
        
        stats = manager.create_hoa_and_link_subdivisions(
            hoa_name='Savanna',
            subdivision_ids=savanna_subdivisions,
            hoa_properties=savanna_properties
        )
        
        if stats:
            print("\n" + "=" * 80)
            print("SAVANNA HOA SUMMARY")
            print("=" * 80)
            print(f"HOA Name: {stats['hoa_name']}")
            print(f"Subdivisions: {stats['subdivision_count']}")
            print(f"Total Units: {stats['total_units']}")
            print(f"Subdivision IDs: {', '.join(stats['subdivision_ids'])}")
        
        # Verify the relationships
        print("\n" + "=" * 80)
        print("VERIFICATION - SAVANNA HOA DETAILS")
        print("=" * 80)
        
        details = manager.verify_hoa_relationships('Savanna')
        
        if details:
            total_units = 0
            for i, record in enumerate(details, 1):
                units = record['unit_count'] or 0
                total_units += units
                print(f"\n{i}. Subdivision: {record['subdivision_id']}")
                print(f"   Units: {units}")
                print(f"   Legal Line: {record['legal_line']}")
                print(f"   Location: {record['city']}, {record['zip']}")
            
            print(f"\n{'=' * 80}")
            print(f"Total Units: {total_units}")
            print(f"{'=' * 80}")
        
        # Show all HOAs
        print("\n" + "=" * 80)
        print("ALL HOAs IN DATABASE")
        print("=" * 80)
        
        all_hoas = manager.verify_hoa_relationships()
        
        if all_hoas:
            for record in all_hoas:
                print(f"\n• {record['hoa_name']} (ID: {record['hoa_id']})")
                print(f"  Subdivisions: {record['subdivision_count']}")
                print(f"  Total Units: {record['total_units']}")
        else:
            print("\nNo HOAs found in database")
        
        print("\n" + "=" * 80)
        print("COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        manager.close()


if __name__ == "__main__":
    main()
