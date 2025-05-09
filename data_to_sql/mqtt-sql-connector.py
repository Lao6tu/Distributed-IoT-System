#pip install paho-mqtt
#pip install mysql-connector-python

import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error


# MySQL configurations
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'mqtt_data'
}

def create_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        print("MySQL Database connection successful")
        return connection
    except Error as err:
        print(f"Error: '{err}'")

def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except mysql.connector.Error as err:
        print(f"Error: {err}")

# Create tables if not exists
tables = [
    '''
    CREATE TABLE IF NOT EXISTS solar_box (
        id INT AUTO_INCREMENT PRIMARY KEY,
        topic VARCHAR(255) NOT NULL,
        payload VARCHAR(255) NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS solar_farm_panel (
        id INT AUTO_INCREMENT PRIMARY KEY,
        topic VARCHAR(255) NOT NULL,
        payload VARCHAR(255) NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS solar_farm_battery (
        id INT AUTO_INCREMENT PRIMARY KEY,
        topic VARCHAR(255) NOT NULL,
        payload VARCHAR(255) NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''
]

# Initialize database connection and create tables
connection = create_db_connection()
for table_query in tables:
    execute_query(connection, table_query)

# MQTT configurations
MQTT_BROKER = '192.168.0.105'
MQTT_PORT = 1883

# Define MQTT eventsö
def on_connect(client, userdata, flags, rc):
    client.subscribe("esp32/DHT11/Temperature")
    client.subscribe("esp32/DHT11/Humidity")
    client.subscribe("esp32/BME280/Temperature")
    client.subscribe("esp32/BME280/Humidity")
    client.subscribe("esp32/BME280/Pressure")
    client.subscribe("esp32/BME280/Altitude")
    client.subscribe("esp32/INA219/Load Voltage")
    client.subscribe("esp32/INA219/Current")
    client.subscribe("esp32/INA219/Power")
    client.subscribe("esp32/BH1750/Light")
    client.subscribe("esp32/Battery/Voltage")
    client.subscribe("esp32/Battery/Level")
    client.subscribe("esp_bat.1/Charge_Current")
    client.subscribe("esp_bat.1/Discharge_Current")
    client.subscribe("esp_bat.1/Battery_Voltage")
    client.subscribe("esp_Farm_PA/power_SA_total")
    client.subscribe("esp_Farm_PA/current_SA_total")
    client.subscribe("esp_Farm_PA/energy_SA_total")
    for i in range(0, 8):
        client.subscribe("esp_Farm_PA/load_voltage_SA_" + str(i))
        client.subscribe("esp_Farm_PA/current_SA_" + str(i))
        client.subscribe("esp_Farm_PA/power_SA_" + str(i))


def on_message(client, userdata, message):
    payload = message.payload.decode('utf-8')
    topic = message.topic
    print(f"Received message '{payload}' on topic '{topic}'")
    
    # Store data in MySQL
    try:
        conn = mysql.connector.connect(**db_config)   
        cursor = conn.cursor()
        if "esp32" in topic:
            query = "INSERT INTO solar_box (topic, payload) VALUES (%s, %s)"
        elif "esp_Farm_PA" in topic:
            query = "INSERT INTO solar_farm_panel (topic, payload) VALUES (%s, %s)"
        elif "esp_bat.1" in topic:
            query = "INSERT INTO solar_farm_battery (topic, payload) VALUES (%s, %s)"
        else:
            # Handle unknown topic or define another action as needed
            print(f"Unknown topic: {topic}")
            return
        cursor.execute(query, (topic, payload))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    except Exception as e:
        print(f"Error: {e}")


# Initialize MQTT client
client = mqtt.Client(client_id="tecspace_server")
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)


try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()


