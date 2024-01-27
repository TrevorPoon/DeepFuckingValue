import yfinance as yf
import numpy as np
from bokeh.plotting import figure, show, output_file
import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from bokeh.models import Range1d, LogAxis, LinearAxis, NumeralTickFormatter
from bokeh.layouts import gridplot
from bokeh.models import HoverTool
from bokeh.models import DataTable, TableColumn
from bokeh.models.widgets import HTMLTemplateFormatter
from bokeh.models import ColumnDataSource
from tabulate import tabulate
import os
from bokeh.models.widgets import Div


# Prompt the user for the ticker symbol

def convert_to_numeric(value):
    try:
        return pd.to_numeric(value)
    except (TypeError, ValueError):
        return value

def OpenInsider(ticker, driver):

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
            "Time Period": "1 Month",
            "Distinct Names Bought":
                filtered_data[(filtered_data["Trade Date"] > one_month_ago) & (filtered_data["Value"] > 0)][
                    "Insider Name"].nunique(),
            "Distinct Names Sold":
                filtered_data[(filtered_data["Trade Date"] > one_month_ago) & (filtered_data["Value"] < 0)][
                    "Insider Name"].nunique(),
            "Total Bought": filtered_data[(filtered_data["Trade Date"] > one_month_ago) & (filtered_data["Value"] > 0)][
                "Value"].sum(),
            "Total Sold": filtered_data[(filtered_data["Trade Date"] > one_month_ago) & (filtered_data["Value"] < 0)][
                "Value"].sum()
        }

        six_months_ago = pd.to_datetime(str(datetime.today() - timedelta(days=180)).split(" ")[0])
        summary_6m = {
            "Time Period": "6 Months",
            "Distinct Names Bought":
                filtered_data[(filtered_data["Trade Date"] > six_months_ago) & (filtered_data["Value"] > 0)][
                    "Insider Name"].nunique(),
            "Distinct Names Sold":
                filtered_data[(filtered_data["Trade Date"] > six_months_ago) & (filtered_data["Value"] < 0)][
                    "Insider Name"].nunique(),
            "Total Bought":
                filtered_data[(filtered_data["Trade Date"] > six_months_ago) & (filtered_data["Value"] > 0)][
                    "Value"].sum(),
            "Total Sold": filtered_data[(filtered_data["Trade Date"] > six_months_ago) & (filtered_data["Value"] < 0)][
                "Value"].sum()
        }

        two_years_ago = pd.to_datetime(str(datetime.today() - timedelta(days=730)).split(" ")[0])
        summary_2yrs = {
            "Time Period": "2 Years",
            "Distinct Names Bought":
                filtered_data[(filtered_data["Trade Date"] > two_years_ago) & (filtered_data["Value"] > 0)][
                    "Insider Name"].nunique(),
            "Distinct Names Sold":
                filtered_data[(filtered_data["Trade Date"] > two_years_ago) & (filtered_data["Value"] < 0)][
                    "Insider Name"].nunique(),
            "Total Bought": filtered_data[(filtered_data["Trade Date"] > two_years_ago) & (filtered_data["Value"] > 0)][
                "Value"].sum(),
            "Total Sold": filtered_data[(filtered_data["Trade Date"] > two_years_ago) & (filtered_data["Value"] < 0)][
                "Value"].sum()
        }
        # Create a DataFrame with the summary statistics
        summary_df = pd.DataFrame([summary_1m, summary_6m, summary_2yrs])

        # Rearrange the columns
        summary_df = summary_df[
            ["Time Period", "Distinct Names Bought", "Total Bought", "Distinct Names Sold", "Total Sold"]]

        summary_df["Total Bought"] = summary_df["Total Bought"].apply(
            lambda x: f"{x / 10 ** 3:.1f}k" if abs(x) < 10 ** 6 else f"{x / 10 ** 6:.1f}M" if abs(
                x) < 10 ** 9 else f"{x / 10 ** 9:.1f}B" if abs(x) < 10 ** 12 else f"{x / 10 ** 12:.1f}T")

        summary_df["Total Sold"] = summary_df["Total Sold"].apply(
            lambda x: f"{x / 10 ** 3:.1f}k" if abs(x) < 10 ** 6 else f"{x / 10 ** 6:.1f}M" if abs(
                x) < 10 ** 9 else f"{x / 10 ** 9:.1f}B" if abs(x) < 10 ** 12 else f"{x / 10 ** 12:.1f}T")


        columns = [
            TableColumn(field="Time Period", title="Time Period"),
            TableColumn(field="Distinct Names Bought", title="Names Bought"),
            TableColumn(field="Total Bought", title="Total Bought"),
            TableColumn(field="Distinct Names Sold", title="Names Sold"),
            TableColumn(field="Total Sold", title="Total Sold")
        ]

        UI_table = DataTable(source=ColumnDataSource(summary_df), columns=columns, index_position=None, width = 400)

        return OpenInsider_Data, UI_table

    except Exception as e:
        print(f"Error: {str(e)}")

def Insider_Buying_graph(ticker_symbol, OpenInsider_Data):
    try:
        # Fetch historical data using yfinance for the past 10 years
        data = yf.download(ticker_symbol, period="4y")

        # Create a Bokeh figure
        p = figure(title=f"Insider Buying for {ticker_symbol}", x_axis_label="Date", x_axis_type="datetime", height=300)

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

def Ten_Yrs_Price_Movement_graph(ticker_symbol):

    try:
        # Fetch historical data using yfinance for the past 10 years
        data = yf.download(ticker_symbol, period="10y")

        # Create a Bokeh figure
        p = figure(title=f"10 Yrs Price Movement for {ticker_symbol}", x_axis_label="Date", x_axis_type="datetime", y_axis_type="log", height=300)

        # Plot the closing prices on the primary y-axis
        line = p.line(data.index, data["Close"], line_width=2, color="blue")

        # Set the range of the primary y-axis
        p.y_range = Range1d(start=data["Close"].min() * 0.9, end=data["Close"].max() * 1.1)

        hover_tool = HoverTool(renderers=[line], tooltips=[("Price", "@y")], mode="vline")
        p.add_tools(hover_tool)

        return p

    except Exception as e:
        print(f"Error: {str(e)}")

def annual_financial_table(ticker, period):

    folder_path = os.path.join(os.getcwd(), "../MacroTrend")
    ticker_folder = None
    ticker_file = None

    # Find folder with ticker name
    for folder_name in os.listdir(folder_path):
        if folder_name.upper() == ticker.upper():
            ticker_folder = folder_name
            break

    if ticker_folder is None:
        print(f"Folder for ticker '{ticker}' not found.")
        return None

    # Find file with suffix "_A"
    ticker_folder_path = os.path.join(folder_path, ticker_folder)
    for file_name in os.listdir(ticker_folder_path):
        if file_name.endswith("_" + period[0] +".xlsx"):
            ticker_file = file_name
            break

    if ticker_file is None:
        print(f"File with suffix '_A' not found in folder '{ticker_folder}'.")
        return None

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
    df = df.apply(lambda x: pd.to_numeric(x).apply(
        lambda y: f'{y / 1000:.1f}K' if abs(float(y)) >= 1e3 else f'{y:.1f}'))

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

    # Convert DataFrame to Bokeh DataTable
    columns = [TableColumn(field=col, title=col) for col in df.columns]
    source = ColumnDataSource(df)
    full_fs = DataTable(source=source, columns=columns, width = 600)

    source = ColumnDataSource(essence_data)
    essence_fs = DataTable(source=source, columns=columns, width = 600)

    return full_fs, essence_fs

def main():

    # ticker_symbol = input("Enter the ticker symbol: ").upper()
    # Set Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Start WebDriver maximized



    # Create the WebDriver with the specified options
    driver = webdriver.Chrome(options=chrome_options)

    ticker = "GLT"

    OpenInsider_Data, UI_OpenInsider_Table = OpenInsider(ticker, driver)
    insider_graph = Insider_Buying_graph(ticker, OpenInsider_Data)
    Ten_Yrs_price_movement_graph = Ten_Yrs_Price_Movement_graph(ticker)
    UI_full_annual_fs, UI_essence_annual_fs = annual_financial_table(ticker, "Annual")
    UI_full_quarter_fs, UI_essence_quarter_fs = annual_financial_table(ticker, "Quarter")

    # Create the grid layout
    grid = gridplot([[Ten_Yrs_price_movement_graph, insider_graph, UI_OpenInsider_Table,UI_full_annual_fs, UI_full_quarter_fs],
                     [UI_essence_annual_fs, UI_essence_quarter_fs]])

    grid.sizing_mode = 'scale_both'

    show(grid)

if __name__ == "__main__":
    main()