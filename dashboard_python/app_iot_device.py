import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import dash_daq as daq
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine

app = dash.Dash(__name__, title='Dashboard', external_stylesheets=[dbc.themes.DARKLY])

DB_URI = "mysql+mysqlconnector://root:password@localhost:3306/mqtt_data"
engine = create_engine(DB_URI)

# Function to fetch temperature data
def fetch_temperature_data():
    current_time = datetime.now()
    minute_ago = current_time - timedelta(seconds=10)
    query = f'''
        SELECT timestamp, payload 
        FROM solar_box 
        WHERE topic = 'esp32/DH11/Temperature' AND timestamp > '{minute_ago}'
    '''
    df = pd.read_sql_query(query, engine)
    # Convert payload to float
    df['payload'] = df['payload'].str.extract(r'(\d+\.\d+)').astype(float)
    return df

# Function to fetch humidity data
def fetch_humidity_data():
    current_time = datetime.now()
    minute_ago = current_time - timedelta(minutes=5)
    query = f'''
        SELECT timestamp, payload 
        FROM solar_box 
        WHERE topic = 'esp32/DH11/Humidity' AND timestamp > '{minute_ago}'
    '''
    df = pd.read_sql_query(query, engine)
    # Convert payload to integer
    df['payload'] = df['payload'].str.extract(r'(\d+)').astype(int)
    return df

def fetch_light_data():
    current_time = datetime.now()
    seconds_ago = current_time - timedelta(seconds=10)
    query = f'''
        SELECT timestamp, payload 
        FROM solar_box 
        WHERE topic = 'esp32/BH1750/Light' AND timestamp > '{seconds_ago}'
    '''
    df = pd.read_sql_query(query, engine)
    # Convert payload to float
    df['payload'] = df['payload'].str.extract(r'(\d+)').astype(int)
    return df

def fetch_battery_data_1():
    current_time = datetime.now()
    seconds_ago = current_time - timedelta(seconds=10)
    query = f'''
        SELECT timestamp, payload 
        FROM solar_box 
        WHERE topic = 'esp32/Battery/Votalge' AND timestamp > '{seconds_ago}'
    '''
    df = pd.read_sql_query(query, engine)
    # Convert payload to float
    df['payload'] = df['payload'].str.extract(r'(\d+\.\d+\d+)').astype(float)
    return df

def fetch_battery_data_2():
    current_time = datetime.now()
    seconds_ago = current_time - timedelta(seconds=10)
    query = f'''
        SELECT timestamp, payload 
        FROM solar_box 
        WHERE topic = 'esp32/Battery/Level' AND timestamp > '{seconds_ago}'
    '''
    df = pd.read_sql_query(query, engine)
    # Convert payload to float
    df['payload'] = df['payload'].str.extract(r'(\d+)').astype(int)
    return df


# Set Mapbox access token
mapbox_token = 'pk.eyJ1IjoicGVycnk2IiwiYSI6ImNscGp4djcybTA0MWgyaW56amNndGk5YnEifQ.nkNtsN46y8hR0VcP-aIRtA'
mapbox_style = 'mapbox://styles/mapbox/outdoors-v12'


app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H1("ESP32 IoT Dashboard", className="text-center mt-3 mb-4", style={'color': '#34568B'}),
            ),
            justify="center"
        ),

        dbc.Row(
            [
                dbc.Col(
                    daq.Gauge(
                        id="temperature-gauge",
                        showCurrentValue=True,
                        color={"gradient":True,"ranges":{"blue":[0,15],"white":[15,30],"yellow":[30,40],"red":[40,50]}},
                        value=0,
                        units="°C",
                        label='Temperature',
                        max=50,
                        min=0
                    ),
                    width=3
                ),
                dbc.Col(
                    daq.Gauge(
                        id="humidity-gauge",
                        showCurrentValue=True,
                        color={"gradient":True,"ranges":{"orange":[0,30],"white":[30,70],"blue":[70,100]}},
                        value=0,
                        units="%",
                        label='Humidity',
                        max=100,
                        min=0
                    ),
                    width=3
                ),
                dbc.Col(
                    daq.Gauge(
                        id="light-gauge",
                        value=0,
                        units='lux',
                        showCurrentValue=True,
                        color={"gradient":True,"ranges":{"white":[0,2000],"yellow":[2000,5000],"orange":[5000,20000]}},
                        label='Light Intensity',
                        max=20000,
                        min=0
                    ),
                    width=3
                ),     
                dbc.Col(
                    dbc.Row(
                        [
                            daq.GraduatedBar(
                                id="battery-bar",
                                showCurrentValue=True,
                                color="green",
                                size=200,
                                value=0,
                                label='Battery Level',
                                step=10,
                                max=100,
                                min=0
                            ),
                            html.Div(style={'height': '50px'}),
                            daq.LEDDisplay(
                                id="battery-led",
                                color="green",
                                value=0.00,
                                label='Battery Voltage(V)'
                            )           
                        ],
                        justify="center"
                    ),
                    width=3    
                )
            ],
            justify="center"
        ),
        
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        id="world-map",
                        figure={
                            "data": [
                                {
                                "type": "scattermapbox",
                                "lat": [1.3346421068282964],
                                "lon": [103.7762975692158],
                                "hoverinfo": "text+lon+lat",
                                "text": "FYP_ESP32",
                                "mode": "markers",
                                "marker": {"size": 15, "color": "#FF0000"},
                                },
                            ],
                            "layout": {
                                "mapbox": {
                                    "accesstoken": mapbox_token,
                                    "style": mapbox_style,
                                    "center": dict(lat=1.3336322068282964, lon=103.7752975692158),
                                    "zoom": 15.5
                                },
                                "width": 546,
                                "height": 400,
                                "showlegend": False,
                                "autosize": True,
                                "paper_bgcolor": "#1e1e1e",
                                "plot_bgcolor": "#1e1e1e",
                                "margin": {"t": 2, "r": 2, "b": 2, "l": 2},
                                "padding": 50
                            }
                        },
                        config={"displayModeBar": True, "scrollZoom": True}
                    ),
                    width=6,
                    className="mb-4"
                ),

                dbc.Col(
                    dcc.Graph(
                        id="humidity-plot",
                        style={'width': '100%', 'height': '400px'},
                        figure={
                            'layout': {
                                'plot_bgcolor': '#D3D3D3',
                                'paper_bgcolor': '#D3D3D3',
                                'font': {'color': '#ff0000'}
                            }
                        }
                    ),
                    width=6,
                    className="mb-4"
                )
            ],
            justify="center"
        ),

        dcc.Interval(
            id='update-interval',
            interval=2 * 1000,  # Update every 2 seconds
            n_intervals=0
        )
    ],
    style={'margin-top': '20px', 'margin-bottom': '20px'}
)

# Callbacks for updating the plots
@app.callback(
    Output('temperature-gauge', 'value'),
    Input('update-interval', 'n_intervals')
)
def plot_temperature(n_intervals):
    data = fetch_temperature_data()
    value = data['payload'][n_intervals % len(data)]
    return value

@app.callback(
    Output('humidity-gauge', 'value'),
    Input('update-interval', 'n_intervals')
)
def gauge_humidity(n_intervals):
    data = fetch_humidity_data()
    value = data['payload'][n_intervals % len(data)]
    return value

@app.callback(
    Output('light-gauge', 'value'),
    Input('update-interval', 'n_intervals')
)
def gauge_light(n_intervals):
    data = fetch_light_data()
    value = data['payload'][n_intervals % len(data)]
    return value

@app.callback(
    Output('battery-led','value'),
    Input('update-interval', 'n_intervals')       
)
def led_battery(n_intervals):
    data = fetch_battery_data_1()
    value = data['payload'][n_intervals % len(data)]
    return value

@app.callback(
    Output('battery-bar', 'value'),
    Input('update-interval', 'n_intervals')
)
def bar_battery(n_intervals):
    data = fetch_battery_data_2()
    value = data['payload'][n_intervals % len(data)]
    return value

@app.callback(
    Output('battery-bar', 'color'), 
    Output('battery-led', 'color'),
    Input('update-interval', 'n_intervals')
)
def get_battery_color():
    battery_level = bar_battery()
    if battery_level >= 30:
        return "green"
    elif 10 <= battery_level < 30:
        return "yellow"
    else:
        return "red"

@app.callback(
    Output('humidity-plot', 'figure'),
    Input('update-interval', 'n_intervals')
)
def plot_humidity():
    data = fetch_humidity_data()
    data['timestamp'] = data['timestamp'].dt.time
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['payload'], mode='lines', name='Humidity'))
    fig.update_xaxes(type='category', tickformat='%H:%M:%S')
    fig.update_layout(title='Real Time Humidity Plot - Last 5 Minutes',
                      #xaxis_title='Timestamp',
                      yaxis_title='Humidity (%)')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
