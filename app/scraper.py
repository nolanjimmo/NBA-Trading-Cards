import csv
import requests
from bs4 import BeautifulSoup

URL = "https://www.basketball-reference.com/leagues/NBA_2020_totals.html"
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')
results = soup.find(id='totals_stats')

players = results.find_all('tr', class_='full_table')

names = []
for p in players:
    link = p.find('a')['href']
    link = link[:-4] + "jpg"
    name = str(p.find('a'))
    startIndex = name.index(">")
    name = name[startIndex + 1:][:-4]
    link = link[0:9] + link[11:]
    name = name.replace('ā', 'a')
    name = name.replace('á', 'a')
    name = name.replace('ć', 'c')
    name = name.replace('č', 'c')
    name = name.replace('Č', 'C')
    name = name.replace('İ', 'I')
    name = name.replace('í', 'i')
    name = name.replace('ž', 'z')
    name = name.replace('ņ', 'n')
    name = name.replace('ģ', 'g')
    name = name.replace('ū', 'u')
    name = name.replace('Ž', 'Z')
    name = name.replace('ó', 'o')
    name = name.replace('ò', 'o')
    name = name.replace('ö', 'o')
    name = name.replace('è', 'e')
    name = name.replace('é', 'e')
    name = name.replace('š', 's')
    name = name.replace('Š', 'S')
    name = name.replace('ý', 'y')

    # print(name)
    # f.write(name + "," + "https://www.basketball-reference.com/req/202104203/images" + link + "\n")

    with open('NBAdata.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in csvreader:
            if name == row[0]:
                names.append(name + ",https://www.basketball-reference.com/req/202104203/images" + link)
                # names.append("https://www.basketball-reference.com/req/202104203/images" + link)
                # print(row[0])
                # f.write(name + "," + "https://www.basketball-reference.com/req/202104203/images" + link + "\n")

f = open("players_pic.csv", "w")
names = sorted(names)
for name in names:
    f.write(name + "\n")
f.close()
