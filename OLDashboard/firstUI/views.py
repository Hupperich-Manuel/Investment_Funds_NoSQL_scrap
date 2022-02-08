from multiprocessing import Value
from django.shortcuts import render
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from firstUI import Download_SEC, Tickers


def initialpage(request):
    a = "Manuel"
    context = {"name":a}
    return render(request, "home.html", context)



# Create your views here.
def indexPage(request):


    print("Manuel")
    cik = "0001061768"

    #company = pd.read_excel('/Users/Usuario/Desktop/Latest_Codes/GitHub/Investment/SCION_ASSET_MANAGEMENT_LLC_NEW.xlsx')
    company, fund = Download_SEC.getfundData(cik)
    company.reset_index(inplace=True)
    company.fillna("Other", inplace=True)
    totalCount = company["Valor Empresa"].sum()
    company = company.sort_values("Valor Empresa", ascending=False)
    names = company["Empresa"].values.tolist()
    values = company["Valor Empresa"].values.tolist()

    context = {'totalCount':totalCount, 'names':names, 'values':values, "fund":fund}

    return render(request, 'index.html', context)

def selectComp(request):

    cik = request.POST.get("nadine")
    print("Ia am manuel")
    company, fund = Download_SEC.getfundData(cik)
    company.fillna("Other", inplace=True)
    company.reset_index(inplace=True)
    totalCount = company["Valor Empresa"].sum()
    company = company.sort_values("Valor Empresa", ascending=False)
    names = company["Empresa"].values.tolist()
    values = company["Valor Empresa"].values.tolist()

    context = {'totalCount':totalCount, 'names':names, 'values':values, "fund":fund}
    return render(request, 'index.html', context)

def stock(request):
    company_name = request.POST.get('selectComp', "TSLA")
    print(f"companyis {company_name}")
    tickers = Tickers.gettickers()
    print(tickers)
    security = list(tickers["Security"].values)
    security = [i for i in security if company_name in i.lower()]

    try:
        ticker = tickers.loc[tickers["Security"]==security]["Symbol"].values.tolist()   
        stock_prices = yf.download(ticker, start="2020-11-30")["Close"]
    except ValueError:
        stock_prices = yf.download("AAPL", start="2020-11-30")["Close"]

    # income_st = pd.read_excel("/Users/usuario/Desktop/Latest_Codes/GitHub/Statements/Cleaned_Reports/Apple_Inc/Merged_ISApple_Inc.xlsx", index_col=0).iloc[:-6].T
    # income_st.reset_index(inplace=True)
    # income_st.rename(columns={"index":"Date"}, inplace=True)
    # income_st.dropna(1, inplace=True)
    # income_st = [dict(income_st.iloc[i]) for i in range(income_st.shape[0])]


    
    time = stock_prices.index.tolist()[1:]
    time = [datetime.strftime(i, '%d-%m-%Y') for i in time]
    stock_prices = stock_prices.fillna(method="pad")
    stock_prices = list((1+np.log(stock_prices/stock_prices.shift(1))).cumprod().dropna())

    context = {'company_name':company_name, 'stock_prices':stock_prices, 'time':time}
    return render(request, 'index.html', context)
