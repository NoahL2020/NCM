from bs4 import BeautifulSoup
import pandas as pd
from collections import deque
import http.client, urllib
from IPython.display import display
import time 
from curl_cffi import requests as crequests
import requests
from datetime import datetime, timezone, timedelta

refreshtime = 40
fail_sleep = 20
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
                    itemstring = f"Description: {info['Description']}\nQuantity Available: {info['Qty Avail']}\nPackage Info: {info['Pkg. Info']}\nCost: {info['$']}\n\n"
                    message += itemstring
                message += "https://eharvest.acfb.org/InventoryView.aspx"
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
        current_time = time.time()

        # Convert the time to a datetime object in UTC
        utc_time = datetime.fromtimestamp(current_time, tz=timezone.utc)

        # Define the EST timezone (UTC-5 hours)
        est_timezone = timezone(timedelta(hours=-5))

        # Convert UTC time to EST time
        est_time = utc_time.astimezone(est_timezone)

        # Format the EST time as hours, minutes, and seconds
        formatted_est_time = est_time.strftime('%I:%M:%S %p')
        print(f"Fail at: {formatted_est_time}")
        print(f"Error: {e}")
        print("Relogging in.")

        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://eharvest.acfb.org',
            'priority': 'u=1, i',
            'referer': 'https://eharvest.acfb.org/Login.aspx',
            'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'x-microsoftajax': 'Delta=true',
            'x-requested-with': 'XMLHttpRequest',
        }

        data = {
            'RadScriptManager1': 'btnLoginPanel|btnLogin',
            'RadStyleSheetManager1_TSSM': ';Telerik.Web.UI, Version=2021.3.914.45, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en-US:bd4f5d20-e2f4-41b1-99ef-02ee4a064af0:45085116:27c5704c:505983de:d7e35272:959c7879:ba1b8630:3e0dfe6c;Telerik.Web.UI.Skins, Version=2021.3.914.45, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en-US:bd68d779-31cd-457f-adc8-06e8ac5469a8:a7b34603:d237931b:a4a302e4',
            'RadScriptManager1_TSM': ';;System.Web.Extensions, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35:en-US:18f1b484-bbc5-4e2e-8ca4-477603537f34:ea597d4b:b25378d2;Telerik.Web.UI:en-US:bd4f5d20-e2f4-41b1-99ef-02ee4a064af0:16e4e7cd:f7645509:22a6274a:ed16cbdc:88144a7a:33715776:b7778d6c:24ee1bba:6d43f6d9:874f8ea2:c128760b:b2e06756:19620875:92fe8ea0:fa31b949:4877f69a:f46195d3:490a9d4e:11e117d7',
            '__EVENTTARGET': 'btnLogin',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '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',
            '__VIEWSTATEGENERATOR': 'C2EE9ABB',
            '__EVENTVALIDATION': 'DFsdWOkpvy88LFn9erpxveplqIdazqPAhwT70RvuOqbgPBvfku9LztHbnlU+e20Oh34qheWtd34Zctg4GWBkLydfxARpGosIQmEey/s/hsWv9NLE1G3BFV4iuOjBMnO/qz9XD+87GNGXXsDQBAORfT+HtiR338P85etyfEUMsLPQmRZBDGMxfFBejLMsfGlYyEvW7KrbzS4BICEYWNEqi29/HDQ0fe+AaGO7YKN7VVz21YAP8aEMabd1557mVjIWQGPJ7WpXxsQe3iaUNqh+L4b9f8fo0F/5oj890gCVaoyatT5PUbL/0FpMKNDcWeVsZlB1BYExa6IDg0wmlBrabGzCQzECbD8SQ4GLMS4P+VI=',
            'txtUserName': 'shirley@ourncm.org',
            'txtUserName_ClientState': '{"enabled":true,"emptyMessage":"Enter Email Address/Username","validationText":"shirley@ourncm.org","valueAsString":"shirley@ourncm.org","lastSetTextBoxValue":"shirley@ourncm.org"}',
            'txtPasswordMask': 'Enter Password',
            'txtPasswordMask_ClientState': '{"enabled":true,"emptyMessage":"Enter Password","validationText":"","valueAsString":"","lastSetTextBoxValue":"Enter Password"}',
            'txtPassword': 'nwqgj48',
            'txtPassword_ClientState': '{"enabled":true,"emptyMessage":"","validationText":"nwqgj48","valueAsString":"nwqgj48","lastSetTextBoxValue":"nwqgj48"}',
            'btnLogin_ClientState': '{"text":"LOG IN","value":"","checked":false,"target":"","navigateUrl":"","commandName":"","commandArgument":"","autoPostBack":true,"selectedToggleStateIndex":0,"validationGroup":null,"readOnly":false,"primary":false,"enabled":true}',
            'winForgotPassword$C$txtEmailAddress': '',
            'winForgotPassword_C_txtEmailAddress_ClientState': '{"enabled":true,"emptyMessage":"","validationText":"","valueAsString":"","lastSetTextBoxValue":""}',
            'winForgotPassword$C$captchaEmail$CaptchaTextBox': '',
            'winForgotPassword_C_captchaEmail_ClientState': '',
            'winForgotPassword_C_btnUpdatePassword_ClientState': '{"text":"Reset Password","value":"","checked":false,"target":"","navigateUrl":"","commandName":"","commandArgument":"","autoPostBack":true,"selectedToggleStateIndex":0,"validationGroup":null,"readOnly":false,"primary":false,"enabled":true}',
            'winForgotPassword_C_btnCancelPassword_ClientState': '{"text":"Close","value":"","checked":false,"target":"","navigateUrl":"","commandName":"","commandArgument":"","autoPostBack":false,"selectedToggleStateIndex":0,"validationGroup":null,"readOnly":false,"primary":false,"enabled":true}',
            'winForgotPassword_ClientState': '',
            '__ASYNCPOST': 'true',
            'RadAJAXControlID': 'RadAjaxManager1',
        }

        response = requests.post('https://eharvest.acfb.org/Login.aspx', cookies=cookies, headers=headers, data=data)
        print(f"Login Response: {response.text}")

    if(not failure):
        time.sleep(refreshtime)
    elif(failure and failcount < maxfailcount):
        time.sleep(fail_sleep)
    else:
        failcount = 0 
        failure = False
        time.sleep(refreshtime)