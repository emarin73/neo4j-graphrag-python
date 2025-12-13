"""
Query Savanna HOA Units
========================

Find how many units are associated with Savanna HOA.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")


def query_savanna_hoa():
    """Query Savanna HOA information."""
    
    driver = GraphDatabase.driver(
        NEO4J_URI, 
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        with driver.session() as session:
            print("=" * 80)
            print("SAVANNA HOA QUERY")
            print("=" * 80)
            
            # Search for Savanna HOA or subdivisions with "Savanna" in the name
            query = """
            MATCH (s:Subdivision)
            WHERE toLower(s.subdivision_id) CONTAINS 'savanna' 
               OR toLower(s.name) CONTAINS 'savanna'
               OR toLower(s.legal_line) CONTAINS 'savanna'
            RETURN s.subdivision_id as folio8,
                   s.name as name,
                   s.legal_line as legal_line,
                   s.unit_count as unit_count,
                   s.situs_city as city,
                   s.situs_zip_code as zip
            ORDER BY s.unit_count DESC
            """
            
            results = session.run(query)
            records = list(results)
            
            if not records:
                print("\n⚠ No subdivisions found with 'Savanna' in the name")
                
                # Try to find HOA nodes
                hoa_query = """
                MATCH (hoa:HOA)
                WHERE toLower(hoa.name) CONTAINS 'savanna'
                OPTIONAL MATCH (hoa)<-[:MANAGED_BY]-(s:Subdivision)
                RETURN hoa.name as hoa_name,
                       count(s) as subdivision_count,
                       sum(s.unit_count) as total_units
                """
                
                hoa_results = session.run(hoa_query)
                hoa_records = list(hoa_results)
                
                if hoa_records:
                    print("\nHOA Nodes Found:")
                    for record in hoa_records:
                        print(f"\nHOA: {record['hoa_name']}")
                        print(f"  Subdivisions: {record['subdivision_count']}")
                        print(f"  Total Units: {record['total_units']}")
                else:
                    print("\n⚠ No HOA nodes found with 'Savanna' in the name")
            else:
                print(f"\nFound {len(records)} subdivision(s) with 'Savanna':")
                print("-" * 80)
                
                total_units = 0
                for i, record in enumerate(records, 1):
                    units = record['unit_count'] or 0
                    total_units += units
                    
                    print(f"\n{i}. FOLIO8: {record['folio8']}")
                    print(f"   Name: {record['name'] or 'N/A'}")
                    print(f"   Legal Line: {record['legal_line'] or 'N/A'}")
                    print(f"   Units: {units}")
                    print(f"   City: {record['city'] or 'N/A'}")
                    print(f"   ZIP: {record['zip'] or 'N/A'}")
                
                print("\n" + "=" * 80)
                print(f"TOTAL UNITS: {total_units}")
                print("=" * 80)
    
    finally:
        driver.close()


if __name__ == "__main__":
    query_savanna_hoa()
