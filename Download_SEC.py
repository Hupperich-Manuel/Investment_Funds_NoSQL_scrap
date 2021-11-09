import requests
import pandas as pd
from bs4 import BeautifulSoup
from openpyxl import Workbook, workbook
import regex as re
import lxml.html as lh
import os
import xlsxwriter

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'}

def web():
    '''Copy the link below'''
    cik = input("Write the CIK of the fund of your desire: ")
    return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=13F&dateb=&owner=exclude&count=40"

url = web()
page = requests.get(url, headers=headers)
soup = BeautifulSoup(page.text, 'lxml')
found = soup.find_all('span', {'class':"companyName"})
texts = [i.text for i in found][0]
fund = re.search(r'(.*?)#', texts).group(1).replace(" ", "_").upper().replace("_CIK", "").replace(",", "").replace("/", "_").replace(".", "")
found = soup.find_all('td',{"nowrap":"nowrap"})
tr = [[str(tr)] for tr in found]
url = f"https://www.sec.gov/{tr[1][0][29:107]}"

page = requests.get(url, headers=headers)
soup = BeautifulSoup(page.text, 'lxml')
found = soup.find_all('td',{"scope":"row"})
tr = [[str(tr)] for tr in found]
l = []
for i in tr:
    if len(i[0])>100:
        l.append(i[0])
        
m=[]
for i in l:
    m.append(re.findall(r'"(.*?)"', i)[1])
    
link = f"https://www.sec.gov/{m[2]}"

url= link
#Create a handle, page, to handle the contents of the website
page = requests.get(url, headers=headers)
#Store the contents of the website under doc
doc = lh.fromstring(page.content)
#Parse data that are stored between <tr>..</tr> of HTML

tr_elements = doc.xpath('//tr')
#Create empty list
col=[]
i=0
#For each row, store each first element (header) and an empty list
for t in tr_elements[10]:
    i+=1
    name=t.text_content()
    print('%d:"%s"'%(i,name))
    col.append((name,[]))
#Since out first row is the header, data is stored on the second row onwards
for j in range(11,len(tr_elements)):
    #T is our j'th row
    T=tr_elements[j]
    
    #If row is not of size 10, the //tr data is not from our table 
    if len(T)!=12:
        break
    
    #i is the index of our column
    i=0
    
    #Iterate through each element of the row
    for t in T.iterchildren():
        data=t.text_content() 
        #Check if row is empty
        if i>0:
        #Convert any numerical value to integers
            try:
                data=int(data)
            except:
                pass
        #Append the data to the empty list of the i'th column
        col[i][1].append(data)
        #Increment i for the next column
        i+=1
[len(C) for (title,C) in col]
Dict1={title:column for (title,column) in col}
df1=pd.DataFrame(Dict1)
path = f'/Users/Usuario/Desktop/Eden_Fund/Python for Investing/Stock_Data/Current_Fund_Data/{fund}.xlsx'
date = '08-2021'
def download(path, df1):

    try:
        with pd.ExcelWriter(path ,engine='openpyxl', mode='w') as writer:
            df1.to_excel(writer, sheet_name=date)

    except FileNotFoundError:

        xlsxwriter.Workbook(path)

    pass
download(path, df1)

path = f'/Users/Usuario/Desktop/Eden_Fund/Python for Investing/Stock_Data/Current_Fund_Data/{fund}.xlsx'
def file(path, date):
    file = path
    xl=pd.ExcelFile(file)
    data=xl.parse(date)
    return data
data=file(path, date)

def test():
    dato=data.copy(deep=True)
    cols = dato.columns
    if 'Unnamed: 0' in cols:
        dato=dato.rename(columns={'NAME OF ISSUER':'Empresa', 'TITLE OF CLASS':'Tipo de Activo', 
                                  'CUSIP':'Cusip', '(x$1000)':'Valor Empresa', 'PRN AMT':'NºAcciones'})
        dato=dato.drop(['PRN', 'CALL', 'DISCRETION', 'MANAGER', 'SOLE', 'SHARED', 'NONE', 'Unnamed: 0'], axis=1)
    else:
        dato=dato.rename(columns={'NAME OF ISSUER':'Empresa', 'TITLE OF CLASS':'Tipo de Activo', 
                                  'CUSIP':'Cusip', '(x$1000)':'Valor Empresa', 'PRN AMT':'NºAcciones'})
        dato=dato.drop(['PRN', 'CALL', 'DISCRETION', 'MANAGER', 'SOLE', 'SHARED', 'NONE'], axis=1)
    dato['Valor Empresa'] = dato['Valor Empresa'].astype(str)
    dato['NºAcciones'] = dato['NºAcciones'].astype(str)
    dato['Valor Empresa']=dato['Valor Empresa'].str.replace(',', '').astype(int)
    dato['NºAcciones'] = dato['NºAcciones'].str.replace(',', '').astype(int)
    dato=pd.DataFrame(dato)
    return dato
dato=test()
def org():
    datos=dato.duplicated(dato.columns[~dato.columns.isin(['Tipo de Activo'])])
    dato['Valor Empresa'] = dato['Valor Empresa'].astype(int)
    dato['NºAcciones'] = dato['NºAcciones'].astype(int)
    datos=dato.groupby(['Empresa','Cusip','Tipo de Activo']).sum()
    datos['Precio del Activo']=(datos['Valor Empresa']*1000)/datos['NºAcciones']
    datos['% Valor']=datos['Valor Empresa']/(datos['Valor Empresa'].sum())
    return datos
df=org()
path = f'/Users/Usuario/Desktop/Eden_Fund/Python for Investing/Stock_Data/Old_Fund_Data/{fund}/{fund}.xlsx'

def download(df, path):
    try:
        with pd.ExcelWriter(path ,engine='openpyxl', mode='a') as writer:
            df.to_excel(writer, sheet_name=date)
    except FileNotFoundError:
        os.mkdir(f'/Users/Usuario/Desktop/Eden_Fund/Python for Investing/Stock_Data/Old_Fund_Data/{fund}')
    
download(df, path)

if not os.listdir(f'/Users/Usuario/Desktop/Eden_Fund/Python for Investing/Stock_Data/Old_Fund_Data/{fund}') :
    try:
        with pd.ExcelWriter(path ,engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, sheet_name=date)
    except FileNotFoundError:
        print("No FIle")
else:    
    print("Directory is not empty")

print("Done ;)")

print(f"The organized data is stored in the ./Stored_Data/Old_Current_Fund {path}")
 