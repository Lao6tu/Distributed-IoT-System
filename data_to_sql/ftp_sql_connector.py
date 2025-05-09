import os
import time
import ftplib
import pandas as pd
import numpy as np
import sqlalchemy
import mysql.connector
from mysql.connector import Error
import warnings
warnings.filterwarnings('ignore')

# FTP server details
FTP_HOST = "153.20.39.129"
FTP_USER = "admin"
FTP_PASS = "admin"

# Local directory to save files
LOCAL_DIR = "C:/Users/EEstaff/Documents/FTP_SYNC"

def format_data_to_sql():
    # Import Plant 1 data
    df_plant = pd.read_csv("C:/Users/EEstaff/Documents/FTP_SYNC/" + filename, skiprows=1)
    df_plant = df_plant.iloc[:, 0].str.split(';', expand = True)
    # Find the index where the split should happen
    split_index = df_plant[df_plant.iloc[:, 0] == '#INV2 ESN:6T2319022619'].index[0]
    # Split the DataFrame
    df_inv1 = df_plant.iloc[:split_index]
    df_inv2 = df_plant.iloc[split_index + 1:]
    # Delete the "#" at beginning of the row
    df_inv1[0] = df_inv1[0].str.lstrip('#')
    df_inv2[0] = df_inv2[0].str.lstrip('#')
    # Set the first row values as column names
    df_inv1.columns = df_inv1.iloc[0]
    df_inv2.columns = df_inv2.iloc[0]
    # Drop the first row (if needed)
    df_inv1 = df_inv1[1:]
    df_inv2 = df_inv2[1:]
    # Drop the last blank column
    df_inv1 = df_inv1.iloc[:, :-1]
    df_inv2 = df_inv2.iloc[:, :-1]
    # Reset index (if needed)
    df_inv1.reset_index(drop=True, inplace=True)
    df_inv2.reset_index(drop=True, inplace=True)
    # adjust data format
    df_inv1['Time'] = pd.to_datetime(df_inv1['Time'], format='%d-%m-%Y %H:%M:%S')
    df_inv2['Time'] = pd.to_datetime(df_inv2['Time'], format='%d-%m-%Y %H:%M:%S')
    df_inv1 = df_inv1.astype({'Pac': float, 'E-Day': float, 'E-Total': float})
    df_inv2 = df_inv2.astype({'Pac': float, 'E-Day': float, 'E-Total': float})
    # Add two inverters data
    df_sum = pd.DataFrame()
    df_sum['Time'] = df_inv1['Time']
    df_sum['Pac'] = df_inv1['Pac'] + df_inv2['Pac']
    df_sum['E-Day'] = df_inv1['E-Day'] + df_inv2['E-Day']
    df_sum['E-Total'] = df_inv1['E-Total'] + df_inv2['E-Total']

    # MySQL configurations
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'password',
        'database': 'ftp_data'
    }

    # Function to execute a query
    def execute_query(db_config, query):
        try:
            # Create a database connection
            connection = mysql.connector.connect(
                host=db_config['host'],
                user=db_config['user'],
                passwd=db_config['password'],
                database=db_config['database']
            )
            cursor = connection.cursor()
            # Execute the query
            cursor.execute(query, multi=True)
            # Commit the changes
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    # Create a connection to the database
    engine = sqlalchemy.create_engine(f'mysql+mysqlconnector://root:password@localhost:3306/ftp_data')

    # Insert the DataFrame into MySQL using the to_sql() method
    df_inv1.to_sql('inverter_1', con=engine, if_exists='append', index=False)
    df_inv2.to_sql('inverter_2', con=engine, if_exists='append', index=False)
    df_sum.to_sql('total_energy', con=engine, if_exists='append', index=False)

    query_1 = '''
    ALTER TABLE inverter_1
    MODIFY Uac1 FLOAT,
    MODIFY Uac2 FLOAT,
    MODIFY Uac3 FLOAT,
    MODIFY Iac1 FLOAT,
    MODIFY Iac2 FLOAT,
    MODIFY Iac3 FLOAT,
    MODIFY Upv1 FLOAT,
    MODIFY Upv2 FLOAT,
    MODIFY Upv3 FLOAT,
    MODIFY Upv4 FLOAT,
    MODIFY Upv5 FLOAT,
    MODIFY Upv6 FLOAT,
    MODIFY Upv7 FLOAT,
    MODIFY Upv8 FLOAT,
    MODIFY Ipv1 FLOAT,
    MODIFY Ipv2 FLOAT,
    MODIFY Ipv3 FLOAT,
    MODIFY Ipv4 FLOAT,
    MODIFY Ipv5 FLOAT,
    MODIFY Ipv6 FLOAT,
    MODIFY Ipv7 FLOAT,
    MODIFY Ipv8 FLOAT,
    MODIFY Pac FLOAT,
    MODIFY Qac FLOAT,
    MODIFY Eac FLOAT,
    MODIFY `E-Day` FLOAT,
    MODIFY `E-Total` FLOAT,
    MODIFY Temp FLOAT,
    MODIFY fac FLOAT,
    MODIFY cos FLOAT,
    MODIFY Status VARCHAR(50),
    MODIFY Error VARCHAR(50),
    MODIFY `Cycle Time` FLOAT;
    '''
    query_2 ='''
    ALTER TABLE inverter_2
    MODIFY Uac1 FLOAT,
    MODIFY Uac2 FLOAT,
    MODIFY Uac3 FLOAT,
    MODIFY Iac1 FLOAT,
    MODIFY Iac2 FLOAT,
    MODIFY Iac3 FLOAT,
    MODIFY Upv1 FLOAT,
    MODIFY Upv2 FLOAT,
    MODIFY Upv3 FLOAT,
    MODIFY Upv4 FLOAT,
    MODIFY Upv5 FLOAT,
    MODIFY Upv6 FLOAT,
    MODIFY Upv7 FLOAT,
    MODIFY Upv8 FLOAT,
    MODIFY Ipv1 FLOAT,
    MODIFY Ipv2 FLOAT,
    MODIFY Ipv3 FLOAT,
    MODIFY Ipv4 FLOAT,
    MODIFY Ipv5 FLOAT,
    MODIFY Ipv6 FLOAT,
    MODIFY Ipv7 FLOAT,
    MODIFY Ipv8 FLOAT,
    MODIFY Pac FLOAT,
    MODIFY Qac FLOAT,
    MODIFY Eac FLOAT,
    MODIFY `E-Day` FLOAT,
    MODIFY `E-Total` FLOAT,
    MODIFY Temp FLOAT,
    MODIFY fac FLOAT,
    MODIFY cos FLOAT,
    MODIFY Status VARCHAR(50),
    MODIFY Error VARCHAR(50),
    MODIFY `Cycle Time` FLOAT;
    '''

    # Execute the queries
    execute_query(db_config, query_1)
    execute_query(db_config, query_2)
    print("Query successful")


while True: 
    print("Syncing files...")

    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd('/test')  # change to the directory with CSV files
        for filename in ftp.nlst():
            if filename.endswith('.csv'):
                local_filepath = os.path.join(LOCAL_DIR, filename)
                if not os.path.exists(local_filepath):
                    with open(local_filepath, 'wb') as f:
                        ftp.retrbinary('RETR ' + filename, f.write)
                    print(f"Downloaded: {filename}")
                    format_data_to_sql()

    print("Next sync in 5 minutes...")
    time.sleep(300)
