# %% [markdown]
# # Surf Web Scraping

# %%
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os.path
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# %% [markdown]
# ### Neah Bay Buoy

# %%
url = "https://www.ndbc.noaa.gov/station_page.php?station=46087"  # Replace with the URL of the website you want to scrape
response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

# Extract specific information from the HTML
title = soup.title.text  # Extract the page title
tables = soup.find_all("table")

# Print the extracted information
print("Title:", title)

# %%
rows = tables[5].find_all("tr")
del rows[0]

# %%
html_rows = rows

html_table = f'<table>{html_rows}</table>'

soup = BeautifulSoup(html_table, 'html.parser')
table = soup.find('table')

# %%
data = []
for row in table.find_all('tr'):
    date_tag = row.find('span', class_='nowrap')
    date = date_tag.get_text(strip=True)
    time = date_tag.find_next_sibling('span').get_text(strip=True)
    values = [td.get_text(strip=True) for td in row.find_all('td')]
    data.append({'Date': date, 'Time': time, 'Values': values})

# %%
date = []
date_format = "%Y-%m-%d"
time = []
time_format = "%I:%M %p"
wave_height = []
period = []
direction = []

for i in range(len(data)):
    date.append(datetime.strptime(data[i]['Date'],date_format))
    time.append(datetime.strptime(data[i]['Time'],time_format).time())
    wave_height.append(float(data[i]['Values'][0]))
    period.append(float(data[i]['Values'][2]))
    direction.append(data[i]['Values'][3]) 

# %%
df2 = pd.DataFrame({'Date':date,
                    'Time':time,
                    'Wave Height [ft]':wave_height,
                    'Period [s]':period,
                    'Swell Direction':direction})

# %%
rows = tables[3].find_all("tr")
del rows[0]

html_rows = rows

html_table = f'<table>{html_rows}</table>'

soup = BeautifulSoup(html_table, 'html.parser')
table = soup.find('table')

data = []
for row in table.find_all('tr'):
    date_tag = row.find('span', class_='nowrap')
    date = date_tag.get_text(strip=True)
    time = date_tag.find_next_sibling('span').get_text(strip=True)
    values = [td.get_text(strip=True) for td in row.find_all('td')]
    data.append({'Date': date, 'Time': time, 'Values': values})


# %%
date = []
date_format = "%Y-%m-%d"
time = []
time_format = "%I:%M %p"
wind_direction = []
wind_speed = []

for i in range(len(data)):
    if data[i]['Values'][1] == '-':
        continue 
    date.append(datetime.strptime(data[i]['Date'],date_format))
    time.append(datetime.strptime(data[i]['Time'],time_format).time())
    wind_direction.append(data[i]['Values'][0])
    wind_speed.append((float(data[i]['Values'][1])*1.852))

# %%
df3 = pd.DataFrame({'Date':date,
                    'Time':time,
                    'Wind Direction':wind_direction,
                    'Wind Speed [kts]':wind_speed})

# %%
# Convert Date to string format in case it's already datetime
df3["Date"] = df3["Date"].astype(str)
df2["Date"] = df2["Date"].astype(str)

# Convert Time to string format if it's not already
df3["Time"] = df3["Time"].astype(str)
df2["Time"] = df2["Time"].astype(str)


# Convert Date and Time columns to a single Datetime column in both dataframes
df3["Datetime"] = pd.to_datetime(df3["Date"] + " " + df3["Time"])
df2["Datetime"] = pd.to_datetime(df2["Date"] + " " + df2["Time"])

# Merge dataframes on the Datetime column, keeping only matching rows
merged_df = pd.merge(df3, df2, on="Datetime", how="inner")

# Move the Datetime column to the first position and remove redundant Date and Time columns
columns_to_keep = ["Datetime", "Wave Height [ft]", "Swell Direction", "Period [s]", "Wind Direction", "Wind Speed [kts]"]
merged_df = merged_df[columns_to_keep].round(1)

# %%
buoy = merged_df

# %%
now = buoy.iloc[0]

# %%
print(now)

# %% [markdown]
# ##### Check conditions and send email

# %%
# If modifying scopes, delete the token.json file
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def gmail_send_message():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no valid credentials, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    # Create the message
    message = EmailMessage()
    message.set_content("This is an automated surf alert!"+str(now))
    message['To'] = 'neahbuoy@gmail.com'
    message['From'] = 'neahbuoy@gmail.com'
    message['Subject'] = 'Surf’s up!'

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {'raw': encoded_message}

    send_message = service.users().messages().send(userId='me', body=create_message).execute()
    print(f"✅ Message sent! ID: {send_message['id']}")

if __name__ == "__main__":
    if now[1] > 10 and now[3] >= 15:
        gmail_send_message()



