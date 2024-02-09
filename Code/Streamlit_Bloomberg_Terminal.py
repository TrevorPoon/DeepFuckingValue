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





# Basic Tools
def convert_to_numeric(value):
    try:
        return pd.to_numeric(value)
    except (TypeError, ValueError):
        return value




# Data Extraction
@st.cache_resource
def OpenInsider(ticker):

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("headless")
    driver = uc.Chrome(options=chrome_options)

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
        # Fetch historical data using yfinance for the past 10 years
        data = yf.download(ticker_symbol, period="4y")

        # Create a Bokeh figure
        p = figure(title=f"Insider Buying for {ticker_symbol}", x_axis_label="Date", x_axis_type="datetime", height=200, width=500)

        # Plot the closing prices on the primary y-axis (logarithmic scale)
        line = p.line(data.index, np.log10(data["Close"]), line_width=2, color="blue")
        p.yaxis[0].formatter = NumeralTickFormatter(format="0.00")

        # Create a secondary y-axis for OpenInsider data (logarithmic scale)
        p.extra_y_ranges = {"insider": Range1d(start=1, end=np.log10(OpenInsider_Data["Value"].abs().max()) * 1.1)}
        p.add_layout(LinearAxis(y_range_name="insider", axis_label="Insider Value"), "right")
        p.yaxis[1].formatter = NumeralTickFormatter(format="0.00")

        # Plot the OpenInsider data as bars on the secondary y-axis
        colors = ['green' if value > 0 else 'red' for value in OpenInsider_Data["Value"]]
        p.vbar(x=OpenInsider_Data["Trade Date"], top=np.log10(OpenInsider_Data["Value"].abs()), width=timedelta(days=3),
                fill_color=colors, y_range_name="insider", line_color=None)

        # Set the range of the primary y-axis (logarithmic scale)
        p.y_range = Range1d(start=np.log10(data["Close"].min()) * 0.9, end=np.log10(data["Close"].max()) * 1.1)

        return p

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

@st.cache_resource
def Ten_Yrs_Price_Movement_graph(ticker_symbol):

    try:
        # Fetch historical data using yfinance for the past 10 years
        data = yf.download(ticker_symbol, period="10y")

        # Create a Bokeh figure
        p = figure(title=f"10 Yrs Price Movement for {ticker_symbol}", x_axis_label="Date", x_axis_type="datetime", y_axis_type="log", height=200)

        # Plot the closing prices on the primary y-axis
        line = p.line(data.index, data["Close"], line_width=2, color="blue")

        # Set the range of the primary y-axis
        p.y_range = Range1d(start=data["Close"].min() * 0.9, end=data["Close"].max() * 1.1)

        hover_tool = HoverTool(renderers=[line], tooltips=[("Price", "@y")], mode="vline")
        p.add_tools(hover_tool)

        return p

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

    parent_folder = os.path.dirname(os.path.dirname(os.getcwd()))
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

    rows_formats = {
        'Shares Outstanding': '{:,.0f}',  # Format as integer with commas
        'Revenue': '${:,.0f}',  # Format as currency with two decimal places
        'Gross Profit': '${:,.0f}',
        'Net Income/Loss': '${:,.0f}',
        'Net Acquisitions/Divestitures': '${:,.0f}',
        'Debt Issuance/Retirement Net - Total': '${:,.0f}',
        'Net Total Equity Issued/Repurchased': '${:,.0f}',
        'Total Common And Preferred Stock Dividends Paid': '${:,.0f}',
        'Cash On Hand': '${:,.0f}',
        'Net Cash Flow': '${:,.0f}',
        'Current Ratio': '{:.1%}',  # Format as percentage with two decimal places
        'Long-term Debt / Capital': '{:.1%}',
        'Debt/Equity Ratio': '{:.1%}',
        'Gross Margin': '{:.1%}',
        'Net Profit Margin': '{:.1%}',
        'ROE - Return On Equity': '{:.1%}',
        'Return On Tangible Equity': '{:.1%}',
        'ROA - Return On Assets': '{:.1%}',
        'ROI - Return On Investment': '{:.1%}',
        'Book Value Per Share': '${:,.1f}',
        'Operating Cash Flow Per Share': '${:,.1f}',
        'Free Cash Flow Per Share': '${:,.1f}',
        'EPS - Earnings Per Share': '${:,.1f}'
    }


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
def Streamlit_Interface_MainPage(ticker, OpenInsider_Summary, insider_price_graph, UI_essence_annual_fs, UI_essence_quarter_fs):
    st.title("Bloomberg Terminal -- " + ticker)

    tab1, tab2, tab3 = st.tabs(["📈 TA", "🗃 FA", "🫂 Peers"])

    with tab1:
        st.write("10 Yrs Price Movement")
        st.bokeh_chart(Ten_Yrs_Price_Movement_graph(ticker), use_container_width=True)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("OI Recent Buying (4yrs)")
            st.table(OpenInsider_Summary)
            st.markdown("<style>div[data-testid='stTable'] table { font-size: 11px; }</style>", unsafe_allow_html=True)

        with col2:
            st.write("OI Price/Actions")
            st.bokeh_chart(insider_price_graph, use_container_width=True)

    with tab2:

        st.dataframe(UI_essence_annual_fs, use_container_width=True, hide_index=True)

        print(UI_essence_annual_fs)

        st.data_editor(
            UI_essence_annual_fs.drop(UI_essence_annual_fs.columns[0], axis=1),
            column_config={
                "sales": st.column_config.LineChartColumn(
                    "Sales (last 6 months)",
                    width="medium",
                    help="The sales volume in the last 6 months",
                    y_min=0,
                    y_max=100,
                ),
            },
            hide_index=True,
)
        st.dataframe(UI_essence_quarter_fs, use_container_width=True, hide_index=True)
    
    with tab3:
        st.write("Peers Comparison")

    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def Streamlit_Interface_FullReport(ticker, UI_full_annual_fs, UI_full_quarter_fs):

    cm = sns.light_palette("green", as_cmap=True)

    st.title("Full Financial Report -- " + ticker)

    UI_full_annual_fs = UI_full_annual_fs.style.background_gradient(cmap=cm, axis=1)
    UI_full_quarter_fs = UI_full_quarter_fs.style.background_gradient(cmap=cm, axis=1)

    st.dataframe(UI_full_annual_fs, use_container_width=True, hide_index=True)
    st.dataframe(UI_full_quarter_fs, use_container_width=True, hide_index=True)

    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def Streamlit_Interface_Screener():

    def GetProcessed():

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

        # Display the table in Streamlit
    
    st.title("Cigar Butt Screener")
    options = st.selectbox(
    'Which dataframe would you want?',
    ('Filtered', 'Raw'))

    if options == "Raw":
       st.data_editor(filter_dataframe(GetRaw()), use_container_width=True) 
    elif options == "Filtered":
        st.data_editor(filter_dataframe(GetProcessed()), use_container_width=True)

def Streamlit_Interface(ticker, OpenInsider_Summary, insider_price_graph, UI_full_annual_fs, UI_essence_annual_fs, UI_full_quarter_fs, UI_essence_quarter_fs):
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ("Main Page", "Full Report", "Cigar Butt Screener"))

    if page == "Main Page":
        Streamlit_Interface_MainPage(ticker, OpenInsider_Summary, insider_price_graph, UI_essence_annual_fs, UI_essence_quarter_fs)
    elif page == "Full Report":
        Streamlit_Interface_FullReport(ticker, UI_full_annual_fs, UI_full_quarter_fs)
    elif page == "Cigar Butt Screener":
        Streamlit_Interface_Screener()


def main():

    ticker = "NYCB"

    OpenInsider_Data, OpenInsider_Summary = OpenInsider(ticker)
    insider_price_graph = Insider_Buying_graph(ticker, OpenInsider_Data)
    UI_full_annual_fs, UI_essence_annual_fs = annual_financial_table(ticker, "Annual")
    UI_full_quarter_fs, UI_essence_quarter_fs = annual_financial_table(ticker, "Quarter")

    Streamlit_Interface(ticker, OpenInsider_Summary, insider_price_graph, UI_full_annual_fs, UI_essence_annual_fs, UI_full_quarter_fs, UI_essence_quarter_fs)

if __name__ == "__main__":
    main()
