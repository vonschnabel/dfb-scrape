from bs4 import BeautifulSoup
import requests
import os
import subprocess
import xml.etree.ElementTree as ET

fontbaseurl = "https://www.fussball.de/export.fontface/-/format/woff/id/"
fontappendixurl = "/type/font"
fontsbasepath = "/home/ast/fussball.de/fonts/"
ttxcmdpath = "/home/ast/.local/bin/ttx"

r = requests.get('https://www.fussball.de/spieltagsuebersicht/geomix-thueringenliga-thueringen-verbandsliga-herren-saison2324-thueringen/-/staffel/02M8T1I29O000008VS5489B3VVRQ15EP-G')
r.encoding = 'utf-8' 
#print(r.content) ##

soup = BeautifulSoup(r.content, 'html.parser')
span_elements = soup.find_all("span", {"data-obfuscation": True})
print(soup) ##
"""
for span in span_elements:
  data_obfuscation_value = span.get("data-obfuscation")
  print(data_obfuscation_value)

  if(os.path.isfile(fontsbasepath +data_obfuscation_value) == True):
    if(os.path.isfile(fontsbasepath +data_obfuscation_value +".ttx") == True):
      print(data_obfuscation_value, "already exists")
    else:
      output = subprocess.run([ttxcmdpath, fontsbasepath +data_obfuscation_value])
      print(output)
  else:
    response = requests.get(fontbaseurl +data_obfuscation_value +fontappendixurl)
    file_Path = fontsbasepath +data_obfuscation_value
    if response.status_code == 200:
      with open(file_Path, 'wb') as file:
        file.write(response.content)
      print('File downloaded successfully')
      output = subprocess.run([ttxcmdpath, fontsbasepath +data_obfuscation_value])
      print(output)
    else:
      print('Failed to download file')


fixtures = soup.find_all("div", {"class": "fixtures-matches-table"})
print("len:",len(fixtures))
matches = fixtures[0].find_all("tr")
print("len:",len(matches))
for match in matches:
  fixturedate = match.find("td", {"class": "column-date"})
  print(fixturedate)
  #print(type(fixturedate))
  #print()
"""


"""
ttx_file = fontsbasepath +"sqybcoio" +".ttx"
tree = ET.parse(ttx_file)
root = tree.getroot()
unicode_to_char = {}
for map_element in root.findall(".//map"):
    code = map_element.get("code")
    name = map_element.get("name")
    if code and name:
        unicode_to_char[code] = name

print(unicode_to_char)  # {'0xe715': 't', '0xe70b': 'M', ...}
"""
