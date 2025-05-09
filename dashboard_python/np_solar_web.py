import dash
import pandas as pd
import dash_daq as daq
from dash import dcc, html
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime
from sqlalchemy import create_engine
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output


################################# Fetch Page 1 Data ###########################################
DATABASE_URI_1 = 'mysql+mysqlconnector://root:password@localhost:3306/ftp_data'
engine_1 = create_engine(DATABASE_URI_1)

def fetch_inverter_1_data():
    query = ''' 
    SELECT
        Time, 
        Upv1, Upv2, Upv3, Upv4, Upv5, Upv6, Upv7, Upv8,
        Ipv1, Ipv2, Ipv3, Ipv4, Ipv5, Ipv6, Ipv7, Ipv8,
        Uac1, Uac2, Uac3,
        Iac1, Iac2, Iac3,
        Temp
    FROM
        inverter_1
    ORDER BY
        Time DESC;
    '''
    df_1 = pd.read_sql_query(query, engine_1)
    return df_1

def fetch_inverter_2_data():
    query = ''' 
    SELECT
        Time, 
        Upv1, Upv2, Upv3, Upv4, Upv5, Upv6, Upv7, Upv8,
        Ipv1, Ipv2, Ipv3, Ipv4, Ipv5, Ipv6, Ipv7, Ipv8,
        Uac1, Uac2, Uac3,
        Iac1, Iac2, Iac3,
        Temp
    FROM
        inverter_2
    ORDER BY
        Time DESC;
    '''
    df_2 = pd.read_sql_query(query, engine_1)
    return df_2

def fetch_total_energy_data():
    query = '''
    SELECT
        Time,
        Pac,
        `E-Day`, `E-Total`
    FROM
        total_energy
    ORDER BY
        Time DESC;
    '''
    df_sum = pd.read_sql_query(query, engine_1)
    return df_sum


################################# Fetch Page 2 Data ###########################################
DB_URI_2 = "mysql+mysqlconnector://root:password@localhost:3306/mqtt_data"
engine_2 = create_engine(DB_URI_2)

# Function to fetch temperature data
def fetch_temperature_data():
    query = f'''
        SELECT timestamp, temperature_bme280 
        FROM solar_iot_box 
        ORDER BY timestamp DESC 
        LIMIT 1
    '''
    df = pd.read_sql_query(query, engine_2)
    return df

# Function to fetch humidity data
def fetch_humidity_data():
    query = f'''
        SELECT humidity_bme280 + 20 AS humidity, timestamp
        FROM solar_iot_box 
        ORDER BY timestamp DESC
        LIMIT 1
    '''
    df = pd.read_sql_query(query, engine_2)
    return df

def fetch_light_data():
    query = f'''
        SELECT timestamp, light_bh1750 
        FROM solar_iot_box 
        ORDER BY timestamp DESC 
        LIMIT 1
    '''
    df = pd.read_sql_query(query, engine_2)
    return df

def fetch_battery_data_1():
    query = f'''
        SELECT timestamp, voltage_battery
        FROM solar_iot_box 
        ORDER BY timestamp DESC 
        LIMIT 1
    '''
    df = pd.read_sql_query(query, engine_2)
    return df

def fetch_battery_data_2():
    query = f'''
        SELECT timestamp, level_battery 
        FROM solar_iot_box 
        ORDER BY timestamp DESC 
        LIMIT 1
    '''
    df = pd.read_sql_query(query, engine_2)
    return df

# Solar power capacities data
solar_power_capacities = {
    "SN2-NAP47-599489": 115.05,
    "SN2-NAP39-599489": 175.5,
    "SN2-NAP83-599489": 43.55,
    "SN2-NAP52-599489": 44.85,
    "SN2-NAP72-599489": 64.675,
    "SN2-NAP50-599489": 56.55,
    "SN2-NAPCC-599489": 147.55,
    "SN2-NAP56-599489": 24.7,
    "SN2-NAP80-599489": 78.65,
    "SN2-NAP37-599489": 114.4,
    "SN2-NAP40-599489": 175.5,
    "SN2-NAP34-599489": 37.05,
    "SN2-NAP81-599489": 89.375,
    "SN2-NAP58-599489": 69.225,
}


#################################### Initialize Dash app with Bootstrap ##########################################
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Set Mapbox access token
mapbox_token = 'pk.eyJ1IjoicGVycnk2IiwiYSI6ImNscGp4djcybTA0MWgyaW56amNndGk5YnEifQ.nkNtsN46y8hR0VcP-aIRtA'
mapbox_style = 'mapbox://styles/mapbox/outdoors-v12'

# Define the sidebar
sidebar = html.Div(
    [
        html.Img(src="https://www.np.edu.sg/images/default-source/default-album/img-logo.png", style={"width": "280px", "height": "70px"}),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Synergy Lab", href="/page-1", active="exact"),
                dbc.NavLink("Solar Prediction", href="/page-2", active="exact")
                # Add more navigation items here
            ],
            vertical=True,
            pills=True,
        )
    ],
style={"width": "100%", "height": "100vh", "padding": "2rem 1rem", 'borderRight': '2px solid', 'borderColor': '#d6d6d6'}
)

# Define the main content area (initially blank)
content = html.Div(id="page-content")

# Update the app layout to include both the sidebar and the main content
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(sidebar, width=2),
                dbc.Col(content, width=10),
            ]
        ),
        dcc.Location(id="url"),
    ],
    fluid=True
)

# Callbacks for navigation and page content
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def render_page_content(pathname):
    if pathname == "/":
        ######################################### layout for the home page #######################################################
        return dbc.Container(
            [
                dbc.Row(
                    dbc.Col(
                        html.H1("NP Solar Dashboard", className="text-center mt-3 mb-4", style={'color': '#34568B'}),
                    ),
                    justify="center"
                ),

                dbc.Row(
                    [
                        dbc.Col(
                            daq.Gauge(
                                id="temperature-gauge",
                                showCurrentValue=True,
                                color={"gradient":True,"ranges":{"blue":[0,15],"green":[15,30],"yellow":[30,40],"red":[40,50]}},
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
                                color={"gradient":True,"ranges":{"orange":[0,70], "blue":[70,100]}},
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
                                color={"gradient":True,"ranges":{"white":[0,1000],"yellow":[1000,10000],"orange":[10000,40000],"red":[40000, 50000]}},
                                label='Light Intensity',
                                max=50000,
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
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33359],
                                        "lon": [103.77404],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 34 : 3%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(95, 211, 95)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33274],
                                        "lon": [103.77311],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 37 : 9.25%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(148, 103, 189)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33309],
                                        "lon": [103.77245],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 39 : 14.2%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(31, 119, 180)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33273],
                                        "lon": [103.77202],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 40 : 14.2%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(255, 127, 14)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33241],
                                        "lon": [103.77261],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 47 : 9.3%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(214, 39, 40)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33163],
                                        "lon": [103.77397],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 50 : 4.57%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(23, 190, 207)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33178],
                                        "lon": [103.77501],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 52 : 3.63%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(87, 169, 226)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33238],
                                        "lon": [103.77548],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "NPCC : 11.9%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(44, 160, 44)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33312],
                                        "lon": [103.77613],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 56 : 2%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(231, 124, 124)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33306],
                                        "lon": [103.77510],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 58 : 5.6%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(127, 127, 127)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33186],
                                        "lon": [103.77594],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 72 : 5.23%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(188, 189, 34)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33051],
                                        "lon": [103.77441],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 80 : 6.36%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(227, 119, 194)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33020],
                                        "lon": [103.77496],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 81 : 7.23%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(140, 86, 75)"},
                                        },
                                        {
                                        "type": "scattermapbox",
                                        "lat": [1.33060],
                                        "lon": [103.77497],
                                        "hoverinfo": "text+lon+lat",
                                        "text": "Blk 83 : 3.52%",
                                        "mode": "markers",
                                        "marker": {"size": 15, "color": "rgb(255, 181, 116)"},
                                        }
                                    ],
                                    "layout": {
                                        "mapbox": {
                                            "accesstoken": mapbox_token,
                                            "style": mapbox_style,
                                            "center": dict(lat=1.33212, lon=103.77458),
                                            "zoom": 15.5
                                        },
                                        "width": 700,
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
                            width=7,
                            className="mb-4"
                        ),

                        dbc.Col(
                            dcc.Graph(
                                id='solar_power_pie_chart',
                                figure={
                                    'data': [
                                        go.Pie(
                                            labels=list(solar_power_capacities.keys()),
                                            values=list(solar_power_capacities.values()),
                                            pull=[0.1]*len(solar_power_capacities)  # Optional: Pulls slices out for emphasis
                                        )
                                    ],
                                    'layout': go.Layout(
                                        title='Solar Power Capacity by Block'
                                    )
                                }
                            ),
                            width=5,
                            className="mb-4"
                        )
                    ],
                    justify="center"
                ),

                dcc.Interval(
                    id='update-interval',
                    interval=5 * 1000,  # Update every 5 seconds
                    n_intervals=0
                )
            ],
            style={'margin-top': '20px', 'margin-bottom': '20px'}
        )
     
    elif pathname == "/page-1":
        ######################################### layout for the page 1 #######################################################
        return dbc.Container([
            html.H1("Solar Plant PV Output", className="text-center mt-3 mb-4", style={'color': '#34568B', 'marginTop': '30px'}),

            dcc.Interval(
                id='interval-component',
                interval=1*60000,
                n_intervals=0
            ),

            dbc.Row([
                dbc.Col(dcc.Graph(id='top_left', figure={}), width=6),
                dbc.Col(dcc.Graph(id='top_right', figure={}), width=6)
            ]),

            dbc.Row([
                dbc.Tabs([
                    dbc.Tab(
                        label='inverter_1',
                        children=[
                            dbc.Row([
                                dbc.Col(dcc.Graph(id='bottom_left_1', figure={}), width=6),
                                dbc.Col(dcc.Graph(id='bottom_right_1', figure={}), width=6)
                            ])
                        ]
                    ),
                    dbc.Tab(
                        label='inverter_2',
                        children=[
                            dbc.Row([
                                dbc.Col(dcc.Graph(id='bottom_left_2', figure={}), width=6),
                                dbc.Col(dcc.Graph(id='bottom_right_2', figure={}), width=6)
                            ])
                        ]
                    )
                ])
            ])
        ],
        style={'marginTop': '30px'},
        )
    
    elif pathname == "/page-2":
        ######################################### layout for the page 2 #######################################################
        return html.P("This is Page 2")
    # Add more elif statements for other navigation items
    else:
        return html.P("This is a 404")


################################################## Callbacks for Page 1 ######################################################
@app.callback(
    Output('top_left', 'figure'),
    Input('interval-component', 'n_intervals'))

def graph_1(n_intervals):
    # Graph 1: Daily Energy over Time
    df = fetch_total_energy_data()
    current_date = datetime.now().date()
    df_today = df[(df['Time'].dt.date == current_date) & (df['Time'].dt.hour >= 6)]
    fig = px.line(df_today, x=df_today['Time'], y=df_today['E-Day'], title='Daily Energy over Time')
    fig.update_layout(yaxis_title='Daily Energy(kWh)')
    return fig

@app.callback(
    Output('bottom_left_1', 'figure'),
    Input('interval-component', 'n_intervals'))

def graph_2_1(n_intervals):
    # Graph 2_1: String Current Inputs Over Time
    df = fetch_inverter_1_data()
    current_date = datetime.now().date()
    df_today = df[(df['Time'].dt.date == current_date) & (df['Time'].dt.hour >= 6)]
    fig = go.Figure()
    for i in range(1, 9, 2):    
        fig.add_trace(go.Scatter(
            x=df_today['Time'], 
            y=df_today[f'Ipv{i}'], 
            mode='lines',
            name=f'Current{i}'
        ))
    fig.update_layout(title='String Current Inputs Over Time', xaxis_title='Time', yaxis_title='Current(A)', legend_title='String')
    return fig

@app.callback(
    Output('bottom_left_2', 'figure'),
    Input('interval-component', 'n_intervals'))

def graph_2_2(n_intervals):
    # Graph 2_2: String Current Inputs Over Time
    df = fetch_inverter_2_data()
    current_date = datetime.now().date()
    df_today = df[(df['Time'].dt.date == current_date) & (df['Time'].dt.hour >= 6)]
    fig = go.Figure()
    for i in range(1, 9, 2):    
        fig.add_trace(go.Scatter(
            x=df_today['Time'], 
            y=df_today[f'Ipv{i}'], 
            mode='lines',
            name=f'Current{i}'
        ))
    fig.update_layout(title='String Current Inputs Over Time', xaxis_title='Time', yaxis_title='Current(A)', legend_title='String')
    return fig

@app.callback(
    Output('bottom_right_1', 'figure'),
    Input('interval-component', 'n_intervals'))

def graph_3_1(n_intervals):
    # Graph 3_1: String Voltage Inputs Over Time
    df = fetch_inverter_1_data()
    current_date = datetime.now().date()
    df_today = df[(df['Time'].dt.date == current_date) & (df['Time'].dt.hour >= 6)]
    fig = go.Figure()
    for i in range(1, 9):
        fig.add_trace(go.Scatter(
            x=df_today['Time'], 
            y=df_today[f'Upv{i}'], 
            mode='lines',
            name=f'Voltage{i}'
        ))
    fig.update_layout(title='String Voltage Inputs Over Time', xaxis_title='Time', yaxis_title='Voltage(V)', legend_title='String')
    return fig

@app.callback(
    Output('bottom_right_2', 'figure'),
    Input('interval-component', 'n_intervals'))

def graph_3_2(n_intervals):
    # Graph 3_2: String Voltage Inputs Over Time
    df = fetch_inverter_2_data()
    current_date = datetime.now().date()
    df_today = df[(df['Time'].dt.date == current_date) & (df['Time'].dt.hour >= 6)]
    fig = go.Figure()
    for i in range(1, 9):
        fig.add_trace(go.Scatter(
            x=df_today['Time'], 
            y=df_today[f'Upv{i}'], 
            mode='lines',
            name=f'Voltage{i}'
        ))
    fig.update_layout(title='String Voltage Inputs Over Time', xaxis_title='Time', yaxis_title='Voltage(V)', legend_title='String')
    return fig

@app.callback(
    Output('top_right', 'figure'),
    Input('interval-component', 'n_intervals'))

def graph_4(n_intervals):
    # Graph 4: Pac over Time
    df = fetch_total_energy_data()
    current_date = datetime.now().date()
    df_today = df[(df['Time'].dt.date == current_date) & (df['Time'].dt.hour >= 6)]
    fig = px.line(df_today, x=df_today['Time'], y=df_today['Pac'], title='Pac over Time')
    fig.update_layout(yaxis_title='Output Power(kW)')
    return fig


################################################## Callbacks for Page 2 ########################################################
@app.callback(
    Output('temperature-gauge', 'value'),
    Input('update-interval', 'n_intervals')
)
def plot_temperature(n_intervals):
    data = fetch_temperature_data()
    value = data['temperature_bme280'].iloc[0]
    return value

@app.callback(
    Output('humidity-gauge', 'value'),
    Input('update-interval', 'n_intervals')
)
def gauge_humidity(n_intervals):
    data = fetch_humidity_data()
    value = data['humidity'].iloc[0]
    return value

@app.callback(
    Output('light-gauge', 'value'),
    Input('update-interval', 'n_intervals')
)
def gauge_light(n_intervals):
    data = fetch_light_data()
    value = data['light_bh1750'].iloc[0]
    return value

@app.callback(
    Output('battery-led','value'),
    Input('update-interval', 'n_intervals')       
)
def led_battery(n_intervals):
    data = fetch_battery_data_1()
    value = data['voltage_battery'].iloc[0]
    return value

@app.callback(
    Output('battery-bar', 'value'),
    Input('update-interval', 'n_intervals')
)
def bar_battery(n_intervals):
    data = fetch_battery_data_2()
    value = data['level_battery'].iloc[0]
    return value

@app.callback(
    Output('battery-bar', 'color'), 
    Output('battery-led', 'color'),
    Input('update-interval', 'n_intervals')
)
def get_battery_color(n_intervals):
    data = fetch_battery_data_2()
    value = data['level_battery'].iloc[0]
    if value >= 20:
        return "green", "green"
    elif 10 <= value < 20:
        return "yellow", "yellow"
    else:
        return "red", "red"


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
