import argparse
import json
import csv
import sys
import os
import ijson

TARGET_NICHES_PREFIXES = [
    "41", "43",          # Rakennus & Remontointi
    "96022", "86",       # Kauneus & Terveys
    "56",                # Ravintola & Kahvila
    "96021",             # Parturi & Kampaamo
    "62", "63", "70",    # IT & Konsultointi
    "742",               # Valokuvaus
    "93130", "96040",    # Kuntoilu & Hyvinvointi
    "452",               # Autokorjaamo
    "49", "52"           # Kuljetus & Logistiikka
]

def process_companies(data_file, city=None, industry=None, require_website=False, no_website=False, limit=None, exclude_housing=False, only_ltd=False, target_niches=False):
    print(f"Luetaan ja suodatetaan massadataa tiedostosta {data_file} (tämä voi kestää hetken)...")
    
    if city:
        print(f"Kaupunki: {city}")
    if industry:
        print(f"Toimiala: {industry}")
    if target_niches:
        print(f"Toimiala: Vain valitut kohdetoimialat (Rakennus, IT, Ravintolat jne.)")
    if require_website:
        print(f"Vaatimus: Vain yritykset joilla on verkkosivu")
    if no_website:
        print(f"Vaatimus: Vain yritykset joilla ei ole verkkosivua")
    if exclude_housing:
        print(f"Vaatimus: Ei asunto- tai kiinteistöosakeyhtiöitä")
    if only_ltd:
        print(f"Vaatimus: Vain osakeyhtiöt (Oy)")
    if limit:
        print(f"Rajoitus: {limit} tulosta")
        
    companies_data = []
    processed_count = 0
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            # ijson.items tuottaa generaattorin json-taulukon elementeistä
            companies = ijson.items(f, 'item')
            for company in companies:
                processed_count += 1
                if processed_count % 100000 == 0:
                    print(f"Käyty läpi {processed_count} yritystä...")
                    
                # Ohitetaan yritykset, joilla on lopetuspäivämäärä (eli ovat lakanneet)
                if company.get("endDate"):
                    continue
                    
                # Verkkosivu
                website_info = company.get("website")
                website_url = website_info.get("url", "") if isinstance(website_info, dict) else ""
                
                if require_website and not website_url:
                    continue
                    
                if no_website and website_url:
                    continue
                    
                # Toimialakoodi
                main_business_line = company.get("mainBusinessLine")
                industry_code = main_business_line.get("type", "") if isinstance(main_business_line, dict) else ""
                
                if industry and industry != industry_code:
                    continue
                    
                if target_niches and industry_code:
                    if not any(industry_code.startswith(prefix) for prefix in TARGET_NICHES_PREFIXES):
                        continue
                elif target_niches and not industry_code:
                    continue
                    
                # Yhtiömuoto
                if only_ltd:
                    company_forms = company.get("companyForms", [])
                    is_ltd = False
                    for form in company_forms:
                        if form.get("type") in ["16", "17"]:
                            is_ltd = True
                            break
                    if not is_ltd:
                        continue
                        
                # Osoite (kaupunki)
                addresses = company.get("addresses", [])
                city_matches = False
                primary_city_name = ""
                
                if addresses:
                    for addr in addresses:
                        post_offices = addr.get("postOffices", [])
                        for po in post_offices:
                            c_name = po.get("city", "")
                            if not primary_city_name and po.get("languageCode") == "1":
                                primary_city_name = c_name
                            elif not primary_city_name:
                                primary_city_name = c_name
                                
                            if city and city.lower() in c_name.lower():
                                city_matches = True
                                
                if not city:
                    city_matches = True
                    
                if city and not city_matches:
                    continue
                    
                # Nimi
                business_id = company.get("businessId", {}).get("value", "") if company.get("businessId") else ""
                names = company.get("names", [])
                company_name = names[0].get("name", "") if names else ""
                
                if exclude_housing:
                    name_lower = company_name.lower()
                    if any(term in name_lower for term in ["asunto oy", "asunto-osakeyhtiö", "kiinteistö oy", "kiinteistöosakeyhtiö", "as.oy", "as. oy", "asunto-oy"]):
                        continue
                    if industry_code and industry_code.startswith("682"):
                        continue
                
                companies_data.append({
                    "Nimi": company_name,
                    "Y-tunnus": business_id,
                    "Kaupunki": primary_city_name,
                    "Toimialakoodi": industry_code,
                    "Verkkosivu": website_url
                })
                
                if limit and len(companies_data) >= limit:
                    print(f"\nRajoitus ({limit}) saavutettu, lopetetaan haku.")
                    break
    except Exception as e:
        print(f"Virhe käsiteltäessä tiedostoa: {e}")
        return []
        
    print(f"Käyty läpi yhteensä {processed_count} yritystä.")
    return companies_data

def save_to_csv(companies_data, output_file):
    if not companies_data:
        print("Ei tallennettavaa dataa.")
        return
        
    keys = ["Nimi", "Y-tunnus", "Kaupunki", "Toimialakoodi", "Verkkosivu"]
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(companies_data)
        print(f"Tallennettu {len(companies_data)} yritystä tiedostoon {output_file}")
    except IOError as e:
        print(f"Virhe tiedostoon kirjoittaessa: {e}")

def main():
    parser = argparse.ArgumentParser(description="PRH Lead Generator - Suodattaa paikallisesta PRH json bulk -datasta")
    parser.add_argument("--city", "-c", help="Kaupunki (esim. Helsinki)", type=str)
    parser.add_argument("--industry", "-i", help="Toimialakoodi (esim. 62010)", type=str)
    parser.add_argument("--require-website", "-w", help="Ota mukaan vain yritykset, joilla on verkkosivu", action="store_true")
    parser.add_argument("--no-website", "-nw", help="Ota mukaan vain yritykset, joilla EI ole verkkosivua", action="store_true")
    parser.add_argument("--exclude-housing", "-eh", help="Jätä pois asunto- ja kiinteistöosakeyhtiöt", action="store_true")
    parser.add_argument("--only-ltd", "-ol", help="Ota mukaan vain Osakeyhtiöt (Oy)", action="store_true")
    parser.add_argument("--target-niches", "-tn", help="Ota mukaan vain valitut kohdetoimialat (Rakennus, Kauneus, IT, Ravintolat yms.)", action="store_true")
    parser.add_argument("--limit", "-l", help="Rajoita tulosten määrää", type=int)
    parser.add_argument("--output", "-o", help="Tulostiedosto (oletus: leads.csv)", default="leads.csv", type=str)
    parser.add_argument("--data", "-d", help="Polku PRH:n massalataus json-tiedostoon", default="data_20260603.json", type=str)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data):
        print(f"Virhe: Datatiedostoa '{args.data}' ei löydy.")
        print("Oletko purkanut ZIP-tiedoston tähän kansioon?")
        sys.exit(1)
        
    data = process_companies(
        data_file=args.data,
        city=args.city,
        industry=args.industry,
        require_website=args.require_website,
        no_website=args.no_website,
        limit=args.limit,
        exclude_housing=args.exclude_housing,
        only_ltd=args.only_ltd,
        target_niches=args.target_niches
    )
    
    save_to_csv(data, args.output)

if __name__ == "__main__":
    main()
