import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Path to your credentials file
credentials_file = "inventoryentry-380f630ca6cb.json"

# Define the scope
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

# Authenticate using the credentials file
creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
client = gspread.authorize(creds)

# Open the Google Sheet using the URL provided
sheet_url = "https://docs.google.com/spreadsheets/d/1Fcflq4wRjSzzmz77KnVk1PL7CYbbohfyFuYsf_Ax6JQ/edit?usp=sharing"
sheet = client.open_by_url(sheet_url)
worksheet = sheet.get_worksheet(0)

# Data
tabel = st.text_input("gsheet", "https://docs.google.com/spreadsheets/d/1Fcflq4wRjSzzmz77KnVk1PL7CYbbohfyFuYsf_Ax6JQ/edit?usp=sharing")
tabel_csv = tabel.replace('/edit?usp=sharing','/gviz/tq?tqx=out:csv' )
tabel_df = pd.read_csv(tabel_csv)
st.write(tabel_df)

# search bar
search = st.text_input("Inventory Search    ")
if search :
    df1 = tabel_df[tabel_df.apply(lambda row: row.astype(str).str.contains(search, case = False).any(),axis=1)]
    st.write(df1)

def add_row(name, email):
    worksheet.append_row([name, email])
    return f"Row with name '{name}' and email '{email}' has been added."

# delete data
def delete_row_by_name(part_number):
    record = worksheet.get_all_records() 
    for idx, record in enumerate(record, start=2):
        if record.get("Part Number") == part_number :
            worksheet.delete_rows(idx)
            return f"component with part number '{part_number}' has been deleted"
    return f"there is no component corresponding to part number '{part_number}'"

# update quantity data
def update_quantity(part_number, new_quantity):
    record = worksheet.get_all_records() 
    for idx, record in enumerate(record, start=2):
        if record.get("Part Number") == part_number :
            worksheet.update_cell(idx, 3 , new_quantity)
            return f"component quantity has bee updated"
    return f"there is no component corresponding to part number '{part_number}'"




def main():
    st.title("Google Sheets Data Management")

    # Data Entry Form
    st.header("Add Data to Sheet")
    with st.form(key='add_data_form'):
        name_to_add = st.text_input('Name')
        email_to_add = st.text_input('Email')
        add_button = st.form_submit_button(label='Add')

    if add_button:
        if not name_to_add or not email_to_add:
            st.error("Please provide both a name and an email.")
        else:
            result = add_row(name_to_add, email_to_add)
            st.write(result)

    # Data Deletion Form
    st.header("Delete Data from Sheet")
    with st.form(key='delete_data_form'):
        name_to_delete = st.text_input('Name to Delete')
        delete_button = st.form_submit_button(label='Delete')

    if delete_button:
        if not name_to_delete:
            st.error("Please provide a name to delete.")
        else:
            result = delete_row_by_name(name_to_delete)
            st.write(result)
    
    # Data Update Form
    st.header("Update Data Form")
    with st.form(key='Update_data_form'):
        name_to_update = st.text_input('Name to Update')
        new_quantity = st.text_input('input new quantity')
        update_button = st.form_submit_button(label='Update')
        

    if update_button:
        if not name_to_update or not new_quantity:
            st.error("Please provide a name to update.")
        else:
            result = update_quantity(name_to_update, new_quantity)
            st.write(result)

if __name__ == '__main__':
    main()
