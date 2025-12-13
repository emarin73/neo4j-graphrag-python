"""
Check Current State of Subdivision Nodes
=========================================

This script checks the current state of Subdivision nodes in Neo4j
to see what data they have and what needs to be enriched.

Usage:
    python check_subdivision_state.py
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")


def check_subdivision_state():
    """Check the current state of Subdivision nodes."""
    
    driver = GraphDatabase.driver(
        NEO4J_URI, 
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        with driver.session() as session:
            print("=" * 80)
            print("SUBDIVISION NODE STATE CHECK")
            print("=" * 80)
            print(f"Neo4j URI: {NEO4J_URI}\n")
            
            # Get total count
            query1 = """
            MATCH (s:Subdivision)
            RETURN count(s) as total
            """
            result = session.run(query1).single()
            total = result['total']
            print(f"Total Subdivision nodes: {total}\n")
            
            if total == 0:
                print("⚠ No Subdivision nodes found in the database!")
                return
            
            # Get property statistics
            query2 = """
            MATCH (s:Subdivision)
            RETURN 
                count(s) as total,
                sum(CASE WHEN s.subdivision_id IS NOT NULL THEN 1 ELSE 0 END) as with_id,
                sum(CASE WHEN s.unit_count IS NOT NULL THEN 1 ELSE 0 END) as with_unit_count,
                sum(CASE WHEN s.legal_line IS NOT NULL THEN 1 ELSE 0 END) as with_legal_line,
                sum(CASE WHEN s.legal_line_2 IS NOT NULL THEN 1 ELSE 0 END) as with_legal_line_2,
                sum(CASE WHEN s.millage_code IS NOT NULL THEN 1 ELSE 0 END) as with_millage_code,
                sum(CASE WHEN s.use_code IS NOT NULL THEN 1 ELSE 0 END) as with_use_code,
                sum(CASE WHEN s.situs_city IS NOT NULL THEN 1 ELSE 0 END) as with_situs_city,
                sum(CASE WHEN s.situs_zip_code IS NOT NULL THEN 1 ELSE 0 END) as with_situs_zip_code
            """
            
            stats = session.run(query2).single()
            
            print("Property Coverage:")
            print(f"  subdivision_id:     {stats['with_id']:>6} / {stats['total']} ({stats['with_id']/stats['total']*100:.1f}%)")
            print(f"  unit_count:         {stats['with_unit_count']:>6} / {stats['total']} ({stats['with_unit_count']/stats['total']*100:.1f}%)")
            print(f"  legal_line:         {stats['with_legal_line']:>6} / {stats['total']} ({stats['with_legal_line']/stats['total']*100:.1f}%)")
            print(f"  legal_line_2:       {stats['with_legal_line_2']:>6} / {stats['total']} ({stats['with_legal_line_2']/stats['total']*100:.1f}%)")
            print(f"  millage_code:       {stats['with_millage_code']:>6} / {stats['total']} ({stats['with_millage_code']/stats['total']*100:.1f}%)")
            print(f"  use_code:           {stats['with_use_code']:>6} / {stats['total']} ({stats['with_use_code']/stats['total']*100:.1f}%)")
            print(f"  situs_city:         {stats['with_situs_city']:>6} / {stats['total']} ({stats['with_situs_city']/stats['total']*100:.1f}%)")
            print(f"  situs_zip_code:     {stats['with_situs_zip_code']:>6} / {stats['total']} ({stats['with_situs_zip_code']/stats['total']*100:.1f}%)")
            
            # Get sample nodes
            query3 = """
            MATCH (s:Subdivision)
            RETURN s
            LIMIT 5
            """
            
            print("\nSample Subdivision Nodes (first 5):")
            print("-" * 80)
            samples = session.run(query3)
            for i, record in enumerate(samples, 1):
                s = record['s']
                print(f"\n{i}. Subdivision ID: {s.get('subdivision_id', 'N/A')}")
                print(f"   Properties:")
                for key in sorted(s.keys()):
                    value = s[key]
                    if value is not None:
                        print(f"     {key}: {value}")
            
            # Check what properties exist on Subdivision nodes
            query4 = """
            MATCH (s:Subdivision)
            WITH s LIMIT 1
            RETURN keys(s) as properties
            """
            
            result = session.run(query4).single()
            if result:
                print("\n" + "=" * 80)
                print("All Properties Found on Subdivision Nodes:")
                print("-" * 80)
                props = sorted(result['properties'])
                for prop in props:
                    print(f"  - {prop}")
            
    finally:
        driver.close()


if __name__ == "__main__":
    check_subdivision_state()
