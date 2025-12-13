"""
Enrich Subdivision Nodes with Parcel Data from CSV
===================================================

This script reads the BCPA CSV file and enriches Subdivision nodes
with parcel-level data: UNIT_COUNT, LEGAL_LINE, LEGAL_LINE_2, 
MILLAGE_CODE, USE_CODE, SITUS_CITY, SITUS_ZIP_CODE

Usage:
    python enrich_subdivisions_parcel_data.py
"""

import os
import csv
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

CSV_FILE = "BCPA_Subdivision_Name_file_20250923.csv"


class SubdivisionParcelEnricher:
    """Enrich Subdivision nodes with parcel data from CSV."""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def load_csv_data(self):
        """
        Load CSV data mapping FOLIO8 to parcel properties.
        Extracts first 8 characters of FOLIO8 as subdivision_id to match Subdivision nodes.
        
        Returns:
            dict: Mapping of subdivision_id (first 8 chars of FOLIO8) to parcel data
        """
        print("=" * 80)
        print("LOADING CSV DATA")
        print("=" * 80)
        
        # Use subdivision_id (first 8 chars) as key since multiple FOLIO8 records
        # may belong to the same subdivision
        subdivision_data = {}
        total_records = 0
        
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                folio8 = row.get('FOLIO8', '').strip()
                
                if folio8 and len(folio8) >= 8:
                    # Extract first 8 characters as subdivision_id
                    subdivision_id = folio8[:8]
                    total_records += 1
                    
                    # Extract only the fields you specified
                    unit_count = row.get('UNIT_COUNT', '').strip()
                    legal_line = row.get('LEGAL_LINE', '').strip()
                    legal_line_2 = row.get('LEGAL_LINE_2', '').strip()
                    millage_code = row.get('MILLAGE_CODE', '').strip()
                    use_code = row.get('USE_CODE', '').strip()
                    situs_city = row.get('SITUS_CITY', '').strip()
                    situs_zip_code = row.get('SITUS_ZIP_CODE', '').strip()
                    
                    # Store data by subdivision_id (first 8 chars)
                    # If multiple FOLIO8 records exist for same subdivision, keep the first one
                    if subdivision_id not in subdivision_data:
                        subdivision_data[subdivision_id] = {
                            'subdivision_id': subdivision_id,
                            'folio8': folio8,  # Keep original for reference
                            'unit_count': int(unit_count) if unit_count else None,
                            'legal_line': legal_line if legal_line else None,
                            'legal_line_2': legal_line_2 if legal_line_2 else None,
                            'millage_code': millage_code if millage_code else None,
                            'use_code': use_code if use_code else None,
                            'situs_city': situs_city if situs_city else None,
                            'situs_zip_code': situs_zip_code if situs_zip_code else None,
                        }
        
        print(f"[OK] Loaded {total_records} CSV records")
        print(f"[OK] Mapped to {len(subdivision_data)} unique subdivisions (first 8 chars of FOLIO8)")
        return subdivision_data
    
    def enrich_subdivision_batch(self, batch_data):
        """
        Enrich a batch of Subdivision nodes with parcel data.
        
        Args:
            batch_data: List of dictionaries containing parcel data with subdivision_id
            
        Returns:
            int: Number of nodes updated
        """
        with self.driver.session() as session:
            query = """
            UNWIND $batch as row
            MATCH (s:Subdivision {subdivision_id: row.subdivision_id})
            SET s.unit_count = row.unit_count,
                s.legal_line = row.legal_line,
                s.legal_line_2 = row.legal_line_2,
                s.millage_code = row.millage_code,
                s.use_code = row.use_code,
                s.situs_city = row.situs_city,
                s.situs_zip_code = row.situs_zip_code,
                s.enriched_from_csv = true,
                s.last_updated = datetime()
            RETURN count(s) as updated
            """
            
            try:
                result = session.run(query, batch=batch_data)
                record = result.single()
                return record['updated'] if record else 0
            except Exception as e:
                print(f"  [WARNING] Error processing batch: {e}")
                return 0
    
    def check_subdivision_existence(self, subdivision_ids):
        """
        Check which subdivision IDs exist in the database.
        
        Args:
            subdivision_ids: List of subdivision_id values to check
            
        Returns:
            dict: Mapping of subdivision_id to existence status
        """
        with self.driver.session() as session:
            query = """
            UNWIND $subdivision_ids as sub_id
            OPTIONAL MATCH (s:Subdivision {subdivision_id: sub_id})
            RETURN sub_id, s IS NOT NULL as exists
            """
            
            result = session.run(query, subdivision_ids=subdivision_ids)
            return {record['sub_id']: record['exists'] for record in result}
    
    def enrich_all_subdivisions(self):
        """
        Main method to enrich all subdivisions from CSV.
        """
        print("\n" + "=" * 80)
        print("ENRICHING SUBDIVISION NODES WITH PARCEL DATA")
        print("=" * 80)
        
        # Load CSV data (now keyed by subdivision_id)
        subdivision_data = self.load_csv_data()
        
        if not subdivision_data:
            print("[WARNING] No data loaded from CSV file. Exiting.")
            return
        
        # Verify Subdivision nodes exist in database
        print(f"\nChecking which subdivisions exist in database...")
        subdivision_ids = list(subdivision_data.keys())
        existence_map = self.check_subdivision_existence(subdivision_ids)
        existing_count = sum(1 for exists in existence_map.values() if exists)
        print(f"[OK] Found {existing_count}/{len(subdivision_ids)} subdivisions in database")
        
        if existing_count == 0:
            print("[WARNING] No matching Subdivision nodes found in database!")
            print("   Please ensure Subdivision nodes have been created first.")
            return
        
        # Process in batches for better performance
        batch_size = 1000
        batch = []
        total_updated = 0
        total_processed = 0
        
        print(f"\nEnriching subdivisions in batches of {batch_size}...")
        
        for subdivision_id, data in subdivision_data.items():
            # Only process if subdivision exists in database
            if existence_map.get(subdivision_id, False):
                batch.append(data)
                total_processed += 1
                
                if len(batch) >= batch_size:
                    updated = self.enrich_subdivision_batch(batch)
                    total_updated += updated
                    print(f"  Processed {total_processed}/{existing_count} existing subdivisions ({total_updated} updated)...")
                    batch = []
        
        # Process remaining items
        if batch:
            updated = self.enrich_subdivision_batch(batch)
            total_updated += updated
        
        print(f"\n[OK] Successfully enriched {total_updated} subdivision nodes")
        
        # Calculate how many were not found
        not_found = existing_count - total_updated
        if not_found > 0:
            print(f"[WARNING] {not_found} subdivision IDs could not be updated (may have been skipped)")
        
        missing_from_db = len(subdivision_ids) - existing_count
        if missing_from_db > 0:
            print(f"[INFO] {missing_from_db} subdivision IDs from CSV don't exist in database (skipped)")
    
    def verify_enrichment(self):
        """
        Verify the enrichment results.
        """
        print("\n" + "=" * 80)
        print("VERIFICATION RESULTS")
        print("=" * 80)
        
        with self.driver.session() as session:
            # Check enriched subdivisions
            query = """
            MATCH (s:Subdivision)
            RETURN 
                count(s) as total,
                sum(CASE WHEN s.enriched_from_csv = true THEN 1 ELSE 0 END) as enriched_count,
                sum(CASE WHEN s.unit_count IS NOT NULL THEN 1 ELSE 0 END) as with_unit_count,
                sum(CASE WHEN s.legal_line IS NOT NULL THEN 1 ELSE 0 END) as with_legal_line,
                sum(CASE WHEN s.legal_line_2 IS NOT NULL THEN 1 ELSE 0 END) as with_legal_line_2,
                sum(CASE WHEN s.millage_code IS NOT NULL THEN 1 ELSE 0 END) as with_millage_code,
                sum(CASE WHEN s.use_code IS NOT NULL THEN 1 ELSE 0 END) as with_use_code,
                sum(CASE WHEN s.situs_city IS NOT NULL THEN 1 ELSE 0 END) as with_situs_city,
                sum(CASE WHEN s.situs_zip_code IS NOT NULL THEN 1 ELSE 0 END) as with_situs_zip_code
            """
            
            stats = session.run(query).single()
            
            print(f"\nSubdivision Statistics:")
            print(f"  Total subdivisions:     {stats['total']}")
            print(f"  Enriched from CSV:      {stats['enriched_count']}")
            print(f"\nProperty Coverage:")
            print(f"  unit_count:         {stats['with_unit_count']:>6} / {stats['total']} ({stats['with_unit_count']/stats['total']*100:.1f}%)")
            print(f"  legal_line:         {stats['with_legal_line']:>6} / {stats['total']} ({stats['with_legal_line']/stats['total']*100:.1f}%)")
            print(f"  legal_line_2:       {stats['with_legal_line_2']:>6} / {stats['total']} ({stats['with_legal_line_2']/stats['total']*100:.1f}%)")
            print(f"  millage_code:       {stats['with_millage_code']:>6} / {stats['total']} ({stats['with_millage_code']/stats['total']*100:.1f}%)")
            print(f"  use_code:           {stats['with_use_code']:>6} / {stats['total']} ({stats['with_use_code']/stats['total']*100:.1f}%)")
            print(f"  situs_city:         {stats['with_situs_city']:>6} / {stats['total']} ({stats['with_situs_city']/stats['total']*100:.1f}%)")
            print(f"  situs_zip_code:     {stats['with_situs_zip_code']:>6} / {stats['total']} ({stats['with_situs_zip_code']/stats['total']*100:.1f}%)")
            
            # Show sample enriched subdivisions
            query2 = """
            MATCH (s:Subdivision)
            WHERE s.enriched_from_csv = true
            RETURN s
            LIMIT 5
            """
            
            print(f"\nSample Enriched Subdivisions:")
            print("-" * 80)
            samples = session.run(query2)
            for i, record in enumerate(samples, 1):
                s = record['s']
                print(f"\n{i}. Subdivision ID: {s.get('subdivision_id')}")
                print(f"   unit_count: {s.get('unit_count')}")
                print(f"   legal_line: {s.get('legal_line')}")
                print(f"   legal_line_2: {s.get('legal_line_2')}")
                print(f"   millage_code: {s.get('millage_code')}")
                print(f"   use_code: {s.get('use_code')}")
                print(f"   situs_city: {s.get('situs_city')}")
                print(f"   situs_zip_code: {s.get('situs_zip_code')}")


def main():
    """Main entry point."""
    
    # Check if CSV file exists
    if not os.path.exists(CSV_FILE):
        print(f"ERROR: CSV file not found: {CSV_FILE}")
        print(f"Please ensure the file is in the same directory as this script.")
        return
    
    enricher = SubdivisionParcelEnricher()
    
    try:
        print("=" * 80)
        print("SUBDIVISION PARCEL DATA ENRICHMENT")
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
