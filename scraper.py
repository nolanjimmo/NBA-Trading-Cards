import requests
from bs4 import BeautifulSoup

URL = "https://www.basketball-reference.com/leagues/NBA_2020_totals.html"
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')
results = soup.find(id='totals_stats')

players = results.find_all('tr', class_='full_table')

f = open("players_pic.txt", "w")


for p in players:
    link = p.find('a')['href']
    link = link[:-4] + "jpg"
    prelink = link[0:9]
    postlink = link[11:]
    link = prelink + postlink
    print(link)

    f.write("https://www.basketball-reference.com/req/202104203/images" + link + "\n")

f.close()
