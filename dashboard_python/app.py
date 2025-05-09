import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine

app = dash.Dash(__name__, title='Dashboard')

# Database connection parameters
DB_URI = "mysql+mysqlconnector://root:password@192.168.0.103:3306/broker_data"

# Create an SQLAlchemy engine
engine = create_engine(DB_URI)

# Function to fetch data
def fetch_temperature_data():
    current_time = datetime.now()
    minute_ago = current_time - timedelta(minutes=5)
    query = f'''
        SELECT timestamp, payload 
        FROM broker_messages 
        WHERE topic = 'esp32/DH11/Temperature' AND timestamp > '{minute_ago}'
    '''
    df = pd.read_sql_query(query, engine)
    
    # Convert payload to float
    df['payload'] = df['payload'].str.extract(r'(\d+\.\d+)').astype(float)
    
    return df

def fetch_humidity_data():
    current_time = datetime.now()
    minute_ago = current_time - timedelta(minutes=5)
    query = f'''
        SELECT timestamp, payload 
        FROM broker_messages 
        WHERE topic = 'esp32/DH11/Humidity' AND timestamp > '{minute_ago}'
    '''
    df = pd.read_sql_query(query, engine)
    
    # Convert payload to float
    df['payload'] = df['payload'].str.extract(r'(\d+)').astype(int)
    
    return df


app.layout = html.Div(
    style={
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center',
        'height': '100vh'  # Set the height of the main Div to full viewport height
    },
    children=[
        html.H1('PV Dashboard - Real Time Data', style={'textAlign': 'center'}),
        
        html.Div(
            style={
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
                'flexDirection': 'row',
                'width': '80%',  # Adjust the width of the container
                'margin': '20px'  # Add some margin around the container
            },
            children=[
                dcc.Graph(
                    id='temperature-plot',
                    style={'width': '50%', 'height': '600px'}  # Adjust the size of the chart
                ),
                dcc.Graph(
                    id='humidity-plot',
                    style={'width': '50%', 'height': '600px'}  # Adjust the size of the chart
                )
            ]
        ),       
        
        dcc.Interval(
            id='update-interval',
            interval=1*2000,  # Update every 2 second
            n_intervals=0
        )
    ]
)


# Callbacks for updating the plots
def format_timestamp_to_time(data):
    # Format timestamp column to show only time
    data['timestamp'] = data['timestamp'].dt.time
    return data

# Plotting function for temperature data
def plot_temperature(data):
    fig = make_subplots()
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['payload'], mode='lines'))
    fig.update_xaxes(type='category', tickformat='%H:%M:%S')
    fig.update_layout(title='Real Time Temperature Plot - Last 5 Minutes',
                      #xaxis_title='Timestamp',
                      yaxis_title='Temperature (°C)')
    return fig

@app.callback(
    Output('temperature-plot', 'figure'),
    Input('update-interval', 'n_intervals')
)

def update_temperature_plot(n_intervals):
    data = fetch_temperature_data()
    data = format_timestamp_to_time(data)
    fig = plot_temperature(data)
    return plot_temperature(data)

# Plotting function for humidity data
def plot_humidity(data):
    fig = make_subplots()
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['payload'], mode='lines', name='Humidity'))
    fig.update_xaxes(type='category', tickformat='%H:%M:%S')
    fig.update_layout(title='Real Time Humidity Plot - Last 5 Minutes',
                      #xaxis_title='Timestamp',
                      yaxis_title='Humidity (%)')
    return fig

@app.callback(
    Output('humidity-plot', 'figure'),
    Input('update-interval', 'n_intervals')
)

def update_humidity_plot(n_intervals):
    data = fetch_humidity_data() 
    data = format_timestamp_to_time(data)
    fig = plot_humidity(data)
    return plot_humidity(data)

if __name__ == '__main__':
    app.run_server(debug=True)

