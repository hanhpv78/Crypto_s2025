import os
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

def get_google_sheets_client():
    """Kết nối Google Sheets using Streamlit secrets"""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        if not hasattr(st, 'secrets') or 'gcp_service_account' not in st.secrets:
            st.error("❌ No Google credentials found in secrets")
            return None
        
        service_account_info = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(
            service_account_info, 
            scopes=scopes
        )
        
        return gspread.authorize(credentials)
        
    except Exception as e:
        st.error(f"❌ Google Sheets connection failed: {str(e)}")
        return None

def get_tier1_realtime_data(spreadsheet_url):
    """Load data from Tier1_Real_Time sheet"""
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
            
        # Mở spreadsheet
        sheet = client.open_by_url(spreadsheet_url)
        
        # Tìm sheet Tier1_Real_Time
        try:
            worksheet = sheet.worksheet("Tier1_Real_Time")
        except gspread.WorksheetNotFound:
            st.error("❌ Sheet 'Tier1_Real_Time' not found")
            return pd.DataFrame()
        
        # Lấy data
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
            st.warning("⚠️ No data found in Tier1_Real_Time sheet")
            return pd.DataFrame()
            
        st.success(f"✅ Loaded {len(df)} rows from Tier1_Real_Time sheet")
        return df
        
    except Exception as e:
        st.error(f"❌ Failed to load from Tier1_Real_Time: {str(e)}")
        return pd.DataFrame()

def append_to_tier1_realtime(new_data, spreadsheet_url):
    """Append new data to Tier1_Real_Time sheet"""
    try:
        client = get_google_sheets_client()
        if client is None:
            return False
            
        sheet = client.open_by_url(spreadsheet_url)
        worksheet = sheet.worksheet("Tier1_Real_Time")
        

        # Convert data to string format
        if isinstance(new_data, pd.DataFrame):
            # Convert all columns to string
            new_data_clean = new_data.copy()
            for col in new_data_clean.columns:
                new_data_clean[col] = new_data_clean[col].astype(str)
            values = new_data_clean.values.tolist()
        else:
            # Convert each value to string
            values = [[str(cell) for cell in row] for row in new_data]
            
        # Append data
        worksheet.append_rows(values)
        st.success(f"✅ Appended {len(values)} rows to Tier1_Real_Time")
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to append data: {str(e)}")
        return False

def update_tier1_realtime_full(df, spreadsheet_url):
    """Update entire Tier1_Real_Time sheet with new data"""
    try:
        # Kiểm tra input
        if not isinstance(df, pd.DataFrame):
            st.error(f"❌ Expected DataFrame, got {type(df)}")
            return False
            
        if df.empty:
            st.warning("⚠️ DataFrame is empty")
            return False
        
        client = get_google_sheets_client()
        if client is None:
            return False
            
        sheet = client.open_by_url(spreadsheet_url)
        worksheet = sheet.worksheet("Tier1_Real_Time")
        
        # Clear existing data
        worksheet.clear()
        
        # Convert DataFrame to safe format
        df_clean = df.copy()
        
        # Handle NaN values and convert to string
        df_clean = df_clean.fillna('')
        
        # Convert all values to string safely
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str)
        
        # Prepare data
        headers = df_clean.columns.tolist()
        rows = df_clean.values.tolist()
        
        # Final safety check - ensure all are strings
        clean_headers = [str(h) for h in headers]
        clean_rows = []
        for row in rows:
            clean_row = [str(cell) for cell in row]
            clean_rows.append(clean_row)
        
        # Combine
        all_data = [clean_headers] + clean_rows
        
        # Update sheet
        worksheet.update('A1', all_data)
        st.success(f"✅ Updated Tier1_Real_Time with {len(df)} rows")
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to update sheet: {str(e)}")
        import traceback
        st.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def append_live_data_to_tier1(new_df, spreadsheet_url):
    """Append new live data to Tier1_Real_Time sheet (không xóa data cũ)"""
    try:
        client = get_google_sheets_client()
        if client is None:
            return False
            
        sheet = client.open_by_url(spreadsheet_url)
        worksheet = sheet.worksheet("Tier1_Real_Time")
        
        if new_df.empty:
            st.warning("⚠️ No new data to append")
            return False
        
        # Convert to string format
        df_clean = new_df.copy()
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('').astype(str)
        
        # Get data as rows (không include headers vì đã có trong sheet)
        rows = df_clean.values.tolist()
        
        # Convert to strings
        clean_rows = []
        for row in rows:
            clean_row = [str(cell) for cell in row]
            clean_rows.append(clean_row)
        
        # Append to sheet (không xóa data cũ)
        worksheet.append_rows(clean_rows)
        st.success(f"✅ Appended {len(clean_rows)} new rows to Tier1_Real_Time")
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to append data: {str(e)}")
        return False

# Backward compatibility - giữ tên cũ
def get_universe_data(spreadsheet_url):
    """Alias for get_tier1_realtime_data"""
    return get_tier1_realtime_data(spreadsheet_url)

def export_tier1_to_existing_gsheet(data, spreadsheet_url):
    """Alias for update_tier1_realtime_full"""
    return update_tier1_realtime_full(data, spreadsheet_url)

def load_tier1_universe_from_gsheet(spreadsheet_url):
    """Alias for get_tier1_realtime_data"""
    return get_tier1_realtime_data(spreadsheet_url)

def export_tier1_to_existing_gsheet(spreadsheet_url, data_to_export):
    """Append new data to Google Sheets with duplicate detection"""
    try:
        client = get_google_sheets_client()
        if client is None:
            return False
            
        sheet = client.open_by_url(spreadsheet_url)
        worksheet = sheet.worksheet("Tier1_Real_Time")
        
        # Get existing data
        existing_data = worksheet.get_all_records()
        existing_df = pd.DataFrame(existing_data)
        
        # New data
        new_df = pd.DataFrame(data_to_export[1:], columns=data_to_export[0])
        
        if existing_df.empty:
            # Empty sheet, add headers + all data
            all_data = [data_to_export[0]] + data_to_export[1:]
            worksheet.update(all_data)
            st.success(f"✅ Added {len(data_to_export[1:])} rows to empty sheet")
        else:
            # Check for duplicates (by symbol và timestamp)
            if 'Symbol' in new_df.columns and 'Last_Updated' in new_df.columns:
                # Filter out duplicates
                new_df['timestamp_check'] = new_df['Last_Updated'].astype(str)
                existing_df['timestamp_check'] = existing_df['Last_Updated'].astype(str)
                
                # Find truly new rows
                merged = new_df.merge(
                    existing_df[['Symbol', 'timestamp_check']], 
                    on=['Symbol', 'timestamp_check'], 
                    how='left', 
                    indicator=True
                )
                truly_new = merged[merged['_merge'] == 'left_only']
                
                if not truly_new.empty:
                    # Remove merge column
                    truly_new = truly_new.drop(['_merge', 'timestamp_check'], axis=1)
                    
                    # Append only new rows
                    new_rows = truly_new.values.tolist()
                    worksheet.append_rows(new_rows)
                    
                    st.success(f"✅ Appended {len(new_rows)} new rows (filtered duplicates)")
                    st.info(f"📊 Skipped {len(new_df) - len(new_rows)} duplicate rows")
                else:
                    st.warning("⚠️ All data already exists - no new rows added")
            else:
                # No duplicate detection, just append all
                new_rows = new_df.values.tolist()
                worksheet.append_rows(new_rows)
                st.success(f"✅ Appended {len(new_rows)} rows (no duplicate check)")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Append failed: {e}")
        return False
