from bs4 import BeautifulSoup
import pandas as pd
from collections import deque
import http.client, urllib
from IPython.display import display
import time 
from curl_cffi import requests as crequests

refreshtime = 120
fail_sleep = 100
maxfailcount = 2

chat_id = "a94osfnfyb8fb3hswqrs9ft2z9tq99"
chat_token = "uvmzvi8phoysi7r4pt8bmzzjxbpf6y"

cookies = {
    'optimizelyEndUserId': 'oeu1724175484800r0.2073426791383468',
    'ASP.NET_SessionId': 'gxrnlx1hajirovv05jwu1r21',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'priority': 'u=0, i',
    'referer': 'https://eharvest.acfb.org/Default.aspx',
    'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
}

def filter_ids(df, existing_ids):
    return {index: row for index, row in df.iterrows() if (row['Item #'] + '***' + row['Description']) not in existing_ids}


existing_row_info = []
firstrun = True

while(True):

    failcount = 0

    try:
        response = crequests.get('https://eharvest.acfb.org/InventoryView.aspx', headers=headers, cookies=cookies, timeout = 5)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'grdData_ctl00'})  # Locate the table by ID
        
        # Extract the table rows
        rows = table.find_all('tr')
        
        # Initialize a list to hold the row data
        table_data = []
        
        # Loop through each row and extract the data
        for row in rows[1:]:  # Skip the header row
            cells = row.find_all('td')
            row_data = [
                cells[0].text.strip(),  # Category
                cells[1].text.strip(),  # Item #
                cells[2].text.strip(),  # Description
                cells[3].text.strip(),  # Pkg. Info
                cells[4].text.strip(),  # Storage
                cells[5].text.strip(),  # Qty Avail
                cells[6].text.strip(),  # Qty Limit
                cells[7].text.strip(),  # Qty Min
                cells[8].text.strip(),  # Price ($)
                cells[9].text.strip()   # Cs/Pallet
            ]
            table_data.append(row_data)
        
        # Create a dataframe
        columns = ['Product Category', 'Item #', 'Description', 'Pkg. Info', 'Storage', 'Qty Avail', 'Qty Limit', 'Qty Min', '$', 'Cs/Pallet']
        df = pd.DataFrame(table_data, columns=columns)
        if(not firstrun):
            reduced_dict = filter_ids(df, existing_row_info)
            if(reduced_dict):
                message = "<b> NEW ITEMS ADDED </b>\n\n"
                for ind, info in reduced_dict.items():
                    itemstring = f"Description: {info['Description']}\nQuantity Available: {info['Qty Avail']}\nCost: {info['$']}\n\n"
                    message += itemstring
                message = message[0:-2]
                conn = http.client.HTTPSConnection("api.pushover.net:443")
                conn.request("POST", "/1/messages.json",
                urllib.parse.urlencode({
                    "token": chat_id,
                    "user": chat_token,
                    "message": message,
                    "html": 1
                }), { "Content-type": "application/x-www-form-urlencoded" })
                conn.getresponse()
    
        existing_row_info= (df['Item #'] + '***' + df['Description']).to_list()
        
        firstrun = False
        failure = False
        failcount = 0
        
    except Exception as e:
        failure = True
        failcount += 1
        print(f"Response: {response.text}")
        print(f"Error: {e}")

    if(not failure):
        time.sleep(refreshtime)
    elif(failure and failcount < maxfailcount):
        time.sleep(fail_sleep)
    else:
        failcount = 0 
        failure = False
        time.sleep(refreshtime)