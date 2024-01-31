

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import time
from bs4 import BeautifulSoup
import pandas as pd
import random
from datetime import date, datetime, timedelta
import os
import numpy as np
import matplotlib.pyplot as plt
import pyautogui
import re
import selenium
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
import subprocess
import requests
import yfinance as yf
import pandas_datareader.data as web
from pandas.api.types import CategoricalDtype
from typing import Dict
import openpyxl




# Tool Function
def removing_ads(driver):
    # Get the first window handle
    main_window = driver.window_handles[0]

    # Perform actions that may open a new tab or window
    # For example, clicking a link or button

    # Close any additional windows or tabs
    for window in driver.window_handles[1:]:
        driver.switch_to.window(window)
        driver.close()

    # Switch back to the main window
    driver.switch_to.window(main_window)
def convert_to_numeric(value):
    try:
        return pd.to_numeric(value)
    except (TypeError, ValueError):
        return value



# Extract Function
def Get_Result_From_Finviz(driver, name, link):

    min_delay = 0.1
    max_delay = 1

    directory = os.path.join(os.path.dirname(os.getcwd()), "Raw Data", "Finviz") # Get the current working directory
    print(directory)
    for filename in os.listdir(directory):
        if filename.startswith(name) and filename.endswith(".csv"):
            os.remove(os.path.join(directory, filename))
            print(f"Deleted file: {filename}")

    driver.get(link)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    pagination = soup.find(id="screener_pagination")
    href_list = [a["href"] for a in pagination.find_all("a")]
    # Extract the numbers from the href values that are on the RHS of "&r="
    try:
        numbers = [int(href.split("&r=")[1]) for href in href_list if "&r=" in href]
        # Get the maximum number from the list
        max_number = max(numbers)
    except:
        max_number = 1

    # Extract all the href values from the pagination element


    table = soup.find("table", class_="styled-table-new is-rounded is-tabular-nums w-full screener_table")
    headers = [th.text for th in table.find_all("th")]

    data = []
    index = 1

    while index <= max_number:

        driver.get(link + "&r=" + str(index))
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find("table", class_="styled-table-new is-rounded is-tabular-nums w-full screener_table")

        for row in table.find_all("tr"):
            row_data = [td.text for td in row.find_all("td")]
            if row_data:
                data.append(row_data)

        index += 20
        time.sleep(random.uniform(min_delay, max_delay))

    df = pd.DataFrame(data, columns=headers)

    df["Market Cap"] = df["Market Cap"].str.replace(",", "")  # Remove commas in numbers
    df["Market Cap"] = df["Market Cap"].str.replace("K", "e3", case=False)  # Convert 'k' to '*1e3' (thousand)
    df["Market Cap"] = df["Market Cap"].str.replace("M", "e6", case=False)  # Convert 'm' to '*1e6' (million)
    df["Market Cap"] = df["Market Cap"].str.replace("B", "e9", case=False)  # Convert 'b' to '*1e9' (billion)
    df["Market Cap"] = df["Market Cap"].str.replace("T", "e12", case=False)  # Convert 't' to '*1e12' (trillion)

    df = df.apply(lambda x: x.str.replace("%$", "e-2", regex=True) if x.dtype == 'object' else x)
    df = df.map(convert_to_numeric)
    filepath = os.path.join(directory, name + str(date.today()) + ".csv")
    df.to_csv(filepath, index=False)
    print(name + str(date.today()) + " Success!")

def OpenInsider(ticker, driver):

    try:
        url = f"http://openinsider.com/screener?s={ticker}&o=&pl=&ph=&ll=&lh=&fd=1461&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1"
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        table = soup.find('table', class_='tinytable')
        headers = [th.text.replace('\xa0', ' ') for th in table.find_all('th')]
        rows = []
        for tr in table.find_all('tr'):
            row = [td.text for td in tr.find_all('td')]
            if row:
                rows.append(row)

        # Create a DataFrame from the extracted data
        df_openinsider = pd.DataFrame(rows, columns=headers)
        df_openinsider["Value"] = df_openinsider["Value"].str.replace("$", "").str.replace("+", "").str.replace(",", "")
        df_openinsider['Trade Date'] = pd.to_datetime(df_openinsider['Trade Date'])
        df_openinsider.map(convert_to_numeric)

        today = datetime.today().date()
        six_months_ago = today - timedelta(days=6 * 30)
        filtered_df = df_openinsider[(df_openinsider['Trade Date'].dt.date >= six_months_ago) &
                                     (df_openinsider['Trade Date'].dt.date <= today)]

        # Calculate the sum of 'Values' column
        return filtered_df['Value'].astype(float).sum()

    except:
        return 0

def MarketWatch(ticker, driver):

    try:
        url = f"https://www.marketwatch.com/investing/stock/{ticker}/financials"
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        table = soup.select_one('table[aria-label="Financials - data table"]')
        # Get the header row (th elements)
        header_row = table.select('thead tr th')
        headers = [header.text.strip() for header in header_row]

        # Get the data rows (tr elements)
        data_rows = table.select('tbody tr')

        # Initialize a list to store the table data
        table_data = []

        # Loop through each data row and extract the content of td elements
        for row in data_rows:
            data = [cell.text.strip() for cell in row.select('td')]
            table_data.append(data)

        # Create a DataFrame from the table data
        table_data = pd.DataFrame(table_data, columns=headers)

        # Save the filtered DataFrame to a CSV file
        # Filter the DataFrame to include rows with "Net Income \n Net Income" in the first column
        filtered_data = table_data[table_data.iloc[:, 0].str.contains(r"Net Income\s*\n\s*Net Income")]

        # Iterate over the columns and perform replacements for four-digit number columns
        for col in filtered_data.columns:
            if re.match(r'^\d{4}$', col):  # Check if the column name is a four-digit number
                filtered_data.loc[:, col] = filtered_data.loc[:, col].replace(
                    {"-": "0", "\\(": "-", "\\)": "", "K": "e3", "M": "e6", "B": "e9", "T": "e12"}, regex=True)

        # Print the filtered DataFrame with replacements

        filtered_data = filtered_data.map(convert_to_numeric)

        for col in filtered_data.columns:
            if re.match(r'^\d{4}$', col):
                if filtered_data.iloc[0, filtered_data.columns.get_loc(col)] > 0:
                    return True

        return False

    except Exception as e:
        print(e)
        return False

def Cigar_Butt_Filter (name, driver):

    directory = os.path.join(os.path.dirname(os.getcwd()), "Processed Data", "Finviz")  # Get the current working directory

    for filename in os.listdir(directory):

        if filename.startswith(name) and filename.endswith(".csv"):
            os.remove(os.path.join(directory, filename))
            print(f"Deleted file: {filename}")

    RawData_directory = os.path.join(os.path.dirname(os.getcwd()), "Raw Data", "Finviz")

    for filename in os.listdir(RawData_directory):

        if filename.startswith("Screener_Cigar_Butt_Investing_") and filename.endswith(".csv"):
            file_path = os.path.join(RawData_directory, filename)
            df = pd.read_csv(file_path)
            df.replace("-", "-999", inplace=True)

            criteria = {
                "Sector": {"= Healthcare": False},
                "Industry": {"= Biotechnology": True},
                "Market Cap": {"< 100000000": False, "> 100000000000": False},
                "P/E": {"< 0": False, "> 30": True},
                "P/B": {"> 1": False},
                "EPS past 5Y": {"< 0": False},
                "Sales past 5Y": {"< 0": False},
                "Insider Trans": {"< 0": True},
                "ROE": {"< -0.3": False},
                "Profit M": {"< -1": True},
                "52W Low": {"< 0.05": False},
                "Quick R": {"< 1": False},
                "All-Time High": {"> -0.7": True}
            }

            # Apply filters
            for column, conditions in criteria.items():
                if conditions:
                    for condition, status in conditions.items():
                        if status:
                            operator, value = condition.split()
                            if operator == "<":
                                df = df[df[column].astype(float) >= float(value)]
                            elif operator == ">":
                                df = df[df[column].astype(float) <= float(value)]
                            elif operator == "=":
                                df = df[df[column].astype(str) != str(value)]

            df = df.sort_values(by="52W High", ascending=True)

            sum_values_list = []
            greater_than_100000_list = []
            Profit_5_yrs_list = []

            for ticker in df['Ticker']:

                sum_values = OpenInsider(ticker, driver)
                any_profit = MarketWatch(ticker, driver)

                # Append the calculated values to the lists
                sum_values_list.append(sum_values)
                greater_than_100000_list.append(sum_values > 100000)
                Profit_5_yrs_list.append(any_profit)

            df['Insider 6M Sum'] = sum_values_list
            df['Insider 6M Sum > 100K'] = greater_than_100000_list
            df['Any profit over 5 years'] = Profit_5_yrs_list

            file_path = os.path.join(directory, name + str(date.today()) + ".csv")
            df.to_csv(file_path, index=False)

            # Filter the DataFrame for rows where 'Sum > 100000' is True
            filtered_df = df[df['Insider 6M Sum > 100K'] == True]
            file_path = os.path.join(directory, name + 'Ins100K_' + str(date.today()) + ".csv")
            filtered_df.to_csv(file_path, index=False)

            filtered_df = filtered_df[filtered_df['Any profit over 5 years'] == True]
            file_path = os.path.join(directory, name + 'Ins100K_P5Y_' + str(date.today()) + ".csv")
            filtered_df.to_csv(file_path, index=False)


            print(name + " Success!")

def Directly_Copy_From_MacroTrend_Python(ticker, period, driver, parent_folder):

    try:
        pyautogui.moveRel(1, 1)
        pyautogui.moveRel(-1, -1)

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
                    driver.quit()
                    print("EMPTY TICKER")
            # error message for ticker that doesn't exist
            else:
                print("INVALID TICKER")
    except Exception as e:
        print(e)


def Get_Result_From_MacroTrend(csv_start_with, period, driver, Renew_all):

    directory = os.path.join(os.path.dirname(os.getcwd()), "Processed Data", "Finviz")

    for filename in os.listdir(directory):
        if filename.startswith(csv_start_with) and filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            df = pd.read_csv(file_path)
            tickers = df["Ticker"].tolist()

            #Overide
            # tickers = ["AAPL", "NVDA"]

            parent_folder = os.path.dirname(os.getcwd())
            directory = os.path.join(parent_folder, "MacroTrend")


            if Renew_all:
                for ticker in tickers:
                        Directly_Copy_From_MacroTrend_Python(ticker, period, driver, parent_folder)
                        removing_ads(driver)
            else:
                for ticker in tickers:
                    if ticker in os.listdir(directory):
                        print(ticker + " Repeated")
                        continue
                    Directly_Copy_From_MacroTrend_Python(ticker, period, driver, parent_folder)
                    removing_ads(driver)
            break

def main():

    run_Finviz = False
    run_Cigar_Butt = True
    run_MacroTrend = True

    # Set Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("start-maximized")  # Start WebDriver maximized

    # Create the WebDriver with the specified options
    driver = uc.Chrome(options=chrome_options)

    if run_Finviz:

        name = "Screener_Cigar_Butt_Investing_"
        link = "https://finviz.com/screener.ashx?v=152&f=cap_microover,sh_instown_o10,sh_price_o1&ft=4&o=high52w&c=0,1,3,4,5,6,7,8,9,10,11,74,19,21,27,28,29,31,33,36,38,41,53,57,58,125,126,65"
        Get_Result_From_Finviz(driver, name, link)

        name = "Screener_Most_Shorted_Stocks_"
        link = "https://finviz.com/screener.ashx?v=152&f=sh_instown_o10,sh_short_o30&ft=3&o=-shortinterestratio&c=0,1,3,4,5,6,7,8,9,10,11,74,19,21,27,28,29,31,33,36,38,41,53,57,58,125,126,65"
        Get_Result_From_Finviz(driver, name, link)

    if run_Cigar_Butt:
        Cigar_Butt_Filter("CB_", driver)

    if run_MacroTrend:

        Renew_all = False

        csv_start_with = "CB_2024-01-30"
        period = ["A", "Q"]
        Get_Result_From_MacroTrend(csv_start_with, period, driver, Renew_all)

    try:
        driver.quit()
    except:
        pass

if __name__ == "__main__":
    main()





