from django.shortcuts import render, redirect
from .models import Stock, Portfolio
from .forms import StockForm, PortfolioForm
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth import update_session_auth_hash
from pandas.io.json import json_normalize
from datetime import datetime, timedelta, timezone


import requests
import json
import os
import pandas as pd
import pyEX
import csv
import alpha_vantage.techindicators as ti
import calendar
import random

# Create your views here.


def str_date(date):
    if date.month < 10:
        month = '0' + str(date.month)
    else:
        month = str(date.month)
    if date.day < 10:
        day = '0' + str(date.day)
    else:
        day = str(date.day)
    return str(date.year) + '-' + month + '-' + day


def str_value(value):
    if value > 0:
        return '+' + str(value)
    else:
        return str(value)


def home(request):
    # news apis: 96bea4fd5cef4c9abb161006b3e3887f, 3493322e6d854f4397ed215c2e595591, 8a278e1211284e7fa2caf1e195718500
    # news apis: 71e8dec2dcdb4c16b61ef435bf86fd6f
    news_url = (
        'https://newsapi.org/v2/everything?q=stock&sortBy=publishedAt&language=en&pageSize=3&apiKey=96bea4fd5cef4c9abb161006b3e3887f')
    news_api_request = requests.get(news_url)
    news = json.loads(news_api_request.content)
    apis = {}

    stock_url = ("")
    for i in range(3, 6):
        apis['news_' + str(i - 3)] = news['articles'][i - 3]

    news_keywords = ["\"IT\"AND\"stock\"", "\"invest\"AND\"stock\"", "stock_market",
                     "\"finance\"AND\"stock\"", "\"business\"AND\"stock\"", "\"politics\"AND\"stock\"", "\"economy\"AND\"stock\""]
    random.seed(5)
    choices = random.sample(news_keywords, 3)
    for i in range(3, 6):
        news_url = (
            'https://newsapi.org/v2/everything?q=' + choices[i - 3] + '&from=2019-11-04&pageSize=1&language=en&apiKey=96bea4fd5cef4c9abb161006b3e3887f')
        news_api_request = requests.get(news_url)
        news = json.loads(news_api_request.content)
        apis['news_' + str(i)] = news['articles'][0]

    stock_list = {'AAPL': 'Apple Inc', 'GOOGL': 'Alphabet Cl A', 'TIF': 'Tiffany & Co.', 'STCN': 'Steel Connect Inc',
                  'BAC': 'Bank of America Corporation', 'PCG': 'PG&E Corporation'}  # ,'NOK':'Nokia Corporation','CWEN':'Clearway Energy, Inc.'}

    apis['week_rate'] = float('-inf')
    apis['month_rate'] = float('-inf')
    apis['year_rate'] = float('-inf')

    c = pyEX.Client('pk_6d5a654f915b4b2e9fbd3f9f380dc52b')
    stocks = {}

    path = os.getcwd()
    time_series = pd.read_csv(path + '/timeSeries.csv')
    time_series = time_series.set_index('stock')
    for s in stock_list:
        # time_series[s] = c.advancedStats(s)
        stocks[s] = c.book(s)
        s_last_week_rate = time_series.loc[s]['day5ChangePercent']
        s_last_month_rate = time_series.loc[s]['month1ChangePercent']
        s_last_year_rate = time_series.loc[s]['year1ChangePercent']
        if s_last_week_rate > apis['week_rate']:
            apis['week_rate'] = s_last_week_rate
            apis['week_stock'] = s

        if s_last_month_rate > apis['month_rate']:
            apis['month_rate'] = s_last_month_rate
            apis['month_stock'] = s

        if s_last_year_rate > apis['year_rate']:
            apis['year_rate'] = s_last_year_rate
            apis['year_stock'] = s

    apis['week_stock_company'] = stock_list[apis['week_stock']]
    apis['week_price'] = stocks[apis['week_stock']]['quote']['latestPrice']

    apis['month_stock_company'] = stock_list[apis['month_stock']]
    apis['month_price'] = stocks[apis['month_stock']]['quote']['latestPrice']

    apis['year_stock_company'] = stock_list[apis['year_stock']]
    apis['year_price'] = stocks[apis['year_stock']]['quote']['latestPrice']

    apis['last_week_price'] = str_value(
        round(apis['week_price'] / (1 + apis['week_rate']) * apis['week_rate'], 2))
    apis['last_month_price'] = str_value(
        round(apis['month_price'] / (1 + apis['month_rate']) * apis['month_rate'], 2))
    apis['last_year_price'] = str_value(
        round(apis['year_price'] / (1 + apis['year_rate']) * apis['year_rate'], 2))
    apis['week_rate'] = str_value(round(apis['week_rate'] * 100, 2))
    apis['month_rate'] = str_value(round(apis['month_rate'] * 100, 2))
    apis['year_rate'] = str_value(round(apis['year_rate'] * 100, 2))
    all_stocks = pd.read_csv(
        "../capstone-project-ghost-in-the-code/stock_symbols/iex_symbols.csv")
    apis['all_stocks'] = all_stocks.set_index(
        'symbol').T.to_dict()  # .to_json(orient='records')
    # apis['all_stocks'] = all_stocks.to_json(orient='records')
    return render(request, 'home.html', apis)


def search(request):
    q = request.POST['search']
    print(q)
    print('xadasfasf')
    if q:
        symbol = q.split()[-1]
        print(symbol)

        request.session["symbol"] = symbol
        c = pyEX.Client('pk_6d5a654f915b4b2e9fbd3f9f380dc52b')
        data = c.chartDF(symbol, '3m')
        with open('../capstone-project-ghost-in-the-code/static/js/test1.js', 'w') as f:
            f.write("var dataSeries = [[")
        for index, rows in data.iterrows():
            temp_dict = {}
            temp_dict["date"] = index.strftime('%Y-%m-%d')
            temp_dict["value"] = float(rows.close)
            jsobj = json.dumps(temp_dict)
            print(jsobj)
            with open('../capstone-project-ghost-in-the-code/static/js/test1.js', 'a') as f:
                f.write(jsobj)
                f.write(',')
        with open('../capstone-project-ghost-in-the-code/static/js/test1.js', 'a') as f:
            f.write("]]")
        return redirect(charts_display)
    else:
        return render(request, 'test.html')


def search_news(request):
    q = request.POST['search_news']
    print(q)
    print('xadasfasf')
    if q:
        return redirect('https://www.google.com/search?q=' + q)
    else:
        return redirect('https://www.google.com')


def news(request):
    apis = {}
    # news apis: 96bea4fd5cef4c9abb161006b3e3887f,3493322e6d854f4397ed215c2e595591,8a278e1211284e7fa2caf1e195718500
    # news apis: 71e8dec2dcdb4c16b61ef435bf86fd6f
    news_url = (
        'https://newsapi.org/v2/everything?q=stock&sortBy=publishedAt&language=en&pageSize=3&apiKey=71e8dec2dcdb4c16b61ef435bf86fd6f')
    news_api_request = requests.get(news_url)
    trend = json.loads(news_api_request.content)
    for i in range(3):
        apis['trend_' + str(i)] = (trend['articles'][i]
                                   ['title'], trend['articles'][i]['url'])

    keywords = {"business": ['trade', 'markets', "small business", 'economy'],
                "finance": ["banking", "wall street", "money", "ipo"], "world": ['global', 'USA', "\"europe\"OR\"european\"", "\"asia\"OR\"asian\""], "industry": ["energy", "technology", "manufacture", "real estate"]}
    # ["banking","wallstreet","money","ipo"],\
    # 'global','USA',"\"europe\"OR\"european\"","\"asia\"OR\"asian\""
    # ["energy","technology","manufacture","real_estate"]}
    topics = {}

    for i in keywords:
        if i != 'world':
            news_url = ('https://newsapi.org/v2/everything?q=' + i +
                        '&from=2019-11-01&language=en&pageSize=4&apiKey=71e8dec2dcdb4c16b61ef435bf86fd6f')
            num = 4
        else:
            news_url = (
                'https://newsapi.org/v2/everything?q="australian"AND"stocks"&language=en&pageSize=4&apiKey=71e8dec2dcdb4c16b61ef435bf86fd6f')
            i = 'australia'
            num = 4

        news_api_request = requests.get(news_url)
        topics[i] = json.loads(news_api_request.content)
        apis[i] = {'name': i, 'data': []}
        for j in range(num):
            date = datetime.strptime(
                topics[i]['articles'][j]['publishedAt'][5:10], "%m-%d")
            name = topics[i]['articles'][j]['author']
            if not name:
                name = topics[i]['articles'][j]['source']['name']
            apis[i]['data'].append((topics[i]['articles'][j]['title'], topics[i]['articles'][j]['url'],
                                    topics[i]['articles'][j]['urlToImage'], name,
                                    date.strftime('%b %d')))

    news_url = (
        'https://newsapi.org/v2/everything?q=stock&language=en&pageSize=5&apiKey=71e8dec2dcdb4c16b61ef435bf86fd6f')
    news_api_request = requests.get(news_url)
    popular = json.loads(news_api_request.content)
    apis['popular'] = []
    for i in range(5):
        apis['popular'].append(
            (popular['articles'][i]['title'], popular['articles'][i]['url']))

    for i in keywords:
        for j in keywords[i]:
            news_url = ('https://newsapi.org/v2/everything?q="' + j +
                        '"AND"stocks"&pageSize=4&apiKey=71e8dec2dcdb4c16b61ef435bf86fd6f')
            print('https://newsapi.org/v2/everything?q="' + j +
                  '"AND"stocks"&pageSize=4&apiKey=71e8dec2dcdb4c16b61ef435bf86fd6f')
            news_api_request = requests.get(news_url)
            temp = json.loads(news_api_request.content)
            j = j.replace(" ", "_")
            if i == 'world':
                if j == "\"europe\"OR\"european\"":
                    j = "europe"
                elif j == "\"asia\"OR\"asian\"":
                    j = "asian"
            apis[j] = []
            for k in range(4):

                date = datetime.strptime(
                    temp['articles'][k]['publishedAt'][5:10], "%m-%d")
                apis[j].append((temp['articles'][k]['title'], temp['articles'][k]['url'],
                                temp['articles'][k]['urlToImage'], date.strftime('%b %d')))

            print(j, apis[j][0])
    return render(request, 'news.html', apis)


def news_category(request, name):
    keywords = {"business": ['general', 'trade', 'markets', 'small business', 'economy'],
                "finance": ['general', "banking", "wallstreet", "money", "ipo"], "world": ['global', 'USA', "\"europe\"OR\"european\"", "\"asia\"OR\"asian\""], "industry": ['general', "energy", "technology", "manufacture", "real_estate"]}
    apis = {}

    for sub_kind in keywords[name]:
        if sub_kind == 'general':
            sub_kind = name

        news_url = ('https://newsapi.org/v2/everything?q=' + sub_kind +
                    '&language=en&&apiKey=71e8dec2dcdb4c16b61ef435bf86fd6f')
        news_api_request = requests.get(news_url)
        temp = json.loads(news_api_request.content)
        if name == 'world':
            if sub_kind == "\"europe\"OR\"european\"":
                sub_kind = "europe"
            elif sub_kind == "\"asia\"OR\"asian\"":
                sub_kind = "asian"
        apis[sub_kind] = []
        for k in range(20):
            date = datetime.strptime(
                temp['articles'][k]['publishedAt'][5:10], "%m-%d")
            source = temp['articles'][k]['source']['name'].split(".")[0]
            apis[j].append((temp['articles'][k]['title'], temp['articles'][k]['url'],
                            temp['articles'][k]['urlToImage'], date.strftime('%b %d'), source))

    return render(request, 'news_category.html', apis)


def base(request):
    return render(request, 'base.html', {})


def add_stock(request):

    if request.method == 'POST':
        form = StockForm(request.POST or None)

        if form.is_valid():
            form.save()
            messages.success(request, ("Stock Has Been Added!"))
            return redirect('add_stock')

    else:
        ticker = Stock.objects.all()  # pull off all the db about the ticker
        output = []  # save the stock we pull off (symbol)
        # companyName = []

        for ticker_item in ticker:
            api_request = requests.get("https://cloud.iexapis.com/stable/stock/" + str(
                ticker_item) + "/quote?token=pk_74cd4d03d660401ba132a6c69609a3cf")

            try:
                api = json.loads(api_request.content)  # decode json
                output.append(api)
                # companyName.append(api[companyName])

            except Exception as e:
                api = "Error..."

        all_stocks = pd.read_csv(
            "../capstone-project-ghost-in-the-code/stock_symbols/iex_symbols.csv")
        all_stocks = all_stocks.set_index(
            'symbol').T.to_dict()  # .to_json(orient='records')

        return render(request, 'add_stock.html', {'ticker': ticker, 'output': output, "all_stocks": all_stocks})


def delete(request, stock_id):
    item = Stock.objects.get(pk=stock_id)
    item.delete()
    messages.success(request, ('Stock Has Been Deleted!'))
    return redirect(add_stock)


def mydelete(request, stock_id):
    item = Stock.objects.get(pk=stock_id)
    item.delete()
    messages.success(request, ('Stock Has Been Deleted!'))
    return redirect(mystock)


def portfolio(request):
    print("222")
    if request.method == 'POST':
        data = request.POST
        # portfolio = request.POST.get('portfolio')
        form = StockForm(request.POST or None)

        if form.is_valid():
            form.save()
            messages.success(request, ("Stock Has Been Added!"))
            return redirect('portfolio')

    else:
        print("11")
        port = Portfolio.objects.all()
        myticker = Stock.objects.all()
        mystock = []

        for ticker_item in myticker:
            api_request = requests.get("https://cloud.iexapis.com/stable/stock/" + str(
                ticker_item) + "/quote?token=pk_74cd4d03d660401ba132a6c69609a3cf")

            try:
                api = json.loads(api_request.content)
                mystock.append(api)

            except Exception as e:
                api = "Error..."
        print(myticker)
        print(mystock)
        print(port)
        return render(request, 'portfolio.html', {'myticker': myticker, 'mystock': mystock, 'port': port})


def aapl(request):
    return render(request, 'aapl.html', {})


def goog(request):
    return render(request, 'goog.html', {})


def bac(request):
    return render(request, 'bac.html', {})


def mstf(request):
    return render(request, 'mstf.html', {})


def amzn(request):
    return render(request, 'amzn.html', {})


def tif(request):
    return render(request, 'tif.html', {})


def about(request):
    all_stocks = pd.read_csv(
        "../capstone-project-ghost-in-the-code/stock_symbols/iex_symbols.csv")
    all_stocks = all_stocks.set_index(
        'symbol').T.to_dict()  # .to_json(orient='records')
    return render(request, 'about.html', {'all_stocks': all_stocks})


def setting(request):
    return render(request, 'setting.html', {})


def account(request):
    return render(request, 'account.html', {})


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, 'You are now logged in')
            return redirect('portfolio')
        else:
            messages.error(request, 'Invalid credantials')
            return redirect('login')
    return render(request, 'login.html', {})


def logout(request):
    if request.method == "POST":
        auth.logout(request)
        messages.success(request, 'You are now logged out.')
        return redirect('home')


def register(request):
    if request.method == 'POST':
        # messages.error(request, 'Testing error messgae')
        # Get from values
        data = request.POST
        # print(data)
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        # Check if passwords match
        if password == password2:
            # Check username
            if User.objects.filter(username=username).exists():
                messages.error(request, 'That username is taken')
                return redirect('register')
            else:
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'That email is been used')
                    return redirect('register')
                else:
                    # Looks good
                    user = User.objects.create_user(username=username, password=password,
                                                    email=email, first_name=first_name, last_name=last_name)
                    # Login after register
                    # auth.login(request, user)
                    # messages.success(request, 'You are now logged in')
                    # return redirect('home')
                    user.save()
                    messages.success(
                        request, 'You are now registered and can log in')
                    return redirect('login')
        else:
            messages.error(request, 'Passwords do not match')
            return redirect('register')

    else:
        return render(request, 'register.html', {})


def account_setting(request):
    all_stocks = pd.read_csv(
        "../capstone-project-ghost-in-the-code/stock_symbols/iex_symbols.csv")
    all_stocks = all_stocks.set_index(
        'symbol').T.to_dict()  # .to_json(orient='records')
    return render(request, 'account_settings.html', {"all_stocks": all_stocks})


def change_pass(request, id):
    user = User.objects.get(pk=id)
    data = request.POST['new_password']
    user.set_password(str(data))
    user.save()
    return redirect(login)


def profile_setting(request):
    all_stocks = pd.read_csv(
        "../capstone-project-ghost-in-the-code/stock_symbols/iex_symbols.csv")
    all_stocks = all_stocks.set_index(
        'symbol').T.to_dict()  # .to_json(orient='records')
    return render(request, 'profile_settings.html', {"all_stocks": all_stocks})


def charts_data(request, symbol):
    request.session["symbol"] = symbol
    c = pyEX.Client('pk_6d5a654f915b4b2e9fbd3f9f380dc52b')
    data = c.chartDF(symbol, '3m')
    with open('../capstone-project-ghost-in-the-code/static/js/test1.js', 'w') as f:
        f.write("var dataSeries = [[")
    for index, rows in data.iterrows():
        temp_dict = {}
        temp_dict["date"] = index.strftime('%Y-%m-%d')
        temp_dict["value"] = float(rows.close)
        jsobj = json.dumps(temp_dict)
        print(jsobj)
        with open('../capstone-project-ghost-in-the-code/static/js/test1.js', 'a') as f:
            f.write(jsobj)
            f.write(',')
    with open('../capstone-project-ghost-in-the-code/static/js/test1.js', 'a') as f:
        f.write("]]")

    # with open('../capstone-project-ghost-in-the-code/static/js/test1.js', 'w') as f:
    #     f.write("var dataSeries = [[")
    # for index, rows in data.iterrows():
    #     temp_dict = {}
    #     temp_dict["date"] = index.strftime('%Y-%m-%d')
    #     temp_dict["value"] = float(rows.close)
    #     jsobj = json.dumps(temp_dict)
    #     print(jsobj)
    #     with open('../capstone-project-ghost-in-the-code/static/js/test1.js', 'a') as f:
    #         f.write(jsobj)
    #         f.write(',')
    # with open('../capstone-project-ghost-in-the-code/static/js/test1.js', 'a') as f:
    #     f.write("]]")
    return redirect(charts_display)


def charts_display(request):

    symbol = request.session["symbol"]
    api_request = requests.get("https://cloud.iexapis.com/stable/stock/" +
                               str(symbol) + "/quote?token=pk_6d5a654f915b4b2e9fbd3f9f380dc52b")

    # txt1 = api_request.text
    txt1 = json.loads(api_request.content)
    # print(txt1)
    top_news = []

    news_url = ('https://newsapi.org/v2/everything?q=' +
                txt1['symbol'] + '&apiKey=96bea4fd5cef4c9abb161006b3e3887f')

    print(txt1['companyName'])

    news_api_request = requests.get(news_url)
    top = json.loads(news_api_request.content)
    for j in range(3):
        try:
            date = datetime.strptime(
                top['articles'][j]['publishedAt'][5:10], "%m-%d")
        except:
            date = ''
        name = top['articles'][j]['author']
        if not name:
            name = top['articles'][j]['source']['name']
        top_news.append((top['articles'][j]['title'], top['articles'][j]['url'],
                         top['articles'][j]['urlToImage'], name,
                         date.strftime('%b %d')))
    all_stocks = pd.read_csv(
        "../capstone-project-ghost-in-the-code/stock_symbols/iex_symbols.csv")
    all_stocks = all_stocks.set_index(
        'symbol').T.to_dict()  # .to_json(orient='records')

    return render(request, 'charts.html', {"txt1": txt1, "symbol": symbol, "top_news": top_news, "all_stocks": all_stocks})


def mystock(request):
    if request.method == 'POST':
        form = StockForm(request.POST or None)

        if form.is_valid():
            form.save()
            messages.success(request, ("Stock Has Been Added!"))
            return redirect('mystock')

    else:
        myticker = Stock.objects.all()  # pull off all the db about the ticker
        mystock = []  # save the stock we pull off (symbol)
        # companyName = []

        for ticker_item in myticker:
            api_request = requests.get("https://cloud.iexapis.com/stable/stock/" + str(
                ticker_item) + "/quote?token=pk_74cd4d03d660401ba132a6c69609a3cf")

            try:
                api = json.loads(api_request.content)  # decode json
                mystock.append(api)
                # companyName.append(api[companyName])

            except Exception as e:
                api = "Error..."

        return render(request, 'mystock.html', {'myticker': myticker, 'mystock': mystock})


def portfolio_data(request):
    v = request.GET
    with open('../capstone-project-ghost-in-the-code/static/js/portfolio.js', 'w') as f:
        f.write("var dataSeries = [[")
    with open('../capstone-project-ghost-in-the-code/stocks/static/js/portfolio.js', 'w') as f:
        f.write("var dataSeries = [[")

    avg = []

    count = 0
    for i in v:
        symbol = v[i]
        API_key = 'X8Y2IU749F7LW9R2'
        TEMPLATE_URL = 'https://www.alphavantage.co/query?'
        function = 'TIME_SERIES_DAILY'

        # source_url = TEMPLATE_URL + 'function=' + function + \
        #     '&symbol=' + str(symbol) + '&outputsize=full' + '&apikey=' + API_key

        source_url = TEMPLATE_URL + 'function=' + function + \
            '&symbol=' + str(symbol) + '&apikey=' + API_key

        response = requests.get(source_url)
        txt = response.text
        json_data = json.loads(txt)
        # print(txt)

        if 'Time Series (Daily)' not in json_data:
            output = []
            # print(output)
        data = ''
        hist_data = iter(json_data['Time Series (Daily)'])
        # with open('../capstone-project-ghost-in-the-code/static/js/portfolio.js', 'w') as f:
        #     f.write("var dataSeries = [[")
        count_data = 0
        for date, OHLCV in json_data['Time Series (Daily)'].items():
            temp_dict = {}
            temp_dict["date"] = str(date)
            temp_dict["value"] = float(OHLCV["4. close"])
            jsobj = json.dumps(temp_dict)

            stock1 = {}
            stock1["date"] = str(date)
            stock1["value"] = float(OHLCV["4. close"])
            avgj = json.dumps(stock1)
            avgj = json.loads(avgj)
            # print(avgj)
            avg.append(avgj)

            # print(jsobj)
            if count_data == 99:
                with open('../capstone-project-ghost-in-the-code/static/js/portfolio.js', 'a') as f:
                    f.write(jsobj)
                with open('../capstone-project-ghost-in-the-code/stocks/static/js/portfolio.js', 'a') as f:
                    f.write(jsobj)
            else:
                with open('../capstone-project-ghost-in-the-code/static/js/portfolio.js', 'a') as f:
                    f.write(jsobj)
                    f.write(',')
                with open('../capstone-project-ghost-in-the-code/stocks/static/js/portfolio.js', 'a') as f:
                    f.write(jsobj)
                    f.write(',')

            count_data += 1
        print(count)
        if count == len(v) - 1:
            with open('../capstone-project-ghost-in-the-code/static/js/portfolio.js', 'a') as f:
                f.write("]")
            with open('../capstone-project-ghost-in-the-code/stocks/static/js/portfolio.js', 'a') as f:
                f.write("]")
        else:
            with open('../capstone-project-ghost-in-the-code/static/js/portfolio.js', 'a') as f:
                f.write("],[")
            with open('../capstone-project-ghost-in-the-code/stocks/static/js/portfolio.js', 'a') as f:
                f.write("],[")

        count += 1

    with open('../capstone-project-ghost-in-the-code/static/js/portfolio.js', 'a') as f:
        f.write(",[")
    with open('../capstone-project-ghost-in-the-code/stocks/static/js/portfolio.js', 'a') as f:
        f.write(",[")

    count_avg = 0

    stock1 = avg[:100]
    stock2 = avg[100:]
    # print(stock1)
    # print(stock2)

    for i in range(100):
        avg = {}
        avg["date"] = stock1[i]["date"]
        avg["value"] = (stock1[i]["value"] + stock2[i]["value"]) / 2
        avgj = json.dumps(avg)

        if count_avg == 99:
            with open('../capstone-project-ghost-in-the-code/static/js/portfolio.js', 'a') as f:
                f.write(avgj)
            with open('../capstone-project-ghost-in-the-code/stocks/static/js/portfolio.js', 'a') as f:
                f.write(avgj)
        else:
            with open('../capstone-project-ghost-in-the-code/static/js/portfolio.js', 'a') as f:
                f.write(avgj)
                f.write(',')
            with open('../capstone-project-ghost-in-the-code/stocks/static/js/portfolio.js', 'a') as f:
                f.write(avgj)
                f.write(',')

        count_avg += 1
    print(count_avg)

    with open('../capstone-project-ghost-in-the-code/static/js/portfolio.js', 'a') as f:
        f.write("]]")

    with open('../capstone-project-ghost-in-the-code/stocks/static/js/portfolio.js', 'a') as f:
        f.write("]]")

    return redirect(portfolio_chart)


def portfolio_chart(request):
    return render(request, 'portfolio_chart.html')
