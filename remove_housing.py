import json
import ijson
import os

def main():
    input_file = "data_20260603.json"
    temp_file = "data_20260603_tmp.json"
    
    print(f"Aloitetaan suodatus: {input_file} (tämä voi kestää hetken, tiedosto on iso)")
    
    processed_count = 0
    removed_count = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as fin, open(temp_file, 'w', encoding='utf-8') as fout:
            fout.write("[\n")
            
            companies = ijson.items(fin, 'item')
            first = True
            
            for company in companies:
                processed_count += 1
                if processed_count % 100000 == 0:
                    print(f"Käsitelty {processed_count} yritystä, poistettu asunto/kiinteistö-yhtiöitä tähän mennessä {removed_count}...")
                
                names = company.get("names", [])
                company_name = names[0].get("name", "") if names else ""
                name_lower = company_name.lower()
                
                main_business_line = company.get("mainBusinessLine")
                industry_code = main_business_line.get("type", "") if isinstance(main_business_line, dict) else ""
                
                is_housing = False
                if any(term in name_lower for term in ["asunto oy", "asunto-osakeyhtiö", "kiinteistö oy", "kiinteistöosakeyhtiö", "as.oy", "as. oy", "asunto-oy"]):
                    is_housing = True
                elif industry_code and industry_code.startswith("682"):
                    is_housing = True
                    
                if is_housing:
                    removed_count += 1
                    continue
                    
                if not first:
                    fout.write(",\n")
                first = False
                
                json.dump(company, fout, ensure_ascii=False)
                
            fout.write("\n]\n")
            
        print(f"\nSuodatus valmis!")
        print(f"Käsitelty yhteensä: {processed_count} yritystä.")
        print(f"Poistettu lopullisesti: {removed_count} asunto/kiinteistöyhtiötä.")
        print("Korvataan alkuperäinen tiedosto uudella puhtaammalla versiolla...")
        
        os.replace(temp_file, input_file)
        print("Tiedosto korvattu onnistuneesti!")
        
    except Exception as e:
        print(f"Virhe: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    main()
