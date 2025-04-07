from bs4 import BeautifulSoup
import requests
import os
import subprocess
import xml.etree.ElementTree as ET
import html  # HTML-Entities dekodieren

# URLs und Pfade
fontbaseurl = "https://www.fussball.de/export.fontface/-/format/woff/id/"
fontappendixurl = "/type/font"
fontsbasepath = "/home/ast/fussball.de/fonts/"
ttxcmdpath = "/home/ast/.local/bin/ttx"

# Webseite abrufen mit korrekter Encoding-Erkennung
#link_spieltag = 'https://www.fussball.de/spieltagsuebersicht/3liga-deutschland-3-liga-herren-saison2425-deutschland/-/staffel/02Q2QFKHQO000007VS5489B3VVLDQQH4-G#!/'
#link_spieltag = 'https://www.fussball.de/spieltag/2bundesliga-deutschland-2bundesliga-herren-saison2425-deutschland/-/spieltag/20/staffel/02Q0U33JRK000019VS5489B4VVE5FNTJ-G#!/'
#link_spieltag = 'https://www.fussball.de/spieltag/geomix-thueringenliga-thueringen-verbandsliga-herren-saison2324-thueringen/-/spieltag/20/staffel/02M8T1I29O000008VS5489B3VVRQ15EP-G#!/'
#link_spieltag =  = requests.get('https://www.fussball.de/spieltag/kreisliga-sti-kreis-erfurt-soemmerda-kreisliga-herren-saison2425-thueringen/-/spieltag/13/staffel/02PUMRP5FS000007VS5489B3VSK4BA2V-G'
link_spieltag = 'https://www.fussball.de/spieltag/kreisliga-sti-kreis-erfurt-soemmerda-kreisliga-herren-saison2425-thueringen/-/spieltag/13/staffel/02PUMRP5FS000007VS5489B3VSK4BA2V-G'

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

def getmatchday(link_spieltag):
  r = requests.get(link_spieltag)
  r.encoding = r.apparent_encoding  # Korrekte Zeichensatz-Erkennung
  soup = BeautifulSoup(r.text, 'html.parser')

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

  matchday = []
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
        matchday.append(match_object)

    return matchday
  else:
    print("No fixtures found.")

import json
#matchday = getmatchday(link_spieltag)
#json_object = json.dumps(matchday, indent = 2)
#print(json_object)

def getmatchtable(link_spieltag):
  table = []
  r = requests.get(link_spieltag)
  r.encoding = r.apparent_encoding  # Korrekte Zeichensatz-Erkennung
  soup = BeautifulSoup(r.text, 'html.parser')

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
    table.append(table_entry)
  return table