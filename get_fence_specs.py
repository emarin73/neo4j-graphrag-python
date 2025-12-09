
import os
import sys
import re
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def extract_fence_specs(parcel_id):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            # Get parcel info
            query_info = """
            MATCH (p:Parcel {parcel_id: $pid})
            OPTIONAL MATCH (p)-[:HAS_ADDRESS]->(a:Address)
            OPTIONAL MATCH (p)-[:HAS_ZONING]->(z:Zoning)
            OPTIONAL MATCH (z)-[:GOVERNED_BY]->(oz:Zone)
            RETURN p, a, z, oz LIMIT 1
            """
            results = list(session.run(query_info, pid=parcel_id))
            
            if not results:
                print(f"Parcel {parcel_id} not found.")
                return
            
            result = results[0]
            parcel = result['p']
            addr = result['a']
            ord_zone = result['oz']
            
            print("="*80)
            print("FENCE SETBACK AND HEIGHT REQUIREMENTS")
            print("="*80)
            print(f"\nParcel: {parcel_id}")
            if addr:
                print(f"Address: {addr.get('street', 'N/A')}, {addr.get('city', 'N/A')}")
            if ord_zone:
                print(f"Zoning: {ord_zone.get('name')} ({ord_zone.get('code')})")
            print(f"Property Type: {parcel.get('property_type', 'N/A')}")
            print(f"Corner Lot: {'Yes' if parcel.get('is_corner_lot') else 'No'}")
            
            # Get all fence rules
            query_rules = """
            MATCH (s:Section)
            WHERE s.id STARTS WITH 'Weston::' 
              AND toLower(s.text) CONTAINS 'fence'
            RETURN s.name, s.text
            ORDER BY s.name
            """
            all_rules = list(session.run(query_rules))
            
            # Search for height and setback specifications
            height_specs = []
            setback_specs = []
            
            for r in all_rules:
                text = r['s.text']
                section = r['s.name']
                
                # Look for height mentions (feet, ft, inches, in, height)
                height_patterns = [
                    r'(\d+)\s*(?:feet|ft\.?|\')\s*(?:tall|high|height|maximum)',
                    r'(?:height|tall|high|maximum).*?(\d+)\s*(?:feet|ft\.?|\')',
                    r'(\d+)\s*(?:feet|ft\.?)\s*(\d+)\s*(?:inches|in\.?|\")',
                    r'maximum.*?height.*?(\d+)',
                    r'shall not exceed.*?(\d+)\s*(?:feet|ft)',
                ]
                
                for pattern in height_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        context_start = max(0, match.start() - 100)
                        context_end = min(len(text), match.end() + 100)
                        context = text[context_start:context_end].strip()
                        height_specs.append({
                            'section': section,
                            'spec': match.group(0),
                            'context': context
                        })
                
                # Look for setback mentions
                setback_patterns = [
                    r'setback.*?(\d+)\s*(?:feet|ft\.?)',
                    r'(\d+)\s*(?:feet|ft\.?).*?setback',
                    r'(?:front|rear|side).*?(?:yard|line|boundary).*?(\d+)\s*(?:feet|ft)',
                    r'property line.*?(\d+)\s*(?:feet|ft)',
                ]
                
                for pattern in setback_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        context_start = max(0, match.start() - 100)
                        context_end = min(len(text), match.end() + 100)
                        context = text[context_start:context_end].strip()
                        setback_specs.append({
                            'section': section,
                            'spec': match.group(0),
                            'context': context
                        })
            
            # Display results
            print("\n" + "="*80)
            print("HEIGHT REQUIREMENTS")
            print("="*80)
            
            if height_specs:
                seen = set()
                for spec in height_specs:
                    key = (spec['section'], spec['spec'])
                    if key not in seen:
                        seen.add(key)
                        print(f"\n[Section {spec['section']}]")
                        print(f"  Specification: {spec['spec']}")
                        print(f"  Context: ...{spec['context']}...")
            else:
                print("\nNo specific height requirements found in extracted text.")
                print("Review the full regulations file for details.")
            
            print("\n" + "="*80)
            print("SETBACK REQUIREMENTS")
            print("="*80)
            
            if setback_specs:
                seen = set()
                for spec in setback_specs:
                    key = (spec['section'], spec['spec'])
                    if key not in seen:
                        seen.add(key)
                        print(f"\n[Section {spec['section']}]")
                        print(f"  Specification: {spec['spec']}")
                        print(f"  Context: ...{spec['context']}...")
            else:
                print("\nNo specific setback requirements found in extracted text.")
                print("Review the full regulations file for details.")
            
            print("\n" + "="*80)
            print("\nNOTE: These are automated extractions. Please review the complete")
            print("regulations in fence_rules_503911073240.txt for full context and")
            print("any additional requirements that may apply to your specific situation.")
            print("="*80)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    pid_arg = sys.argv[1] if len(sys.argv) > 1 else "503911073240"
    extract_fence_specs(pid_arg)
