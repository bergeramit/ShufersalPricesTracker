import requests
import gzip
from bs4 import BeautifulSoup
from io import StringIO
from datetime import datetime
import xml.etree.ElementTree as ET
import pandas as pd

CATEGORY_ID=2
STORE_ID=11

MAIN_URL = f"http://prices.shufersal.co.il/FileObject/UpdateCategory?catID={CATEGORY_ID}&storeId={STORE_ID}"
CSV_FILE = f"/Users/amitberger/Desktop/HST/ShufersalPricesTracker/price_track_{CATEGORY_ID}_{STORE_ID}.csv"

def extrace_field(et, field):
    obj = et.find(field)
    if obj is not None:
        return obj.text
    return ""

def get_current_csv_table():
    res = requests.get(MAIN_URL)
    soup = BeautifulSoup(res.text, "html.parser")
    for link in soup.find_all("a"):
        if "http://pricesprodpublic.blob.core.windows.net" in link.attrs["href"]:
            target = link.attrs["href"]
            break

    res = requests.get(target)
    raw_csv = gzip.decompress(res.content)
    table = ET.parse(StringIO(raw_csv.decode('utf-8'))).getroot()
    current_date = table.find("Items").find("Item").find("PriceUpdateDate").text
    current_date = datetime.strptime(current_date, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d")
    return table, current_date


def update_table():
    df = pd.read_csv(CSV_FILE, index_col=0)
    print(df)
    table, table_date = get_current_csv_table()
    
    # New column
    df[table_date] = [None for _ in range(len(df.index))]

    for item in table.find("Items").findall("Item"):
        name = extrace_field(item, "ItemName")
        price = extrace_field(item, "ItemPrice")
        code = extrace_field(item, "ItemCode")
        current_index = df.index[df['ItemCode'] == int(code)]
        try:
            df.at[current_index[0], table_date] = price
        except IndexError:
            print(f"New item code: {int(code)} (name: {name})")
            continue

    df.to_csv(CSV_FILE)


def new_table():
    table, table_date = get_current_csv_table()

    df = {"ItemName": [], "ItemCode": [], table_date: []}
    for item in table.find("Items").findall("Item"):
        df["ItemName"].append(extrace_field(item, "ItemName"))
        df[table_date].append(extrace_field(item, "ItemPrice"))
        df["ItemCode"].append(extrace_field(item, "ItemCode"))

    table = pd.DataFrame(df, columns=["ItemName", "ItemCode", table_date])
    table.to_csv(CSV_FILE)


if __name__ == "__main__":
    try:
        update_table()
    except FileNotFoundError:
        new_table()