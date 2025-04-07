from bs4 import BeautifulSoup
import requests
import os
import subprocess
import xml.etree.ElementTree as ET

# URLs und Pfade
fontbaseurl = "https://www.fussball.de/export.fontface/-/format/woff/id/"
fontappendixurl = "/type/font"
fontsbasepath = "/home/ast/fussball.de/fonts/"
ttxcmdpath = "/home/ast/.local/bin/ttx"

# Webseite abrufen
r = requests.get('https://www.fussball.de/spieltagsuebersicht/geomix-thueringenliga-thueringen-verbandsliga-herren-saison2324-thueringen/-/staffel/02M8T1I29O000008VS5489B3VVRQ15EP-G')
soup = BeautifulSoup(r.content, 'html.parser')

# Schritt 1: Fonts herunterladen und TTX-Dateien erstellen
span_elements = soup.find_all("span", {"data-obfuscation": True})
for span in span_elements:
    data_obfuscation_value = span.get("data-obfuscation")
    font_file_path = os.path.join(fontsbasepath, data_obfuscation_value)
    ttx_file_path = f"{font_file_path}.ttx"

    # Prüfen, ob die TTX-Datei existiert
    if os.path.isfile(ttx_file_path):
        print(f"Font {data_obfuscation_value} already processed.")
    else:
        # Font herunterladen, falls nicht vorhanden
        if not os.path.isfile(font_file_path):
            font_url = f"{fontbaseurl}{data_obfuscation_value}{fontappendixurl}"
            response = requests.get(font_url)
            if response.status_code == 200:
                with open(font_file_path, 'wb') as file:
                    file.write(response.content)
                print(f"Font {data_obfuscation_value} downloaded successfully.")
            else:
                print(f"Failed to download font {data_obfuscation_value}")
                continue

        # TTX-Datei erstellen
        subprocess.run([ttxcmdpath, font_file_path])
        print(f"TTX file for font {data_obfuscation_value} created.")

# Schritt 2: Unicode-Zuordnung aus TTX-Datei erstellen
def load_unicode_mapping(ttx_file_path):
    unicode_map = {}
    if os.path.isfile(ttx_file_path):
        tree = ET.parse(ttx_file_path)
        root = tree.getroot()
        for map_element in root.findall(".//map"):
            code = map_element.get("code")
            name = map_element.get("name")
            if code and name:
                unicode_map[code] = name
    return unicode_map

# Schritt 3: Matches extrahieren und übersetzen
fixtures = soup.find_all("div", {"class": "fixtures-matches-table"})
if len(fixtures) > 0:
    matches = fixtures[0].find_all("tr")
    print(f"Number of matches: {len(matches)}")
    
    for match in matches:
        fixturedate = match.find("td", {"class": "column-date"})
        if fixturedate:
            span = fixturedate.find("span", {"data-obfuscation": True})
            if span:
                # TTX-Datei der Font laden
                data_obfuscation_value = span.get("data-obfuscation")
                ttx_file_path = f"{fontsbasepath}{data_obfuscation_value}.ttx"
                unicode_map = load_unicode_mapping(ttx_file_path)
                
                # Obfuskierten Text übersetzen
                obfuscated_text = span.decode_contents()
                translated_text = ""
                for part in obfuscated_text.split(";"):
                    if "&#x" in part:
                        code = part.strip("&#x").lower()
                        translated_text += unicode_map.get(f"0x{code}", "?")  # "?" für unbekannte Zeichen
                    elif part.strip():
                        translated_text += part.strip()  # Nicht-obfuskierten Text hinzufügen
                
                print(f"Match date (translated): {translated_text}")
            else:
                print("No span with data-obfuscation found.")
else:
    print("No fixtures found.")
