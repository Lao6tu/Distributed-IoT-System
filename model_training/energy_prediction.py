import os
import joblib
import pandas as pd
import mysql.connector

# Assuming your CSV files are in the same directory as your script or notebook
csv_folder_path = 'C:/Users/EEstaff/Desktop/NPPVData(2021-2023)/filtered_data'

# Get a list of all CSV files in the folder
csv_files = [file for file in os.listdir(csv_folder_path) if file.endswith('.csv')]

# Create a dictionary to store DataFrames
dfs = {}

# Load each CSV file into a DataFrame and store it in the dictionary
for csv_file in csv_files:
    df_name = f"df_{os.path.splitext(csv_file)[0]}"  # Name the DataFrame based on the CSV file name
    df = pd.read_csv(os.path.join(csv_folder_path, csv_file))
    dfs[df_name] = df

connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password',
    database='mqtt_data'
)
cursor = connection.cursor()
query = "SELECT AVG(light_bh1750) AS light FROM solar_iot_box WHERE timestamp > NOW() - INTERVAL 5 MINUTE" 
cursor.execute(query)
data = cursor.fetchall()
df4 = pd.DataFrame(data, columns=['IRR Value W/m²'])
df4['IRR Value W/m²'] = df4['IRR Value W/m²'] / 52

query = "SELECT AVG(temperature_dht11) AS temp FROM solar_iot_box WHERE timestamp > NOW() - INTERVAL 5 MINUTE"
cursor.execute(query)
data = cursor.fetchall()
df1 = pd.DataFrame(data, columns=['temp'])

query = "SELECT AVG(humidity_dht11) AS humidity FROM solar_iot_box WHERE timestamp > NOW() - INTERVAL 5 MINUTE"
cursor.execute(query)
data = cursor.fetchall()
df2 = pd.DataFrame(data, columns=['humidity'])

query = "SELECT AVG(pressure_bme280) AS pressure FROM solar_iot_box WHERE timestamp > NOW() - INTERVAL 5 MINUTE"
cursor.execute(query)
data = cursor.fetchall()
df3 = pd.DataFrame(data, columns=['pressure'])

combined_df = pd.concat([df1, df2, df3, df4], axis=1)
combined_df.fillna(combined_df.mean(), inplace=True)

print(combined_df)

predictions_df = pd.DataFrame()
for df_name, df in dfs.items():
    model = joblib.load(f'model_{df_name}.pkl')
    prediction = model.predict(combined_df)
    predictions_df[df_name] = prediction / 12

print(predictions_df)