import bokeh.layouts as layouts
import bokeh.models as models
import bokeh.plotting as plotting
import matplotlib.pyplot as plt
import matplotlib as mat
import numpy as np
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import streamlit as st
import seaborn as sns
import tabulate
import time
import undetected_chromedriver as uc
import watchdog
import yfinance as yf
from bokeh.embed import json_item
from bokeh.io import curdoc
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, DataTable, Div, HTMLTemplateFormatter, HoverTool, LinearAxis, NumeralTickFormatter, Range1d
from bokeh.plotting import figure, output_file, show
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
import plotly.figure_factory as ff
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import altair as alt
import webbrowser





# Basic Tools
def convert_to_numeric(value):
    try:
        return pd.to_numeric(value)
    except (TypeError, ValueError):
        return value
    
def transform_kmbt(value):
    num = value[:-1]  # Extract the numerical part of the value
    suffix = value[-1]  # Extract the suffix (k, m, b, t)

    mapping = {'K': 10**3, 'M': 10**6, 'B': 10**9, 'T': 10**12}  # Define the mapping for each suffix

    if suffix.upper() in mapping:
        return float(num) * mapping[suffix.upper()]  # Multiply the numerical part by the corresponding multiplier
    else:
        return float(value) 




# Data Extraction
    
@st.cache_resource
def OpenInsider(ticker):

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("headless")
    try: 
        driver = uc.Chrome(options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)

    url = f"http://openinsider.com/screener?s={ticker}&o=&pl=&ph=&ll=&lh=&fd=1461&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1"
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    try:
        table = soup.find('table', class_='tinytable')
        headers = [th.text.replace('\xa0', ' ') for th in table.find_all('th')]
        rows = []
        for tr in table.find_all('tr'):
            row = [td.text for td in tr.find_all('td')]
            if row:
                rows.append(row)

        # Create a DataFrame from the extracted data
        df_openinsider = pd.DataFrame(rows, columns=headers)
        df_openinsider['Value'] = df_openinsider["Value"].str.replace("$", "").str.replace("+", "").str.replace(",", "")
        df_openinsider['Trade Date'] = pd.to_datetime(df_openinsider['Trade Date'])
        df_openinsider['Value'] = df_openinsider['Value'].map(convert_to_numeric)

        today = datetime.today().date()
        Four_yrs_ago = today - timedelta(days=365 * 4)
        filtered_df = df_openinsider[(df_openinsider['Trade Date'].dt.date >= Four_yrs_ago) &
                                     (df_openinsider['Trade Date'].dt.date <= today)]

        filtered_data = filtered_df[['Trade Date','Insider Name', 'Value']]

        OpenInsider_Data = filtered_data

        # Calculate summary statistics for different time periods
        one_month_ago = pd.to_datetime(str(datetime.today() - timedelta(days=30)).split(" ")[0])
        summary_1m = {
            "Time": "1M",
            "Buy":
                filtered_data[(filtered_data["Trade Date"] > one_month_ago) & (filtered_data["Value"] > 0)][
                    "Insider Name"].nunique(),
            "Sold":
                filtered_data[(filtered_data["Trade Date"] > one_month_ago) & (filtered_data["Value"] < 0)][
                    "Insider Name"].nunique(),
            "TB": filtered_data[(filtered_data["Trade Date"] > one_month_ago) & (filtered_data["Value"] > 0)][
                "Value"].sum(),
            "TS": filtered_data[(filtered_data["Trade Date"] > one_month_ago) & (filtered_data["Value"] < 0)][
                "Value"].sum()
        }

        six_months_ago = pd.to_datetime(str(datetime.today() - timedelta(days=180)).split(" ")[0])
        summary_6m = {
            "Time": "6M",
            "Buy":
                filtered_data[(filtered_data["Trade Date"] > six_months_ago) & (filtered_data["Value"] > 0)][
                    "Insider Name"].nunique(),
            "Sold":
                filtered_data[(filtered_data["Trade Date"] > six_months_ago) & (filtered_data["Value"] < 0)][
                    "Insider Name"].nunique(),
            "TB":
                filtered_data[(filtered_data["Trade Date"] > six_months_ago) & (filtered_data["Value"] > 0)][
                    "Value"].sum(),
            "TS": filtered_data[(filtered_data["Trade Date"] > six_months_ago) & (filtered_data["Value"] < 0)][
                "Value"].sum()
        }

        two_years_ago = pd.to_datetime(str(datetime.today() - timedelta(days=730)).split(" ")[0])
        summary_2yrs = {
            "Time": "2Y",
            "Buy":
                filtered_data[(filtered_data["Trade Date"] > two_years_ago) & (filtered_data["Value"] > 0)][
                    "Insider Name"].nunique(),
            "Sold":
                filtered_data[(filtered_data["Trade Date"] > two_years_ago) & (filtered_data["Value"] < 0)][
                    "Insider Name"].nunique(),
            "TB": filtered_data[(filtered_data["Trade Date"] > two_years_ago) & (filtered_data["Value"] > 0)][
                "Value"].sum(),
            "TS": filtered_data[(filtered_data["Trade Date"] > two_years_ago) & (filtered_data["Value"] < 0)][
                "Value"].sum()
        }
        # Create a DataFrame with the summary statistics
        summary_df = pd.DataFrame([summary_1m, summary_6m, summary_2yrs])

        # Rearrange the columns
        summary_df = summary_df[
            ["Time", "Buy", "TB", "Sold", "TS"]]

        summary_df["TB"] = summary_df["TB"].apply(
            lambda x: f"{x / 10 ** 3:.1f}k" if abs(x) < 10 ** 6 else f"{x / 10 ** 6:.1f}M" if abs(
                x) < 10 ** 9 else f"{x / 10 ** 9:.1f}B" if abs(x) < 10 ** 12 else f"{x / 10 ** 12:.1f}T")

        summary_df["TS"] = summary_df["TS"].apply(
            lambda x: f"{x / 10 ** 3:.1f}k" if abs(x) < 10 ** 6 else f"{x / 10 ** 6:.1f}M" if abs(
                x) < 10 ** 9 else f"{x / 10 ** 9:.1f}B" if abs(x) < 10 ** 12 else f"{x / 10 ** 12:.1f}T")


        driver.quit()

        return OpenInsider_Data, summary_df

    except Exception as e:

        print(f"Error: {str(e)}")
        driver.quit()
        return None, None

@st.cache_resource
def Insider_Buying_graph(ticker_symbol, OpenInsider_Data):
    try:
    # Fetch historical data using yfinance for the past 4 years
        data = yf.download(ticker_symbol, period="4y")

        data = pd.DataFrame(data['Adj Close'])

        # Reset index to convert the date from the index to a column
        data.reset_index(inplace=True)

        # Smoothen the data using rolling mean
        window_size = 5
        data['Smoothed Adj Close'] = data['Adj Close'].rolling(window_size).mean()

        # Create the line chart for closing prices
        line_chart = alt.Chart(data).mark_line().encode(
            x='Date:T', 
            y=alt.Y('Smoothed Adj Close', scale=alt.Scale(type='log', domain=[data['Adj Close'].min() * 0.9,data['Adj Close'].max() * 1.1]), title='Price')
        )

        OpenInsider_Data['abs value'] = abs(OpenInsider_Data['Value'])

        # Create the bar chart for OpenInsider data
        bar_chart = alt.Chart(OpenInsider_Data).mark_bar(size=4, opacity=0.5).encode(
            x="Trade Date:T",
            y=alt.Y("abs value", scale=alt.Scale(type='log'), title="Insider Value"),
            color=alt.condition(alt.datum.Value > 0, alt.value("green"), alt.value("red"))
        )

        # Combine the line chart and bar chart
        chart = (line_chart + bar_chart).resolve_scale(
            y='independent'
         )

        return chart

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

@st.cache_resource
def Ten_Yrs_Price_Movement_graph(ticker_symbol):

    try:
        # Fetch historical data using yfinance for the past 10 years
        data = yf.download(ticker_symbol, period="10y")

        data = pd.DataFrame(data['Adj Close'])

        # Reset index to convert the date from the index to a column
        data.reset_index(inplace=True)

        # Smoothen the data using rolling mean
        window_size = 5
        data['Smoothed Adj Close'] = data['Adj Close'].rolling(window_size).mean()

        # Get the latest adjusted close value
        latest_close = data['Adj Close'].iloc[-1]

        alttable = alt.Chart(data).mark_line().encode(
            x='Date:T',
            y=alt.Y('Smoothed Adj Close', scale=alt.Scale(type='log', domain=[data['Adj Close'].min() * 0.9,data['Adj Close'].max() * 1.1])),
        )

        # Add a dotted line for the latest adjusted close
        latest_close_line = alt.Chart(pd.DataFrame({'Latest Close': [latest_close]})).mark_rule(color='red', strokeDash=[3, 3]).encode(
            y=alt.Y('Latest Close', scale=alt.Scale(type='log', domain=[data['Adj Close'].min() * 0.9,data['Adj Close'].max() * 1.1]))
        )

        # Combine the line chart and the latest close line
        chart = alttable + latest_close_line    

        return chart

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def Directly_Copy_From_MacroTrend_Python(ticker, parent_folder):

    try:

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("start-maximized")
        # chrome_options.add_argument("headless")
        driver = uc.Chrome(options=chrome_options)

        a = ticker.upper()
        print(a)
        wait = WebDriverWait(driver, 10)
        url_src_cp_nm = 'https://stockanalysis.com/stocks/' + ticker + '/company/'
        driver.get(url_src_cp_nm)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'div')))
        cp_nm = driver.find_element(By.CSS_SELECTOR, "div.text-center:nth-child(1)").text
        cp_nm = cp_nm.lower()
        cp_nm = cp_nm.split()
        cp_nm = cp_nm[0].replace(",", "")
        url = 'https://www.macrotrends.net/stocks/charts/' + a + '/' + cp_nm + '/revenue'
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'div')))
        geturl = driver.current_url
        period = ["A", "Q"]
        for j in period:
        # check if the ticker is available in MacroTrends
            if "stocks" in geturl:

                geturlsp = geturl.split("/", 10)
                geturlf = geturl.replace("revenue", "")
                fsurl = geturlf + "income-statement?freq=" + j
                driver.get(fsurl)
                driver.set_window_size(2000, driver.get_window_size()["height"])
                driver.execute_script("document.body.style.transform = 'scale(0.5)'")
                wait.until(EC.presence_of_element_located((By.TAG_NAME, 'div')))
                # check if the data in the ticker is available
                if driver.find_elements(By.CSS_SELECTOR, "div.jqx-grid-column-header:nth-child(1) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1)"):

                    # financial-statements
                    fsa = driver.find_element(By.CSS_SELECTOR, "#contenttablejqxgrid").text
                    da = driver.find_element(By.CSS_SELECTOR, "#columntablejqxgrid").text
                    arrow = driver.find_element(By.CSS_SELECTOR, ".jqx-icon-arrow-right")
                    webdriver.ActionChains(driver).click_and_hold(arrow).perform()
                    time.sleep(4)
                    fsb = driver.find_element(By.CSS_SELECTOR, "#contenttablejqxgrid").text
                    db = driver.find_element(By.CSS_SELECTOR, "#columntablejqxgrid").text

                    # balance-sheet
                    bsurl = geturlf + "balance-sheet?freq=" + j
                    driver.get(bsurl)
                    driver.set_window_size(2000, driver.get_window_size()["height"])
                    driver.execute_script("document.body.style.transform = 'scale(0.5)'")
                    bsa = driver.find_element(By.CSS_SELECTOR, "#contenttablejqxgrid").text
                    arrow = driver.find_element(By.CSS_SELECTOR, ".jqx-icon-arrow-right")
                    webdriver.ActionChains(driver).click_and_hold(arrow).perform()
                    time.sleep(4)
                    bsb = driver.find_element(By.CSS_SELECTOR, "#contenttablejqxgrid").text

                    # cash-flow
                    bsurl = geturlf + "cash-flow-statement?freq=" + j
                    driver.get(bsurl)
                    driver.set_window_size(2000, driver.get_window_size()["height"])
                    driver.execute_script("document.body.style.transform = 'scale(0.5)'")
                    cfa = driver.find_element(By.CSS_SELECTOR, "#contenttablejqxgrid").text
                    arrow = driver.find_element(By.CSS_SELECTOR, ".jqx-icon-arrow-right")
                    webdriver.ActionChains(driver).click_and_hold(arrow).perform()
                    time.sleep(4)
                    cfb = driver.find_element(By.CSS_SELECTOR, "#contenttablejqxgrid").text

                    # financial-ratio
                    bsurl = geturlf + "financial-ratios?freq=" + j
                    driver.get(bsurl)
                    driver.set_window_size(2000, driver.get_window_size()["height"])
                    driver.execute_script("document.body.style.transform = 'scale(0.5)'")
                    fra = driver.find_element(By.CSS_SELECTOR, "#contenttablejqxgrid").text
                    arrow = driver.find_element(By.CSS_SELECTOR, ".jqx-icon-arrow-right")
                    webdriver.ActionChains(driver).click_and_hold(arrow).perform()
                    time.sleep(4)
                    frb = driver.find_element(By.CSS_SELECTOR, "#contenttablejqxgrid").text

                    # remove symbols from variables
                    fsz = fsa.replace("$", "").replace(",", "")
                    fsx = fsb.replace("$", "").replace(",", "")
                    bsz = bsa.replace("$", "").replace(",", "")
                    bsx = bsb.replace("$", "").replace(",", "")
                    cfz = cfa.replace("$", "").replace(",", "")
                    cfx = cfb.replace("$", "").replace(",", "")
                    frz = fra.replace("$", "").replace(",", "")
                    frx = frb.replace("$", "").replace(",", "")
                    dz = da.replace("$", "").replace(".", "").replace(".", "")
                    dx = db.replace("$", "").replace(".", "").replace(".", "")
                    # split variables into lists
                    fszs = fsz.splitlines()
                    fsxs = fsx.splitlines()
                    bszs = bsz.splitlines()
                    bsxs = bsx.splitlines()
                    cfzs = cfz.splitlines()
                    cfxs = cfx.splitlines()
                    frzs = frz.splitlines()
                    frxs = frx.splitlines()
                    dzs = dz.splitlines()
                    dxs = dx.splitlines()
                    # removing title from dates dataframe
                    dzsr = np.delete(dzs, (0), axis=0)
                    dxsr = np.delete(dxs, (0), axis=0)
                    # define headers for data
                    last_key = None
                    fszsr = {}
                    for i in fszs:
                        if not (i.replace(".", "").isnumeric() or i == '-' or i.replace(".", "").startswith('-')):
                            last_key = i
                        elif last_key in fszsr:
                            fszsr[last_key].append(i)
                        else:
                            fszsr[last_key] = [i]
                    last_key = None
                    fsxsr = {}
                    for i in fsxs:
                        if not (i.replace(".", "").isnumeric() or i == '-' or i.replace(".", "").startswith('-')):
                            last_key = i
                        elif last_key in fsxsr:
                            fsxsr[last_key].append(i)
                        else:
                            fsxsr[last_key] = [i]
                    last_key = None
                    bszsr = {}
                    for i in bszs:
                        if not (i.replace(".", "").isnumeric() or i == '-' or i.replace(".", "").startswith('-')):
                            last_key = i
                        elif last_key in bszsr:
                            bszsr[last_key].append(i)
                        else:
                            bszsr[last_key] = [i]
                    last_key = None
                    bsxsr = {}
                    for i in bsxs:
                        if not (i.replace(".", "").isnumeric() or i == '-' or i.replace(".", "").startswith('-')):
                            last_key = i
                        elif last_key in bsxsr:
                            bsxsr[last_key].append(i)
                        else:
                            bsxsr[last_key] = [i]
                    last_key = None
                    cfzsr = {}
                    for i in cfzs:
                        if not (i.replace(".", "").isnumeric() or i == '-' or i.replace(".", "").startswith('-')):
                            last_key = i
                        elif last_key in cfzsr:
                            cfzsr[last_key].append(i)
                        else:
                            cfzsr[last_key] = [i]
                    last_key = None
                    cfxsr = {}
                    for i in cfxs:
                        if not (i.replace(".", "").isnumeric() or i == '-' or i.replace(".", "").startswith('-')):
                            last_key = i
                        elif last_key in cfxsr:
                            cfxsr[last_key].append(i)
                        else:
                            cfxsr[last_key] = [i]
                    last_key = None
                    frzsr = {}
                    for i in frzs:
                        if not (i.replace(".", "").isnumeric() or i == '-' or i.replace(".", "").startswith('-')):
                            last_key = i
                        elif last_key in frzsr:
                            frzsr[last_key].append(i)
                        else:
                            frzsr[last_key] = [i]
                    last_key = None
                    frxsr = {}
                    for i in frxs:
                        if not (i.replace(".", "").isnumeric() or i == '-' or i.replace(".", "").startswith('-')):
                            last_key = i
                        elif last_key in frxsr:
                            frxsr[last_key].append(i)
                        else:
                            frxsr[last_key] = [i]
                    # creating dataframes
                    fszdf = pd.DataFrame(fszsr)
                    fsxdf = pd.DataFrame(fsxsr)
                    bszdf = pd.DataFrame(bszsr)
                    bsxdf = pd.DataFrame(bsxsr)
                    cfzdf = pd.DataFrame(cfzsr)
                    cfxdf = pd.DataFrame(cfxsr)
                    frzdf = pd.DataFrame(frzsr)
                    frxdf = pd.DataFrame(frxsr)
                    dzsrf = pd.DataFrame(dzsr)
                    dxsrf = pd.DataFrame(dxsr)
                    # treating dataframes
                    fszdff = fszdf.replace("-", "0")
                    fszdff = fszdff.astype(float)
                    fsxdff = fsxdf.replace("-", "0")
                    fsxdff = fsxdff.astype(float)
                    bszdff = bszdf.replace("-", "0")
                    bszdff = bszdff.astype(float)
                    bsxdff = bsxdf.replace("-", "0")
                    bsxdff = bsxdff.astype(float)
                    cfzdff = cfzdf.replace("-", "0")
                    cfzdff = cfzdff.astype(float)
                    cfxdff = cfxdf.replace("-", "0")
                    cfxdff = cfxdff.astype(float)
                    frzdff = frzdf.replace("-", "0")
                    frzdff = frzdff.astype(float)
                    frxdff = frxdf.replace("-", "0")
                    frxdff = frxdff.astype(float)
                    # naming dates dataframe
                    ddzsrf = dzsrf.set_axis(["Dates"], axis=1)
                    ddxsrf = dxsrf.set_axis(["Dates"], axis=1)
                    # merging dataframes
                    fszdffd = ddzsrf.merge(fszdff, left_index=True, right_index=True)
                    fsxdffd = ddxsrf.merge(fsxdff, left_index=True, right_index=True)
                    bszdffd = ddzsrf.merge(bszdff, left_index=True, right_index=True)
                    bsxdffd = ddxsrf.merge(bsxdff, left_index=True, right_index=True)
                    cfzdffd = ddzsrf.merge(cfzdff, left_index=True, right_index=True)
                    cfxdffd = ddxsrf.merge(cfxdff, left_index=True, right_index=True)
                    frzdffd = ddzsrf.merge(frzdff, left_index=True, right_index=True)
                    frxdffd = ddxsrf.merge(frxdff, left_index=True, right_index=True)
                    # defining dates as rows headers
                    fszn = fszdffd.set_index("Dates")
                    fsxn = fsxdffd.set_index("Dates")
                    bszn = bszdffd.set_index("Dates")
                    bsxn = bsxdffd.set_index("Dates")
                    cfzn = cfzdffd.set_index("Dates")
                    cfxn = cfxdffd.set_index("Dates")
                    frzn = frzdffd.set_index("Dates")
                    frxn = frxdffd.set_index("Dates")
                    # concatenate whole data
                    fsconcatdd = pd.concat([fszn, fsxn])
                    fsdados = fsconcatdd.drop_duplicates()
                    bsconcatdd = pd.concat([bszn, bsxn])
                    bsdados = bsconcatdd.drop_duplicates()
                    cfconcatdd = pd.concat([cfzn, cfxn])
                    cfdados = cfconcatdd.drop_duplicates()
                    frconcatdd = pd.concat([frzn, frxn])
                    frdados = frconcatdd.drop_duplicates()
                    # creating final dataframe
                    ca = fsdados.merge(bsdados, left_index=True, right_index=True)
                    cb = ca.merge(cfdados, left_index=True, right_index=True)
                    complete = cb.merge(frdados, left_index=True, right_index=True)

                    # managing plots
                    fig1, f1_axes = plt.subplots(ncols=2, nrows=2, figsize=(30, 20))
                    fig1.suptitle(a, size=50)
                    f1_axes[0, 0].plot(complete['Revenue'], lw=2, marker='.', markersize=10, label="Revenue")
                    f1_axes[0, 0].plot(complete['Gross Profit'], lw=2, marker='.', markersize=10, label="Gross Profit")
                    f1_axes[0, 0].plot(complete['Net Income'], lw=2, marker='.', markersize=10, label="Net Income")
                    f1_axes[0, 0].plot(complete['EBITDA'], lw=2, marker='.', markersize=10, label="EBITDA")
                    f1_axes[0, 0].plot(complete['Total Assets'], lw=2, marker='.', markersize=10, label="Total Assets")
                    f1_axes[0, 0].plot(complete['Total Liabilities'], lw=2, marker='.', markersize=10, label="Total Liabilities")
                    f1_axes[0, 0].plot(complete['Total Depreciation And Amortization - Cash Flow'], lw=2, marker='.', markersize=10, label="Cash Flow")
                    f1_axes[0, 0].plot(complete['Net Cash Flow'], lw=2, marker='.', markersize=10, label="Net Cash Flow")
                    f1_axes[0, 1].plot(complete['EPS - Earnings Per Share'], lw=2, marker='.', markersize=10, label="EPS")
                    f1_axes[1, 0].plot(complete['ROE - Return On Equity'], lw=2, marker='.', markersize=10, label="ROE")
                    f1_axes[1, 0].plot(complete['ROA - Return On Assets'], lw=2, marker='.', markersize=10, label="ROA")
                    f1_axes[1, 0].plot(complete['ROI - Return On Investment'], lw=2, marker='.', markersize=10, label="ROI")
                    f1_axes[1, 1].plot(complete['Shares Outstanding'], lw=2, marker='.', markersize=10, label="Shares Outstanding")
                    f1_axes[0, 0].legend()
                    f1_axes[0, 0].invert_xaxis()
                    f1_axes[0, 1].legend()
                    f1_axes[0, 1].invert_xaxis()
                    f1_axes[1, 0].legend()
                    f1_axes[1, 0].invert_xaxis()
                    f1_axes[1, 1].legend()
                    f1_axes[1, 1].invert_xaxis()
                    # creating folder for data and images

                    if not os.path.exists(os.path.join(parent_folder, "MacroTrend", a)):
                        os.makedirs(os.path.join(parent_folder, "MacroTrend", a))

                    plt.savefig(os.path.join(parent_folder, "MacroTrend", a, a + "data_" + j + ".png"))
                    complete.to_excel(os.path.join(parent_folder, "MacroTrend", a, geturlsp[5] + "_" + j + ".xlsx"),
                                      sheet_name=geturlsp[5] + "_" + j)
                    # confirmation message for ticker that exists and have data
                    print(a + " " + j + " SUCCESS")
                # error message for ticker that exists but have no data
                else:
                    print("EMPTY TICKER")
            # error message for ticker that doesn't exist
            else:
                print("INVALID TICKER")
        driver.quit()
    except Exception as e:
        print(e)

def Check_MacroTrend(ticker, period):

    parent_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder_path = os.path.join(parent_folder, "MacroTrend")
    ticker_folder = None
    ticker_file = None

    # Find folder with ticker name
    for folder_name in os.listdir(folder_path):
        if folder_name.upper() == ticker.upper():
            ticker_folder = folder_name
            break

    if ticker_folder is None:
        print(f"Folder for ticker '{ticker}' not found, running MacroTrend Scrap.")
        Directly_Copy_From_MacroTrend_Python(ticker, parent_folder)
        return Check_MacroTrend(ticker, period)

    # Find file with suffix "_A"
    ticker_folder_path = os.path.join(folder_path, ticker_folder)
    for file_name in os.listdir(ticker_folder_path):
        if file_name.endswith("_" + period[0] + ".xlsx"):
            ticker_file = file_name
            break

    if ticker_file is None:
        print(f"Xlsx Files not found in folder '{ticker_folder}', running MacroTrend Scrap.")
        Directly_Copy_From_MacroTrend_Python(ticker, parent_folder)
        return Check_MacroTrend(ticker, period)

    return ticker_folder_path, ticker_file

@st.cache_resource
def annual_financial_table(ticker, period):


    ticker_folder_path, ticker_file = Check_MacroTrend(ticker, period)

    # Read Excel file into DataFrame
    file_path = os.path.join(ticker_folder_path, ticker_file)
    # Read Excel file into DataFrame and transpose it
    df = pd.read_excel(file_path).transpose()


    # Move the first row into column headers
    new_headers = df.iloc[0]
    df = df[1:]
    df.rename(columns=new_headers, inplace=True)
    df = df.iloc[:, ::-1]

    # Convert column headers to show year only
    if period == "Annual":
        df.columns = [col[:4] for col in df.columns]

    # Format numerical values in KMBT formatting
    # df = df.apply(lambda x: pd.to_numeric(x).apply(lambda y: f'{y / 1000:.1f}K' if abs(float(y)) >= 1e3 else f'{y:.1f}'))
    df = df.map(convert_to_numeric)

    # Move index to a new column
    df.reset_index(level=0, inplace=True)
    df.rename(columns={'index': period + ' Report'}, inplace=True)

    df = df.round(3)


    search_values = ['Shares Outstanding', 'Revenue', 'Gross Profit', 'Net Income/Loss',
                     'Net Acquisitions/Divestitures',
                     'Debt Issuance/Retirement Net - Total', 'Net Total Equity Issued/Repurchased',
                     'Total Common And Preferred Stock Dividends Paid', 'Cash On Hand', 'Net Cash Flow',
                     'Current Ratio',
                     'Long-term Debt / Capital', 'Debt/Equity Ratio', 'Gross Margin', 'Net Profit Margin',
                     'ROE - Return On Equity', 'Return On Tangible Equity', 'ROA - Return On Assets',
                     'ROI - Return On Investment', 'Book Value Per Share', 'Operating Cash Flow Per Share',
                     'Free Cash Flow Per Share', 'EPS - Earnings Per Share']

    # Filter the DataFrame based on the values in the first column
    essence_data = df[df.iloc[:, 0].isin(search_values)]

    full_fs = df
    essence_fs = essence_data

    return full_fs, essence_fs

def filter_dataframe(df):
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    _min,
                    _max,
                    (_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].str.contains(user_text_input)]

    return df




#Pagination
def Streamlit_Interface_BT(ticker, OpenInsider_Summary, _insider_price_graph, UI_full_annual_fs, UI_essence_annual_fs, UI_full_quarter_fs, UI_essence_quarter_fs):

    st.header("Bloomberg Terminal -- " + ticker, divider='rainbow')

    tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🖥️ Basic Info", "📈 TA", "🗃 FA", "🫂 Peers", "🔗 Websites", "🚀 Options", "📜 Transcript", "📝 Investment Thesis"])

    with tab0:

        yf_ticker = yf.Ticker(ticker)

        yf_info = yf_ticker.info

        def stream_data(info):
            for word in info.split(" "):
                yield word + " " 
                time.sleep(0.01)

        col1, col2  = st.columns([1,1])

        def KeyRatios(yf_ticker):

            financials = yf_ticker.quarterly_income_stmt
            balance_sheet = yf_ticker.quarterly_balance_sheet
            info = yf_ticker.info

            # Calculate Z-Score
            try:
                total_assets = balance_sheet.loc['Total Assets', balance_sheet.columns[0]]
                current_assets = balance_sheet.loc['Current Assets', balance_sheet.columns[0]]
                current_liabilities = balance_sheet.loc['Current Liabilities', balance_sheet.columns[0]]
                retained_earnings = balance_sheet.loc['Retained Earnings', balance_sheet.columns[0]]
                ebit = financials.loc['EBIT', financials.columns[0:4]].sum()
                market_cap = info['marketCap']
                total_liabilities = balance_sheet.loc['Total Liabilities Net Minority Interest', balance_sheet.columns[0]]
                Sales = financials.loc['Total Revenue', financials.columns[0:4]].sum()

                z_score = (1.2 * (current_assets - current_liabilities) +
                        1.4 * retained_earnings +
                        3.3 * ebit + Sales) / total_assets + 0.6 * market_cap / total_liabilities
                z_score = round(z_score,3)
            except:
                z_score = "/"

            # Calculate MarketCap / EV
            try:
                market_cap = info['marketCap']
                enterprise_value = info['enterpriseValue']
                market_cap_ev = market_cap / enterprise_value
                market_cap_ev = round(market_cap_ev,3)
            except:
                market_cap_ev = "/"

            # Calculate Leverage
            try:
                total_liabilities = balance_sheet.loc['Total Liabilities Net Minority Interest', balance_sheet.columns[0]]
                book_value = balance_sheet.loc['Common Stock Equity', balance_sheet.columns[0]]
                leverage = total_assets / book_value
                leverage = round(leverage,3)
            except:
                leverage = "/"

            # Calculate NCAV per Share
            try:
                shares_outstanding = info['sharesOutstanding']
                current_assets = balance_sheet.loc['Current Assets', balance_sheet.columns[0]]
                total_liabilities = balance_sheet.loc['Total Liabilities Net Minority Interest', balance_sheet.columns[0]]
                ncav_per_share = (current_assets - total_liabilities) / shares_outstanding
                ncav_per_share = round(ncav_per_share, 3)
            except:
                ncav_per_share = "/"

            # Create DataFrame
            data = {
                    'Metrics': ['Z-Score', 'MarketCap / EV', 'Leverage', 'NCAV per Share'],
                    'Values': [z_score, market_cap_ev, leverage, ncav_per_share],
                    'Description': ["A score below 1.81 means it's likely the company is headed for bankruptcy, while companies with scores above 2.99 are healthy", 
                                    "The smaller it is, the larger EV is, implying a higher debt obligation", 
                                    "Total Assets/ Book Value. The larger the absolute value it is, the more leverage it has.", 
                                    "Margin of Safety"]
                }
            
            df = pd.DataFrame(data)

            return df
        
        with col1:
        
            st.subheader(yf_info['longName'])

            st.write('Industry')
            st.caption(yf_info['industry'])

            st.write('Country')
            st.caption(yf_info['country'])
            
            st.write('Key Ratios')
            st.dataframe(KeyRatios(yf_ticker), use_container_width=True, hide_index=True)

            
        with col2:   
            st.write('Description')
            st.caption(yf_info['longBusinessSummary'])

        st.divider()
        news = pd.DataFrame(yf_ticker.news)

        news = news[['title', 'publisher', 'link', 'relatedTickers']]

        st.write('News Sentiment')
        st.dataframe(
            news,
            column_config={
                "link": st.column_config.LinkColumn("URL")

            },
            hide_index=True)
        st.divider()

        st.write('Earnings')
        st.dataframe(yf_ticker.earnings_dates, use_container_width=True)

        with st.expander("Management"):
            try:
                st.dataframe(yf_info['companyOfficers'])
            except Exception as e:
                st.write("Error occurred while displaying Management data:", e)

        with st.expander("Major holders"):
            try:
                st.dataframe(yf_ticker.major_holders)
            except Exception as e:
                st.write("Error occurred while displaying Major holders data:", e)

        with st.expander("Institutional Holders"):
            try:
                st.dataframe(yf_ticker.institutional_holders)
            except Exception as e:
                st.write("Error occurred while displaying Institutional Holders data:", e)

        with st.expander("Mutual Fund Holders"):
            try:
                st.dataframe(yf_ticker.mutualfund_holders)
            except Exception as e:
                st.write("Error occurred while displaying Mutual Fund Holders data:", e)

        with st.expander('Recommendation Summary'): 
            try:
                st.dataframe(yf_ticker.recommendations, use_container_width=True)
            except Exception as e:
                st.write("Error occurred while displaying Recommendation Summary data:", e)

        with st.expander("Yahoo Finance Info"):
            try:
                st.write(yf_info)
            except Exception as e:
                st.write("Error occurred while displaying Yahoo Finance Info:", e)

    with tab1:
        st.write("10 Yrs Price Movement")
        st.altair_chart(Ten_Yrs_Price_Movement_graph(ticker), use_container_width=True)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("OI Recent Buying (4yrs)")
            st.dataframe(OpenInsider_Summary, use_container_width=True, hide_index=True)

        with col2:
            st.write("OI Price/Actions")
            st.altair_chart(_insider_price_graph, use_container_width=True)

    with tab2:

        def statement_bar(full, essence, choice):

            transposed_essence_df = essence.transpose().reset_index()
            transposed_essence_df.columns = transposed_essence_df.iloc[0]
            transposed_essence_df = transposed_essence_df[1:]

            chart = alt.Chart(transposed_essence_df).mark_bar().encode(
                x=transposed_essence_df.columns[0],
                y=choice,
                color=alt.condition(
                    alt.datum[choice] > 0,
                    alt.value("orange"),  # The positive color
                    alt.value("brown")  # The negative color
                )
            ).properties(height=300)
                
            transposed_full_df = full.transpose()
            transposed_full_df.columns = transposed_full_df.iloc[0]
            transposed_full_df = transposed_full_df[1:]

            bar = pd.DataFrame(columns=["Bar"])

            for i in range(len(transposed_full_df.columns)):
                temp_list = []
                for j in range(len(transposed_full_df)):
                    temp_list.append(transposed_full_df.iloc[j, i])
                bar.loc[i] = [temp_list]

            df = pd.concat([essence, bar], axis=1, ignore_index=False)

            search_values = ['Shares Outstanding', 'Revenue', 'Gross Profit', 'Net Income/Loss',
                    'Net Acquisitions/Divestitures',
                    'Debt Issuance/Retirement Net - Total', 'Net Total Equity Issued/Repurchased',
                    'Total Common And Preferred Stock Dividends Paid', 'Cash On Hand', 'Net Cash Flow',
                    'Current Ratio',
                    'Long-term Debt / Capital', 'Debt/Equity Ratio', 'Gross Margin', 'Net Profit Margin',
                    'ROE - Return On Equity', 'Return On Tangible Equity', 'ROA - Return On Assets',
                    'ROI - Return On Investment', 'Book Value Per Share', 'Operating Cash Flow Per Share',
                    'Free Cash Flow Per Share', 'EPS - Earnings Per Share']

            # Filter the DataFrame based on the values in the first column
            df = df[df.iloc[:, 0].isin(search_values)]

            No_Deci = ['Shares Outstanding', 'Revenue', 'Gross Profit', 'Net Income/Loss',
                    'Net Acquisitions/Divestitures',
                    'Debt Issuance/Retirement Net - Total', 'Net Total Equity Issued/Repurchased',
                    'Total Common And Preferred Stock Dividends Paid', 'Cash On Hand', 'Net Cash Flow',
                    ]
            
            Fun_statement = df[df.iloc[:, 0].isin(No_Deci)].round(0)
            Fun_statement.set_index(Fun_statement.columns[0], inplace=True)
            
            ratio_statement = df[~df.iloc[:, 0].isin(No_Deci)].round(3)
            ratio_statement.set_index(ratio_statement.columns[0], inplace=True)

                    
            return chart, Fun_statement, ratio_statement

        transposed_essence_df = UI_essence_annual_fs.transpose().reset_index()
        transposed_essence_df.columns = transposed_essence_df.iloc[0]
        transposed_essence_df = transposed_essence_df[1:]

        choice = st.select_slider('Choose One Metric', options=transposed_essence_df.columns[1:])

        st.subheader("Annual Report")
        annual_chart, Fun_statement, ratio_statement = statement_bar(UI_full_annual_fs, UI_essence_annual_fs, choice)
        st.altair_chart(annual_chart, use_container_width=True)
        with st.expander('Fundamentals'):
                st.dataframe(
                    Fun_statement,
                    column_config={
                        "Bar": st.column_config.BarChartColumn(
                            "Trend",
                        ),
                    },
                    use_container_width=True, 
                    hide_index=False,
                )
        with st.expander('Key Ratios'):
                st.dataframe(
                    ratio_statement,
                    column_config={
                        "Bar": st.column_config.BarChartColumn(
                            "Trend",
                        ),
                    },
                    use_container_width=True, 
                    hide_index=False,
                )

        st.subheader("Quarterly Report")
        quarter_chart, Fun_statement, ratio_statement = statement_bar(UI_full_quarter_fs, UI_essence_quarter_fs, choice)
        st.altair_chart(quarter_chart, use_container_width=True)
        with st.expander('Fundamentals'):
                st.dataframe(
                    Fun_statement,
                    column_config={
                        "Bar": st.column_config.BarChartColumn(
                            "Trend",
                        ),
                    },
                    use_container_width=True, 
                    hide_index=False,
                )
        with st.expander('Key Ratios'):
                st.dataframe(
                    ratio_statement,
                    column_config={
                        "Bar": st.column_config.BarChartColumn(
                            "Trend",
                        ),
                    },
                    use_container_width=True, 
                    hide_index=False,
                )

    with tab3:

        def GetRaw():

            # Get the parent directory of the Python code
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                # Go to the "Processed Data" folder
            processed_data_dir = os.path.join(parent_dir, "Raw Data", "Finviz")

            os.chdir(processed_data_dir)

            csv_files = [file for file in os.listdir() if file.startswith("Screener_Cigar_Butt") and file.endswith(".csv")]

                # Sort the CSV files by name to get the latest one
            csv_files.sort(reverse=False)

            if csv_files:
                # Get the latest CSV file
                latest_csv = os.path.join(processed_data_dir, csv_files[0])

                # Read the CSV file into a DataFrame
                df = pd.read_csv(latest_csv)

                df = df.drop(columns = ["No."])
                
                return df

        df = GetRaw()

        Industry = df.loc[df['Ticker'] == ticker, 'Industry'].iloc[0]

        Peers = df.loc[df['Industry'] == Industry]

        ticker_table = Peers.loc[df['Ticker'] == ticker]

        st.dataframe(ticker_table, hide_index=True)

        st.write(Industry, Peers['Ticker'].count())

        def avg_table():
            metrics = ['P/E', 'Fwd P/E', 'PEG', 'P/S', 'P/B', 'EPS past 5Y', 'Sales past 5Y', 'ROE', 'Quick R', 'Debt/Eq', 'Profit M', 'SMA50']
            data = {'Metric': [], ticker: [], 'Average': [], 'Average Market Cap': [], 'Percentile': []}

            for metric in metrics:

                metric_values = convert_to_numeric(Peers[Peers[metric] != "-"][metric])
                try:
                    ticker_metric = convert_to_numeric(ticker_table[metric].iloc[0])
                except:
                    ticker_metric = float(None)

                metric_avg = round(metric_values.mean(), 2)
                metric_avg_mc = round((metric_values * convert_to_numeric(Peers[Peers[metric] != "-"]['Market Cap'])).sum() / convert_to_numeric(Peers[Peers[metric] != "-"]['Market Cap']).sum(), 2)

                try:
                    if metric in ['P/E', 'Fwd P/E', 'PEG', 'P/S', 'P/B', 'Debt/Eq', 'SMA50']: 
                        percentile = round(1 - (np.searchsorted(metric_values, ticker_metric) / len(metric_values)),2)
                    else:
                        percentile = round((np.searchsorted(metric_values, ticker_metric) / len(metric_values)),2)
                except:
                    percentile = "-"

                data['Metric'].append(metric)
                data[ticker].append(ticker_metric)
                data['Average'].append(metric_avg)
                data['Average Market Cap'].append(metric_avg_mc)
                data['Percentile'].append(percentile)

            return data

        summary_table = avg_table()

        st.dataframe(
            summary_table,
            column_config={
                "Metric": "Metric",
                ticker: ticker,
                "Average": "Avg",
                "Average Market Cap": "Avg MC",
                "Percentile": st.column_config.ProgressColumn(
                    "Percentile",
                    help="Relative Valuation across Industry",
                    format="%f",
                    min_value=0,
                    max_value=1,  
                ),
            },
            use_container_width=True, 
            hide_index=True,
        )

        st.divider()

        st.dataframe(Peers, hide_index=True)

    with tab4:

        url1 = ["Finviz", "https://finviz.com/quote.ashx?t=" + ticker + "&p=d" ]
        url2 = ['Gurufocus', "https://www.gurufocus.com/stock/" + ticker + "/summary"]
        url3 = ['Tradingview', "https://www.tradingview.com/chart/?symbol=" + ticker]
        url4 = ['Investor Relations', "https://www.google.com/search?q=" + ticker + "+investor+relations+press+release"]
        url5 = ['Seeking Alpha', "https://seekingalpha.com/symbol/" + ticker]
        url6 = ['Open Insider', "http://openinsider.com/" + ticker]
        url7 = ['Whale Wisdom', "https://whalewisdom.com/stock/" + ticker + "#listings_table-sticky-header"]
        url8 = ['Twitter', "https://twitter.com/search?q=%24" + ticker + "&src=typed_query&f=top"]
        url9 = ['Bond Supermart', "https://www.bondsupermart.com/bsm/general-search/" + ticker]
        url10 = ['Moody\'s Report', "https://www.google.com/search?q=mooody+report+" + ticker]
        url12 = ['Simply Wall St', "https://simplywall.st/dashboard"]
        url13 = ['Alpha Spread', "https://www.alphaspread.com/dashboard"]
        url14 = ['FINRA', "https://www.finra.org/finra-data/fixed-income/corp-and-agency"]
        url15 = ['Yahoo Finance', "https://finance.yahoo.com/quote/" + ticker + "/"]
        

        urls = [url1, url2, url3, url4, url5, url6, url7, url8, url9, url10, url12, url13, url14, url15]

        data = []
        for name, url in urls:
            data.append([name, url])

        data.sort()

        df = pd.DataFrame(data, columns=["Name", "URL"])

        if st.button("Open All URLs"):
            for url in df["URL"]:
                webbrowser.open_new_tab(url)

        st.dataframe(
            df,
            column_config={
                "URL": st.column_config.LinkColumn("URL")

            },
                     
            hide_index=True)

    with tab5:

        yf_ticker = yf.Ticker(ticker)

        for date in yf_ticker.options:

            with st.expander(date):

                df_calls = yf_ticker.option_chain(date).calls
                df_puts = yf_ticker.option_chain(date).puts

                df_calls_grpah = df_calls[['strike','impliedVolatility']]
                df_puts_graph = df_puts[['strike', 'impliedVolatility']]

                call_chart = alt.Chart(df_calls_grpah).mark_line(color='blue').encode(
                    x='strike',
                    y='impliedVolatility',
                    tooltip=['strike', 'impliedVolatility'],
                )

                # Create a chart for put options
                df_puts_graph = df_puts[['strike', 'impliedVolatility']]
                put_chart = alt.Chart(df_puts_graph).mark_line(color='red').encode(
                    x='strike',
                    y='impliedVolatility',
                    tooltip=['strike', 'impliedVolatility'],
                    )
                # Combine both charts
                combined_chart = (call_chart + put_chart)

                # Display the combined chart using Streamlit
                st.subheader("Options Volatility Smile")
                st.altair_chart(combined_chart, use_container_width=True)
                st.caption("Blue: Calls, Red: Puts")

                st.divider()
                st.subheader("Calls")
                st.dataframe(df_calls, hide_index=True)
                st.divider()
                st.subheader("Puts")
                st.dataframe(df_puts, hide_index=True)
    
    with tab6:

        st.write("[Go to Seeking Alpha Transcript](https://seekingalpha.com/symbol/"+ ticker +"/earnings/transcripts)")
        
    with tab7:

        pitch = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"Investment Thesis", "Pitch", ticker + '.csv')

        check_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"Investment Thesis", "Criteria_Checklist", ticker + '.csv')

        To_Do_Save = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"Investment Thesis", "To Do", ticker + '.csv')

        blank_pitch = {
                        'Information' : ['Long', 'Short', 'Industry Performance'], 
                        'Market Stance' : ["[input]"] * 3, 
                        'My Stance / Rebuttal' : ["[input]"] * 3 
                    }
        

        FCF = UI_essence_quarter_fs.loc[UI_full_quarter_fs.iloc[:, 0] == "Free Cash Flow Per Share"]
        Debt_Issuance = UI_essence_quarter_fs.loc[UI_full_quarter_fs.iloc[:, 0] == "Debt Issuance/Retirement Net - Total"]
        Equity_Issuance = UI_essence_quarter_fs.loc[UI_full_quarter_fs.iloc[:, 0] == "Net Total Equity Issued/Repurchased"]

        To_Do_Blank_List = {
                        'Task' : ['Go Through Official Websites', 'Read Last 4 Quarter Financial Report','Go through all the fundamentals','Check the management team', 'Seeking Alpha', 'Investment Thesis'], 
                        'Done' : [False] * 6, 
                        'Notes' : [''] * 6
                    }

        check_list = {
    
            'Metrics': [
                'Boring sector',
                'Free Cash flow',
                'Reducing Debt',
                'Repurchasing Shares',
                'Low debt to equity',
                'Past 10 year CAGR',
                'Historical low valuation',
                'ATH < -60%',
                'PB > 0',
                'Insider buying > 100K',
                '52 wk low 15%',
                'Forming a base'
            ],
            'Figures': [
                yf_info['industry'],
                FCF.iloc[:,-4:].values.tolist(),
                Debt_Issuance.iloc[:,-4:].values.tolist(),
                Equity_Issuance.iloc[:,-4:].values.tolist(),
                float(ticker_table['Debt/Eq'].iloc[0]),
                round((yf.download(ticker, period="10y")['Adj Close'].iloc[-1] / yf.download(ticker, period="10y")['Adj Close'].iloc[0]) ** (1/10) - 1, 4),
                ticker_table['P/E'].iloc[0],
                ticker_table['All-Time High'].iloc[0],
                ticker_table['P/B'].iloc[0],
                OpenInsider_Summary.loc[OpenInsider_Summary.iloc[:, 0] == "1M","TB"].iloc[0],
                ticker_table['52W Low'].iloc[0],
                ticker_table['SMA50'].iloc[0]
            ],
            'Checks': [
                False,
                FCF.iloc[:, -4:].values.sum() > 0,
                Debt_Issuance.iloc[:,-4:].values.sum() < 0,
                Equity_Issuance.iloc[:,-4:].values.sum() < 0,
                float(ticker_table['Debt/Eq'].iloc[0]) < 1,
                round((yf.download(ticker, period="10y")['Adj Close'].iloc[-1] / yf.download(ticker, period="10y")['Adj Close'].iloc[0]) ** (1/10) - 1, 4) > 0.08,
                False,
                float(ticker_table['All-Time High'].iloc[0]) < -0.6,
                float(ticker_table['P/B'].iloc[0]) < 1,
                transform_kmbt(OpenInsider_Summary.loc[OpenInsider_Summary.iloc[:, 0] == "1M","TB"].iloc[0]) > 100000,
                float(ticker_table['52W Low'].iloc[0]) < 0.15,
                float(ticker_table['SMA50'].iloc[0]) > 0
            ],
            'URL': [
                '',
                '',
                '',
                '',
                '',
                '',
                'https://www.gurufocus.com/stock/' + ticker + '/summary',
                '',
                '',
                '',
                '',
                ''
            ],
            'Notes': [
                'Manual',
                'Statement Below',
                'Statement Below',
                'Statement Below',
                'Industry Average',
                '',
                'Gurufocus',
                '',
                '',
                '',
                '',
                ''
            ],
            'Commentaries': [
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                ''
            ] 
        }

        if st.button("Refresh"): 
            st.rerun()
        
        st.subheader("To Do List")
        with st.form("To Do List"):

            if To_Do_Save: 
                try:
                    to_do_df = pd.read_csv(To_Do_Save) 
                except: 
                    to_do_df = pd.DataFrame(To_Do_Blank_List)

            st.session_state['updated_todo'] = st.data_editor(to_do_df, hide_index=True, use_container_width=True)
            
            uploaded = st.form_submit_button("Upload")
            Clear_all = st.form_submit_button("Clear_All")
            confirmation = st.checkbox('Are you sure to delete the file?')

            if uploaded:
                pd.DataFrame(st.session_state['updated_todo']).to_csv(To_Do_Save, index=False)

            if Clear_all and confirmation:
                os.remove(To_Do_Save)


        st.subheader("Investment Thesis")
        with st.form("Investment Thesis"):

            if pitch: 
                try:
                    pitch_df = pd.read_csv(pitch) 
                except: 
                    pitch_df = pd.DataFrame(blank_pitch)

            st.session_state['amend_pitch'] = st.data_editor(pitch_df, hide_index=True, use_container_width=True)
            
            uploaded = st.form_submit_button("Upload")
            Clear_all = st.form_submit_button("Clear_All")
            confirmation = st.checkbox('Are you sure to delete the file?')

            if uploaded:
                pd.DataFrame(st.session_state['amend_pitch']).to_csv(pitch, index=False)

            if Clear_all and confirmation:
                os.remove(pitch)


        st.subheader("CheckList")
        with st.form("Checklist"):

            if check_file: 
                try:
                    check_file_df = pd.read_csv(check_file) 
                except: 
                    check_file_df = pd.DataFrame(check_list)

            st.session_state['amend_pitch_check'] = st.data_editor(check_file_df, 
                                                                   column_config = {
                                                                       'URL': st.column_config.LinkColumn('URL')
                                                                       },
                                                                        hide_index=True, use_container_width=True)
            
            uploaded = st.form_submit_button("Upload")
            Clear_all = st.form_submit_button("Clear_All")
            confirmation = st.checkbox('Are you sure to delete the file?')

            if uploaded:
                pd.DataFrame(st.session_state['amend_pitch_check']).to_csv(check_file, index=False)

            if Clear_all and confirmation: 
                os.remove(check_file)
                st.rerun()
 
            
        with st.expander("Supplementary Quarterly Statement"):
            
            FCF_graph = FCF.set_index(FCF.columns[0], inplace=False).transpose()
            Debt_Issuance_graph = Debt_Issuance.set_index(Debt_Issuance.columns[0], inplace=False).transpose()
            Equity_Issuance_graph = Equity_Issuance.set_index(Equity_Issuance.columns[0], inplace=False).transpose()

            st.subheader(FCF_graph.columns[0])
            st.bar_chart(FCF_graph, color = "#FF9800")
            st.subheader(Debt_Issuance_graph.columns[0])
            st.bar_chart(Debt_Issuance_graph, color="#4CAF50")
            st.subheader(Equity_Issuance_graph.columns[0])
            st.bar_chart(Equity_Issuance_graph, color= "#2196F3")

    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 2rem;
            padding-bottom: 1rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    return ticker

def Streamlit_Interface_FS(ticker, UI_full_annual_fs, UI_essence_annual_fs, UI_full_quarter_fs, UI_essence_quarter_fs):

    st.header("Full Financial Report -- " + ticker, divider = 'rainbow')

    tab0, tab1 = st.tabs(["MacroTrend", "Yahoo Finance"])

    with tab0:

        def statement_bar(full, essence, choice):

            transposed_full_df = full.transpose().reset_index()
            transposed_full_df.columns = transposed_full_df.iloc[0]
            transposed_full_df = transposed_full_df[1:]

            chart = alt.Chart(transposed_full_df).mark_bar().encode(
                x=transposed_full_df.columns[0],
                y=choice,
                color=alt.condition(
                    alt.datum[choice] > 0,
                    alt.value("orange"),  # The positive color
                    alt.value("brown")  # The negative color
                )
            )

            transposed_df = full.transpose()
            transposed_df.columns = transposed_df.iloc[0]
            transposed_df = transposed_df[1:]

            bar = pd.DataFrame(columns=["Bar"])

            for i in range(len(transposed_df.columns)):
                temp_list = []
                for j in range(len(transposed_df)):
                    temp_list.append(transposed_df.iloc[j, i])
                bar.loc[i] = [temp_list]

            df = pd.concat([full, bar], axis=1, ignore_index=False)
            df.set_index(df.columns[0], inplace=True)
        
            return chart, df

        transposed_essence_df = UI_full_annual_fs.transpose().reset_index()
        transposed_essence_df.columns = transposed_essence_df.iloc[0]
        transposed_essence_df = transposed_essence_df[1:]

        choice = st.select_slider('Choose One Metric', options=transposed_essence_df.columns[1:])

        st.subheader("Annual Report")
        annual_chart, financials = statement_bar(UI_full_annual_fs, UI_essence_annual_fs, choice)
        st.altair_chart(annual_chart, use_container_width=True)
        with st.expander('Financials'):
            st.dataframe(
                financials,
                column_config={
                    "Bar": st.column_config.BarChartColumn(
                        "Trend",
                    ),
                },
                use_container_width=True, 
                hide_index=False,
            )

        st.subheader("Quarterly Report")
        quarter_chart, financials = statement_bar(UI_full_quarter_fs, UI_essence_quarter_fs, choice)
        st.altair_chart(quarter_chart, use_container_width=True)
        with st.expander('Financials'):
            st.dataframe(
                financials,
                column_config={
                    "Bar": st.column_config.BarChartColumn(
                        "Trend",
                    ),
                },
                use_container_width=True, 
                hide_index=False,
            )

    with tab1:

        yf_ticker = yf.Ticker(ticker)

        col1, col2 = st.columns([1,1])

        with col1:
            st.subheader("Income Statement")
            st.dataframe(yf_ticker.income_stmt)
            st.subheader("Balance Sheet")
            st.dataframe(yf_ticker.balance_sheet)
            st.subheader("Cashflow statement")
            st.dataframe(yf_ticker.cashflow)
        
        with col2:
            st.subheader(".")
            st.dataframe(yf_ticker.quarterly_income_stmt)
            st.subheader(".")
            st.dataframe(yf_ticker.quarterly_balance_sheet)
            st.subheader(".")
            st.dataframe(yf_ticker.quarterly_cashflow)

    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 2rem;
            padding-bottom: 1rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def Streamlit_Interface_Screener(pathway):


    def GetProcessed():

        # Get the parent directory of the Python code
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # Go to the "Processed Data" folder
        processed_data_dir = os.path.join(parent_dir, "Processed Data", "Finviz")

        os.chdir(processed_data_dir)

        csv_files = [file for file in os.listdir() if file.startswith("CB_Filter") and file.endswith(".csv")]

            # Sort the CSV files by name to get the latest one
        csv_files.sort(reverse=False)

        if csv_files:
            # Get the latest CSV file
            latest_csv = os.path.join(processed_data_dir, csv_files[0])

            # Read the CSV file into a DataFrame
            df = pd.read_csv(latest_csv)

            df = df.drop(columns = ["No."])

            df = df.sort_values(by=['Fundamental Score', '52W High'], ascending=[False, True])
            
            return df
    
    def GetRaw():

        # Get the parent directory of the Python code
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # Go to the "Processed Data" folder
        processed_data_dir = os.path.join(parent_dir, "Processed Data", "Finviz")

        os.chdir(processed_data_dir)

        csv_files = [file for file in os.listdir() if file.startswith("CB_") and file.endswith(".csv")]

            # Sort the CSV files by name to get the latest one
        csv_files.sort(reverse=False)

        if csv_files:
            # Get the latest CSV file
            latest_csv = os.path.join(processed_data_dir, csv_files[0])

            # Read the CSV file into a DataFrame
            df = pd.read_csv(latest_csv)

            df = df.drop(columns = ["No."])
            
            return df

        # Display the table in Streamlit
    
    st.header("Cigar Butt Screener", divider = 'rainbow')


    col1, col2 = st.columns([5,1])

    with col1:

        options = st.selectbox(
        'Which screener would you want?',
        ('Filtered', 'Raw'))

        if options == "Raw":
            df = GetRaw()
            st.data_editor(filter_dataframe(df), use_container_width=True)
            st.write("[Go to Finviz Charts](https://finviz.com/screener.ashx?v=212&f=cap_microover,sh_instown_o10,sh_price_o1&ft=4&o=tickersfilter)")

        elif options == "Filtered":
            df = GetProcessed()
            st.data_editor(filter_dataframe(df), use_container_width=True)
            tickers = ','.join(df['Ticker'])
            st.write("[Go to Finviz Charts](https://finviz.com/screener.ashx?v=212&f=cap_microover,sh_instown_o10,sh_price_o1&ft=4&t=" + tickers + "&o=tickersfilter)")

    with col2:

         with st.form("Ticker Input"):

            Ticker_Input = st.text_input('Ticker')
            
            Submitted = st.form_submit_button("Submit")

            if Submitted:

                with open(pathway, "w") as file:
                    file.write(Ticker_Input)
                
    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 2rem;
            padding-bottom: 1rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
def Streamlit_Interface_Portfolio(pathway):

    pathway = os.path.join(pathway, "Streamlit_Data_Save", "Portfolio.csv")

    df = pd.read_csv(pathway)

    # Initialize cash balance
    cash_balance = 0

    # Iterate through each trade in the trading log
    for index, trade in df.iterrows():
        # Get the trade details
        asset_category = trade['Asset Category']
        currency = trade['Currency']
        symbol = trade['Symbol']
        quantity = trade['Quantity']
        t_price = trade['T. Price']
        
        # Calculate the trade amount
        trade_amount = quantity * t_price
        
        # Update cash balance based on the asset category
        if asset_category == 'Cash':
            cash_balance += trade_amount
        elif asset_category == 'Stocks':
            cash_balance -= trade_amount - trade['Comm/Fee']
        elif asset_category == 'Equity and Index Options':
            cash_balance -= trade_amount * 100 - trade['Comm/Fee']

    # Get the unique symbols in the trading log
    symbols = df['Symbol'].unique()

    # Create an empty list to store current portfolio position
    current_portfolio = []

    # Get the current price for each symbol
    for symbol in symbols:

        asset_category = df.loc[(df['Symbol'] == symbol), 'Asset Category'].iloc[0]

        if asset_category != 'Cash': 

            ticker = yf.Ticker(symbol)

            current_price = ticker.history().tail(1)['Close'].values[0]

            if asset_category == 'Equity and Index Options':
                letters = ""
                for char in symbol:
                    if char.isdigit():
                        break
                    letters += char
                ticker = yf.Ticker(letters)
            
            sector = ticker.info.get('sector', 'Fund')
            industry = ticker.info.get('industry', 'Fund')
            marketcap = ticker.info.get('marketCap', )
            
            quantity = df.loc[(df['Symbol'] == symbol), 'Quantity'].sum()

            quantity = quantity * 100 if asset_category == 'Equity and Index Options' else quantity

            current_portfolio.append({
                'Asset Category': asset_category, 
                'Symbol': symbol,
                'Current Price': round(current_price,2),
                'Quantity': quantity, 
                'Sector': sector, 
                'Industry': industry,
                'Market Cap': marketcap,
                'Amount': round(current_price * quantity,2)
            })
        
    current_portfolio.append({
        'Asset Category': 'Cash', 
        'Symbol': 'Cash',
        'Sector': 'Cash', 
        'Industry': 'Cash',
        'Amount': round(cash_balance,2)
    })

    current_portfolio = pd.DataFrame(current_portfolio)
    current_portfolio = current_portfolio[current_portfolio['Amount'] != 0]
    current_portfolio = current_portfolio.sort_values('Amount', ascending=False)


    # Display the current portfolio position
    st.header('Portfolio Overview', divider = 'rainbow')
    
    st.subheader("\nCurrent Portfolio Position")
    st.dataframe(current_portfolio, use_container_width=True, hide_index=True)

    col1, col2 = st.columns([1,1])

    with col1:

        sector_df = pd.DataFrame(current_portfolio.groupby(['Sector'])['Amount'].sum()).reset_index()
        sector_df['Percent Holdings'] = round(sector_df['Amount'] / sector_df['Amount'].sum() * 100, 1) 

        sector_piechart = alt.Chart(sector_df).mark_arc().encode(
            theta="Percent Holdings",
            color="Sector", 
        )

        sector_piechart = sector_piechart.mark_arc(outerRadius=70)
        sector_piechart_label = sector_piechart.mark_text(radius=90, size=10).encode(text="Percent Holdings:N")

        st.altair_chart(sector_piechart + sector_piechart_label, theme='streamlit', use_container_width=True)
    
    with col2:

        industry_df = pd.DataFrame(current_portfolio.groupby(['Industry'])['Amount'].sum()).reset_index()
        industry_df['Percent Holdings'] = round(industry_df['Amount'] / industry_df['Amount'].sum() * 100, 1) 

        Industry_piechart = alt.Chart(industry_df).mark_arc().encode(
            theta="Percent Holdings",
            color="Industry", 
        )

        Industry_piechart = Industry_piechart.mark_arc(outerRadius=70)
        Industry_piechart_label = Industry_piechart.mark_text(radius=90, size=10).encode(text="Percent Holdings:N")

        st.altair_chart(Industry_piechart + Industry_piechart_label, theme='streamlit', use_container_width=True)

    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 2rem;
            padding-bottom: 1rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
        


                 




def main():

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ("Portfolio Overview", "Cigar Butt Screener", "Bloomberg Terminal", "Financial Statement"))

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    terminal_ticker_pathway = os.path.join(parent_dir, "Streamlit_Data_Save", "Terminal_Ticker.txt")

    if page == "Cigar Butt Screener":
        Streamlit_Interface_Screener(terminal_ticker_pathway)
    elif page == "Portfolio Overview":
        Streamlit_Interface_Portfolio(parent_dir)


    with open(terminal_ticker_pathway, "r") as file:
        ticker = file.read()

    if ticker:

        OpenInsider_Data, OpenInsider_Summary = OpenInsider(ticker)
        insider_price_graph = Insider_Buying_graph(ticker, OpenInsider_Data)
        UI_full_annual_fs, UI_essence_annual_fs = annual_financial_table(ticker, "Annual")
        UI_full_quarter_fs, UI_essence_quarter_fs = annual_financial_table(ticker, "Quarter")

        if page == "Bloomberg Terminal":
            Streamlit_Interface_BT(ticker, OpenInsider_Summary, insider_price_graph, UI_full_annual_fs, UI_essence_annual_fs, UI_full_quarter_fs, UI_essence_quarter_fs)
        elif page == "Financial Statement":
            Streamlit_Interface_FS(ticker, UI_full_annual_fs, UI_essence_annual_fs, UI_full_quarter_fs, UI_essence_quarter_fs)

if __name__ == "__main__":
    main()
