# Service account: rakanspreadsheet@stoked-legend-467903-m4.iam.gserviceaccount.com
from google.oauth2 import service_account
from googleapiclient.discovery import build

import os, sys

def resource_path(filename):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(__file__), filename)

SERVICE_ACCOUNT_FILE = resource_path('Gsheets_account.json')

# Create credentials using the service account file
credentials = service_account.Credentials.from_service_account_file(
    filename=SERVICE_ACCOUNT_FILE
)

# Build the Sheets API client
service_sheets = build('sheets', 'v4', credentials=credentials)

GOOGLE_SHEETS_ID = '1swKESzi1g1-k47CGhN34qVIHGY0TEqJcowkORFOWBR4'

worksheet_name = 'Sheet1!'
cell_range_insert = 'A1' 




def save_to_google_sheets(values): 
    value_range_body = {
        'majorDimension': 'ROWS',
        'values': values
    }

    service_sheets.spreadsheets().values().append(
        spreadsheetId=GOOGLE_SHEETS_ID,
        valueInputOption='USER_ENTERED',
        range=worksheet_name + cell_range_insert,
        body=value_range_body
    ).execute()

''' #Example usage:
values = [
    ['03/17', '2000', 'Insurance', 'Transportation']
]
save_to_google_sheets(values)
'''