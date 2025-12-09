
import os
import sys
import re
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def get_fence_requirements(parcel_id):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    output_file = f"fence_requirements_{parcel_id}.txt"
    
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
            
            # Get all fence rules
            query_rules = """
            MATCH (s:Section)
            WHERE s.id STARTS WITH 'Weston::' 
              AND toLower(s.text) CONTAINS 'fence'
            RETURN s.name, s.text
            ORDER BY s.name
            """
            all_rules = list(session.run(query_rules))
            
            # Collect all relevant excerpts
            height_info = []
            setback_info = []
            
            for r in all_rules:
                text = r['s.text']
                section = r['s.name']
                text_lower = text.lower()
                
                # Look for height-related content
                if 'height' in text_lower or 'tall' in text_lower or 'high' in text_lower:
                    # Extract sentences containing height info
                    sentences = re.split(r'[.!?]\s+', text)
                    for sent in sentences:
                        if any(word in sent.lower() for word in ['height', 'tall', 'high', 'feet', 'ft']):
                            if re.search(r'\d+\s*(?:feet|ft|\')', sent):
                                height_info.append({
                                    'section': section,
                                    'text': sent.strip()
                                })
                
                # Look for setback-related content
                if 'setback' in text_lower or 'property line' in text_lower or 'yard' in text_lower:
                    sentences = re.split(r'[.!?]\s+', text)
                    for sent in sentences:
                        if any(word in sent.lower() for word in ['setback', 'property line', 'yard', 'boundary']):
                            if re.search(r'\d+\s*(?:feet|ft|\')', sent):
                                setback_info.append({
                                    'section': section,
                                    'text': sent.strip()
                                })
            
            # Write to file and console
            output = []
            output.append("="*80)
            output.append("FENCE HEIGHT AND SETBACK REQUIREMENTS SUMMARY")
            output.append("="*80)
            output.append(f"\nParcel ID: {parcel_id}")
            if addr:
                output.append(f"Address: {addr.get('street', 'N/A')}, {addr.get('city', 'N/A')}")
            if ord_zone:
                output.append(f"Zoning: {ord_zone.get('name')} ({ord_zone.get('code')})")
            output.append(f"Property Type: {parcel.get('property_type', 'N/A')}")
            output.append(f"Corner Lot: {'Yes' if parcel.get('is_corner_lot') else 'No'}")
            output.append("")
            
            output.append("="*80)
            output.append("HEIGHT REQUIREMENTS")
            output.append("="*80)
            
            if height_info:
                seen = set()
                for item in height_info:
                    if item['text'] not in seen:
                        seen.add(item['text'])
                        output.append(f"\n[Section {item['section']}]")
                        output.append(f"{item['text']}")
            else:
                output.append("\nNo specific height requirements found.")
            
            output.append("\n" + "="*80)
            output.append("SETBACK REQUIREMENTS")
            output.append("="*80)
            
            if setback_info:
                seen = set()
                for item in setback_info:
                    if item['text'] not in seen:
                        seen.add(item['text'])
                        output.append(f"\n[Section {item['section']}]")
                        output.append(f"{item['text']}")
            else:
                output.append("\nNo specific setback requirements found.")
            
            output.append("\n" + "="*80)
            output.append("IMPORTANT NOTES:")
            output.append("- These are automated extractions from the ordinance text")
            output.append("- Review fence_rules_503911073240.txt for complete regulations")
            output.append("- Consult with Weston Building Department for official interpretation")
            output.append("- HOA rules may impose additional restrictions")
            output.append("="*80)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output))
            
            # Print to console
            for line in output:
                print(line)
            
            print(f"\n✓ Summary saved to: {output_file}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    pid_arg = sys.argv[1] if len(sys.argv) > 1 else "503911073240"
    get_fence_requirements(pid_arg)
