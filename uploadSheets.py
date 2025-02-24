import pandas as pd
import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

csv_files = ['tiktok_metrics.csv', 'instagram_metrics.csv']
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'service_account.json'
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

URL_COLUMNS = ["Song Link", "Video Url", "Thumbnail Url"]

def sheet_exists(service, spreadsheet_id, sheet_name):
    sheets = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute().get('sheets', [])
    return any(sheet['properties']['title'] == sheet_name for sheet in sheets)

def create_sheet(service, spreadsheet_id, sheet_name):
    request_body = {"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=request_body).execute()

def get_row_count(service, spreadsheet_id, sheet_name):
    range_name = f"{sheet_name}!A:A"
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    return len(result.get('values', []))

def rename_columns(service, spreadsheet_id, sheet_name, new_headers):
    range_name = f"{sheet_name}!1:1"
    body = {'values': [new_headers]}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

def auto_resize_columns(service, spreadsheet_id, sheet_name):
    sheets = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute().get('sheets', [])
    sheet_id = next(sheet['properties']['sheetId'] for sheet in sheets if sheet['properties']['title'] == sheet_name)
    request_body = {"requests": [{"autoResizeDimensions": {"dimensions": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0}}}]}
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=request_body).execute()

def convert_urls_to_hyperlinks(df, headers):
    for col in URL_COLUMNS:
        if col in headers and col in df.columns:
            display_text = col.replace(" Url", "").replace(" Link", "") 
            df[col] = df[col].apply(lambda url: f'=HYPERLINK("{url}", "{display_text}")' if pd.notna(url) else "")
    return df

def upload_csv_to_sheet(service, spreadsheet_id, csv_file):
    print(f"Starting upload for {csv_file}...")
    
    sheet_name = os.path.splitext(csv_file)[0].replace('_', ' ').title()
    df = pd.read_csv(csv_file)

    new_headers = [
        "Id", "Description", "Likes", "Comments", "Views", "Shares", "Reposts",
        "Music Title", "Music Artist", "Song Link", "Song Id", "Sound Id", "UGC",
        "Owner Username", "Owner Nickname", "Owner Verified", "Video Url",
        "Thumbnail Url", "Timestamp"
    ]

    df = convert_urls_to_hyperlinks(df, new_headers)

    # Convert all numbers to string without scientific notation
    for col in df.select_dtypes(include=['float64', 'int64']).columns:
        df[col] = df[col].apply(lambda x: f"{x:.0f}")

    values = [new_headers] + df.values.tolist()

    if not sheet_exists(service, spreadsheet_id, sheet_name):
        create_sheet(service, spreadsheet_id, sheet_name)
    
    row_count = get_row_count(service, spreadsheet_id, sheet_name)
    
    if row_count == 0:
        range_name = f"{sheet_name}!A1"
        body = {'values': [new_headers] + df.values.tolist()}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
    else:
        range_name = f"{sheet_name}!A{row_count + 1}"
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body={'values': df.values.tolist()}
        ).execute()

    auto_resize_columns(service, spreadsheet_id, sheet_name)
    print(f"✅ Successfully uploaded data to '{sheet_name}'.")

    # Delete the marker file after successful upload
    try:
        os.remove(f"{csv_file}_uploaded")
        print(f"Marker file for {csv_file} deleted.")
    except Exception as e:
        print(f"Error deleting marker file: {e}")

# Check for existing files and upload if one exists and doesn't have an uploaded marker
existing_files = [file for file in csv_files if os.path.exists(file) and not os.path.exists(f"{file}_uploaded")]

if len(existing_files) == 1:
    csv_file = existing_files[0]
    upload_csv_to_sheet(service, SPREADSHEET_ID, csv_file)
else:
    print("Error: Either no file or multiple files found. Please ensure only one of 'tiktok_metrics.csv' or 'instagram_metrics.csv' exists.")