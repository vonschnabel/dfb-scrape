from bs4 import BeautifulSoup
import requests
import os
import subprocess
import xml.etree.ElementTree as ET
import html
import json
import csv
import re
from flask import Flask, render_template, request, jsonify, send_from_directory, render_template, redirect, url_for

fontbaseurl = "https://www.fussball.de/export.fontface/-/format/woff/id/"
fontappendixurl = "/type/font"
fontsbasepath = "./fonts/"
ttxcmdpath = "/home/ast/.local/bin/ttx"

def sanitize_filename(filename):
  forbidden = r'[\\/:*?"<>|]'
  filename = filename.replace('/', '_')
  filename = re.sub(forbidden, '', filename)
  filename = filename.strip()
  return filename

# Funktion zum Laden des Unicode-Mappings
def load_unicode_mapping(ttx_file_path):
  unicode_map = {
    "0x20": " ", "0x7c": "", "0xa0": ""
  }
  if os.path.isfile(ttx_file_path):
    tree = ET.parse(ttx_file_path)
    root = tree.getroot()
    for map_element in root.findall(".//map"):
      code = map_element.get("code")
      name = map_element.get("name")
      if code and name:
        unicode_map[code.lower()] = name  # Unicode-Wert als Key speichern

  # Nummern-Wörter in echte Zahlen umwandeln
  number_map = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "colon": ":", "comma": ",", "period": ".", "hyphen": "-"
  }

  for code, name in unicode_map.items():
    if name in number_map:
      unicode_map[code] = number_map[name]  # Wörter zu Zahlen umwandeln

  return unicode_map

def getmatchday(url):
  r = requests.get(url)
  r.encoding = r.apparent_encoding  # Korrekte Zeichensatz-Erkennung
  soup = BeautifulSoup(r.text, 'html.parser')

  tmp = soup.find('select', attrs={'name': 'spieltag'})
  matchdaynumber = tmp.find('option', attrs={'selected': 'selected'})
  matchdaynumber = matchdaynumber.text.split('.')[0]
  tmp = soup.find('div', {"class": "stage-content"})
  leaguename = tmp.find('h2').text
  season = tmp.find('h4').text

  # Das Element finden, nach dem alles entfernt werden soll
  cutoff_element = soup.find("td", {"class": "row-headline"}, string="Verlegte Spiele außerhalb des Spieltages")

  if cutoff_element:
    # Entferne alle nachfolgenden Elemente von `cutoff_element`
    next_element = cutoff_element.find_parent("tr").find_next_sibling()
    while next_element:
      to_remove = next_element
      next_element = next_element.find_next_sibling()
      to_remove.decompose()  # Löscht das Element komplett aus dem HTML-Baum

    # Optional: Auch das `cutoff_element` selbst entfernen
    cutoff_element.find_parent("tr").decompose()

  # Schritt 1: Fonts herunterladen und TTX-Dateien erstellen
  span_elements = soup.find_all("span", {"data-obfuscation": True})
  for span in span_elements:
    data_obfuscation_value = span.get("data-obfuscation")
    font_file_path = os.path.join(fontsbasepath, data_obfuscation_value)
    ttx_file_path = f"{font_file_path}.ttx"

    if os.path.isfile(ttx_file_path):
      print(f"Font {data_obfuscation_value} already processed.")
    else:
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

  matchday = {
    "leaguename": leaguename,
    "season": season,
    "matchday": matchdaynumber,
    "matches": []
  }

  # Matches extrahieren
  fixtures = soup.find_all("div", {"class": "fixtures-matches-table"})
  if fixtures:
    matches = fixtures[0].find_all("tr")
    prevdate = ""

    for match in matches:
      fixturedate = match.find("td", {"class": "column-date"})
      fixturescore = match.find("td", {"class": "column-score"})
      fixtureteamname = match.find_all("div", {"class": "club-name"})
      fixtureteamid = match.find_all("a", {"class": "club-wrapper"})
      translated_date = ""
      translated_time = ""
      translated_score = ""
      hometeamname = ""
      awayteamname = ""
      hometeamid = ""
      awayteamid = ""
      if fixtureteamname:
        if(len(fixtureteamname) == 2):
          hometeamname = html.unescape(fixtureteamname[0].decode_contents())
          hometeamname = hometeamname.strip()
          tmp = hometeamname.split("\t")
          hometeamname = "".join(tmp)
          awayteamname = html.unescape(fixtureteamname[1].decode_contents())
          awayteamname = awayteamname.strip()
          tmp = awayteamname.split("\t")
          awayteamname = "".join(tmp)
        elif(len(fixtureteamname) == 1):
          hometeamname = html.unescape(fixtureteamname[0].decode_contents())
          hometeamname = hometeamname.strip()
          tmp = hometeamname.split("\t")
          hometeamname = "".join(tmp)
          awayteamname = match.find("span", {"class": "info-text"})
          awayteamname = html.unescape(awayteamname.decode_contents())
        else:
          #print("<< ERROR >>")
          return "<< ERROR >>"
      if fixtureteamid:
        if(len(fixtureteamid) == 2):
          hometeamid = fixtureteamid[0].get("href")
          awayteamid = fixtureteamid[1].get("href")
          if(hometeamid):
            hometeamid = hometeamid.split("team-id/")
            hometeamid = hometeamid[1]
          if(awayteamid):
            awayteamid = awayteamid.split("team-id/")
            awayteamid = awayteamid[1]

      # **📅 Spieldatum entschlüsseln**
      if fixturedate:
        spans = fixturedate.find_all("span", {"data-obfuscation": True})
        if spans:
          if(len(spans) > 1):
            data_obfuscation_value = spans[0].get("data-obfuscation")
            ttx_file_path = f"{fontsbasepath}{data_obfuscation_value}.ttx"
            unicode_map = load_unicode_mapping(ttx_file_path)

            obfuscated_text = html.unescape(spans[0].decode_contents())  # HTML-Entities dekodieren
            for part in obfuscated_text:
              code = hex(ord(part))
              translated_date += unicode_map.get(code, "?")  # Zeichen ersetzen
            if(prevdate != translated_date):
              prevdate = translated_date

            data_obfuscation_value = spans[1].get("data-obfuscation")
            ttx_file_path = f"{fontsbasepath}{data_obfuscation_value}.ttx"
            unicode_map = load_unicode_mapping(ttx_file_path)

            obfuscated_text = html.unescape(spans[1].decode_contents())  # HTML-Entities dekodieren
            for part in obfuscated_text:
              code = hex(ord(part))
              translated_time += unicode_map.get(code, "?")  # Zeichen ersetzen
          else:
            data_obfuscation_value = spans[0].get("data-obfuscation")
            ttx_file_path = f"{fontsbasepath}{data_obfuscation_value}.ttx"
            unicode_map = load_unicode_mapping(ttx_file_path)

            obfuscated_text = html.unescape(spans[0].decode_contents())  # HTML-Entities dekodieren
            for part in obfuscated_text:
              code = hex(ord(part))
              translated_time += unicode_map.get(code, "?")  # Zeichen ersetzen
            translated_date = prevdate

      # **⚽ Spielergebnis entschlüsseln**
      if fixturescore:
        score_left_span = fixturescore.find("span", {"data-obfuscation": True, "class": "score-left"})
        score_right_span = fixturescore.find("span", {"data-obfuscation": True, "class": "score-right"})

        score_left = ""
        score_right = ""

        if score_left_span and score_right_span:
          data_obfuscation_value = score_left_span.get("data-obfuscation")
          ttx_file_path = f"{fontsbasepath}{data_obfuscation_value}.ttx"
          unicode_map = load_unicode_mapping(ttx_file_path)

          # **Score-Left entschlüsseln**
          obfuscated_text = html.unescape(score_left_span.decode_contents())
          for part in obfuscated_text:
            code = hex(ord(part))
            score_left += unicode_map.get(code, "?")

          # **Score-Right entschlüsseln**
          obfuscated_text = html.unescape(score_right_span.decode_contents())
          for part in obfuscated_text:
            if(part == "<"):
              break
            else:
              code = hex(ord(part))
              score_right += unicode_map.get(code, "?")

          translated_score = f"{score_left}:{score_right}"

      #print(f"Match date: {translated_date}, Score: {translated_score}")
      if(translated_date != ""):
        match_object = {
          "date": translated_date,
          "time": translated_time,
          "score": translated_score,
          "hometeamname": hometeamname,
          "awayteamname": awayteamname,
          "hometeamid": hometeamid,
          "awayteamid": awayteamid
        }
        matchday["matches"].append(match_object)

    return matchday
  else:
    print("No fixtures found.")

def getmatchtable(url):  
  
  r = requests.get(url)
  r.encoding = r.apparent_encoding  # Korrekte Zeichensatz-Erkennung
  soup = BeautifulSoup(r.text, 'html.parser')

  tmp = soup.find('select', attrs={'name': 'spieltag'})
  matchdaynumber = tmp.find('option', attrs={'selected': 'selected'})
  matchdaynumber = matchdaynumber.text.split('.')[0]
  tmp = soup.find('div', {"class": "stage-content"})
  leaguename = tmp.find('h2').text
  season = tmp.find('h4').text

  table = {
    "leaguename": leaguename,
    "season": season,
    "matchday": matchdaynumber,
    "table": []
  }

  table_element = soup.find("div", {"id": "fixture-league-tables"})
  table_body = table_element.find("tbody")

  table_teams = table_body.find_all("tr")
  for team_row in table_teams:
    teamname = team_row.find("div", {"class": "club-name"})
    teamname = teamname.decode_contents()
    teamname = teamname.strip()
    tmp = teamname.split("\t")
    teamname = "".join(tmp)

    teamid_tmp = team_row.find("td", {"class": "column-club"})
    teamid = teamid_tmp.find("a", {"class": "club-wrapper"})
    teamid = teamid.get('href')
    if(teamid is not None):
      teamid = teamid.split("team-id/")
      teamid = teamid[1]

    promotion_relegation = team_row.get('class')
    if(promotion_relegation is not None):
      promotion_relegation = promotion_relegation[0]
    if(promotion_relegation in ["row-promotion","row-promotion-playoff","row-relegation","row-relegation-playoff"]):
      promotion_relegation = promotion_relegation.replace("row-", "")
    else:
      promotion_relegation = None

    rank = team_row.find("td", {"class": "column-rank"})
    rank = rank.decode_contents()
    rank = rank.strip()
    tmp = rank.split("\t")
    rank = "".join(tmp)
    rank = rank.replace('.', '')

    points = team_row.find("td", {"class": "column-points"})
    points = points.decode_contents()
    points = points.strip()
    #tmp = points.split("\t")
    #points = "".join(tmp)

    miscdata = team_row.find_all("td")

    rank_change = team_row.find("td", {"class": "column-icon"})
    rank_change = rank_change.find("span")
    rank_change = rank_change.get('class')[0]
    rank_change_map = {
      "up-right": "up", "down-right": "down", "right": "stay"
    }
    rank_change = rank_change.replace("icon-arrow-", "")
    rank_change = rank_change_map[rank_change]

    matches_played = miscdata[3].decode_contents()
    matches_played = matches_played.strip()
    #tmp = matches_played.split("\t")
    #matches_played = "".join(tmp)

    won = miscdata[4].decode_contents()
    won = won.strip()
    #tmp = won.split("\t")
    #won = "".join(tmp)

    draw = miscdata[5].decode_contents()
    draw = draw.strip()
    #tmp = draw.split("\t")
    #draw = "".join(tmp)

    lost = miscdata[6].decode_contents()
    lost = lost.strip()
    #tmp = lost.split("\t")
    #lost = "".join(tmp)

    goals_scored = miscdata[7].decode_contents()
    goals_scored = goals_scored.strip()
    #tmp = goals_scored.split("\t")
    #goals_scored = "".join(tmp)
    goals_scored = goals_scored.replace(" ","")
    tmp_goals_scored = goals_scored.split(":")
    goals_scored = tmp_goals_scored[0]

    goals_conceded = tmp_goals_scored[1]

#row-promotion
#row-promotion-playoff
#row-relegation
#row-relegation-playoff
#row-promotion odd
#row-promotion-playoff odd
#row-relegation odd
#row-relegation-playoff odd


    table_entry = {
      "teamname": teamname,
      "teamid": teamid,
      "points": points,
      "goals_scored": goals_scored,
      "goals_conceded": goals_conceded,
      "won": won,
      "draw": draw,
      "lost": lost,
      "matches_played": matches_played,
      "rank": rank,
      "rank_change": rank_change,
      "promotion_relegation": promotion_relegation
    }
    #table.append(table_entry)
    table["table"].append(table_entry)
  return table

def getmatchrange(url):
  r = requests.get(url)
  r.encoding = r.apparent_encoding  # Korrekte Zeichensatz-Erkennung
  soup = BeautifulSoup(r.text, 'html.parser')
  tmp = soup.find("a", string="Spieltage / Tabellen")
  matchdaylink = tmp.get('href')

  r = requests.get(matchdaylink)
  r.encoding = r.apparent_encoding  # Korrekte Zeichensatz-Erkennung
  soup = BeautifulSoup(r.text, 'html.parser')
  tmp = soup.find('select', attrs={'name': 'spieltag'})
  options = tmp.find_all('option')
  firstelement = int(options[0].text.split('.')[0])
  lastelement = int(options[-1].text.split('.')[0])
  
  return firstelement, lastelement

def getlinks(url, min=None, max=None):
  r = requests.get(url)
  r.encoding = r.apparent_encoding  # Korrekte Zeichensatz-Erkennung
  soup = BeautifulSoup(r.text, 'html.parser')
  tmp = soup.find("a", string="Spieltage / Tabellen")
  matchdaylink = tmp.get('href')

  r = requests.get(matchdaylink)
  r.encoding = r.apparent_encoding  # Korrekte Zeichensatz-Erkennung
  soup = BeautifulSoup(r.text, 'html.parser')
  tmp = soup.find('select', attrs={'name': 'spieltag'})
  options = tmp.find_all('option')
  firstelement = int(options[0].text.split('.')[0])
  lastelement = int(options[-1].text.split('.')[0])

  try:
    if(max >= min):
      pass
    else:
      print("<< Min - Max Error>>")
      return
  except:
    print("min or max are no int values")
    return
  if(min == None):
    min = int(firstelement)
  if(max == None):
    max = int(lastelement)
  if(min < firstelement or max > lastelement):
    print("<< Min - Max Error>>")
    return
  links = []
  for item in options:
    if(int(item.text.split('.')[0]) >= min and int(item.text.split('.')[0]) <= max):
      links.append(item.get("data-href"))

  print(links)
  return links



from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
  return render_template('index.html')

@app.route('/loadmatchrange', methods=['GET'])
def loadmatchrange():
  url = request.args.get('url')
  if url:
    #print(f"GET empfangene URL (onblur): {url}")
    firstitem, lastitem = getmatchrange(url)
    return jsonify({'min': firstitem, 'max': lastitem})


download_folder = "downloads"

@app.route("/files")
def list_files():
  """Listet alle heruntergeladenen Dateien auf."""
  files = os.listdir(download_folder)
  return jsonify({"files": files})

@app.route("/files/<filename>")
def get_file(filename):
  """Ermöglicht das Herunterladen von Dateien aus dem 'downloads'-Ordner."""
  return send_from_directory(download_folder, filename, as_attachment=True)

@app.route("/downloads")
def downloads_page():
  """Zeigt eine Liste der heruntergeladenen Dateien als HTML-Seite."""
  files = sorted(os.listdir(download_folder))
  return render_template("files.html", files=files)

@app.route('/loadmatches', methods=['POST'])
def loadmatches():
  url = request.form.get('url_input')
  min_value = int(request.form.get('min_value'))
  max_value = int(request.form.get('max_value'))
  if url:
    matches = getlinks(url, min_value, max_value)
    #print(matches)
    matchlist = []
    tablelist = []
    for match in matches:
      #print("url:",url)
      matchitem = getmatchday(match)
      tableitem = getmatchtable(match)
      #json_object = json.dumps(item, indent = 2)
      #matchlist.append(json_object)
      matchlist.append(matchitem)
      tablelist.append(tableitem)
      #print(json_object)
      #print()

    filename = matchlist[0]["leaguename"]
    tmp = matchlist[0]["season"]
    tmp = tmp.replace('Saison', '')
    tmp = tmp.strip()
    filename += "_" +tmp +"_" +str(min_value) +"-" +str(max_value)
    print("filename:",filename)
    filename = sanitize_filename(filename)
    print("sanitized filename:",filename)

    with open("downloads/" +filename +"-matchlist.json", "w", encoding="utf-8") as file:
      json.dump(matchlist, file, ensure_ascii=False, indent=2)
    with open("downloads/" +filename +"-tablelist.json", "w", encoding="utf-8") as file:
      json.dump(tablelist, file, ensure_ascii=False, indent=2)  

    fieldnamesmatchday = ['liga', 'saison', 'spieltag', 'datum', 'uhrzeit', 'ergebnis', 'heimteam', 'gastteam']
    fieldnamestable = ['liga', 'saison', 'spieltag', 'tabellenplatz', 'teamname', 'punkte', 'spiele', 'siege', 'unentschieden', 'niederlagen', 'tore', 'gegentore', 'tordifferenz', 'tabellenplatzaenderung', 'aufstieg-abstieg']

    rows = []
    for block in matchlist:
      liga = block['leaguename']
      saison = block['season']
      spieltag = block['matchday']
      for match in block['matches']:
        row = {
          'liga': liga,
          'saison': saison,
          'spieltag': spieltag,
          'datum': match['date'].strip(),
          'uhrzeit': match['time'],
          'ergebnis': match['score'],
          'heimteam': match['hometeamname'],
          'gastteam': match['awayteamname']
        }
        rows.append(row)

    with open("downloads/" +filename +"-matches.csv", 'w', newline='', encoding='utf-8') as csvfile:
      writer = csv.DictWriter(csvfile, fieldnames=fieldnamesmatchday)
      writer.writeheader()
      writer.writerows(rows)

    rows.clear()
    for block in tablelist:
      liga = block['leaguename']
      saison = block['season']
      spieltag = block['matchday']
      for tablerow in block['table']:
        row = {
          'liga': liga,
          'saison': saison,
          'spieltag': spieltag,
          'tabellenplatz': tablerow['rank'],           
          'teamname': tablerow['teamname'],
          'punkte': tablerow['points'],
          'spiele': int(tablerow['won']) +int(tablerow['draw']) +int(tablerow['lost']),
          'siege': tablerow['won'],
          'unentschieden': tablerow['draw'],
          'niederlagen': tablerow['lost'],
          'tore': tablerow['goals_scored'],
          'gegentore': tablerow['goals_conceded'],
          'tordifferenz': int(tablerow['goals_scored']) -int(tablerow['goals_conceded']),
          'tabellenplatzaenderung': tablerow['rank_change'],
          'aufstieg-abstieg': tablerow['promotion_relegation']
        }
        rows.append(row)

    with open("downloads/" +filename +"-tables.csv", 'w', newline='', encoding='utf-8') as csvfile:
      writer = csv.DictWriter(csvfile, fieldnames=fieldnamestable)
      writer.writeheader()
      writer.writerows(rows)

    return redirect(url_for('index'))

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=5000, debug=True)












"""
#url = "https://www.fussball.de/spieltagsuebersicht/3liga-deutschland-3-liga-herren-saison2425-deutschland/-/staffel/02Q2QFKHQO000007VS5489B3VVLDQQH4-G#!/"
#url = "https://www.fussball.de/spieltag/3liga-deutschland-3-liga-herren-saison2425-deutschland/-/spieltag/8/staffel/02Q2QFKHQO000007VS5489B3VVLDQQH4-G"
url = "https://www.fussball.de/spieltagsuebersicht/nofv-oberliga-sued-deutschland-oberliga-herren-saison2324-deutschland/-/staffel/02M4M5VPIG00000DVS5489B4VUAB0UC4-G#!/"
#object = getmatchday(url)
#json_object = json.dumps(object, indent = 2)
#print(json_object)
#getmatchrange(url)
#getlinks(url)
#getlinks(url, max=8, min=4)

firstitem, lastitem = getmatchrange(url)
#print("firstitem:",firstitem)
#print("lastitem:",lastitem)
#print()
matches = getlinks(url, 1, 2)
matchlist = []
tablelist = []
for match in matches:
  #print("url:",url)
  matchitem = getmatchday(match)
  tableitem = getmatchtable(match)
  #json_object = json.dumps(item, indent = 2)
  #matchlist.append(json_object)
  matchlist.append(matchitem)
  tablelist.append(tableitem)
  #print(json_object)
  #print()

with open("matchlist.json", "w", encoding="utf-8") as file:
  json.dump(matchlist, file, ensure_ascii=False, indent=2)
with open("tablelist.json", "w", encoding="utf-8") as file:
  json.dump(tablelist, file, ensure_ascii=False, indent=2)  

fieldnamesmatchday = ['liga', 'saison', 'spieltag', 'datum', 'uhrzeit', 'ergebnis', 'heimteam', 'gastteam']
fieldnamestable = ['liga', 'saison', 'spieltag', 'tabellenplatz', 'teamname', 'punkte', 'spiele', 'siege', 'unentschieden', 'niederlagen', 'tore', 'gegentore', 'tordifferenz', 'tabellenplatzaenderung', 'aufstieg-abstieg']

rows = []
for block in matchlist:
  liga = block['leaguename']
  saison = block['season']
  spieltag = block['matchday']
  for match in block['matches']:
    row = {
      'liga': liga,
      'saison': saison,
      'spieltag': spieltag,
      'datum': match['date'].strip(),
      'uhrzeit': match['time'],
      'ergebnis': match['score'],
      'heimteam': match['hometeamname'],
      'gastteam': match['awayteamname']
    }
    rows.append(row)

with open('matches.csv', 'w', newline='', encoding='utf-8') as csvfile:
  writer = csv.DictWriter(csvfile, fieldnames=fieldnamesmatchday)
  writer.writeheader()
  writer.writerows(rows)

rows.clear()
for block in tablelist:
  liga = block['leaguename']
  saison = block['season']
  spieltag = block['matchday']
  for tablerow in block['table']:
    row = {
      'liga': liga,
      'saison': saison,
      'spieltag': spieltag,
      'tabellenplatz': tablerow['rank'],           
      'teamname': tablerow['teamname'],
      'punkte': tablerow['points'],
      'spiele': int(tablerow['won']) +int(tablerow['draw']) +int(tablerow['lost']),
      'siege': tablerow['won'],
      'unentschieden': tablerow['draw'],
      'niederlagen': tablerow['lost'],
      'tore': tablerow['goals_scored'],
      'gegentore': tablerow['goals_conceded'],
      'tordifferenz': int(tablerow['goals_scored']) -int(tablerow['goals_conceded']),
      'tabellenplatzaenderung': tablerow['rank_change'],
      'aufstieg-abstieg': tablerow['promotion_relegation']
    }
    rows.append(row)

with open('tables.csv', 'w', newline='', encoding='utf-8') as csvfile:
  writer = csv.DictWriter(csvfile, fieldnames=fieldnamestable)
  writer.writeheader()
  writer.writerows(rows)
"""