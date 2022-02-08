import requests
from bs4 import BeautifulSoup
import pandas as pd

def gettickers():
    req = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = BeautifulSoup(req.text, "lxml")
    table = soup.find_all("tbody")
    rows = []
    for row in table:
        tr = row.find_all("tr")
        td = [td.text for td in tr]
        rows.append(td)
    tickers = [rows[0][i].split() for i in range(len(rows[0]))]
    tickers = pd.DataFrame(tickers)
    tickers.drop([15, 16, 17, 18, 19], 1, inplace=True)
    tickers.columns = tickers.iloc[0]
    tickers.drop([0], 0, inplace=True)
    return tickers