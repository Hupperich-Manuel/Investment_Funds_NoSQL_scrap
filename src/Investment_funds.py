import requests
import pandas as pd
from bs4 import BeautifulSoup
from openpyxl import Workbook, workbook
import regex as re
import lxml.html as lh
import os
import xlsxwriter
from datetime import datetime
import json
import matplotlib.pyplot as plt
import numpy as np

class SEC_Funds(object):
    def __init__(self):

        while True:
            print(f"From which fund do you want the data?")
            cik = [input("Write the cik of the fund of your desire: ").strip().replace("/", "-")][0]
            if not cik:
                print("No cik found")
                pass
            else:
                print("Cik found")
                break
        
        self.headers = {'User-Agent': 'header'}
        self.cik = cik

    def get_dates(self, soup):
        table = soup.find_all("table", {"class": "tableFile2"})
        for td in table:
            tr = td.find_all("td")
            tr_desc = td.find_all("td", {"class":"small"})
            description = {index:str(td.text) for index, td in enumerate(tr_desc)}
            dropping_index = [index for index in description.keys() if "[Amend]" in description[index]]
            text = [str(td) for td in tr]
            links = [re.findall(r">(.*?)<", i) for i in text]
            dates = [i[0] for index, i in enumerate(links) if len(i[0])==10]
            dates = [date for i, date in enumerate(dates) if i not in dropping_index]
        return dates, dropping_index

    def getmainurl(self):

        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.cik}&type=13F&dateb=&owner=exclude&count=40"
        page = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(page.text, 'lxml')

        found = soup.find_all('span', {'class':"companyName"})
        texts = [i.text for i in found][0]
        fund = re.search(r'(.*?)#', texts).group(1).replace(" ", "_").upper().replace("_CIK", "").replace(",", "").replace("/", "_").replace(".", "")
        found = soup.find_all('td',{"nowrap":"nowrap"})
        tr = [[str(tr)] for tr in found]
        url = [f"https://www.sec.gov/{tr[i][0][29:107]}" for i in range(1, len(tr), 3) if len(tr[i][0])>100]
        return url, fund, soup

    def getfundurl(self):
        urls, _, soup = self.getmainurl()

        while True:
            dates, drop_dates = self.get_dates(soup)
            url = [i for index, i in enumerate(urls) if index not in drop_dates]
            print(f"From which quarter do you want the data?:{dates}")
            print()
            years = input("Write the date of your desire: ").replace("'", "").replace(",", "").strip().split()

            links = {}
            for year in years:

                try:
                    datetime.strptime(year, "%Y-%m-%d")
                    requested_url = {date: ur for date, ur in zip(dates, url)}
                    links[year] = [requested_url[date] for date in requested_url.keys() if date==year][0]
                    if not url:
                        print("Date not found")
                        pass
                    else:
                        pass
                except ValueError:
                    print("The date format is not valid")
                    links = self.getfundurl()
                    pass
            print(f"Processed {len(links)}: {links.keys()} out of {len(years)}")
            break     
        return links

    def second_fund_page(self):

        url = self.getfundurl()

        soup = {}
        for year in url.keys():
            page = requests.get(url[year], headers=self.headers)
            soup[year] = BeautifulSoup(page.text, 'lxml')

        links = {}
        for year in soup.keys():
            found = soup[year].find_all('td',{"scope":"row"})
            tr = [[str(tr)] for tr in found]
            l = []
            for i in tr:
                if len(i[0])>100:
                    l.append(i[0])

            m=[]
            for i in l:
                m.append(re.findall(r'"(.*?)"', i)[1])

            link = f"https://www.sec.gov/{m[2]}"

            links[year] = link

        return links

    def extract_fund_data(self):

        url= self.second_fund_page()

        doc = {}
        for year in url.keys():
            page = requests.get(url[year], headers=self.headers)
            doc[year] = lh.fromstring(page.content)


        data_funds = {}
        for year in doc.keys():
            tr_elements = doc[year].xpath('//tr')
            col=[]
            i=0
            for t in tr_elements[10]:
                i+=1
                name=t.text_content()
                col.append((name,[]))
            for j in range(11,len(tr_elements)):
                T=tr_elements[j]
                if len(T)!=12:
                    break
                i=0

                for t in T.iterchildren():
                    data=t.text_content() 
                    if i>0:
                        try:
                            data=int(data)
                        except:
                            pass
                    col[i][1].append(data)
                    i+=1
            Dict1={title:column for (title,column) in col}
            data_funds[year] = pd.DataFrame(Dict1)

        print(data_funds.keys())

        return data_funds


    def rearrange_data(self):
        dato = self.extract_fund_data().copy()

        data_funds = {}
        for year in dato.keys():
            cols = dato[year].columns
            datos = dato[year]
            if 'Unnamed: 0' in cols:
                datos=datos.rename(columns={'NAME OF ISSUER':'Empresa', 'TITLE OF CLASS':'Tipo de Activo', 
                                            'CUSIP':'Cusip', '(x$1000)':'Valor Empresa', 'PRN AMT':'NºAcciones'})
                datos=datos.drop(['PRN', 'CALL', 'DISCRETION', 'MANAGER', 'SOLE', 'SHARED', 'NONE', 'Unnamed: 0'], axis=1)
            else:
                datos=datos.rename(columns={'NAME OF ISSUER':'Empresa', 'TITLE OF CLASS':'Tipo de Activo', 
                                            'CUSIP':'Cusip', '(x$1000)':'Valor Empresa', 'PRN AMT':'NºAcciones'})
                datos=datos.drop(['PRN', 'CALL', 'DISCRETION', 'MANAGER', 'SOLE', 'SHARED', 'NONE'], axis=1)
            datos['Valor Empresa'] = datos['Valor Empresa'].astype(str)
            datos['NºAcciones'] = datos['NºAcciones'].astype(str)
            datos['Valor Empresa']=datos['Valor Empresa'].str.replace(',', '').astype(int)
            datos['NºAcciones'] = datos['NºAcciones'].str.replace(',', '').astype(int)
            datos=pd.DataFrame(datos)

            data_funds[year] = datos

        return data_funds

    def normalize_data(self):
        _, fund, _ = self.getmainurl()
        dato = self.rearrange_data().copy()
        print(dato.keys())

        df_funds = {}
        for year in dato.keys():
            data = dato[year]
            datos=data.duplicated(data.columns[~data.columns.isin(['Tipo de Activo'])])
            data['Valor Empresa'] = data['Valor Empresa'].astype(int)
            data['NºAcciones'] = data['NºAcciones'].astype(int)
            datos=data.groupby(['Empresa','Cusip','Tipo de Activo']).sum()
            datos['Precio del Activo']=round((datos['Valor Empresa']*1000)/datos['NºAcciones'], 2)
            datos['% Valor']=datos['Valor Empresa']/(datos['Valor Empresa'].sum())
            df_funds[year] = datos.sort_values("% Valor", ascending=False)
            print("Done")

        data_fund = pd.concat(df_funds, keys=df_funds.keys(), axis=1)
        with pd.ExcelWriter("SEC.xlsx" ,engine='openpyxl', mode='w') as writer:
            data_fund.to_excel(writer)
        while True:
            plot = input("Do you want to see the evolution in terms of participation of any particular stock?:").lower().strip()
            if plot =="yes":
                print(f"Which company?: {data_fund.index.get_level_values(0)}")
                company = input("Write your company here:").upper().strip()
                plt.figure(figsize=(16, 10))
                plt.bar(data_fund.columns.get_level_values(0).unique().tolist(), data_fund.loc[company, data_fund.columns.get_level_values(1)=='% Valor'].values.tolist()[0], color="grey", alpha=0.4)
                #plt.plot(data_fund.columns.get_level_values(0).unique().tolist(), data_fund.loc[company, data_fund.columns.get_level_values(1)=='Valor Empresa'].values.tolist()[0], color="red")
                plt.xticks(rotation=45)
                plt.show()
                continue    
            else:
                break
        return data_fund, fund
#0001067983
# 2022-02-14', '2021-11-15', '2021-08-16', '2021-05-17', '2021-02-16', '2021-02-16

df, _ = SEC_Funds().normalize_data()
print(df)