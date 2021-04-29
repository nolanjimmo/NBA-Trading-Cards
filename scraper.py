import csv
import requests
from bs4 import BeautifulSoup

URL = "https://www.basketball-reference.com/leagues/NBA_2020_totals.html"
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')
results = soup.find(id='totals_stats')

players = results.find_all('tr', class_='full_table')

f = open("players_pic.csv", "w")

for p in players:
    link = p.find('a')['href']
    name = p.find('a')
    name = str(name)
    name = name[36:][:-4]
    link = link[:-4] + "jpg"
    prelink = link[0:9]
    postlink = link[11:]
    link = prelink + postlink
    # print(name)
    with open('NBAdata.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in csvreader:
            if (name == row[0]):
                print(row[0])
                f.write("https://www.basketball-reference.com/req/202104203/images" + link + "," + name +  "\n")



f.close()
