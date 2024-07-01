import streamlit as st
import math
import scipy.stats as stat
import pandas as pd
import csv
import matplotlib.pyplot as plt
from statistics import NormalDist
from streamlit_option_menu import option_menu
from streamlit_gsheets import GSheetsConnection
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials

# Sidebar Nav
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=["Manual", "Inventory Database", "Data Entry","Optimization Calculator"],
        icons = ["house", "book", "pencil","calculator"],
        menu_icon=["cast"],
        default_index=0,
    )

if selected == "Home":
    st.title("Inventory Management Application")
    st.write("*Manage and Optimmize your inventory system*")

if selected == "Data Entry":
    # Path to your credentials file
    credentials_file = "C:\\Users\\ENVY\\.streamlit\\inventoryentry-380f630ca6cb.json"

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

    # title 
    st.title("Database Management")
    #st.header("Add component data to the database")
    st.subheader("Add component data and calculate its optimum ordering quantity and reordering level")

    ###
    ## Data
    #tabel = st.text_input("gsheet", "https://docs.google.com/spreadsheets/d/1Fcflq4wRjSzzmz77KnVk1PL7CYbbohfyFuYsf_Ax6JQ/edit?usp=sharing")
    #tabel_csv = tabel.replace('/edit?usp=sharing','/gviz/tq?tqx=out:csv' )
    #tabel_df = pd.read_csv(tabel_csv)
    #st.write(tabel_df)

    ## search bar
    #search = st.text_input("Inventory Search    ")
    #if search :
    #    df1 = tabel_df[tabel_df.apply(lambda row: row.astype(str).str.contains(search, case = False).any(),axis=1)]
    #    st.write(df1)
    

    # optimization calculation noncritical
    def optimize_noncritical(D, std, L, p, A, h, Cu):
        
        # determining demand during lead and std during lead
        D_L = D*L/12 
        std_L = std*math.sqrt(L/12)

        # Solving initials (q init, alpha init, r init, z)
        q_global = math.sqrt(2*A*D/h)
        alpha_init = h*q_global/Cu/D
        print(alpha_init)
        z = stat.norm.ppf(1-alpha_init)
        print("z: ", z)
        r_initial = D_L + z*std_L
        print(r_initial)

        # looping for q and r final
        V = True

        while V :
            
            # Finding Q
            # Calculate N
            pdf = math.exp(-0.5*z*z)/(math.sqrt(2*math.pi))
            # print(pdf)
            pos = pdf - z*(1-NormalDist().cdf(z))
            #print(pos)
            N = math.ceil(std_L*(pdf-z*pos))
            print("N: ", N)

            q = math.sqrt(2*D*(A+Cu*N)/h)                                                                                                                                                             
            #print(q)
            alpha = h*q/Cu/D
            z = stat.norm.ppf(1-alpha)
            r_2 = D_L + z*std_L
            #print(r_2)
            if abs(r_2 - r_initial) > 0.01:
                r_initial = r_2
                V = True
                
            else:
                V = False
    
        # Service Level and Total Cost
        # Service Level
        ss_unrounded =  (1 - (N / D_L))  * 100 
        print("srvc level: ", ss_unrounded)
        sl = round(ss_unrounded,2)
        print("Service Level: ", sl)

        # Total Cost
        OT_unrounded = D * p + (A*D/q) + (h*(0.5*q + r_2 - D_L)) + (Cu*(D/q)*N)
        print("OT: ", OT_unrounded)
        OT = round(OT_unrounded,2)
        print("Total Cost: ", OT)
        
        # return q, r, sl, OT
        return q, r_2, sl, OT

    # optimization calculator critical
    def optimize_critical(D, std, L, p, A, h, Cu,sl):
        # Find demand and std. deviation during lead time
        D_L = D*L/12 
        std_L = std*math.sqrt(L/12)

        # Find N based on service level
        N = D_L*(1 - (sl/100))

        # Find ordering quantity 
        q = math.sqrt((2*D*(A + Cu*N))/h)

        # Find alpha
        alpha = h*q/Cu/D

        # Find Z alpha
        z = stat.norm.ppf(1-alpha)

        # calculate reorder level r, safert stock ss, total cost OT
        r = D_L + z*std_L
        ss = z*std_L
        OT_unrounded = D * p + (A*D/q) + (h*(0.5*q + r - D_L)) + (Cu*(D/q)*N)
        OT = round(OT_unrounded,2)
        return q, r, OT
    
    # add data non-critical
    def add_row_noncritical(part_number, component, quantity, D, std, L, p, A, h, Cu, q, r_2, sl, OT):
        worksheet.append_row([part_number, component, quantity, D, std, L, p, A, h, Cu, q, r_2, sl, OT])
        return f"New data has been succesfully recorded."
    
    #add data critical
    def add_row_critical(part_number, component, quantity, D, std, L, p, A, h, Cu, q, r, sl, OT):
        worksheet.append_row([part_number, component, quantity, D, std, L, p, A, h, Cu, q, r, sl, OT])
        return f"New data has been succesfully recorded."

    # delete data
    def delete_row_by_name(part_number):
        record = worksheet.get_all_records() 
        for idx, record in enumerate(record, start=2):
            if record.get("Part Number") == part_number :
                worksheet.delete_rows(idx)
                return f"component with part number '{part_number}' has been deleted"
        return f"there is no component corresponding to part number '{part_number}'"
    
    # Navigation for safety non safety selection
    selected = option_menu(
        menu_title="Determine if the item is safety-critical or not",
        options=["non-safety-critical", "safety-critical"],
        icons = ["house", "book"],
        menu_icon=["info"],
        default_index=0,
        orientation="horizontal"
    )
    
    if selected == "non-safety-critical":
        # Data Entry Form
        with st.form(key='add_data_form'):
            part_number = st.text_input('Part Number')
            component = st.text_input('Component Name')
            quantity = st.number_input('Quantity')
            D = st.number_input('Annual Demand')
            std = st.number_input('Standard Deviation of Annual Demand')
            L = st.number_input('Lead Time (month)')
            p = st.number_input('Unit Cost ($)')
            A = st.number_input('Ordering Cost ($)')
            h = 0.2*p
            Cu = st.number_input('Shortage Cost per Item ($)')
            add_button = st.form_submit_button(label='Add')

        if add_button:
            if not D or not L:
                st.error("Please fill the required forms")
            else:
                q, r_2, sl , OT = optimize_noncritical(D, std, L, p, A, h, Cu)
                result = add_row_noncritical(part_number, component, quantity, D, std, L, p, A, h, Cu, q, r_2, sl, OT)
                st.write(result)        
                #Outputs
                st.write(f"Optimum Reorder Level :")
                st.info(round(r_2))

                st.write(f"Optimum Ordering Quantity :")
                st.info(round(q))

                st.write(f"Service Level (%) :")
                st.info(sl)

                st.write(f"Optimized Total Cost :")
                st.info(OT)


    elif selected == "safety-critical": 
        # Data Entry Form
        with st.form(key='add_data_form'):
            part_number = st.text_input('Part Number')
            component = st.text_input('Component Name')
            sl = st.number_input('Service Level (%)')
            quantity = st.number_input('Quantity')
            D = st.number_input('Annual Demand')
            std = st.number_input('Standard Deviation of Annual Demand')
            L = st.number_input('Lead Time (month)')
            p = st.number_input('Unit Cost ($)')
            A = st.number_input('Ordering Cost ($)')
            h = 0.2*p
            Cu = st.number_input('Shortage Cost ($)')
            add_button = st.form_submit_button(label='Add')

        if add_button:
            if not D or not L:
                st.error("Please fill the required forms")
            else:
                q, r , OT = optimize_critical(D, std, L, p, A, h, Cu,sl)
                result = add_row_critical(part_number, component, quantity, D, std, L, p, A, h, Cu, q, r, sl, OT)
                st.write(result)
                #Outputs
                st.write(f"Optimum Reorder Level :")
                st.info(round(r))

                st.write(f"Optimum Ordering Quantity :")
                st.info(round(q))

                st.write(f"Service Level (%) :")
                st.info(sl)

                st.write(f"Optimized Total Cost :")
                st.info(OT)
                
    # Data Deletion Form
    st.header("Delete component data from the database")
    with st.form(key='delete_data_form'):
        name_to_delete = st.text_input('Name to Delete')
        delete_button = st.form_submit_button(label='Delete')

    if delete_button:
        if not name_to_delete:
            st.error("Please provide a name to delete.")
        else:
            result = delete_row_by_name(name_to_delete)
            st.write(result)

if selected == "Inventory Database":
    st.title("Inventory Database")

    # Path to your credentials file
    credentials_file = "C:\\Users\\ENVY\\.streamlit\\inventoryentry-380f630ca6cb.json"

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
    # tes output
    tabel = st.text_input("gsheet", "https://docs.google.com/spreadsheets/d/1Fcflq4wRjSzzmz77KnVk1PL7CYbbohfyFuYsf_Ax6JQ/edit?usp=sharing")
    tabel_csv = tabel.replace('/edit?usp=sharing','/gviz/tq?tqx=out:csv' )
    tabel_df = pd.read_csv(tabel_csv)
    st.write(tabel_df)

    # search bar
    st.header("Inventory Search")
    search = st.text_input("Enter Component's Part Number:")
    if search :
        df1 = tabel_df[tabel_df.apply(lambda row: row.astype(str).str.contains(search, case = False).any(),axis=1)]
        st.write(df1)  
    
    # update quantity data
    def update_quantity(part_number, new_quantity):
        record = worksheet.get_all_records() 
        for idx, record in enumerate(record, start=2):
            if record.get("Part Number") == part_number :
                worksheet.update_cell(idx, 3 , new_quantity)
                return f"component quantity has bee updated"
        return f"there is no component corresponding to part number '{part_number}'"
    
    # Data Update Form
    st.header("Inventory Quantity Update")
    with st.form(key='Update_data_form'):
        name_to_update = st.text_input("Enter Component's Part Number:")
        new_quantity = st.number_input('input new quantity', min_value = 10)
        update_button = st.form_submit_button(label='Update')
            
    if update_button:
        if not name_to_update or not new_quantity:
            st.error("Please provide a name to update.")
        else:
            result = update_quantity(name_to_update, new_quantity)
            record = worksheet.get_all_records() 
            st.info(result)
            for idx, record in enumerate(record, start=2):
                if record.get("Part Number") == name_to_update :
                    if new_quantity <= record.get("Optimum Reorder Level"):                   
                        st.warning("WARNING! Inventory level is below reorder level. Make a new order immidiately!", icon=":material/warning:")                     
    
if selected == "Optimization Calculator":
    st.title("Optimization Calculator")
    
    # user inputs on sidebar
    D = st.number_input("Annual Demand: ", min_value = 10)
    std = st.number_input("Standard Deviation: ", min_value = 10)
    # L = st.sidebar.number_input("Lead Time: ", min_value = 10)
    L = st.slider("Lead Time: ", min_value = 1, max_value = 30)
    p = st.number_input("Unit Cost: ", min_value = 10)
    A = st.number_input("Ordering Cost: ", min_value = 10)
    # h = int(input("Storing Cost: "))
    h = 0.2*p
    Cu = st.number_input("Shortage Cost", min_value = 10)

    D_L = D*L/12 
    std_L = std*math.sqrt(L/12)

    # Solve

    q_global = math.sqrt(2*A*D/h)
    alpha_init = h*q_global/Cu/D
    print(alpha_init)
    z = stat.norm.ppf(1-alpha_init)
    print("z: ", z)

    r_initial = D_L + z*std_L
    print(r_initial)

    V = True

    while V :
        
        # Finding Q
        
        # Calculate N
        pdf = math.exp(-0.5*z*z)/(math.sqrt(2*math.pi))
        # print(pdf)
        pos = pdf - z*(1-NormalDist().cdf(z))
        #print(pos)
        N = math.ceil(std_L*(pdf-z*pos))
        print("N: ", N)

        q = math.sqrt(2*D*(A+Cu*N)/h)                                                                                                                                                             
    #print(q)
        alpha = h*q/Cu/D
        z = stat.norm.ppf(1-alpha)
        r_2 = D_L + z*std_L
        #print(r_2)
        if abs(r_2 - r_initial) > 0.01:
            r_initial = r_2
            V = True
            
        else:
            V = False

    # Service Level and Total Cost

    # Service Level

    ss_unrounded =  (1 - (N / D_L))  * 100 
    print("srvc level: ", ss_unrounded)
    sl = round(ss_unrounded,2)
    print("Service Level: ", sl)


    # Total Cost

    OT_unrounded = D * p + (A*D/q) + (h*(0.5*q + r_2 - D_L)) + (Cu*(D/q)*N)
    print("OT: ", OT_unrounded)
    OT = round(OT_unrounded,2)
    print("Total Cost: ", OT)

    # Main Body

    st.header("*Optimized Result using Q model (continuous review)*")

    #Outputs
    st.write(f"Optimum Reorder Level :")
    st.info(round(r_2))

    st.write(f"Optimum Ordering Quantity :")
    st.info(round(q))

    st.write(f"Service Level (%) :")
    st.info(sl)

    st.write(f"Optimized Total Cost :")
    st.info(OT)



