import requests
import gzip
from bs4 import BeautifulSoup
from io import StringIO
from IPython import embed
from datetime import datetime
import xml.etree.ElementTree as ET
import pandas as pd

CATEGORY_ID = 2
STORE_ID = 11

MAIN_URL = f"http://prices.shufersal.co.il/FileObject/UpdateCategory?catID={CATEGORY_ID}&storeId={STORE_ID}"
CSV_FILE = f"price_track_{CATEGORY_ID}_{STORE_ID}.csv"


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
    date_td = soup.find_all("td")[1]
    current_date = datetime.strptime(date_td.text, "%m/%d/%Y %I:%M:%S %p").strftime("%Y-%m-%d")
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
            print(f"New item code: {int(code)} (name: {name}) price: {price}")
            df.loc[df.shape[0]] = [None for _ in range(len(df.columns))]
            df.at[df.shape[0]-1, "ItemCode"] = int(code)
            df.at[df.shape[0]-1, "ItemName"] = name
            df.at[df.shape[0]-1, table_date] = price
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