"""
Enrich Subdivision Nodes from BCPA CSV File
============================================

This script reads the BCPA_Subdivision_Name_file_20250923.csv and enriches
Subdivision nodes in Neo4j with subdivision names, HOA information, and
property management details.

Usage:
    python enrich_subdivisions_from_csv.py
"""

import os
import csv
from neo4j import GraphDatabase
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

CSV_FILE = "BCPA_Subdivision_Name_file_20250923.csv"


class SubdivisionEnricher:
    """Enrich Subdivision nodes from BCPA CSV data."""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def load_csv_data(self):
        """
        Load and aggregate CSV data by FOLIO8 (subdivision ID).
        
        Returns:
            dict: Mapping of subdivision_id to enrichment data
        """
        print("=" * 80)
        print("LOADING CSV DATA")
        print("=" * 80)
        
        subdivision_data = {}
        
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                folio8 = row.get('FOLIO8', '').strip()
                subdivision_name = row.get('Subdivision', '').strip()
                hoa_name = row.get('HOA', '').strip()
                hoa_webpage = row.get('HOA Webpage', '').strip()
                property_mgmt = row.get('Property Management', '').strip()
                property_mgmt_webpage = row.get('Property Management Wegpage', '').strip()  # Note: typo in CSV header
                
                # Only process rows with actual subdivision data
                if subdivision_name or hoa_name:
                    if folio8 not in subdivision_data:
                        subdivision_data[folio8] = {
                            'subdivision_id': folio8,
                            'name': subdivision_name if subdivision_name else None,
                            'hoa_name': hoa_name if hoa_name else None,
                            'hoa_webpage': hoa_webpage if hoa_webpage else None,
                            'property_management': property_mgmt if property_mgmt else None,
                            'property_management_webpage': property_mgmt_webpage if property_mgmt_webpage else None,
                        }
        
        print(f"✓ Loaded data for {len(subdivision_data)} unique subdivisions")
        return subdivision_data
    
    def enrich_subdivision(self, subdivision_id: str, data: dict):
        """
        Enrich a single Subdivision node with CSV data.
        
        Args:
            subdivision_id: The subdivision ID (FOLIO8)
            data: Dictionary containing enrichment data
        """
        with self.driver.session() as session:
            query = """
            MATCH (s:Subdivision {subdivision_id: $subdivision_id})
            SET s.name = COALESCE($name, s.name),
                s.hoa_name = COALESCE($hoa_name, s.hoa_name),
                s.hoa_webpage = COALESCE($hoa_webpage, s.hoa_webpage),
                s.property_management = COALESCE($property_management, s.property_management),
                s.property_management_webpage = COALESCE($property_management_webpage, s.property_management_webpage),
                s.enriched_from_csv = true,
                s.last_updated = datetime()
            RETURN s.subdivision_id as id, s.name as name
            """
            
            result = session.run(
                query,
                subdivision_id=subdivision_id,
                name=data.get('name'),
                hoa_name=data.get('hoa_name'),
                hoa_webpage=data.get('hoa_webpage'),
                property_management=data.get('property_management'),
                property_management_webpage=data.get('property_management_webpage')
            )
            
            record = result.single()
            return record is not None
    
    def create_hoa_nodes_and_links(self):
        """
        Create HOA nodes from subdivision data and link them.
        """
        print("\n" + "=" * 80)
        print("CREATING HOA NODES AND RELATIONSHIPS")
        print("=" * 80)
        
        with self.driver.session() as session:
            # Create HOA nodes and MANAGED_BY relationships
            query = """
            MATCH (s:Subdivision)
            WHERE s.hoa_name IS NOT NULL AND s.hoa_name <> ''
            MERGE (hoa:HOA {name: s.hoa_name})
            ON CREATE SET 
                hoa.hoa_id = toLower(replace(s.hoa_name, ' ', '-')),
                hoa.website = s.hoa_webpage,
                hoa.management_company = s.property_management,
                hoa.created = datetime()
            ON MATCH SET
                hoa.website = COALESCE(s.hoa_webpage, hoa.website),
                hoa.management_company = COALESCE(s.property_management, hoa.management_company)
            MERGE (s)-[:MANAGED_BY]->(hoa)
            RETURN count(DISTINCT hoa) as hoas_created, count(DISTINCT s) as subdivisions_linked
            """
            
            result = session.run(query).single()
            print(f"✓ Created/updated {result['hoas_created']} HOA nodes")
            print(f"✓ Linked {result['subdivisions_linked']} subdivisions to HOAs")
    
    def enrich_all_subdivisions(self):
        """
        Main method to enrich all subdivisions from CSV.
        """
        print("\n" + "=" * 80)
        print("ENRICHING SUBDIVISION NODES")
        print("=" * 80)
        
        # Load CSV data
        subdivision_data = self.load_csv_data()
        
        # Enrich each subdivision
        print(f"\nEnriching {len(subdivision_data)} subdivisions...")
        success_count = 0
        not_found_count = 0
        
        for subdivision_id, data in subdivision_data.items():
            if self.enrich_subdivision(subdivision_id, data):
                success_count += 1
                if success_count % 100 == 0:
                    print(f"  Processed {success_count} subdivisions...")
            else:
                not_found_count += 1
        
        print(f"\n✓ Successfully enriched {success_count} subdivisions")
        if not_found_count > 0:
            print(f"⚠ {not_found_count} subdivisions not found in database (will be skipped)")
        
        # Create HOA nodes and relationships
        self.create_hoa_nodes_and_links()
    
    def verify_enrichment(self):
        """
        Verify the enrichment results.
        """
        print("\n" + "=" * 80)
        print("VERIFICATION RESULTS")
        print("=" * 80)
        
        with self.driver.session() as session:
            # Check enriched subdivisions
            query1 = """
            MATCH (s:Subdivision)
            RETURN 
                count(s) as total_subdivisions,
                sum(CASE WHEN s.enriched_from_csv = true THEN 1 ELSE 0 END) as enriched_count,
                sum(CASE WHEN s.name IS NOT NULL THEN 1 ELSE 0 END) as with_name,
                sum(CASE WHEN s.hoa_name IS NOT NULL THEN 1 ELSE 0 END) as with_hoa
            """
            
            stats = session.run(query1).single()
            print(f"\nSubdivision Statistics:")
            print(f"  Total subdivisions: {stats['total_subdivisions']}")
            print(f"  Enriched from CSV: {stats['enriched_count']}")
            print(f"  With name: {stats['with_name']}")
            print(f"  With HOA info: {stats['with_hoa']}")
            
            # Check HOA nodes
            query2 = """
            MATCH (hoa:HOA)
            OPTIONAL MATCH (hoa)<-[:MANAGED_BY]-(s:Subdivision)
            RETURN 
                count(DISTINCT hoa) as total_hoas,
                count(DISTINCT s) as subdivisions_with_hoa
            """
            
            hoa_stats = session.run(query2).single()
            print(f"\nHOA Statistics:")
            print(f"  Total HOA nodes: {hoa_stats['total_hoas']}")
            print(f"  Subdivisions linked to HOAs: {hoa_stats['subdivisions_with_hoa']}")
            
            # Show sample enriched subdivisions
            query3 = """
            MATCH (s:Subdivision)
            WHERE s.enriched_from_csv = true AND s.name IS NOT NULL
            OPTIONAL MATCH (s)-[:MANAGED_BY]->(hoa:HOA)
            RETURN s.subdivision_id as id, s.name as name, hoa.name as hoa_name
            LIMIT 5
            """
            
            print(f"\nSample Enriched Subdivisions:")
            samples = session.run(query3)
            for sample in samples:
                hoa_info = f" (HOA: {sample['hoa_name']})" if sample['hoa_name'] else ""
                print(f"  {sample['id']}: {sample['name']}{hoa_info}")


def main():
    """Main entry point."""
    
    # Check if CSV file exists
    if not os.path.exists(CSV_FILE):
        print(f"ERROR: CSV file not found: {CSV_FILE}")
        print(f"Please ensure the file is in the same directory as this script.")
        return
    
    enricher = SubdivisionEnricher()
    
    try:
        print("=" * 80)
        print("SUBDIVISION ENRICHMENT FROM BCPA CSV")
        print("=" * 80)
        print(f"CSV File: {CSV_FILE}")
        print(f"Neo4j URI: {NEO4J_URI}")
        print()
        
        # Run enrichment
        enricher.enrich_all_subdivisions()
        
        # Verify results
        enricher.verify_enrichment()
        
        print("\n" + "=" * 80)
        print("ENRICHMENT COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        enricher.close()


if __name__ == "__main__":
    main()
