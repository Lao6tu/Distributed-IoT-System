import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Database configuration
db_config = {
    'host': 'localhost',
    'database': 'mqtt_data',
    'user': 'root',
    'password': 'password'
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
    CREATE TABLE IF NOT EXISTS solar_iot_box (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        temperature_dht11 FLOAT,
        humidity_dht11 FLOAT,
        temperature_bme280 FLOAT,
        humidity_bme280 FLOAT,
        pressure_bme280 FLOAT,
        altitude_bme280 FLOAT,
        load_voltage_ina219 FLOAT,
        current_ina219 FLOAT,
        power_ina219 FLOAT,
        light_bh1750 FLOAT,
        voltage_battery FLOAT,
        level_battery FLOAT
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS solar_farm (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        charge_current FLOAT,
        discharge_current FLOAT,
        battery_voltage FLOAT,
        input_power FLOAT,
        input_current FLOAT,
        input_energy FLOAT,
        Upv1 FLOAT, Ipv1 FLOAT,
        Upv2 FLOAT, Ipv2 FLOAT,
        Upv3 FLOAT, Ipv3 FLOAT,
        Upv4 FLOAT, Ipv4 FLOAT,
        Upv5 FLOAT, Ipv5 FLOAT,
        Upv6 FLOAT, Ipv6 FLOAT,
        Upv7 FLOAT, Ipv7 FLOAT,
        Upv8 FLOAT, Ipv8 FLOAT
    );
    '''
]

# Initialize database connection and create tables
connection = create_db_connection()
for table_query in tables:
    execute_query(connection, table_query)

# MQTT Topics to subscribe
topics_1 = [
    "esp32/DHT11/Temperature",
    "esp32/DHT11/Humidity",
    "esp32/BME280/Temperature",
    "esp32/BME280/Humidity",
    "esp32/BME280/Pressure",
    "esp32/BME280/Altitude",
    "esp32/INA219/Load Voltage",
    "esp32/INA219/Current",
    "esp32/INA219/Power",
    "esp32/BH1750/Light",
    "esp32/Battery/Voltage",
    "esp32/Battery/Level",
]
topics_2 = [
    "esp_bat.1/Charge_Current",
    "esp_bat.1/Discharge_Current",
    "esp_bat.1/Battery_Voltage",
    "esp_Farm_PA/power_SA_total",
    "esp_Farm_PA/current_SA_total",
    "esp_Farm_PA/energy_SA_total",
]
for i in range(8):
    topics_2.append("esp_Farm_PA/load_voltage_SA_" + str(i))
    topics_2.append("esp_Farm_PA/current_SA_" + str(i))

# Initialize a dictionary to store incoming data
data_1 = {topic: None for topic in topics_1}
data_2 = {topic: None for topic in topics_2}

def on_connect(client, userdata, flags, rc):
    for topic in topics_1 + topics_2:
        client.subscribe(topic)

received_topics = set()  # Tracks topics from which messages have been received

def on_message(client, userdata, msg):
    global data_1, data_2, received_topics  # Use the global variables
    topic = msg.topic
    message = msg.payload.decode("utf-8")
    
    try:
        message = float(message)
    except ValueError:
        pass  # Keep message as a string if it's not a number

    # Determine which data dictionary to update
    if topic in data_1:
        data_1[topic] = message
        received_topics.add(topic)
        data_dict = data_1
    elif topic in data_2:
        data_2[topic] = message
        received_topics.add(topic)
        data_dict = data_2
    else:
        print(f"Topic {topic} not recognized.")
        return

    # Decide which function to call based on the topic set
    if all(value is not None for value in data_1.values()) or all(value is not None for value in data_2.values()):
        if data_dict is data_1:
            handle_iot_box_data(topic, message)
            data_1 = {topic: None for topic in topics_1}  # Reset after handling
        elif data_dict is data_2:
            handle_solar_farm_data(topic, message)
            data_2 = {topic: None for topic in topics_2}  # Reset after handling

        received_topics.clear()  # Clear the received topics set for the next round
        print("Stored the result messages into table.")

    print(f"Received message '{message}' on topic '{topic}'")


def handle_iot_box_data(topic, message):
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor()
            query = """
                INSERT INTO solar_iot_box 
                (timestamp, temperature_dht11, humidity_dht11, temperature_bme280, humidity_bme280, pressure_bme280, altitude_bme280,
                load_voltage_ina219, current_ina219, power_ina219, light_bh1750, voltage_battery, level_battery)  
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                datetime.now(),
                data_1.get("esp32/DHT11/Temperature"),
                data_1.get("esp32/DHT11/Humidity"),
                data_1.get("esp32/BME280/Temperature"),
                data_1.get("esp32/BME280/Humidity"),
                data_1.get("esp32/BME280/Pressure"),
                data_1.get("esp32/BME280/Altitude"),
                data_1.get("esp32/INA219/Load Voltage"),
                data_1.get("esp32/INA219/Current"),
                data_1.get("esp32/INA219/Power"),
                data_1.get("esp32/BH1750/Light"),
                data_1.get("esp32/Battery/Voltage"),
                data_1.get("esp32/Battery/Level")
            )
            cursor.execute(query, values)
            connection.commit()
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def handle_solar_farm_data(topic, message):
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor()
            query = """
                INSERT INTO solar_farm 
                (timestamp, charge_current, discharge_current, battery_voltage, input_power, input_current, input_energy,
                Upv1, Ipv1, Upv2, Ipv2, Upv3, Ipv3, Upv4, Ipv4, Upv5, Ipv5, Upv6, Ipv6, Upv7, Ipv7, Upv8, Ipv8)  
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Initialize values list with static data
            values_list = [
                datetime.now(),
                data_2.get("esp_bat.1/Charge_Current"),
                data_2.get("esp_bat.1/Discharge_Current"),
                data_2.get("esp_bat.1/Battery_Voltage"),
                data_2.get("esp_Farm_PA/power_SA_total"),
                data_2.get("esp_Farm_PA/current_SA_total"),
                data_2.get("esp_Farm_PA/energy_SA_total"),
            ]  
            # Dynamically add data for each solar array
            for i in range(8):
                values_list.extend([
                    data_2.get(f"esp_Farm_PA/load_voltage_SA_{i}"),
                    data_2.get(f"esp_Farm_PA/current_SA_{i}"),
                ])
            # Ensure the length of values_list matches the placeholders in the SQL query
            if len(values_list) != 23:
                raise ValueError("Incorrect number of values to insert; expected 22.")
            # Convert list to tuple for cursor.execute
            values = tuple(values_list)
            
            cursor.execute(query, values)
            connection.commit()
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# define client name
client = mqtt.Client(client_id="tecspace_server")
client.on_connect = on_connect
client.on_message = on_message

# define mqtt broker ip address and port
client.connect("192.168.0.105", 1883, 60) 

client.loop_forever()
