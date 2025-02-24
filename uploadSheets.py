import pandas as pd
import os
import time
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
    print(f"🚀 Starting upload for {csv_file}...")
    
    sheet_name = os.path.splitext(csv_file)[0].replace('_', ' ').title()
    df = pd.read_csv(csv_file)

    new_headers = [
        "Id", "Description", "Likes", "Comments", "Views", "Shares", "Reposts",
        "Music Title", "Music Artist", "Song Link", "Song Id", "Sound Id", "UGC",
        "Owner Username", "Owner Nickname", "Owner Verified", "Video Url",
        "Thumbnail Url", "Timestamp"
    ]

    df = convert_urls_to_hyperlinks(df, new_headers)

    # Convert numbers to strings (no scientific notation)
    for col in df.select_dtypes(include=['float64', 'int64']).columns:
        df[col] = df[col].apply(lambda x: f"{x:.0f}")

    if not sheet_exists(service, spreadsheet_id, sheet_name):
        create_sheet(service, spreadsheet_id, sheet_name)
        print(f"✅ Created new sheet: '{sheet_name}'.")

    row_count = get_row_count(service, spreadsheet_id, sheet_name)
    range_name = f"{sheet_name}!A{row_count + 1}"
    values = df.values.tolist()

    body = {'values': [new_headers] + values} if row_count == 0 else {'values': values}
    print(f"{'Uploading with headers' if row_count == 0 else f'Appending data to {sheet_name} starting at row {row_count + 1}'}...")

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1" if row_count == 0 else range_name,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

    auto_resize_columns(service, spreadsheet_id, sheet_name)
    print(f"✅ Successfully uploaded data to '{sheet_name}'.")

    # Immediately create the marker file to avoid waiting
    marker_file = f"{csv_file}_uploaded"
    try:
        with open(marker_file, 'w') as f:
            f.write("Uploaded")
        print(f"✅ Marker file created: {marker_file}")
    except Exception as e:
        print(f"❌ Error creating marker file: {e}")

    # Cleanup: delete the CSV file after the marker file is handled
    try:
        os.remove(csv_file)
        print(f"🗑️ Deleted CSV file: {csv_file}")
    except Exception as e:
        print(f"❌ Error deleting CSV file: {e}")
    
    # After everything is completed, delete the marker file
    try:
        os.remove(marker_file)
        print(f"🗑️ Deleted marker file: {marker_file}")
    except Exception as e:
        print(f"❌ Error deleting marker file: {e}")

        
# Main process
existing_files = [file for file in csv_files if os.path.exists(file)]

if len(existing_files) == 1:
    csv_file = existing_files[0]
    marker_file = f"{csv_file}_uploaded"

    if not os.path.exists(marker_file):
        upload_csv_to_sheet(service, SPREADSHEET_ID, csv_file)
    else:
        print(f"⚠️ {csv_file} has already been uploaded. To re-upload, delete the marker file '{marker_file}'.")