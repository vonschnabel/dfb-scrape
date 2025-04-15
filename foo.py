import json
import csv

# Beispiel-JSON-Daten (als Liste von Dictionaries)
data = [
    {"name": "John", "age": 30, "city": "New York"},
    {"name": "Jane", "age": 25, "city": "San Francisco"}
]

data_json = {
  "matchday": "2",
  "matches": [
    {
      "date": "Fr, 04.08.23 ",
      "time": "18:30",
      "score": "2:3",
      "hometeamname": "FC Grimma",
      "awayteamname": "SG Union Sandersdorf",
      "hometeamid": "012M9G9NN8000000VV0AG80NVVJ79KI7",
      "awayteamid": "011MICEN4O000000VTVG0001VTR8C1K7"
    },
    {
      "date": "Sa, 05.08.23 ",
      "time": "13:00",
      "score": "2:2",
      "hometeamname": "FSV Budissa Bautzen",
      "awayteamname": "FC Einheit Rudolstadt",
      "hometeamid": "011MIDBSBG000000VTVG0001VTR8C1K7",
      "awayteamid": "011MIDJ7G0000000VTVG0001VTR8C1K7"
    },
    {
      "date": "Sa, 05.08.23 ",
      "time": "14:00",
      "score": "3:0",
      "hometeamname": "VFC Plauen",
      "awayteamname": "VfL Halle 96",
      "hometeamid": "011MIEDBC8000000VTVG0001VTR8C1K7",
      "awayteamid": "011MIBTUSG000000VTVG0001VTR8C1K7"
    },
    {
      "date": "Sa, 05.08.23 ",
      "time": "14:00",
      "score": "3:3",
      "hometeamname": "VfB Germania Halberstadt",
      "awayteamname": "Bischofswerdaer FV 08",
      "hometeamid": "011MICMTEO000000VTVG0001VTR8C1K7",
      "awayteamid": "011MIBOAL8000000VTVG0001VTR8C1K7"
    },
    {
      "date": "Sa, 05.08.23 ",
      "time": "14:00",
      "score": "2:0",
      "hometeamname": "SC Freital",
      "awayteamname": "SV 09 Arnstadt",
      "hometeamid": "011MIDJ380000000VTVG0001VTR8C1K7",
      "awayteamid": "011MIE9L6C000000VTVG0001VTR8C1K7"
    },
    {
      "date": "Sa, 05.08.23 ",
      "time": "16:00",
      "score": "1:2",
      "hometeamname": "FC Einheit Wernigerode",
      "awayteamname": "VfB Auerbach",
      "hometeamid": "011MICMVNG000000VTVG0001VTR8C1K7",
      "awayteamid": "011MIAVH1O000000VTVG0001VTR8C1K7"
    },
    {
      "date": "So, 06.08.23 ",
      "time": "14:00",
      "score": "1:4",
      "hometeamname": "VfB 1921 Krieschow",
      "awayteamname": "1. FC Magdeburg II",
      "hometeamid": "011MIE1T80000000VTVG0001VTR8C1K7",
      "awayteamid": "011MID1P84000000VTVG0001VTR8C1K7"
    },
    {
      "date": "So, 06.08.23 ",
      "time": "14:00",
      "score": "3:0",
      "hometeamname": "Ludwigsfelder FC",
      "awayteamname": "FSV Motor Marienberg",
      "hometeamid": "011MIBTPOK000000VTVG0001VTR8C1K7",
      "awayteamid": "011MIBTSQS000000VTVG0001VTR8C1K7"
    }
  ]
}


fieldnames = ['spieltag', 'datum', 'uhrzeit', 'ergebnis', 'heimteam', 'gastteam']

with open('spiele.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for match in data_json['matches']:
        row = {
            'spieltag': data_json['matchday'],
            'datum': match['date'],
            'uhrzeit': match['time'],
            'ergebnis': match['score'],
            'heimteam': match['hometeamname'],
            'gastteam': match['awayteamname']
        }
        writer.writerow(row)
