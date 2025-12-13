"""
Query Specific Savanna HOA Subdivisions
========================================

Query the three specific subdivisions that make up Savanna HOA.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")


def query_savanna_subdivisions():
    """Query the three Savanna HOA subdivisions."""
    
    driver = GraphDatabase.driver(
        NEO4J_URI, 
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        with driver.session() as session:
            print("=" * 80)
            print("SAVANNA HOA - SPECIFIC SUBDIVISIONS")
            print("=" * 80)
            
            # Query the three specific FOLIO8 IDs
            query = """
            MATCH (s:Subdivision)
            WHERE s.subdivision_id IN ['50390201', '50391106', '50391107']
            RETURN s.subdivision_id as folio8,
                   s.name as name,
                   s.legal_line as legal_line,
                   s.legal_line_2 as legal_line_2,
                   s.unit_count as unit_count,
                   s.millage_code as millage_code,
                   s.use_code as use_code,
                   s.situs_city as city,
                   s.situs_zip_code as zip
            ORDER BY s.subdivision_id
            """
            
            results = session.run(query)
            records = list(results)
            
            if not records:
                print("\n⚠ No subdivisions found with these FOLIO8 IDs")
                print("   Checking if they exist in the database...")
                
                check_query = """
                MATCH (s:Subdivision)
                WHERE s.subdivision_id STARTS WITH '5039'
                RETURN s.subdivision_id
                ORDER BY s.subdivision_id
                LIMIT 10
                """
                check_results = session.run(check_query)
                check_records = list(check_results)
                
                if check_records:
                    print("\n   Found subdivisions starting with '5039':")
                    for rec in check_records:
                        print(f"     - {rec['s.subdivision_id']}")
                
            else:
                print(f"\nFound {len(records)} subdivision(s):")
                print("-" * 80)
                
                total_units = 0
                for i, record in enumerate(records, 1):
                    units = record['unit_count'] or 0
                    total_units += units
                    
                    print(f"\n{i}. FOLIO8: {record['folio8']}")
                    print(f"   Name: {record['name'] or 'N/A'}")
                    print(f"   Legal Line: {record['legal_line'] or 'N/A'}")
                    print(f"   Legal Line 2: {record['legal_line_2'] or 'N/A'}")
                    print(f"   Units: {units}")
                    print(f"   Millage Code: {record['millage_code'] or 'N/A'}")
                    print(f"   Use Code: {record['use_code'] or 'N/A'}")
                    print(f"   City: {record['city'] or 'N/A'}")
                    print(f"   ZIP: {record['zip'] or 'N/A'}")
                
                print("\n" + "=" * 80)
                print(f"TOTAL UNITS FOR SAVANNA HOA: {total_units}")
                print("=" * 80)
    
    finally:
        driver.close()


if __name__ == "__main__":
    query_savanna_subdivisions()
