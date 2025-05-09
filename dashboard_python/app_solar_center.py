import dash
from dash import dcc
from dash import html
import plotly.express as px
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine

# Replace with your database connection details
DATABASE_URI = 'mysql+mysqlconnector://root:password@localhost:3306/ftp_data'
engine = create_engine(DATABASE_URI)

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
    df_1 = pd.read_sql_query(query, engine)
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
    df_2 = pd.read_sql_query(query, engine)
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
    df_sum = pd.read_sql_query(query, engine)
    return df_sum

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


# Define app layout
app.layout = dbc.Container([
    html.H1("Solar Plant Visualization", className='text-center', style={'marginTop': '30px'}),

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

@app.callback(
    Output('top_left', 'figure'),
    Input('interval-component', 'n_intervals'))

def graph_1(n_intervals):
    # Graph 1: Daily Energy over Time
    df = fetch_total_energy_data()
    current_date = datetime.now().date()
    df_today = df[(df['Time'].dt.date == current_date) & (df['Time'].dt.hour >= 6)]
    fig = px.line(df_today, x='Time', y='E-Day', title='Daily Energy over Time')
    fig.update_layout(yaxis_title='Daily Energy (kWh)')
    fig.update_xaxes(
        tickmode='linear',
        tick0=0,
        dtick=3600000,  # 1 hour in milliseconds (adjust as needed)
        tickformat='%H:%M',  # Format for hours and minutes
    )
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
    fig.update_xaxes(
        tickmode='linear',
        tick0=0,
        dtick=3600000,  # 1 hour in milliseconds (adjust as needed)
        tickformat='%H:%M',  # Format for hours and minutes
    )
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
    fig.update_xaxes(
        tickmode='linear',
        tick0=0,
        dtick=3600000,  # 1 hour in milliseconds (adjust as needed)
        tickformat='%H:%M',  # Format for hours and minutes
    )
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
    fig.update_xaxes(
        tickmode='linear',
        tick0=0,
        dtick=3600000,  # 1 hour in milliseconds (adjust as needed)
        tickformat='%H:%M',  # Format for hours and minutes
    )
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
    fig.update_xaxes(
        tickmode='linear',
        tick0=0,
        dtick=3600000,  # 1 hour in milliseconds (adjust as needed)
        tickformat='%H:%M',  # Format for hours and minutes
    )
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
    fig.update_xaxes(
        tickmode='linear',
        tick0=0,
        dtick=3600000,  # 1 hour in milliseconds (adjust as needed)
        tickformat='%H:%M',  # Format for hours and minutes
    )
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)