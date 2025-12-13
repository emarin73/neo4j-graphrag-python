"""
Normalize HOA IDs
=================

Update HOA IDs to follow the pattern: HOA-CITY-###-NAME
Example: HOA-WESTON-001-SAVANNA

Usage:
    python normalize_hoa_ids.py
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")


class HOAIDNormalizer:
    """Normalize HOA IDs to standard format."""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def get_city_code_from_subdivisions(self, hoa_name):
        """
        Get the city code from subdivisions managed by this HOA.
        
        Args:
            hoa_name: Name of the HOA
            
        Returns:
            str: City code (e.g., 'WESTON', 'CORAL SPRINGS')
        """
        with self.driver.session() as session:
            query = """
            MATCH (hoa:HOA {name: $hoa_name})<-[:MANAGED_BY]-(s:Subdivision)
            WHERE s.situs_city IS NOT NULL
            RETURN s.situs_city as city_code, count(*) as count
            ORDER BY count DESC
            LIMIT 1
            """
            
            result = session.run(query, hoa_name=hoa_name)
            record = result.single()
            
            if record:
                city_code = record['city_code']
                # Map city codes to full names
                city_map = {
                    'WS': 'WESTON',
                    'PA': 'PARKLAND',
                    'CS': 'CORAL-SPRINGS',
                    'BC': 'BROWARD-COUNTY',
                    'SU': 'SUNRISE',
                    'DB': 'DEERFIELD-BEACH',
                    'CK': 'COCONUT-CREEK'
                }
                return city_map.get(city_code, city_code)
            
            return 'UNKNOWN'
    
    def generate_hoa_id(self, hoa_name, city, sequence_number):
        """
        Generate a normalized HOA ID.
        
        Args:
            hoa_name: Name of the HOA
            city: City name or code
            sequence_number: Sequence number (e.g., 1, 2, 3)
            
        Returns:
            str: Normalized HOA ID (e.g., HOA-WESTON-001-SAVANNA)
        """
        # Clean up HOA name for ID
        name_part = hoa_name.upper().replace(' ', '-').replace('_', '-')
        # Remove common suffixes
        name_part = name_part.replace('-HOA', '').replace('-ASSOCIATION', '')
        name_part = name_part.replace('-MAINTENANCE', '').strip('-')
        
        # Format sequence number with leading zeros
        seq = f"{sequence_number:03d}"
        
        return f"HOA-{city}-{seq}-{name_part}"
    
    def update_hoa_id(self, old_hoa_id, new_hoa_id, hoa_name):
        """
        Update an HOA's ID.
        
        Args:
            old_hoa_id: Current HOA ID
            new_hoa_id: New HOA ID
            hoa_name: HOA name for matching
        """
        with self.driver.session() as session:
            # First, set a temporary ID to avoid constraint conflicts
            temp_id = f"TEMP_{new_hoa_id}_{hoa_name}"
            
            query1 = """
            MATCH (hoa:HOA {name: $hoa_name})
            SET hoa.hoa_id = $temp_id
            RETURN hoa
            """
            
            session.run(query1, hoa_name=hoa_name, temp_id=temp_id)
            
            # Now set the final ID
            query2 = """
            MATCH (hoa:HOA {name: $hoa_name})
            SET hoa.hoa_id = $new_hoa_id,
                hoa.old_hoa_id = $old_hoa_id,
                hoa.updated = datetime()
            RETURN hoa
            """
            
            result = session.run(
                query2,
                hoa_name=hoa_name,
                old_hoa_id=old_hoa_id,
                new_hoa_id=new_hoa_id
            )
            
            return result.single() is not None
    
    def normalize_all_hoas(self):
        """Normalize all HOA IDs in the database."""
        
        import time
        timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
        
        with self.driver.session() as session:
            # Get all HOAs
            query = """
            MATCH (hoa:HOA)
            RETURN hoa.name as name, hoa.hoa_id as current_id
            ORDER BY hoa.name
            """
            
            results = session.run(query)
            hoas = list(results)
            
            print("=" * 80)
            print("NORMALIZING HOA IDs")
            print("=" * 80)
            print(f"Found {len(hoas)} HOA(s) to normalize\n")
            
            # Track sequence numbers per city
            city_sequences = {}
            updates = []
            
            for hoa in hoas:
                hoa_name = hoa['name']
                current_id = hoa['current_id']
                
                # Get city from subdivisions
                city = self.get_city_code_from_subdivisions(hoa_name)
                
                # Get next sequence number for this city
                if city not in city_sequences:
                    city_sequences[city] = 1
                else:
                    city_sequences[city] += 1
                
                sequence = city_sequences[city]
                
                # Generate new ID
                new_id = self.generate_hoa_id(hoa_name, city, sequence)
                
                updates.append({
                    'name': hoa_name,
                    'old_id': current_id,
                    'new_id': new_id,
                    'temp_id': f"TEMP_{timestamp}_{len(updates)}"
                })
                
                print(f"✓ {hoa_name}")
                print(f"  Old ID: {current_id}")
                print(f"  New ID: {new_id}")
                print()
            
            # Now apply all updates in two phases
            print("\nApplying updates...")
            
            # Phase 1: Set all to temporary IDs
            for update in updates:
                query1 = """
                MATCH (hoa:HOA {name: $name})
                SET hoa.hoa_id = $temp_id
                """
                session.run(query1, name=update['name'], temp_id=update['temp_id'])
            
            # Phase 2: Set all to final IDs
            for update in updates:
                query2 = """
                MATCH (hoa:HOA {name: $name})
                SET hoa.hoa_id = $new_id,
                    hoa.old_hoa_id = $old_id,
                    hoa.updated = datetime()
                """
                session.run(
                    query2,
                    name=update['name'],
                    new_id=update['new_id'],
                    old_id=update['old_id']
                )
            
            print(f"✓ Updated {len(updates)} HOA IDs")
    
    def verify_normalization(self):
        """Verify the normalization results."""
        
        with self.driver.session() as session:
            query = """
            MATCH (hoa:HOA)<-[:MANAGED_BY]-(s:Subdivision)
            RETURN 
                hoa.hoa_id as hoa_id,
                hoa.name as hoa_name,
                hoa.old_hoa_id as old_id,
                count(s) as subdivision_count,
                sum(s.unit_count) as total_units
            ORDER BY hoa.hoa_id
            """
            
            results = session.run(query)
            records = list(results)
            
            print("=" * 80)
            print("VERIFICATION - NORMALIZED HOA IDs")
            print("=" * 80)
            
            for record in records:
                print(f"\n• {record['hoa_id']}")
                print(f"  Name: {record['hoa_name']}")
                if record['old_id']:
                    print(f"  Previous ID: {record['old_id']}")
                print(f"  Subdivisions: {record['subdivision_count']}")
                print(f"  Total Units: {record['total_units']}")


def main():
    """Main entry point."""
    
    normalizer = HOAIDNormalizer()
    
    try:
        print("=" * 80)
        print("HOA ID NORMALIZATION")
        print("=" * 80)
        print(f"Neo4j URI: {NEO4J_URI}")
        print(f"Format: HOA-CITY-###-NAME\n")
        
        # Normalize all HOAs
        normalizer.normalize_all_hoas()
        
        # Verify results
        normalizer.verify_normalization()
        
        print("\n" + "=" * 80)
        print("NORMALIZATION COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        normalizer.close()


if __name__ == "__main__":
    main()
