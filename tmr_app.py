
# Dash libraries
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_table_experiments as dte

import plotly

# Data related packages
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb

# Import other libraires
from datetime import datetime as dt
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY

import pandas as pd
import numpy as np
import copy
import os
import base64
import io
import math
import random
import colorlover as cl


# Graph Related packages
import plotly.plotly as py
import plotly.graph_objs as go


import flask
import requests

# App developed functionality
from PreProcessing import load_data, load_data_csv
from helpers import filter_dataframe, active_users, active_users_type, parse_contents_simple, clean_df_parameters
from helpers import summary_user, user_connections_type, load_summaries, active_users_commute, active_users_summary
from helpers import estimate_kpis, table_cell_style, make_kpi_table, make_dash_table, colormap_commute_mode
from tmr_logger import get_logger, get_console_handler, get_file_handler


# Multi-dropdown options
from controls import TRANSPORT_TYPE, COMMUTE_MODE



pd.options.mode.chained_assignment = None

# Get the logger
logger = get_logger("App")
logger.info(" Running app")

#users, rides, matches = load_data()

users, rides, matches = load_data_csv()
connections_user_type, publicaciones_user_sum, conexiones_user_sum = load_summaries()

logger.info("CHECK DATAFRAMES - INICIO")
logger.info(len(rides))
logger.info(len(users))
logger.info(len(matches))

#conexiones, conductor = summary_user(users, rides, matches)
#connections_user_type = user_connections_type(users, rides, matches)

#COMMUNITIES = matches.community.unique()
transport_type=list(rides.type.unique())

COMMUNITIES = ['Citi Mobility Bogota', 'Colpatria', 'Try My Ride', 'UnBosque', 'Compensar', 'Equion', 'Connecta Colectiva', 'ServiEntrega Bogotá', 'MTS Bogota', 'Fontanar Bogotá', 'UNGRD', 'Isarco', 'Bancolombia Medellín', 'Orbis.Com', 'Bancolombia Bogotá', 'ISA', 'Grupo Exito Medellín', 'Comunidad Familia', 'Comunidad TCC', 'Itau', 'Grupo Exito Bogotá', 'ServiEntrega Medellín', 'Protección', 'Comfandi', 'TUYA']
COMMUNITIES.sort()

COMMUNITIES_ALL = copy.deepcopy(COMMUNITIES)
COMMUNITIES_ALL.append('TODAS')

transport_type.append('all')
transport_type.sort()



# LOAD PARAMS
params = df = pd.read_excel('data/puntajes.xlsx')
params_clean, ok, msg = clean_df_parameters(params, COMMUNITIES)


# Define some layout variables
msize = 11
gheight = 320
gwdith = 400
mtop ='10'
ftxt_size =11
layout_margin = {"r": 30, "t": 40, "b": 60, "l": 60}
legend_layout = dict(
    x=0,
    y=1.4,
    traceorder='normal',
    font=dict(
        family='sans-serif',
        size=12,
        color='#000'
    ),
    bgcolor='#E2E2E2',
    bordercolor='#FFFFFF',
    borderwidth=2
)

#rows=params.to_dict('records')

# Start with the dash app

app = dash.Dash(__name__)
server = app.server
app.config['suppress_callback_exceptions'] = True

# Add a static image route that serves images from desktop
# Be *very* careful here - you don't want to serve arbitrary files
# from your computer or server
css_directory = os.getcwd()
stylesheets = ['stylesheet.css']
static_css_route = '/static/'


@app.server.route('{}<stylesheet>'.format(static_css_route))
def serve_stylesheet(stylesheet):
    if stylesheet not in stylesheets:
        raise Exception(
            '"{}" is excluded from the allowed static files'.format(
                stylesheet
            )
        )
    return flask.send_from_directory(css_directory, stylesheet)


for stylesheet in stylesheets:
    app.css.append_css({"external_url": "/static/{}".format(stylesheet)})

external_css = ["https://cdnjs.cloudflare.com/ajax/libs/normalize/7.0.0/normalize.min.css",
                "https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
                "//fonts.googleapis.com/css?family=Raleway:400,300,600",
                #"https://codepen.io/bcd/pen/KQrXdb.css",
                "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css",
                "https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css"]

for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ["https://code.jquery.com/jquery-3.2.1.min.js",
               "https://codepen.io/bcd/pen/YaXojL.js"]

for js in external_js:
    app.scripts.append_script({"external_url": js})


layout = dict(
    autosize=True,
    height=500,
    font=dict(color="#191A1A"),
    titlefont=dict(color="#191A1A", size='14'),
    margin=dict(
        l=35,
        r=35,
        b=35,
        t=45
    ),
    hovermode="closest",
    plot_bgcolor='#fffcfc',
    paper_bgcolor='#fffcfc',
    legend=dict(font=dict(size=10), orientation='h'),
    title='Each dot is an NYC Middle School eligible for SONYC funding',
    mapbox=dict(
        accesstoken='',#mapbox_access_token,
        style="light",
        center=dict(
            lon=-73.91251,
            lat=40.7342
        ),
        zoom=10,
    )
)


# Creating layouts for datatable
layout_right = copy.deepcopy(layout)
layout_right['height'] = 300
layout_right['margin-top'] = '20'
layout_right['font-size'] = '12'


#------------------------------------------------

dftable = pd.DataFrame(np.random.randn(50, 4), columns=['aaaaaaaaaaaaaaaaad   aaaaaaaaaaaaaaa akj;alkjflasflajflak  ljalkfjaldjfladsfj ljaflkjdalfjasdlfj lkaldjfladjf aaaaaaaaaaaaaa aaaaaaaa','bbbbbbbbbbb','cccccccccc','ddddddddddddddddddddddddd'])


def get_actual_period():

    # reduce date at least a month

    td = dt.today().strftime('%Y-%m-%d')
    d1 = dt.strptime(td, '%Y-%m-%d')
    d1 = d1.replace(day=1)
    one_month = relativedelta(months=1)
    d2 = d1 - one_month
    return(d2.strftime("%Y-%m-%d"))


def get_slider_marks():
    td = dt.today().strftime('%Y-%m')
    d1 = dt.today()
    year = d1.year-1

    d2 = d1.replace(year=year)
    d1 = d1.replace(day=1)
    oneMonth = relativedelta(months=1)
    months = [dat.strftime("%Y-%m")
              for dat in rrule(MONTHLY, dtstart=d2,
                              until=d1+oneMonth)]

    marks = {str(year): i for year, i in enumerate(months)}
    return marks


#------------------------------------------------
#app.css.config.serve_locally = True
#app.scripts.config.serve_locally = True


app.layout = html.Div([
    html.Div(
        [
            html.H5(
                'Try My Ride - Reporte Usuarios',
                className='eight columns',
            ),
            html.Img(
                src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe.png",
                className='one columns',
                style={
                    'height': '100',
                    'width': '125',
                    'float': 'right',
                    'position': 'relative',
                },
            ),
        ],
        className='row'
    ),

    html.Div(
        [
            html.Div(
                [

                    html.H5('Seleccione Comunidad:'),
                    dcc.Dropdown(
                        id='dropdown_com',
                        options=[{'label': i, 'value': i} for i in COMMUNITIES_ALL],
                        value=['Bancolombia Medellín'],
                        multi=True
                    )
                ],
                className='seven columns'
                , style={'margin-top': mtop,'margin-left': 30}
            ),

        ],
        className='row'
    ),
    html.Div(
        [

            html.Div(
                [
                    html.H5('Periodo de tiempo:'),

                    dcc.DatePickerRange(
                        id='date-picker-range',
                        start_date=dt(2018, 1, 2),
                        end_date=dt.today().strftime('%Y-%m-%d'),
                        display_format='DD-MM-YY'
                    ),
                ],
                className='seven columns',
                style={'margin-left': 30, 'margin-right': 10, 'margin-top': mtop}

            ),

        ],
        className='row'
    ),






# Tabs information
    dcc.Tabs(id="tabs", vertical=False, children=[


# ----------------------------------------------------------------------------
#  TAB AVANCES COMUNIDADES
# ----------------------------------------------------------------------------


        dcc.Tab(label='Avances Comunidades', children=[
            html.Div([
                html.H5('Periodo:'),
                dcc.DatePickerSingle(
                    date=get_actual_period(),
                    display_format='MMM , YY',
                    id = 'date-picker-advances'
                    )
            ], className='row'),



            html.Div(children=[
                #html.Table(make_kpi_table(score_card))
            ], className='row'),

            # Add scorecard
            html.Div(html.Table(id='advances_table'),
                     className="three columns"
                     , style={'margin-left': 10, 'margin-right': 10, 'margin-top': mtop}
                     )

        ]),

# ----------------------------------------------------------------------------
#  TAB EVOLUCION
# ----------------------------------------------------------------------------


        dcc.Tab(label='Periodo Acumulado', children=[
            html.Div([

                html.Div([

                    html.Div([

                        html.H5("Frecuencia"),
                        dcc.RadioItems(
                            id='frequency',
                            options=[
                                {'label': 'Anual ', 'value': 'Y'},
                                {'label': 'Semestral', 'value': '6M'},
                                {'label': 'Mensual ', 'value': 'M'},
                                {'label': 'Semanal', 'value': 'W'}],
                            value='M',
                            labelStyle={'display': 'inline-block'}
                        )

                    ],
                        className='six columns'),

                ], className='row'
                ),

                # Row 2
                html.Div(
                    [
                        html.Div(
                            [
                                html.H6("Tipo de Usuario"),
                                dcc.RadioItems(
                                    id='user_type',
                                    options=[
                                        {'label': 'Registrados ', 'value': 'all'},
                                        {'label': 'Activos', 'value': 'active'},

                                    ],
                                    value='active',
                                    labelStyle={'display': 'inline-block'}
                                ),
                            ],
                            className='six columns',
                            style={'margin-top': '10'}
                        ),

                        #

                        html.Div(
                            [
                                html.H6("Medio de transporte"),
                                dcc.RadioItems(
                                    id='trans_type_pub',
                                    options=[{'label': key, 'value': val} for key, val in TRANSPORT_TYPE.items()],
                                    # TRANSPORT_TYPE
                                    value='all',
                                    labelStyle={'display': 'inline-block'}
                                )

                            ],className='six columns',
                            style={'margin-top': mtop}),


                    ],
                    className='row',
                    style={'margin-top': mtop}
                ),

                # Row 3

                html.Div([

                    html.Div([
                        html.P('KPIs',
                               className="gs-header gs-text-header padded"),

                        # Add scorecard
                        html.Div(html.Table(id='kpi_table'),
                                 className= "three columns"
                                 , style={'margin-left': 10, 'margin-right': 10,'margin-top': mtop }
                        )
                        #
                        # dte.DataTable(rows=score_card.to_dict('records'),
                        #               columns=score_card.columns,
                        #               id = 'params_table'),


                    ], className="seven columns"


                    ),

                    html.Div([
                        html.P(["Usuarios registrados/poblacion"],
                                className="gs-header gs-table-header padded"),
                        dcc.Graph(id='users_bar_pob'),

                    ], className="five columns"),

                ], className="row",
                    style={'margin-top': mtop}),

                # Row 4

                html.Div([

                    html.Div([
                        html.P('Usuarios',
                                className="gs-header gs-text-header padded"),
                        dcc.Graph(id='users_count')

                    ], className="seven columns"),

                    html.Div([
                        html.P("Usuarios activos/registrados",
                                className="gs-header gs-table-header padded"),
                        dcc.Graph(id='users_bar')
                    ], className="five columns"),

                    ], className="row",
                    style={'margin-top': mtop}),

                 # Row 5
                html.Div(
                    [
                        html.Div(
                            [
                                html.P('Comportamiento de Publicaciones & Conexiones',
                                        className="gs-header gs-text-header padded"),
                                dcc.Graph(id='pub_con_count'),


                            ],
                            className='six columns',
                            style={'margin-top': mtop}
                        ),
                        html.Div(
                            [
                                html.P('Efectividad del programa (conexiones son contadas una sola vez)',
                                        className="gs-header gs-table-header padded"),
                                dcc.Graph(id='pub_con_effect'),


                            ],
                            className='six columns',
                            style={'margin-top': mtop}
                        ),
                    ],
                    className='row',
                    style={'margin-top': mtop}
                ),

                # Row 6

                html.Div(
                    [
                        html.Div(
                            [
                                html.P('Promedio* de Publicaciones & Conexiones',
                                       className="gs-header gs-text-header padded"),
                                dcc.Graph(id='pub_con_prom'),
                                html.P('*Promedio estimado semanalmente incluyendo dias habiles'),

                            ],
                            className='six columns',
                            style={'margin-top': mtop}
                        ),
                        html.Div(
                            [
                                html.P('Cantidad de pasajeros y conductores por perfil',
                                       className="gs-header gs-table-header padded"),
                                dcc.Graph(id='perfil_usuario'),

                            ],
                            className='six columns',
                            style={'margin-top': mtop}
                        ),
                    ],
                    className='row',
                    style={'margin-top': mtop}
                ), # close div

            # Row 7


                # Row 8

                html.Div(
                    [
                        html.Div(
                            [
                                html.P('Distribucion Publicaciones & Conexiones por horario',
                                       className="gs-header gs-text-header padded"),
                                dcc.Graph(id='pub_con_hora_bar'),

                            ],
                            className='six columns',
                            style={'margin-top': mtop}
                        ),
                        html.Div(
                            [
                                html.P('Distribucion horas de publicacion',
                                       className="gs-header gs-table-header padded"),
                                dcc.Graph(id='pub_hora_bar'),

                            ],
                            className='six columns',
                            style={'margin-top': mtop}
                        ),
                    ],
                    className='row',
                    style={'margin-top': mtop}
                ),  # close div


            ]), # close tab div




        ]), # close tab


# ----------------------------------------------------------------------------
#  TAB MIGRACION
# ----------------------------------------------------------------------------


        dcc.Tab(label='Migracion', children=[
            html.Div(
                [
                    html.Div(
                        [
                            html.P('Puntaje de Publicaciones & Conexiones',
                                   className="gs-header gs-text-header padded"),
                            dcc.Graph(id='migration_bar'),

                        ],
                        className='six columns',
                        style={'margin-top': '10'}
                    ),
                    html.Div(
                        [
                            html.P('Migración de tiempo de transporte',
                                   className="gs-header gs-table-header padded"),
                            dcc.Graph(id='migration_bar2'),

                        ],
                        className='six columns',
                        style={'margin-top': '10'}
                    ),
                ],
                className='row',
                style={'margin-top': '10'}
            ),  # close div


            # Row 2

            html.Div([
                html.P('Migración de tiempo de transporte',
                       className="gs-header gs-table-header padded"),

                dcc.Graph(id='migration_graph'),
                dcc.Slider(
                    id='migration-slider',
                    min=0,
                    max=12,
                    value=11,
                    step=None,
                    marks=get_slider_marks()
                )

            ],
                className='twelve columns'),
            html.Div([
                html.P('Medio de Transporte Actual por Localización',
                       className="gs-header gs-table-header padded"),
                dcc.Checklist(
                    options=[{'label': 'Mas de un usuario', 'value': 1}],
                    values=[],
                    id='check_location'

                ),
                dcc.Graph(id='medio_location'),
                html.Br(),
                html.Br(),
                dcc.RadioItems(
                    options=[{'label': 'Todos usuarios', 'value': 0},
                             {'label': ' Mas d 5 usuarios', 'value': 5},
                              {'label': ' 10 usuarios', 'value': 10},
                             {'label': ' 20 usuarios', 'value': 20}],
                    value=0,
                    id='check_location2',
                    labelStyle={'display':'inline-block'}),

                dcc.Graph(id='medio_location2'),

            ],
                className='twelve columns'
                , style={'margin-top': '30'})


        ]), # Cierre tab


# ----------------------------------------------------------------------------
#  TAB PERIODO ACTUAL
# ----------------------------------------------------------------------------


        dcc.Tab(label='Periodo Actual', children=[
            html.Div([

                html.Div([
                    html.Div(
                        [
                            html.H5('Periodo:'),
                            dcc.DatePickerSingle(
                                date=get_actual_period(),
                                display_format='MMM , YY',
                                id='date-picker-month'
                            )
                        ],
                        className='six columns'

                    ),

                    html.Div([

                        html.H5("Frecuencia"),
                        dcc.RadioItems(
                            id='frequency_month',
                            options=[

                                {'label': 'Semanal', 'value': 'W'},
                                {'label': 'Diaria ', 'value': 'D'}
                            ],
                            value='D',
                            labelStyle={'display': 'inline-block'}
                        )

                    ],
                        className='six columns'),

                ], className='row'
                ),

                # Row 2
                html.Div(
                    [

                        html.Div(
                            [
                                html.H6("Medio de transporte"),
                                dcc.RadioItems(
                                    id='trans_type_pub_month',
                                    options=[{'label': key, 'value': val} for key, val in TRANSPORT_TYPE.items()],
                                    # TRANSPORT_TYPE
                                    value='all',
                                    labelStyle={'display': 'inline-block'}
                                )

                            ], className='six columns',
                            style={'margin-top': mtop}),

                    ],
                    className='row',
                    style={'margin-top': mtop}
                ),

                # Row 3

                html.Div([

                    html.Div([
                        html.P('KPIs',
                               className="gs-header gs-text-header padded"),

                        # Add scorecard
                        html.Div(html.Table(id='kpi_table_month'),
                                 className="three columns"
                                 , style={'margin-left': 10, 'margin-right': 10, 'margin-top': mtop}
                                 )
                        #
                        # dte.DataTable(rows=score_card.to_dict('records'),
                        #               columns=score_card.columns,
                        #               id = 'params_table'),

                    ], className="seven columns"

                    ),

                    html.Div([
                        html.P(["Usuarios por medio de transporte"],
                               className="gs-header gs-table-header padded"),
                        dcc.Graph(id='users_med_trans'),

                    ], className="five columns"),

                ], className="row",
                    style={'margin-top': mtop}),

                # Row 4

                html.Div([
                        html.P('Usuarios',
                               className="gs-header gs-text-header padded"),
                        dcc.Graph(id='pub_con_count_month')

                    ], className="twelve columns"),

                # Row 5
                html.Div(
                    [
                        html.Div(
                            [
                                html.P('Distribucion Publicaciones & Conexiones por horario',
                                       className="gs-header gs-text-header padded"),
                                dcc.Graph(id='pub_con_hora_bar_month'),

                            ],
                            className='six columns',
                            style={'margin-top': mtop}
                        ),
                        html.Div(
                            [
                                html.P('Distribucion horas de publicacion',
                                       className="gs-header gs-table-header padded"),
                                dcc.Graph(id='pub_hora_bar_month'),

                            ],
                            className='six columns',
                            style={'margin-top': mtop}
                        ),
                    ],
                    className='row',
                    style={'margin-top': mtop}
                ),  # close div

                # Last row

                html.Div(
                    [
                        html.Div(
                            [
                                html.P('Participación de conductores',
                                       className="gs-header gs-text-header padded"),
                                dcc.Graph(id='hist_driver'),

                            ],
                            className='six columns',
                            style={'margin-top': mtop}
                        ),
                        html.Div(
                            [
                                html.P('Participación de pasajeros',
                                       className="gs-header gs-table-header padded"),
                                dcc.Graph(id='hist_pass'),

                            ],
                            className='six columns',
                            style={'margin-top': mtop}
                        ),
                    ],
                    className='row',
                    style={'margin-top': mtop}
                ),  # close div

            ], className='row')
        ]),


# ----------------------------------------------------------------------------
#  TAB Top Drivers
# ----------------------------------------------------------------------------

        dcc.Tab(label='Puntaje', children=[

            html.Div([

                html.Div([
                    html.H5('Periodo:'),
                    dcc.DatePickerSingle(
                        date=get_actual_period(),
                        display_format='MMM , YY',
                        id='date-picker-puntaje'
                    )
                ], className='six columns'),

                html.Div([

                    html.H5("Acumulado"),
                    dcc.RadioItems(
                        id='radio_scores',
                        options=[
                            {'label': '12 Meses ', 'value': '12'},
                            {'label': '6 Meses', 'value': '6'},
                            {'label': '3 Meses', 'value': '3'}],
                        value='12',
                        labelStyle={'display': 'inline-block'}
                    )

                ],
                    className='six columns'),

            ], className='row'
            ),


            # Row 3

            html.Div([

                html.Div([
                    html.P('Puntaje Detallado por Usuario',
                            className="gs-header gs-text-header padded"),

                    # Add scorecard
                    html.A('Download Scores CSV', id='my-link'),
                    dte.DataTable(#rows=score_card.to_dict('records'),
                                  #columns=score_card.columns,
                                id='scores_table',
                                row_selectable=True,
                                filterable=True,
                                sortable=True,
                                selected_row_indices=[],
                    ),


                ], className="twelve columns"),

                html.Div([
                    html.P(["Puntaje Usuarios"],
                            className="gs-header gs-table-header padded"),
                    dcc.Graph(
                        id='scores_fig'
                    ),

                ], className="twelve columns"),

            ], className="row "),






        ]),

# ----------------------------------------------------------------------------
#  TAB Parametros
# ----------------------------------------------------------------------------

        dcc.Tab(label='Parametros', children=[
            html.Div([
                html.H1("Parametrizacion Comunidades"),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    multiple=False),
                html.Br(),
                html.Button(
                    id='propagate-button',
                    n_clicks=0,
                    children='Actualizar datos'
                ),
                html.Div(
                    #html.Table(make_dash_table(params_clean), className="tiny-header")
                    dte.DataTable(rows=params_clean.to_dict('records'),
                                  columns=params_clean.columns,
                                  id='params_table')

                 ),
                html.Div(id='intermediate-value', style={'display': 'none'})
            ],
                style=layout_right
            )
        ]),

        dcc.Tab(label='Glosario', children=[
            html.Div([
                html.H1("Calculos"),
                html.P("Rides tienen mas de una publicacion. Efectividad es solo contada por el numero the rides con matches"
                       "Usuarios pueden tener mas de una comunidad ( por ejemplo bancolombia, estos son contados doble"),

                dcc.Graph(
                    id='graph',
                    style={'width': '600', 'height': '500'}
                ),
            ])
        ]),

    ],
        style={
        'fontFamily': 'system-ui', 'margin-top': '20'
    },
        content_style={
        'borderLeft': '1px solid #d6d6d6',
        'borderRight': '1px solid #d6d6d6',
        'borderBottom': '1px solid #d6d6d6',
        'padding': '44px'
    },
        parent_style={
        'maxWidth': '1300px',
        'margin': '10 px'
    }
    )


]

)


# ----------------------------------------------------------------------------
#  CALLBACKS
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
#  TAB EVOLUCION -
# ----------------------------------------------------------------------------

# callback to update graph
@app.callback(
    Output('users_count', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-range', 'start_date'),Input('date-picker-range', 'end_date'),
     Input('frequency','value'),
     Input('user_type', 'value')
     ]
)

def update_users_graph(community, start_date, end_date, frequency, user_type):

    if 'TODAS' in community:
        community = COMMUNITIES

    if user_type == 'all':
        # Get all the registered users
        # Only filter by community, since it is  cumulative do not filter by date, only
        # filter after the cum sum
        users_ff = users[users['community'].isin(community)]
        users_ff['usuarios'] = 1
        us = users_ff.resample(frequency).agg(dict(usuarios='sum'))
        us_cum = us['usuarios'].cumsum()
        result1 = pd.DataFrame({'date': us_cum.index, 'usuarios': us_cum.values})
        result1 = result1[(result1['date'] >= start_date) & (result1['date'] < end_date)]
        result1.index = result1['date']
        result1.usuarios = result1.usuarios.astype(int)
    else:
        #get only active users, that is either published or connected
    #  Get the list of active users, this only gets the count by day
        act_users = active_users(rides, matches, community, start_date, end_date)
        result1 = act_users.resample(frequency).nunique()
        result1 = result1.rename(columns={'user_id': 'usuarios'})
        result1.drop(columns=['date'], inplace=True)

    # count the number of distinct users per day
    #cnt = active_users.groupby(active_users.index.date)['user_id'].nunique()
    #cnt.index = pd.to_datetime(cnt.index)
    #act_users = pd.DataFrame({'date': cnt.index, 'users': cnt.values})
    #act_users.index= act_users['date']


    if 'date' in result1.columns.tolist():
        result1.drop(columns=['date'], inplace=True)

    # Now get the percentual change
    pct_change = result1.pct_change()
    pct_change = pct_change.rename(columns={'usuarios': 'pct'})

    # Now get the
    result = pd.merge(result1[['usuarios']], 100*pct_change[['pct']], left_index=True, right_index=True, how='outer')



    cols = result.columns.tolist()

    # Get the displaying axis
    result['date'] = pd.to_datetime(result.index)
    #result.reg_users = result.reg_users.astype(int)
    #result.user_id = result.user_id.astype(int)


    if frequency in ['D']:
        result['date']= result['date'].dt.strftime('%Y-%m-%d')
    elif frequency in ['W', '2W']:
        result['date'] = result['date'].dt.strftime('%Y-%W')
    elif frequency in ['M','3M']:
        result['date'] = result['date'].dt.strftime('%Y-%m')
    else:
        result['date'] = result['date'].dt.strftime('%Y')

    # create data list
    traces = []
    formattedList = ["{:,}".format(member) for member in result['usuarios']]
    traces.append(go.Scatter(
        x=np.arange(len(result)),
        y=round(result['usuarios'],1),
        text=formattedList,
        mode='lines+markers+text',
        textposition='bottom center',
        opacity=0.7,
        marker={
            'size': msize,
            'line': {'width': 0.5, 'color': 'white'}
        },

        name="Usuarios"
         )
    )
    formattedList = ["{:.1f}%".format(member) for member in result['pct']]

    delt = result['usuarios'].max()*1.1
    traces.append(go.Scatter(
        x=np.arange(len(result)-1)+0.5,
        y=result[1:]['usuarios']*0+delt,
        text=formattedList[1:],
        textposition='bottom center',
        hoverinfo='text',
        hovertext=formattedList[1:],
        mode='markers+text',
        opacity=0.7,
        marker={
           'size': msize,
           'line': {'width': 0.5, 'color': 'white'}
     },
        name="Porcentage cambio"
         )
    )



    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            font={
                "family": "Raleway",
                "size": ftxt_size
            },
            height=gheight,
            width=600,
            separators=".,",
            xaxis=dict(
                #type='line',
                showgrid=False,
                tickvals=np.arange(len(result)),
                ticktext=result['date'],
                ticks='outside',
                #automargin= True,
                range=[-0.2,len(result)+0.2]
           ),
            yaxis=dict(
                title='Numero de usuarios',
                showgrid=True,
                automargin=True

            ),
            margin={
                "r": 20,
                "t": 40,
                "b": 80,
                "l": 50
            },
            # legend={'x': 0.5, 'y': 1},
            hovermode='closest',
            showlegend=True,
            legend = {
                     "x": -0.1,
                     "y": 1.2,
                     "orientation": "h",
                     "yanchor": "top"
                 },

        )
    }


# ----------------------------------------------------------------------------
#  TAB EVOLUCION - BAR - REGISTERED/ACTIVE USERS
# ----------------------------------------------------------------------------



# callback to update graph
@app.callback(
    Output('users_bar', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-range', 'start_date'),Input('date-picker-range', 'end_date'),
     Input('frequency','value')
     ]
)


def update_users_graph(community, start_date, end_date, frequency):

    if 'TODAS' in community:
        community = COMMUNITIES

    # Only filter by community, since it is  cumulative do not filter by date, only
    # filter after the cum sum
    users_ff = users[users['community'].isin(community)]
    users_ff['reg_users'] = 1
    us = users_ff.resample(frequency).agg(dict(reg_users='sum'))
    us_cum = us['reg_users'].cumsum()
    result1 = pd.DataFrame({'date': us_cum.index, 'reg_users': us_cum.values})
    result1 = result1[(result1['date'] >= start_date) & (result1['date'] < end_date)]
    result1.index = result1['date']
    result1.reg_users = result1.reg_users.astype(int)
    # Now filter by date and get the active users


    # Get the list of active users, this only gets the count by day
    act_users = active_users(rides, matches, community, start_date, end_date)
    result2 = act_users.resample(frequency).nunique()

    # count the number of distinct users per day
    #cnt = active_users.groupby(active_users.index.date)['user_id'].nunique()
    #cnt.index = pd.to_datetime(cnt.index)
    #act_users = pd.DataFrame({'date': cnt.index, 'users': cnt.values})
    #act_users.index= act_users['date']




    # Now get the
    resultf = pd.merge(result1[['reg_users']], result2[['user_id']], left_index=True, right_index=True, how='outer')
    resultf = resultf.rename(columns={'user_id': 'usuarios activos'})
    resultf = resultf.rename(columns={'reg_users': 'usuarios no activos'})
    resultf.fillna(0, inplace=True)

    total = resultf.sum(axis=1)
    total = resultf['usuarios no activos'] # total should be registered users not the sum of the two
    result = resultf.apply(lambda x: 100 * x / total)
    result['usuarios no activos'] = 100 - result['usuarios activos']
    result.fillna(0, inplace=True)

    cols = result.columns.tolist()

    # Get the displaying axis
    result['date'] = pd.to_datetime(result.index)
    #result.reg_users = result.reg_users.astype(int)
    #result.user_id = result.user_id.astype(int)


    if frequency in ['D']:
        result['date']= result['date'].dt.strftime('%Y-%m-%d')
    elif frequency in ['W', '2W']:
        result['date'] = result['date'].dt.strftime('%Y-%W')
    elif frequency in ['M','3M','6M']:
        result['date'] = result['date'].dt.strftime('%Y-%m')
    else:
        result['date'] = result['date'].dt.strftime('%Y')


    # create data list
    traces = []
    for i in cols:
        formattedList = ["{:.0f}%".format(member) for member in result[i]]
        hover_text = ["{:,}".format(int(member)) for member in resultf[i]]

        traces.append(go.Bar(
            x=result.index,
            y=round(resultf[i]),
            text=formattedList,
            textposition='inside',
            name=i,
            hoverinfo='text',
            hovertext=hover_text

             )
        )


    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            barmode='stack',
            showlegend=True,
            #separators=',.',
            font={
                "family": "Raleway",
                "size": ftxt_size
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },
            margin={
                "r": 30,
                "t": 20,
                "b": 60,
                "l": 60
            },

            width=400,

            xaxis=dict(
                # type='line',
                showgrid=True,
                tickvals=result.index,
                ticktext=result['date'],
                ticks='outside',

                automargin=True
            ),
            yaxis=dict(
                title='Numero de usuarios registrados',
                tickformat=',2r',# tickformat=',.2r'
                zeroline= False,
                titlefont=dict(
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    color='rgb(107, 107, 107)'
                )
            )


        )
    }


# ----------------------------------------------------------------------------
#  TAB EVOLUCION - BAR - REGISTERED USERS POPULATION
# ----------------------------------------------------------------------------



# callback to update graph
@app.callback(
    Output('users_bar_pob', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-range', 'start_date'),Input('date-picker-range', 'end_date'),
     Input('frequency','value'),
     #Input('intermediate-value', 'children'),
     Input('params_table', 'rows')
     ]
)


def update_users_graph(community, start_date, end_date, frequency, params_rows):

    if 'TODAS' in community:
        community = COMMUNITIES


    # Only filter by community, since it is  cumulative do not filter by date, only
    # filter after the cum sum
    users_ff = users[users['community'].isin(community)]
    users_ff['reg_users'] = 1
    us = users_ff.resample(frequency).agg(dict(reg_users='sum'))
    us_cum = us['reg_users'].cumsum()
    result1 = pd.DataFrame({'date': us_cum.index, 'reg_users': us_cum.values})
    result1 = result1[(result1['date'] >= start_date) & (result1['date'] < end_date)]
    result1.index = result1['date']
    result1.reg_users = result1.reg_users.astype(int)
    # Now filter by date and get the active users


    # Get population from the original table
    #params_community = pd.read_json(rows_jsonified, orient='split')
    params_community = pd.DataFrame(params_rows)

    # Read population from the table for the desired community
    # Sum over all populations
    poblacion = params_community[params_community['Comunidad'].isin(community)]['Población'].sum()


    # Get the list of active users, this only gets the count by day
    result1 = result1.rename(columns={'reg_users': 'usuarios registrados'})
    result1['poblacion'] = poblacion
    result1['usuarios no registrados'] = poblacion - result1['usuarios registrados']

    result = result1[['usuarios registrados', 'date']]
    result.index = result['date']

    result['usuarios registrados'] = 100*result1['usuarios registrados']/poblacion
    result['usuarios no registrados'] = 100-result['usuarios registrados']



    cols = ['usuarios registrados', 'usuarios no registrados']

    # Get the displaying axis
    result['date'] = pd.to_datetime(result['date'])
    #result.reg_users = result.reg_users.astype(int)
    #result.user_id = result.user_id.astype(int)


    if frequency in ['D']:
        result['date']= result['date'].dt.strftime('%Y-%m-%d')
    elif frequency in ['W', '2W']:
        result['date'] = result['date'].dt.strftime('%Y-%W')
    elif frequency in ['M','3M']:
        result['date'] = result['date'].dt.strftime('%Y-%m')
    else:
        result['date'] = result['date'].dt.strftime('%Y')




    # create data list
    traces = []
    for i in cols:
        formattedList = ["{:.0f}%".format(member) for member in result[i]]
        hover_text = ["{:,}".format(int(member)) for member in result1[i]]
        traces.append(go.Bar(
            x=result.index,
            y=round(result1[i]),
            text=formattedList,
            textposition='inside',
            name=i,
            hoverinfo='text',
            hovertext=hover_text

             )
        )


    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            barmode='stack',
            showlegend=True,
            separators=',.',
            font={
                "family": "Raleway",
                "size": ftxt_size
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },
            margin={
                "r": 30,
                "t": 20,
                "b": 60,
                "l": 60
            },

            width=400,

            xaxis=dict(
                # type='line',
                showgrid=True,
                tickvals=result.index,
                ticktext=result['date'],
                ticks='outside',

                automargin=True
            ),
            yaxis=dict(
                title='Numero de usuarios',
                zeroline= False,
                tickformat=',2r',
                titlefont=dict(
                    size=ftxt_size,
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    size=ftxt_size,
                    color='rgb(107, 107, 107)'
                )
            )


        )
    }

# ----------------------------------------------------------------------------
#  TAB EVOLUCION - SCATTER - PUBLICACIONES CONEXIONES
# ----------------------------------------------------------------------------

# callback to update graph
@app.callback(
    Output('pub_con_count', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-range', 'start_date'),Input('date-picker-range', 'end_date'),
     Input('trans_type_pub', 'value'),
     Input('frequency','value')
     ]
)

def update_graph(community, start_date, end_date, tranport_type, frequency):

    if 'TODAS' in community:
        community = COMMUNITIES

    rid_ff=filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff=filter_dataframe(matches, community, start_date, end_date,tranport_type)


    rid_ff['publicaciones']=1
    match_ff['conexiones'] = 1

    rid = rid_ff.resample(frequency).agg(dict(publicaciones='sum'))
    mat = match_ff.resample(frequency).agg(dict(conexiones='sum'))


    result = pd.merge(rid[['publicaciones']], mat[['conexiones']], left_index=True, right_index=True, how='outer')
    cols = result.columns.tolist()

    # Get the displaying axis
    result['date'] = pd.to_datetime(result.index)
    result.fillna(0,inplace=True)

    if frequency in ['D']:
        result['date']= result['date'].dt.strftime('%Y-%m-%d')
    elif frequency in ['W', '2W']:
        result['date'] = result['date'].dt.strftime('%Y-%W')
    elif frequency in ['M','3M']:
        result['date'] = result['date'].dt.strftime('%Y-%m')
    else:
        result['date'] = result['date'].dt.strftime('%Y')



    # create data list
    traces = []
    for i in cols:
        formattedList = ["{:,}".format(int(member)) for member in result[i]]
        text_hover = [dat + " , " + "{:,}".format(int(member)) for dat, member in zip(result['date'], result[i])]

        traces.append(go.Scatter(
            x=result.index,
            y=result[i],
            text=formattedList,
            textposition='bottom center',
            mode='lines+markers+text',
            hoverinfo='text',
            hovertext=text_hover,
            opacity=0.7,
            marker={
               'size': msize,
               'line': {'width': 0.5, 'color': 'white'}
         },
            name=i
             )
        )


    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            showlegend=True,
            separators=',.',
            font={
                "family": "Raleway"
                #"size": 11
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },

            width=500,

            margin={
                "r": 20,
                "t": 40,
                "b": 80,
                "l": 50
            },

            xaxis=dict(
                # type='line',
                showgrid=False,
                tickvals=result.index,
                ticktext=result['date'],
                ticks='outside',
                title='Medio de transporte: ' + tranport_type

            ),
            yaxis=dict(
                title='Cantidad de publicaciones/conexiones',
                zeroline=False,
                automargin=True,
                tickformat=',2r',
                titlefont=dict(
                    size=11,
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    size=11,
                    color='rgb(107, 107, 107)'
                )
            )

        )
    }

# ----------------------------------------------------------------------------
#  TAB EVOLUCION - SCATTER -EFFECTIVIDAD PROGRAMA
# ----------------------------------------------------------------------------



# Effectividad programa
# callback to update graph
@app.callback(
    Output('pub_con_effect', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-range', 'start_date'),Input('date-picker-range', 'end_date'),
     Input('trans_type_pub', 'value'),
     Input('frequency','value')
     ]
)

def update_graph_effect(community, start_date, end_date, tranport_type, frequency):

    if 'TODAS' in community:
        community = COMMUNITIES

    rid_ff = filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff1 = filter_dataframe(matches, community, start_date, end_date,tranport_type)


    rid_ff['publicaciones']=1


    rid = rid_ff.resample(frequency).agg(dict(publicaciones='sum'))
    #TODO:  conexiones are over counted - multiple times with multiple matches
    match_ff = match_ff1.drop_duplicates(subset = ['ride_id','date'])
    match_ff['conexiones'] = 1
    mat = match_ff.resample(frequency).agg(dict(conexiones='sum'))


    result = pd.merge(rid[['publicaciones']], mat[['conexiones']], left_index=True, right_index=True, how='outer')
    result['efectividad'] = 100*result['conexiones'] / result['publicaciones']
    result.drop(columns=['publicaciones'], inplace=True)
    result.drop(columns=['conexiones'], inplace=True)
    cols = result.columns.tolist()

    # Get the displaying axis
    result['date'] = pd.to_datetime(result.index)


    if frequency in ['D']:
        result['date']= result['date'].dt.strftime('%Y-%m-%d')
    elif frequency in ['W','2W']:
        result['date'] = result['date'].dt.strftime('%Y-%W')
    elif frequency in ['M','3M']:
        result['date'] = result['date'].dt.strftime('%Y-%m')
    else:
        result['date'] = result['date'].dt.strftime('%Y')



    # create data list
    traces = []
    for i in cols:
        formattedList = ["{:.0f}%".format(member) for member in result[i]]
        text_hover = [dat + " , " + "{:.0f}%".format(member) for dat, member in zip(result['date'], result[i])]
        # my_text = ['(sepal length: ' + '{:.2f}'.format(sl) + ', sepal width:' + '{:.2f}'.format(sw) + ')' +
        #            '<br>(petal length: ' + '{:.2f}'.format(pl) + ', petal width:' + '{:.2f}'.format(pw) + ')'
        #            for sl, sw, pl, pw in zip(list(df['sepal length (cm)']), list(df['sepal width (cm)']),
        #                                      list(df['petal length (cm)']), list(df['petal width (cm)']))]
        traces.append(go.Scatter(
            x=result.index,
            y=result[i],
            text=formattedList,
            textposition='bottom center',
            mode='lines+markers+text',
            hoverinfo='text',
            hovertext= text_hover,
            #text=df.apply(lambda x: "{:.2}".format(x['sepal length (cm)']), axis=1),
            opacity=0.7,
            marker={
               'size': msize,
               'line': {'width': 0.5, 'color': 'white'}
         },
            name=i
             )
        )


    return {
        'data': traces,
        'layout': go.Layout(

            title='',
            showlegend=True,
            separators=',.',
            font={
                "family": "Raleway"
                # "size": 11
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },

            width=500,

            margin={
                "r": 20,
                "t": 40,
                "b": 80,
                "l": 50
            },

            xaxis=dict(
                # type='line',
                showgrid=False,
                tickvals=result.index,
                ticktext=result['date'],
                ticks='outside',
                title='Medio de transporte: ' + tranport_type

            ),
            yaxis=dict(
                title='Porcentage efectividad - conexiones/publicaciones',
                zeroline=False,
                automargin=True,
                tickformat=',2r',
                rangemode= 'tozero',
                titlefont=dict(
                    size=11,
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    size=11,
                    color='rgb(107, 107, 107)')
                )
            )

    }


# ----------------------------------------------------------------------------
#  TAB EVOLUCION - SCATTER - PUBLICACIONES CONEXIONES PROMEDIO
# ----------------------------------------------------------------------------

# callback to update graph
@app.callback(
    Output('pub_con_prom', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-range', 'start_date'),Input('date-picker-range', 'end_date'),
     Input('trans_type_pub', 'value'),
     Input('frequency','value')
     ]
)

def update_graph(community, start_date, end_date, tranport_type, frequency):

    if 'TODAS' in community:
        community = COMMUNITIES

    if len(community)==0:
        pass

    rid_ff1 = filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff1 = filter_dataframe(matches, community, start_date, end_date,tranport_type)

    # Filter rides to only working days

    # Sunday is 1
    rid_ff = rid_ff1[rid_ff1['ride_dow'].isin([2, 3, 4, 5, 6])]
    match_ff = match_ff1[match_ff1['ride_dow'].isin([2, 3, 4, 5, 6])]

    rid_ff['publicaciones'] = 1
    match_ff['conexiones'] = 1

    # First get the summary per week

    rid = rid_ff.resample('W').agg(dict(publicaciones='sum'))
    rid['count'] = rid_ff.resample('W').agg(dict(ride_dow='nunique'))
    rid['promedio publicaciones'] = round(rid['publicaciones']/rid['count'],0)
    rid.fillna(0, inplace=True)



    mat = match_ff.resample('W').agg(dict(conexiones='sum'))
    mat['count'] = match_ff.resample('W').agg(dict(ride_dow='nunique'))
    mat['promedio conexiones'] = round(mat['conexiones']/mat['count'],0)
    mat.fillna(0, inplace=True)



    result1 = pd.merge(rid[['promedio publicaciones']], mat[['promedio conexiones']], left_index=True, right_index=True, how='outer')
    result = result1.resample(frequency).mean()
    result.fillna(0, inplace=True)

    cols = result.columns.tolist()

    # Get the displaying axis
    result['date'] = pd.to_datetime(result.index)

    if frequency in ['D']:
        result['date']= result['date'].dt.strftime('%Y-%m-%d')
    elif frequency in ['W', '2W']:
        result['date'] = result['date'].dt.strftime('%Y-%W')
    elif frequency in ['M','3M','6M']:
        result['date'] = result['date'].dt.strftime('%Y-%m')
    else:
        result['date'] = result['date'].dt.strftime('%Y')

    # create data list
    traces = []
    for i in cols:
        formattedList = ["{:,}".format(int(round(member,0))) for member in result[i]]
        traces.append(go.Scatter(
            x=result.index,
            y=result[i],
            text=formattedList,
            textposition='bottom center',
            mode='lines+markers+text',
            opacity=0.7,
            marker={
               'size': msize,
               'line': {'width': 0.5, 'color': 'white'}
         },
            name=i
             )
        )


    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            showlegend=True,
            separators=',.',
            font={
                "family": "Raleway"
                #"size": 11
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },

            width=500,

            margin={
                "r": 20,
                "t": 40,
                "b": 80,
                "l": 50
            },

            xaxis=dict(
                # type='line',
                showgrid=False,
                tickvals=result.index,
                ticktext=result['date'],
                ticks='outside',
                title='Medio de transporte: ' + tranport_type

            ),
            yaxis=dict(
                title='Promedio publicaciones/conexiones',
                zeroline=False,
                automargin=True,
                tickformat=',2r',
                titlefont=dict(
                    size=11,
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    size=11,
                    color='rgb(107, 107, 107)'
                )
            )

        )
    }



# ----------------------------------------------------------------------------
#  TAB EVOLUCION - SCATTER - PERFIL USUARIO - SOLO MENSUAL
# ----------------------------------------------------------------------------

# callback to update graph
@app.callback(
    Output('perfil_usuario', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-range', 'start_date'),Input('date-picker-range', 'end_date'),
     Input('trans_type_pub', 'value'),
     Input('frequency','value')
     ]
)

def update_graph(community, start_date, end_date, tranport_type, frequency):

    if 'TODAS' in community:
        community = COMMUNITIES


    rid_ff=filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff=filter_dataframe(matches, community, start_date, end_date,tranport_type)

    # First get the summary per week

    rid = rid_ff.resample(frequency).agg(dict(driver_id='nunique'))
    rid = rid.rename(columns={'driver_id': 'usuarios que publican'})

    mat = match_ff.resample(frequency).agg(dict(driver_id='nunique', passenger_id='nunique'))
    mat = mat.rename(columns={'driver_id': 'conductores que conectan'})
    mat = mat.rename(columns={'passenger_id': 'pasajeros'})


    rid.fillna(0, inplace=True)
    mat.fillna(0, inplace=True)



    result = pd.merge(rid[['usuarios que publican']], mat[['conductores que conectan', 'pasajeros']], left_index=True, right_index=True, how='outer')
    result.fillna(0, inplace=True)

    cols = result.columns.tolist()

    # Get the displaying axis
    result['date'] = pd.to_datetime(result.index)

    if frequency in ['D']:
        result['date']= result['date'].dt.strftime('%Y-%m-%d')
    elif frequency in ['W', '2W']:
        result['date'] = result['date'].dt.strftime('%Y-%W')
    elif frequency in ['M','3M','6M']:
        result['date'] = result['date'].dt.strftime('%Y-%m')
    else:
        result['date'] = result['date'].dt.strftime('%Y')

    # create data list
    traces = []
    for i in cols:
        formattedList = ["{:,}".format(int(round(member,0))) for member in result[i]]
        traces.append(go.Scatter(
            x=result.index,
            y=result[i],
            text=formattedList,
            textposition='bottom center',
            mode='lines+markers+text',
            opacity=0.7,
            marker={
               'size': msize,
               'line': {'width': 0.5, 'color': 'white'}
         },
            name=i
             )
        )


    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            showlegend=True,
            separators=',.',
            font={
                "family": "Raleway"
                #"size": 11
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },

            width=500,

            margin={
                "r": 20,
                "t": 40,
                "b": 80,
                "l": 50
            },

            xaxis=dict(
                # type='line',
                showgrid=False,
                tickvals=result.index,
                ticktext=result['date'],
                ticks='outside',
                title='Medio de transporte: ' + tranport_type

            ),
            yaxis=dict(
                title='Promedio publicaciones/conexiones',
                zeroline=False,
                automargin=True,
                tickformat=',2r',
                titlefont=dict(
                    size=11,
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    size=11,
                    color='rgb(107, 107, 107)'
                )
            )

        )
    }



# ----------------------------------------------------------------------------
#  TAB EVOLUCION - SCATTER - PUBLICACIONES CONEXIONES PROMEDIO HORA
# ----------------------------------------------------------------------------

# callback to update graph
@app.callback(
    Output('pub_con_hora', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-range', 'start_date'),Input('date-picker-range', 'end_date'),
     Input('trans_type_pub', 'value')
     ]
)

def update_graph(community, start_date, end_date, tranport_type):
    #rides['pub_hora'] = rides['publication_date'].dt.strftime('%H')
    if 'TODAS' in community:
        community = COMMUNITIES

    rid_ff=filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff=filter_dataframe(matches, community, start_date, end_date,tranport_type)

    # Filter rides to only working days
    rid_ff['publicaciones']=1
    match_ff['conexiones'] = 1

    # Summary
    rid = rid_ff.groupby(['ride_hour']).count()
    mat = match_ff.groupby(['ride_hour']).count()



    result = pd.merge(rid[['publicaciones']], mat[['conexiones']], left_index=True, right_index=True, how='outer')
    result.fillna(0,inplace=True)

    hour = ["{:,}:00 ".format(member) for member in result.index]
    cols = result.columns.tolist()
    # create data list
    traces = []
    for i in cols:
        formattedList = ["{:,}".format(int(round(member, 0))) for member in result[i]]
        #text_hover = [dat + " , " + "{:.0f}%".format(member) for dat, member in zip(result['date'], result[i])]
        # my_text = ['(sepal length: ' + '{:.2f}'.format(sl) + ', sepal width:' + '{:.2f}'.format(sw) + ')' +
        #            '<br>(petal length: ' + '{:.2f}'.format(pl) + ', petal width:' + '{:.2f}'.format(pw) + ')'
        #            for sl, sw, pl, pw in zip(list(df['sepal length (cm)']), list(df['sepal width (cm)']),
        #                                      list(df['petal length (cm)']), list(df['petal width (cm)']))]

        traces.append(go.Scatter(
            y=hour,
            x=result[i],
            text=formattedList,
            textposition='bottom center',
            mode='lines+markers+text',
            opacity=0.7,
            marker={
               'size': msize,
               'line': {'width': 0.5, 'color': 'white'}
         },
            name=i
             )
        )


    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            showlegend=True,
            separators=',.',
            font={
                "family": "Raleway"
                #"size": 11
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },

            width=500,

            margin={
                "r": 20,
                "t": 40,
                "b": 80,
                "l": 50
            },

            xaxis=dict(
                # type='line',
                showgrid=False,
                ticks='outside',
                title='Medio de transporte: ' + tranport_type

            ),
            yaxis=dict(
                tickvals=result.index,
                ticktext=hour,
                title='Cantidad publicaciones/conexiones',
                zeroline=False,
                automargin=True,
                tickformat=',2r',
                titlefont=dict(
                    size=11,
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    size=11,
                    color='rgb(107, 107, 107)'
                )
            )



    #---------------------------------


        )
    }



# ----------------------------------------------------------------------------
#  TAB EVOLUCION  - PUBLICACIONES CONEXIONES PROMEDIO HORA BAR
# ----------------------------------------------------------------------------

# callback to update graph
@app.callback(
    Output('pub_con_hora_bar', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-range', 'start_date'),Input('date-picker-range', 'end_date'),
     Input('trans_type_pub', 'value')
     ]
)

def update_graph(community, start_date, end_date, tranport_type):
    #rides['pub_hora'] = rides['publication_date'].dt.strftime('%H')
    if 'TODAS' in community:
        community = COMMUNITIES

    rid_ff=filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff=filter_dataframe(matches, community, start_date, end_date,tranport_type)

    # Filter rides to only working days
    rid_ff['publicaciones']=1
    match_ff['conexiones'] = 1

    # Summary
    rid = rid_ff.groupby(['ride_hour']).count()
    mat = match_ff.groupby(['ride_hour']).count()



    result = pd.merge(rid[['publicaciones']], mat[['conexiones']], left_index=True, right_index=True, how='outer')
    result.fillna(0,inplace=True)

    hour_n = rides.ride_hour.unique()
    hour_n.sort()
    hour = ["{:,}:00 ".format(member) for member in hour_n]


    cols = result.columns.tolist()
    # create data list
    traces = []

    annotations = []
    add_pt = round(result['publicaciones'].max() / 12)


    for i,j,k in zip(result['publicaciones'],result.index, result['conexiones']):

        annotations.append(dict(x=i+add_pt, y=j, text="{:,}".format(int(i)),
                                font=dict(family='Arial', size=ftxt_size-1, color='black'
                                          ),
                                showarrow=False, ))
        annotations.append(dict(x=-(k+add_pt), y=j, text="{:,}".format(int(k)),
                                font=dict(family='Arial', size=ftxt_size-1, color='black'
                                          ),
                                showarrow=False, ))


    for i in cols:
        if i=='publicaciones':
            color = 'black'
            base = 0
            textposition = 'outside'
        else:
            color = 'black'
            base = -result[i]
            textposition = 'outside'

        formattedList = ["{:,}".format(int(round(member, 0))) for member in result[i]]
        hover_text = ['Publicaciones: ' + "{:,}".format(int(j)) + '<br>' + 'Conexiones: ' + "{:,}".format(int(member))
                      for j, member in zip(result['publicaciones'], result['conexiones'])]


        traces.append(go.Bar(
            y=result.index,
            x=result[i],
            base=base,
            text='',
            textposition='outside',
            orientation='h',
            hoverinfo='text',
            hovertext=hover_text,
            textfont={'size': ftxt_size-1, 'color':color},
            insidetextfont= {'size': ftxt_size-1},
            constraintext = 'none',
            name=i
             )
        )



    return {
        'data': traces,
        'layout': go.Layout(

            title='',
            annotations=annotations,
            barmode='stack',
            showlegend=True,
            #separators=',.',
            font={
                "family": "Raleway",
                "size": ftxt_size
            },
            height=gheight*1.5,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },
            margin={
                "r": 30,
                "t": 20,
                "b": 60,
                "l": 60
            },

            width=500,

            xaxis=dict(
                # type='line',
                showgrid=True,
                ticks='outside',
                tickformat=',2r',  # tickformat=',.2r'
                automargin=True,
                title='Numero publicaciones/conexiones',
                titlefont=dict(
                    size=ftxt_size,
                    color='rgb(107, 107, 107)'
                ),

            ),
            yaxis=dict(
                tickvals=hour_n,
                ticktext=hour,
                range=[-0.5,23.5],
                zeroline= False,
                titlefont=dict(
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    color='rgb(107, 107, 107)'
                )
            )


        )
    }


# ----------------------------------------------------------------------------
#  TAB EVOLUCION  - PUBLICACIONES HORA BAR
# ----------------------------------------------------------------------------

# callback to update graph
@app.callback(
    Output('pub_hora_bar', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-range', 'start_date'),Input('date-picker-range', 'end_date'),
     Input('trans_type_pub', 'value')
     ]
)

def update_graph(community, start_date, end_date, tranport_type):

    if 'TODAS' in community:
        community = COMMUNITIES

    rid_ff = filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff1 = filter_dataframe(matches, community, start_date, end_date,tranport_type)

    # Filter rides to only working days
    rid_ff['publicaciones']=1

    # Summary
    rid_ff['publication_date'] = pd.to_datetime(rid_ff['publication_date'])
    rid_ff['pub_hora'] = rid_ff['publication_date'].dt.strftime('%H')

    match_ff = rid_ff[rid_ff.ride_id.isin(match_ff1.ride_id.unique())]
    match_ff['publicaciones conectadas'] = 1

    rid = rid_ff.groupby(['pub_hora']).count()
    mat = match_ff.groupby(['pub_hora']).count()



    result = pd.merge(rid[['publicaciones']], mat[['publicaciones conectadas']], left_index=True, right_index=True, how='left')
    result.fillna(0,inplace=True)

    result['publicaciones no conectadas'] = result['publicaciones']-result['publicaciones conectadas']
    #resultf = resultf.rename(columns={'publicaciones': 'usuarios'})

    # -------------------

    total = result['publicaciones']  # total should be registered users not the sum of the two
    resultf = result.apply(lambda x: 100 * x / total)
    resultf.fillna(0, inplace=True)

    #cols = result.columns.tolist()
    cols = ['publicaciones no conectadas','publicaciones conectadas']

    # Get the displaying axis
    #resultf['date'] = pd.to_datetime(resultf.index)


    hour = ["{:,}:00 ".format(int(member)) for member in result.index]
    # create data list
    traces = []

    for i in cols:
        formattedList = ["{:.0f}%".format(member) for member in resultf[i]]
        formattedList = ["{:,}".format(int(member)) for member in result[i]]

        if i=='publicaciones no conectadas':
            color= 'white'
            t = 'no conectadas'
        else:
            color = 'black'
            t = 'conectadas'

        hover_text = ['Total publicaciones: ' + "{:,}".format(int(j)) + '<br>' + t + ':  ' + "{:.0f}%".format((member)) for j, member in zip(result['publicaciones'],resultf[i])]


        traces.append(go.Bar(
            y=result.index,
            x=result[i],
            text=formattedList,
            textposition='inside',
            orientation='h',
            hoverinfo='text',
            hovertext=hover_text,
            textfont={'size': ftxt_size-1, 'color' : color},
            insidetextfont= {'size': ftxt_size-1},
            constraintext = 'none',
            name=i
             )
        )
    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            barmode='stack',
            showlegend=True,
            #separators=',.',
            font={
                "family": "Raleway",
                "size": ftxt_size
            },
            height=gheight*1.5,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },
            margin=layout_margin,

            width=500,

            xaxis=dict(
                # type='line',
                showgrid=True,
                ticks='outside',
                tickformat=',2r',  # tickformat=',.2r'
                automargin=True,
                title='Numero publicaciones',
                titlefont=dict(
                    size=ftxt_size,
                    color='rgb(107, 107, 107)'
                ),

            ),
            yaxis=dict(
                tickvals=result.index,
                ticktext=hour,
                zeroline= False,
                titlefont=dict(
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    color='rgb(107, 107, 107)'
                )
            )


        )
    }


# ----------------------------------------------------------------------------
#  TAB EVOLUCION - SLIDER - UPDATE
# ----------------------------------------------------------------------------

@app.callback(
    Output('slider-container', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')])

def change(start_date, end_date):
    d1 = dt.strptime(start_date, '%Y-%m-%d')
    d2 = dt.strptime(end_date, '%Y-%m-%d')
    oneMonth = relativedelta(months=1)
    months = [dt.strftime("%Y-%m")
              for dt in rrule(MONTHLY, dtstart=d1,
                              until=d2 + oneMonth)]


    marks = {str(year): i for year, i in enumerate(months)}
    a = int(dt.strptime(start_date, '%Y-%m-%d').strftime('%m'))
    b = int(dt.strptime(end_date, '%Y-%m-%d').strftime('%m'))

    slider = dcc.Slider(
        id='user_slider',
        min = 0,
        max=len(months)-1,
        value = 0,
        marks=marks
    )
    return slider


@app.callback(
    Output('slider-container-output', 'children'),
    [Input('user_slider', 'value'),
     Input('user_slider', 'marks')])
def display_dates(value,marks):

    return 'You have selected "{}""'.format(value)

# UPdate slider figure

@app.callback(
    Output('slider-container-output2', 'children'),
    [Input('user_slider', 'value'),
     Input('user_slider', 'marks')])
def display_dates(value,marks):

    return 'You have selected "{}""'.format(value)



@app.callback(
    dash.dependencies.Output('graph-with-slider', 'figure'),
    [dash.dependencies.Input('year-slider', 'value')])

def update_figure(selected_year):
    traces = []
    for i in filtered_df.continent.unique():
        df_by_continent = filtered_df[filtered_df['continent'] == i]
        traces.append(go.Scatter(
            x=df_by_continent['gdpPercap'],
            y=df_by_continent['lifeExp'],
            text=df_by_continent['country'],
            mode='markers',
            opacity=0.7,
            marker={
                'size': msize,
                'line': {'width': 0.5, 'color': 'white'}
            },
            name=i
        ))

    return {
        'data': traces,
        'layout': go.Layout(
            xaxis={'type': 'log', 'title': 'GDP Per Capita'},
            yaxis={'title': 'Life Expectancy', 'range': [20, 90]},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest'
        )
    }



@app.callback(Output('intermediate-value', 'children'),
              [Input('params_table', 'rows')])
def clean_data(rows):
    table_data = pd.DataFrame(rows)
    table_data.index = table_data['Comunidad']

    return table_data.to_json(date_format='iso', orient='split')


# callback to update table
@app.callback(
    Output('kpi_table', 'children'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('params_table', 'rows')
     ]
)

def update_table(community, start_date, end_date, params_rows):
    #rides['pub_hora'] = rides['publication_date'].dt.strftime('%H')
    if 'TODAS' in community:
        community = COMMUNITIES

    score_card = pd.DataFrame(columns=['% Usuarios registrados',
                                       '% Usuarios activos',
                                       '% Usuarios con parqueadero que publican',
                                       'Efectividad de uso (conexiones/publicaciones)'])
    score_card.loc[0] = [10, 20, 85, 15]

    score_card = estimate_kpis(users, rides, matches, community, start_date, end_date, params_rows, by_com=False)

    return html.Table(make_kpi_table(score_card))



# ----------------------------------------------------------------------------
#  TAB MIGRATION  - BAR
# ----------------------------------------------------------------------------



@app.callback(
    Output('migration_bar2', 'figure'),
    [Input('migration-slider', 'value'),
     Input('migration-slider', 'marks'),
     Input('dropdown_com', 'value')])

def update_figure(value, marks,community):

    if 'TODAS' in community:
        community = COMMUNITIES


    if value < 13:
        traces = []
        start_date = marks[str(value)]
        end_date = marks[str(value+1)]

        act_users = active_users_commute(users, rides, matches, community, start_date, end_date)
        table = pd.pivot_table(act_users, index=["commute_mode", "type"], values=["user_id"], aggfunc=pd.Series.nunique,
                           fill_value=0)
        #table['% of Total'] = (table.user_id / table.user_id.sum() * 100).astype(str) + '%'
        table['% commute_mode'] = (table.user_id / table.groupby(level=0).user_id.transform(sum) * 100)
        table = table.reset_index()


        # Replace transport type values - to spanish
        for i, val in TRANSPORT_TYPE.items():
            table.ix[table.type == val, 'type'] = i

        # Replace commute mode values - to spanish
        for i, val in COMMUTE_MODE.items():
            table.ix[table.commute_mode == i, 'commute_mode'] = val

        table.sort_values(by=['commute_mode'], inplace=True)

        result = act_users.groupby(['commute_mode'])['user_id'].nunique().reset_index().\
            rename(columns={'user_id': 'users'})
        cmap = colormap_commute_mode()



        cnt = 0
        for i, val in TRANSPORT_TYPE.items():
            if i in ['TODOS', 'VAN']:
                continue

            table_by_type = table[table['type'] == i]

            table_by_type.sort_values(by=['commute_mode'], inplace=True)
            if cnt == 0:
                df = pd.DataFrame(columns=['commute_mode', '% commute_mode'])
                k = 0
                for j, v in COMMUTE_MODE.items():
                    if j in table_by_type.commute_mode.values:
                        df.loc[k] = [j, table_by_type[table_by_type.commute_mode == j]['% commute_mode']]
                    else:
                        df.loc[k] = [j, 0]
                    k = k + 1

                #table_by_type = df

            cnt = cnt + 1

            formattedList = ["{:.0f}%".format(int(round(member, 0))) for member in table_by_type['% commute_mode']]
            traces.append(go.Bar(

                y=table_by_type.commute_mode,
                x=table_by_type['% commute_mode'],
                text=formattedList,
                textposition='inside',
                hoverinfo='text',
                hovertext='',
                textfont={'size': ftxt_size, 'color': 'white'},
                insidetextfont={'size': ftxt_size },
                constraintext='none',
                #marker={'color': '#10ac84'},
                name=i,
                orientation = 'h'
            )
            )

        return {
            'data': traces,
            'layout': go.Layout(
                title='',
                barmode='stack',
                showlegend=True,
                # separators=',.',
                font={
                    "family": "Raleway",
                    "size": ftxt_size
                },
                height=gheight,
                hovermode="closest",
                legend={
                    "x": -0.0228945952895,
                    "y": 1.2,
                    "orientation": "h",
                    "yanchor": "top"
                },
                margin=layout_margin,

                width=500,

                xaxis=dict(
                    # type='line',
                    #tickvals=[j for j in range(len(hist[0]))],
                    #ticktext=bins_text,
                    showgrid=True,
                    ticks='outside',
                    tickformat=',2r',  # tickformat=',.2r'
                    automargin=True,
                    title='',
                    titlefont=dict(
                        size=ftxt_size,
                        color='rgb(107, 107, 107)'
                    ),

                ),
                yaxis=dict(
                    zeroline=False,
                    title='',
                    titlefont=dict(
                        color='rgb(107, 107, 107)'
                    ),
                    tickfont=dict(
                        color='rgb(107, 107, 107)'
                    )
                )
            )
        }



@app.callback(
    Output('migration_bar', 'figure'),
    [Input('migration-slider', 'value'),
     Input('migration-slider', 'marks'),
     Input('dropdown_com', 'value')])

def update_figure(value, marks,community):

    if 'TODAS' in community:
        community = COMMUNITIES


    if value < 13:

        start_date = marks[str(value)]
        end_date = marks[str(value+1)]

        act_users = active_users_commute(users, rides, matches, community, start_date, end_date)
        result = act_users.groupby(['commute_mode'])['user_id'].nunique().reset_index().\
            rename(columns={'user_id': 'users'})

        # Replace commute mode values - to spanish
        for i, val in COMMUTE_MODE.items():
            result.ix[result.commute_mode == i, 'commute_mode'] = val
        #result.sort_values(by=['commute_mode'], inplace=True)

        total = result['users'].sum()
        result['% users'] = 100*result['users']/total
        cmap = colormap_commute_mode()

        traces = []
        cnt = 0
        formattedList = ['No. usuarios: ' + "{:,}".format(int(round(member, 0))) for member in result['users']]
        formattedHover = ["{:.0f}%".format(int(round(member, 0))) for member in result['% users']]
        traces.append(go.Bar(
            x=result['% users'],
            y=result.commute_mode,
            text=formattedHover,
            textposition='inside',
            hoverinfo='text',
            hovertext=formattedList,
            textfont={'size': ftxt_size - 1},
            insidetextfont={'size': ftxt_size - 1},
            constraintext='none',
            marker={'color': cmap},

            orientation = 'h'

        )
        )

        return {
            'data': traces,
            'layout': go.Layout(
                #title='Total usuarios activos: ' + str(total),
                title='Total usuarios activos: ' + str(len(act_users.user_id.unique())),
                barmode='stack',
                showlegend=False,
                # separators=',.',
                font={
                    "family": "Raleway",
                    "size": ftxt_size
                },
                height=gheight,
                hovermode="closest",
                legend={
                    "x": -0.0228945952895,
                    "y": 1.2,
                    "orientation": "h",
                    "yanchor": "top"
                },
                margin=layout_margin,

                width=500,

                xaxis=dict(
                    # type='line',
                    #tickvals=[j for j in range(len(hist[0]))],
                    #ticktext=bins_text,
                    showgrid=True,
                    ticks='outside',
                    tickformat=',2r',  # tickformat=',.2r'
                    automargin=True,
                    title='% usuarios',
                    titlefont=dict(
                        size=ftxt_size,
                        color='rgb(107, 107, 107)'
                    ),

                ),
                yaxis=dict(
                    zeroline=False,
                    title='',
                    titlefont=dict(
                        color='rgb(107, 107, 107)'
                    ),
                    tickfont=dict(
                        color='rgb(107, 107, 107)'
                    )
                )
            )
        }


# ----------------------------------------------------------------------------
#  TAB MIGRATION - SLIDER GRAPH
# ----------------------------------------------------------------------------

@app.callback(
    Output('migration_graph', 'figure'),
    [Input('migration-slider', 'value'),
     Input('migration-slider', 'marks'),
     Input('dropdown_com', 'value')])

def update_figure(value, marks,community):

    if 'TODAS' in community:
        community = COMMUNITIES

    if value < 13:

        start_date = marks[str(value)]
        end_date = marks[str(value+1)]

        act_users = active_users_commute(users, rides, matches, community, start_date, end_date)
        listOfNumbers = []
        listOfNumbers2 = []

        for x in range(0, len(act_users)):
            listOfNumbers.append(random.random())

            if x % 2 == 0:
                listOfNumbers2.append(random.random()+random.random())
            else:
                listOfNumbers2.append(random.random()+2*random.random())




        act_users['x'] = listOfNumbers
        act_users['y'] = listOfNumbers2
        cnt = 0
        x_ticks = []

        cmap = colormap_commute_mode()

        for i, val in TRANSPORT_TYPE.items():
            if i in ['TODOS', 'VAN']:
                continue
            act_users.loc[act_users['type'] == val, ['x']] = act_users['x'] + cnt
            x_ticks.append(i)
            cnt = cnt+1

        traces = []
        cnt = 0
        for i, val in COMMUTE_MODE.items():
            act_users_by_type = act_users[act_users['commute_mode'] == i]

            traces.append(go.Scatter(
                x=act_users_by_type['x'],
                y=act_users_by_type['y'],
                text=act_users_by_type['main_email'],
                hovertext=act_users_by_type['main_email'],
                hoverinfo='text',
                mode='markers',
                opacity=0.7,
                marker={
                    'size': msize,
                    'color': cmap[cnt],
                    'line': {'width': 0.5, 'color': 'white'}
                },
                name=val
            ))
            cnt = cnt + 1

        return {
            'data': traces,
            'layout': go.Layout(
                title='Total usuarios activos: ' + str(len(act_users.user_id.unique())),
                font={
                    "family": "Raleway",
                    "size": ftxt_size
                },
                xaxis={
                    'title':'Tipo transporte actual',
                    'range': [-0.5, 3.5],
                    'tickvals':[0.5, 1.5, 2.5],
                    'ticktext':x_ticks


                },
                #yaxis={'title': 'Life Expectancy', 'range': [20, 90]},
                margin={'l': 40, 'b': 40, 't': 40, 'r': 10},
                legend={'x': 0, 'y': 1},
                hovermode='closest',
                height=gheight*1.2
            )
        }

# ----------------------------------------------------------------------------
#  TAB MIGRATION - medio_location
# ----------------------------------------------------------------------------

@app.callback(
    Output('medio_location2', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('check_location2','value')])

def update_figure(community, min_user):

    if 'TODAS' in community:
        community = COMMUNITIES
    logger.info(min_user)


    table = pd.pivot_table(users, index=["commute_mode", "neighborhood"], values=["user_id"], aggfunc=pd.Series.nunique,
                       fill_value=0)
    #table['% of Total'] = (table.user_id / table.user_id.sum() * 100).astype(str) + '%'
    table['% commute_mode'] = (table.user_id / table.groupby(level=1).user_id.transform(sum) * 100)
    table = table.reset_index()



    table = table[table.user_id > min_user]

    # Replace commute mode values - to spanish
    for i, val in COMMUTE_MODE.items():
        table.ix[table.commute_mode == i, 'commute_mode'] = val

    table.sort_values(by=['commute_mode'], inplace=True)

    traces=[]
    cnt = 0
    for i, val in COMMUTE_MODE.items():

        table_by_type = table[table['commute_mode'] == val]


        formattedList = ["{:.0f}%".format(int(round(member, 0))) for member in table_by_type['% commute_mode']]
        formattedList2 = ["{:,}".format(int(round(member, 0))) for member in table_by_type['user_id']]

        if min_user > 2:
            text = formattedList
        else:
            text = ''

        traces.append(go.Bar(

            x=table_by_type.neighborhood,
            y=table_by_type['user_id'],
            text=text,
            textposition='inside',
            hoverinfo='text',
            hovertext=formattedList2,
            textfont={'color': 'white'},
            insidetextfont={'size': ftxt_size },
            constraintext='none',
            #marker={'color': '#10ac84'},
            name=val,
            #orientation = 'h'
        )
        )

    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            barmode='stack',
            showlegend=True,
            # separators=',.',
            font={
                "family": "Raleway",
                "size": ftxt_size
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },
            margin=layout_margin,

            width=1000,

            xaxis=dict(
                # type='line',
                #tickvals=[j for j in range(len(hist[0]))],
                #ticktext=bins_text,
                showgrid=True,
                ticks='outside',
                tickformat=',2r',  # tickformat=',.2r'
                automargin=True,
                title='',
                titlefont=dict(
                    size=ftxt_size,
                    color='rgb(107, 107, 107)'
                ),

            ),
            yaxis=dict(
                zeroline=False,
                title='',
                titlefont=dict(
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    color='rgb(107, 107, 107)'
                )
            )
        )
    }


@app.callback(
    Output('medio_location', 'figure'),
[Input('migration-slider', 'value'),
     Input('migration-slider', 'marks'),
     Input('dropdown_com', 'value'),
     Input('check_location', 'values')])
def update_figure(value, marks, community, min_user):

    if 'TODAS' in community:
        community = COMMUNITIES

    if value < 13:
        traces = []
        start_date = marks[str(value)]
        end_date = marks[str(value + 1)]

        act_users = active_users_commute(users, rides, matches, community, start_date, end_date)
        table = pd.pivot_table(act_users, index=["commute_mode", "neighborhood"], values=["user_id"],
                               aggfunc=pd.Series.nunique,
                               fill_value=0)
        # table['% of Total'] = (table.user_id / table.user_id.sum() * 100).astype(str) + '%'
        table['% commute_mode'] = (table.user_id / table.groupby(level=1).user_id.transform(sum) * 100)
        table = table.reset_index()


        if len(min_user) > 0:
            table = table[table.user_id > 1]

        # Replace commute mode values - to spanish
        for i, val in COMMUTE_MODE.items():
            table.ix[table.commute_mode == i, 'commute_mode'] = val

        table.sort_values(by=['commute_mode'], inplace=True)

        result = act_users.groupby(['commute_mode'])['user_id'].nunique().reset_index(). \
            rename(columns={'user_id': 'users'})
        cmap = colormap_commute_mode()

        cnt = 0
        for i, val in COMMUTE_MODE.items():

            table_by_type = table[table['commute_mode'] == val]

            formattedList = ["{:.0f}%".format(int(round(member, 0))) for member in table_by_type['% commute_mode']]
            formattedList2 = ["{:,}".format(int(round(member, 0))) for member in table_by_type['user_id']]

            if len(min_user) > 0:
                text = formattedList
            else:
                text = ''

            traces.append(go.Bar(

                x=table_by_type.neighborhood,
                y=table_by_type['user_id'],
                text=text,
                textposition='inside',
                hoverinfo='text',
                hovertext=formattedList2,
                textfont={'color': 'white'},
                insidetextfont={'size': ftxt_size},
                constraintext='none',
                # marker={'color': '#10ac84'},
                name=val,
                # orientation = 'h'
            )
            )

        return {
            'data': traces,
            'layout': go.Layout(
                title='',
                barmode='stack',
                showlegend=True,
                # separators=',.',
                font={
                    "family": "Raleway",
                    "size": ftxt_size
                },
                height=gheight,
                hovermode="closest",
                legend={
                    "x": -0.0228945952895,
                    "y": 1.2,
                    "orientation": "h",
                    "yanchor": "top"
                },
                margin=layout_margin,

                width=1000,

                xaxis=dict(
                    # type='line',
                    # tickvals=[j for j in range(len(hist[0]))],
                    # ticktext=bins_text,
                    showgrid=True,
                    ticks='outside',
                    tickformat=',2r',  # tickformat=',.2r'
                    automargin=True,
                    title='',
                    titlefont=dict(
                        size=ftxt_size,
                        color='rgb(107, 107, 107)'
                    ),

                ),
                yaxis=dict(
                    zeroline=False,
                    title='',
                    titlefont=dict(
                        color='rgb(107, 107, 107)'
                    ),
                    tickfont=dict(
                        color='rgb(107, 107, 107)'
                    )
                )
            )
        }

    #
    # fig = plotly.tools.make_subplots(
    #     rows=3, cols=2, specs=[[{}, {}], [{'colspan': 2}, None], [{'colspan': 2}, None]],
    #     subplot_titles=('Puntaje : ' + dff['email'].iloc[last_index],'', 'Puntaje periodo actual', 'Puntaje acumulado'),
    #     shared_xaxes=False)
    #
    # fig.append_trace({
    #     'x': colsf,
    #     'y': dff[colsf].iloc[last_index],
    #     'type': 'bar',
    #     'hoverinfo':'text',
    #     'marker': {'color':'#10ac84'},
    #     'hovertext': '',
    #     'text': dff[colsf].iloc[last_index],
    #     'textposition':'inside',
    #     'textfont': {'size': ftxt_size , 'color': 'white'}
    #
    #
    # }, 1, 1)
    #
    # fig.append_trace({
    #
    #     'y': dff['Puntaje'],
    #     'type': 'bar',
    #     'text': '',
    #     'hoverinfo':'text',
    #     'hovertext':dff['email'],
    #     'marker': marker
    # }, 2, 1)
    # fig.append_trace({
    #
    #     'y': dff['Puntaje Promedio'],
    #     'type': 'bar',
    #     'marker': marker,
    #     'text': '',
    #     'hoverinfo': 'text',
    #     'hovertext':dff['email'],
    # }, 3, 1)
    # fig['layout']['showlegend'] = False
    # fig['layout']['height'] = 900
    # fig['layout']['yaxis1'].update(title='Puntaje')
    # fig['layout']['yaxis1'].update(tickvals=colsf)
    # fig['layout']['yaxis1'].update(tickvals=colsf)
    # fig['layout']['yaxis3'].update(title='Puntaje')
    # fig['layout']['yaxis4'].update(title='Puntaje')
    # fig['layout']['margin'] = {
    #     'l': 40,
    #     'r': 10,
    #     't': 60,
    #     'b': 200
    # }
    #
    # return fig
# ----------------------------------------------------------------------------
#  TAB ADVANCES
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
#  TAB ADVANCES - TABLE
# ----------------------------------------------------------------------------

# callback to update table advances
@app.callback(
    Output('advances_table', 'children'),
    [Input('date-picker-advances', 'date'),
     Input('params_table', 'rows')
     ]
)
def update_table(date, params_rows):

    # Get the current period date
    d1 = dt.strptime(date, '%Y-%m-%d')
    d1 = d1.replace(day=1)
    one_month = relativedelta(months=1)
    d2 = d1 + one_month
    end_date = d2.strftime("%Y-%m-%d")
    start_date = d1.strftime("%Y-%m-%d")

    # Get KPIS for current period
    score_card = estimate_kpis(users, rides, matches, COMMUNITIES, start_date, end_date, params_rows,
                               by_com=True)

    return html.Table(make_kpi_table(score_card))


# ----------------------------------------------------------------------------
#  TAB ACTUAL PERIOD
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
#  TAB ACTUAL PERIOD - TABLE
# ----------------------------------------------------------------------------


# callback to update table
@app.callback(
    Output('kpi_table_month', 'children'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-month', 'date'),
     Input('params_table', 'rows')
     ]
)

def update_table(community, date, params_rows):
    #rides['pub_hora'] = rides['publication_date'].dt.strftime('%H')
    if 'TODAS' in community:
        community = COMMUNITIES

    # Get the current period date
    d1 = dt.strptime(date, '%Y-%m-%d')
    d1 = d1.replace(day=1)
    one_month = relativedelta(months=1)
    d2 = d1 + one_month
    end_date = d2.strftime("%Y-%m-%d")
    start_date = d1.strftime("%Y-%m-%d")

    score_card = estimate_kpis(users, rides, matches, community, start_date, end_date, params_rows, by_com=False)

    return html.Table(make_kpi_table(score_card))

# ----------------------------------------------------------------------------
#  TAB PERIODO ACTUAL - SCATTER - PUBLICACIONES CONEXIONES
# ----------------------------------------------------------------------------

# callback to update graph
@app.callback(
    Output('pub_con_count_month', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-month', 'date'),
     Input('trans_type_pub_month', 'value'),
     Input('frequency_month','value')
     ]
)

def update_graph(community, date, tranport_type, frequency):

    if 'TODAS' in community:
        community = COMMUNITIES

    # Get the current period date
    d1 = dt.strptime(date, '%Y-%m-%d')
    d1 = d1.replace(day=1)
    one_month = relativedelta(months=1)
    d2 = d1 + one_month
    end_date = d2.strftime("%Y-%m-%d")
    start_date = d1.strftime("%Y-%m-%d")



    rid_ff=filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff=filter_dataframe(matches, community, start_date, end_date,tranport_type)


    rid_ff['publicaciones']=1
    match_ff['conexiones'] = 1

    rid = rid_ff.resample(frequency).agg(dict(publicaciones='sum'))
    mat = match_ff.resample(frequency).agg(dict(conexiones='sum'))


    result = pd.merge(rid[['publicaciones']], mat[['conexiones']], left_index=True, right_index=True, how='outer')
    cols = result.columns.tolist()

    # Get the displaying axis
    result['date'] = pd.to_datetime(result.index)

    if frequency in ['D']:
        result['date']= result['date'].dt.strftime('%Y-%m-%d')
    elif frequency in ['W', '2W']:
        result['date'] = result['date'].dt.strftime('%Y-%m-%d')
    elif frequency in ['M','3M']:
        result['date'] = result['date'].dt.strftime('%Y-%m')
    else:
        result['date'] = result['date'].dt.strftime('%Y')

    result.fillna(0, inplace=True)


    # create data list
    traces = []
    for i in cols:
        formattedList = ["{:,}".format(int(member)) for member in result[i]]
        text_hover = [dat + " , " + "{:,}".format(int(member)) for dat, member in zip(result['date'], result[i])]

        traces.append(go.Scatter(
            x=result.index,
            y=result[i],
            text=formattedList,
            textposition='bottom center',
            mode='lines+markers+text',
            hoverinfo='text',
            hovertext=text_hover,
            opacity=0.7,
            marker={
               'size': msize,
               'line': {'width': 0.5, 'color': 'white'}
         },
            name=i
             )
        )


    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            showlegend=True,
            separators=',.',
            font={
                "family": "Raleway"
                #"size": 11
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },

            width=800,

            margin={
                "r": 20,
                "t": 50,
                "b": 80,
                "l": 50
            },

            xaxis=dict(
                # type='line',
                showgrid=False,
                tickvals=result.index,
                ticktext=result['date'],
                ticks='outside',

            ),
            yaxis=dict(
                title='Cantidad de publicaciones/conexiones',
                zeroline=False,
                automargin=True,
                tickformat=',2r',
                titlefont=dict(
                    size=11,
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    size=11,
                    color='rgb(107, 107, 107)'
                )
            )

        )
    }




# ----------------------------------------------------------------------------
#  TAB PERIODO ACTUAL  - PUBLICACIONES CONEXIONES PROMEDIO HORA BAR
# ----------------------------------------------------------------------------

# callback to update graph
@app.callback(
    Output('pub_con_hora_bar_month', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-month', 'date'),
     Input('trans_type_pub_month', 'value')
     ]
)

def update_graph(community, date, tranport_type):
    #rides['pub_hora'] = rides['publication_date'].dt.strftime('%H')
    if 'TODAS' in community:
        community = COMMUNITIES

    # Get the current period date
    d1 = dt.strptime(date, '%Y-%m-%d')
    d1 = d1.replace(day=1)
    one_month = relativedelta(months=1)
    d2 = d1 + one_month
    end_date = d2.strftime("%Y-%m-%d")
    start_date = d1.strftime("%Y-%m-%d")


    rid_ff=filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff=filter_dataframe(matches, community, start_date, end_date,tranport_type)

    # Filter rides to only working days
    rid_ff['publicaciones']=1
    match_ff['conexiones'] = 1

    # Summary
    rid = rid_ff.groupby(['ride_hour']).count()
    mat = match_ff.groupby(['ride_hour']).count()



    result = pd.merge(rid[['publicaciones']], mat[['conexiones']], left_index=True, right_index=True, how='outer')
    result.fillna(0,inplace=True)


    hour = ["{:,}:00 ".format(member) for member in result.index]
    cols = result.columns.tolist()
    # create data list
    traces = []


    annotations = []
    add_pt = round(result['publicaciones'].max()/12)


    for i,j,k in zip(result['publicaciones'],result.index, result['conexiones']):

        annotations.append(dict(x=i+add_pt, y=j, text="{:,}".format(int(i)),
                                font=dict(family='Arial', size=ftxt_size-1, color='black'
                                          ),
                                showarrow=False, ))
        annotations.append(dict(x=-(k+add_pt), y=j, text="{:,}".format(int(k)),
                                font=dict(family='Arial', size=ftxt_size-1, color='black'
                                          ),
                                showarrow=False, ))




    for i in cols:

        if i=='publicaciones':
            color = 'black'
            base = 0
            textposition = 'outside'
        else:
            color = 'black'
            base = -result[i]
            textposition = 'outside'

        formattedList = ["{:,}".format(int(round(member, 0))) for member in result[i]]
        hover_text = ['Publicaciones: ' + "{:,}".format(int(j)) + '<br>' + 'Conexiones: ' + "{:,}".format(int(member))
                      for j, member in zip(result['publicaciones'], result['conexiones'])]

        traces.append(go.Bar(
            y=result.index,
            x=result[i],
            base=base,
            text='',
            textposition='auto',
            orientation='h',
            hoverinfo='text',
            hovertext=hover_text,
            textfont={'size': ftxt_size-1, 'color': color},
            insidetextfont= {'size': ftxt_size-1},
            constraintext = 'none',
            name=i
             )
        )



    return {
        'data': traces,
        'layout': go.Layout(
            annotations=annotations,
            title='',
            barmode='stack',
            showlegend=True,
            #separators=',.',
            font={
                "family": "Raleway",
                "size": ftxt_size
            },
            height=gheight*1.7,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },
            margin={
                "r": 30,
                "t": 20,
                "b": 60,
                "l": 60
            },

            width=500,

            xaxis=dict(
                # type='line',
                showgrid=True,
                ticks='outside',
                tickformat=',2r',  # tickformat=',.2r'
                automargin=True,
                #range=[0, 23],
                title='Numero publicaciones/conexiones',
                titlefont=dict(
                    size=ftxt_size,
                    color='rgb(107, 107, 107)'
                ),

            ),
            yaxis=dict(
                tickvals=result.index,
                ticktext=hour,
                range=[-0.5, 23.5],
                zeroline= False,
                titlefont=dict(
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    color='rgb(107, 107, 107)'
                )
            )


        )
    }


# ----------------------------------------------------------------------------
#  TAB PERIODO ACTUAL  - PUBLICACIONES HORA BAR
# ----------------------------------------------------------------------------

# callback to update graph
@app.callback(
    Output('pub_hora_bar_month', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-month', 'date'),
     Input('trans_type_pub_month', 'value')
     ]
)

def update_graph(community, date, tranport_type):

    if 'TODAS' in community:
        community = COMMUNITIES

    # Get the current period date
    d1 = dt.strptime(date, '%Y-%m-%d')
    d1 = d1.replace(day=1)
    one_month = relativedelta(months=1)
    d2 = d1 + one_month
    end_date = d2.strftime("%Y-%m-%d")
    start_date = d1.strftime("%Y-%m-%d")



    rid_ff = filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff1 = filter_dataframe(matches, community, start_date, end_date,tranport_type)

    # Filter rides to only working days
    rid_ff['publicaciones']=1

    # Summary
    rid_ff['publication_date'] = pd.to_datetime(rid_ff['publication_date'])
    rid_ff['pub_hora'] = rid_ff['publication_date'].dt.strftime('%H')

    match_ff = rid_ff[rid_ff.ride_id.isin(match_ff1.ride_id.unique())]
    match_ff['publicaciones conectadas'] = 1

    rid = rid_ff.groupby(['pub_hora']).count()
    mat = match_ff.groupby(['pub_hora']).count()



    result = pd.merge(rid[['publicaciones']], mat[['publicaciones conectadas']], left_index=True, right_index=True, how='left')
    result.fillna(0,inplace=True)

    result['publicaciones no conectadas'] = result['publicaciones']-result['publicaciones conectadas']
    #resultf = resultf.rename(columns={'publicaciones': 'usuarios'})

    # -------------------

    total = result['publicaciones']  # total should be registered users not the sum of the two
    resultf = result.apply(lambda x: 100 * x / total)
    resultf.fillna(0, inplace=True)

    #cols = result.columns.tolist()
    cols = ['publicaciones no conectadas','publicaciones conectadas']

    # Get the displaying axis
    #resultf['date'] = pd.to_datetime(resultf.index)


    hour = ["{:,}:00 ".format(int(member)) for member in result.index]
    # create data list
    traces = []

    for i in cols:
        formattedList = ["{:.0f}%".format(member) for member in resultf[i]]
        formattedList = ["{:,}".format(int(member)) for member in result[i]]

        if i=='publicaciones no conectadas':
            color= 'white'
            t = 'no conectadas'
        else:
            color = 'black'
            t = 'conectadas'

        hover_text = ['Total publicaciones: ' + "{:,}".format(int(j)) + '<br>' + t + ':  ' + "{:.0f}%".format((member)) for j, member in zip(result['publicaciones'],resultf[i])]

        traces.append(go.Bar(
            y=result.index,
            x=result[i],
            text=formattedList,
            textposition='inside',
            orientation='h',
            hoverinfo='text',
            hovertext=hover_text,
            textfont={'size': ftxt_size-1, 'color' : color},
            insidetextfont= {'size': ftxt_size-1},
            constraintext = 'none',
            name=i
             )
        )
    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            barmode='stack',
            showlegend=True,
            #separators=',.',
            font={
                "family": "Raleway",
                "size": ftxt_size
            },
            height=gheight*1.7,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },
            margin=layout_margin,

            width=500,

            xaxis=dict(
                # type='line',
                showgrid=True,
                ticks='outside',
                tickformat=',2r',  # tickformat=',.2r'
                automargin=True,
                title='Numero publicaciones',
                titlefont=dict(
                    size=ftxt_size,
                    color='rgb(107, 107, 107)'
                ),

            ),
            yaxis=dict(
                range=[-0.5,23.5],
                tickvals=result.index,
                ticktext=hour,
                zeroline=False,
                titlefont=dict(
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    color='rgb(107, 107, 107)'
                )
            )


        )
    }



# ----------------------------------------------------------------------------
#  TAB PERIODO ACTUAL - histogram driver
# ----------------------------------------------------------------------------

# callback to update graph
@app.callback(
    Output('hist_driver', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-month', 'date'),
     Input('trans_type_pub', 'value')
     ]
)

def update_graph(community, date, tranport_type):
    #rides['pub_hora'] = rides['publication_date'].dt.strftime('%H')
    if 'TODAS' in community:
        community = COMMUNITIES

    # Get the current period date
    d1 = dt.strptime(date, '%Y-%m-%d')
    d1 = d1.replace(day=1)
    one_month = relativedelta(months=1)
    d2 = d1 + one_month
    end_date = d2.strftime("%Y-%m-%d")
    start_date = d1.strftime("%Y-%m-%d")

    rid_ff=filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff=filter_dataframe(matches, community, start_date, end_date,tranport_type)

    # Filter rides to only working days
    rid_ff['publicaciones']=1


    # Summary

    f1 = rid_ff.groupby('driver_id').agg(dict(publicaciones='sum'))
    match_ff['viaje_conductor'] = 1
    f2 = match_ff.groupby('driver_id').agg(dict(viaje_conductor='sum'))
    match_ff['viaje_pasajero'] = 1
    f3 = match_ff.groupby('passenger_id').agg(dict(viaje_pasajero='sum'))


    #bins = [0, 3,  6, 11, 16, 21, 26, 31, 36, 41, 46, 10000]
    bins1 = np.arange(6, 56, 5)
    bins = [0,3]

    for i in bins1:
        bins.append(i)
    bins.append(10000)
    bins_text = ['prueba']
    bins_text = [str(i)+'-'+ str(i) for i in bins[1:-1]]
    hist = np.histogram(f1['publicaciones'], bins=bins)
    bins_text =['1-2', '3-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31-35', '36-40',
                '41-45', '46-50', 'mas de 50']


    cols =['publicaciones']
    # create data list
    traces = []
    for i in cols:
        #formattedList = ["{:,}".format(int(round(member, 0))) for member in result[i]]

        formattedList = ["{:,}".format(int(round(member, 0))) for member in hist[0]]
        traces.append(go.Bar(
            y=hist[0],
            #x=range(len(hist[0])),
            text=formattedList,
            textposition='inside',
            hoverinfo='text',
            hovertext=formattedList,
            textfont={'size': ftxt_size - 1},
            insidetextfont={'size': ftxt_size - 1},
            constraintext='none',
            marker={'color': '#10ac84'},
            name=i
        )
        )

    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            #barmode='stack',
            showlegend=False,
            # separators=',.',
            font={
                "family": "Raleway",
                "size": ftxt_size
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },
            margin=layout_margin,

            width=500,

            xaxis=dict(
                # type='line',
                tickvals=[ j for j in range(len(hist[0]))],
                ticktext=bins_text,
                showgrid=True,
                ticks='outside',
                tickformat=',2r',  # tickformat=',.2r'
                automargin=True,
                title='Numero conexiones',
                titlefont=dict(
                    size=ftxt_size,
                    color='rgb(107, 107, 107)'
                ),

            ),
            yaxis=dict(
                zeroline=False,
                title='Numero de conductores',
                titlefont=dict(
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    color='rgb(107, 107, 107)'
                )
            )
        )
    }

# callback to update graph
@app.callback(
    Output('hist_pass', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-month', 'date'),
     Input('trans_type_pub', 'value')
     ]
)

def update_graph(community, date, tranport_type):
    #rides['pub_hora'] = rides['publication_date'].dt.strftime('%H')
    if 'TODAS' in community:
        community = COMMUNITIES

    # Get the current period date
    d1 = dt.strptime(date, '%Y-%m-%d')
    d1 = d1.replace(day=1)
    one_month = relativedelta(months=1)
    d2 = d1 + one_month
    end_date = d2.strftime("%Y-%m-%d")
    start_date = d1.strftime("%Y-%m-%d")

    rid_ff=filter_dataframe(rides, community, start_date, end_date,tranport_type)
    match_ff=filter_dataframe(matches, community, start_date, end_date,tranport_type)

    # Filter rides to only working days
    rid_ff['publicaciones']=1


    # Summary

    f1 = rid_ff.groupby('driver_id').agg(dict(publicaciones='sum'))
    match_ff['viaje_conductor'] = 1
    f2 = match_ff.groupby('driver_id').agg(dict(viaje_conductor='sum'))
    match_ff['viaje_pasajero'] = 1
    f3 = match_ff.groupby('passenger_id').agg(dict(viaje_pasajero='sum'))


    #bins = [0, 3,  6, 11, 16, 21, 26, 31, 36, 41, 46, 10000]
    bins1 = np.arange(6, 56, 5)
    bins = [0,3]

    for i in bins1:
        bins.append(i)
    bins.append(10000)
    bins_text = ['prueba']
    bins_text = [str(i)+'-'+ str(i) for i in bins[1:-1]]
    hist = np.histogram(f3['viaje_pasajero'], bins=bins)
    bins_text =['1-2', '3-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31-35', '36-40',
                '41-45', '46-50', 'mas de 50']


    cols =['viaje_pasajero']
    # create data list
    traces = []
    for i in cols:
        #formattedList = ["{:,}".format(int(round(member, 0))) for member in result[i]]

        formattedList = ["{:,}".format(int(round(member, 0))) for member in hist[0]]
        traces.append(go.Bar(
            y=hist[0],
            #x=range(len(hist[0])),
            text=formattedList,
            textposition='inside',
            hoverinfo='text',
            hovertext=formattedList,
            textfont={'size': ftxt_size - 1},
            insidetextfont={'size': ftxt_size - 1},
            constraintext='none',
            marker={'color': '#10ac84'},
            name=i
        )
        )

    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            #barmode='stack',
            showlegend=False,
            # separators=',.',
            font={
                "family": "Raleway",
                "size": ftxt_size
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },
            margin=layout_margin,

            width=500,

            xaxis=dict(
                # type='line',
                tickvals=[ j for j in range(len(hist[0]))],
                ticktext=bins_text,
                showgrid=True,
                ticks='outside',
                tickformat=',2r',  # tickformat=',.2r'
                automargin=True,
                title='Numero publicaciones',
                titlefont=dict(
                    size=ftxt_size,
                    color='rgb(107, 107, 107)'
                ),

            ),
            yaxis=dict(
                zeroline=False,
                title='Numero de pasajeros',
                titlefont=dict(
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    color='rgb(107, 107, 107)'
                )
            )

    #---------------------------------


        )
    }


# callback to update graph
@app.callback(
    Output('users_med_trans', 'figure'),
    [Input('dropdown_com', 'value'),
     Input('date-picker-month', 'date')
     ]
)


def update_users_graph(community, date):

    if 'TODAS' in community:
        community = COMMUNITIES

    # Get the current period date
    d1 = dt.strptime(date, '%Y-%m-%d')
    d1 = d1.replace(day=1)
    one_month = relativedelta(months=1)
    d2 = d1 + one_month
    end_date = d2.strftime("%Y-%m-%d")
    start_date = d1.strftime("%Y-%m-%d")

    # Only filter by community, since it is  cumulative do not filter by date, only
    # filter after the cum sum
    act_users = active_users_type(rides, matches, community, start_date, end_date)
    #cnt = act_users.groupby(['user_type', 'type'])['user_id'].value_counts()
    #cnt = act_users.groupby(['type', 'user_type'])['user_id'].nunique()
    #cnt = act_users.groupby(['type', 'user_type'])['user_id'].nunique().reset_index().rename(
    #    columns={'user_id': 'users'})

    result = act_users.groupby(['type', 'user_type'])['user_id'].nunique().unstack().fillna(0).reset_index().rename(
        columns={'user_id': 'users'})

    result = act_users.groupby(['user_type', 'type'])['user_id'].nunique().unstack().fillna(0).reset_index().rename(
        columns={'user_id': 'users'})

    # create data list
    traces = []
    for i in result.user_type:
        cnt = result[result.user_type == i][['bicycle',   'car',  'walk']]
        vals = cnt.values.tolist()
        #formattedList = ["{:.0f}%".format(member) for member in result[i]]
        hover_text = ["{:,}".format(int(member)) for member in vals[0]]
        traces.append(go.Bar(
            x=['bicicleta','carro', 'caminata'],
            y=vals[0],
            text=hover_text,
            textposition='inside',
            name=i,
            hoverinfo='text',
            hovertext=hover_text

             )
        )


    return {
        'data': traces,
        'layout': go.Layout(
            title='',
            #barmode='stack',
            showlegend=True,
            separators=',.',
            font={
                "family": "Raleway",
                "size": ftxt_size
            },
            height=gheight,
            hovermode="closest",
            legend={
                "x": -0.0228945952895,
                "y": 1.2,
                "orientation": "h",
                "yanchor": "top"
            },
            margin={
                "r": 30,
                "t": 20,
                "b": 60,
                "l": 60
            },

            width=400,

            xaxis=dict(
                # type='line',
                showgrid=True,
                #tickvals=[1,2,3],
                #ßticktext=['bicicleta','carro', 'caminata'],
                ticks='outside',

                automargin=True
            ),
            yaxis=dict(
                title='Numero de usuarios',
                zeroline= False,
                tickformat=',2r',
                titlefont=dict(
                    size=ftxt_size,
                    color='rgb(107, 107, 107)'
                ),
                tickfont=dict(
                    size=ftxt_size,
                    color='rgb(107, 107, 107)'
                )
            )


        )
    }





# ----------------------------------------------------------------------------
#  TAB PARAMS
# ----------------------------------------------------------------------------

# callback table creation
@app.callback(Output('params_table', 'rows'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename')])
def update_output(contents, filename):
    if contents is not None:
        df = parse_contents_simple(contents, filename, COMMUNITIES)
        logger.info(df)
        if df is not None:
            return df.to_dict('records')
        else:
            return [{}]
    else:
        return params_clean.to_dict('records')


# ----------------------------------------------------------------------------
#  TAB TOP DRIVER
# ----------------------------------------------------------------------------

# callback table creation
@app.callback(Output('scores_table', 'rows'),
              [Input('dropdown_com', 'value'),
               Input('date-picker-puntaje', 'date'),
               Input('radio_scores','value'),
               Input('params_table', 'rows')
               ]
              )
def update_table(community, date, radio_score,params_rows):
    if 'TODAS' in community:
        community = COMMUNITIES

    params = pd.DataFrame(params_rows)

    # Get the current period date
    d1 = dt.strptime(date, '%Y-%m-%d')
    d1 = d1.replace(day=1)
    one_month = relativedelta(months=1)
    d2 = d1 - (int(radio_score)-1)*one_month
    end_date = d1.strftime("%Y-%m-%d")
    start_date = d2.strftime("%Y-%m-%d")

    summary_user = pd.DataFrame()

    for i in range(int(radio_score)-1):
        d1 =  d2 + (i+1)*one_month
        end_date = d1.strftime("%Y-%m-%d")
        summary = active_users_summary(users, rides, matches, community, params, start_date, end_date)
        if i == 0:
            summary_user['email'] = summary['email']

        summary_user[start_date] = summary['Puntaje']
        start_date = end_date


    summary_user.set_index('email')
    # Make the last period the actual table and join with the summary_user
    d1 = d2 + (i + 2) * one_month
    end_date = d1.strftime("%Y-%m-%d")
    summary = active_users_summary(users, rides, matches, community, params, start_date, end_date)
    summary_final = summary

    summary_final.set_index('email')
    email = summary_final['email']
    summary_final.drop(columns=['email'], inplace=True)
    summary_user.drop(columns=['email'], inplace=True)

    summary_final['Puntaje Promedio1'] = summary_user.sum(axis=1)
    summary_final = pd.merge(summary_final,
                             summary_user,
                             left_index=True, right_index=True, how='inner')

    summary_final['Puntaje Promedio'] = summary_final['Puntaje Promedio1'] + summary_final['Puntaje']
    summary_final.drop(columns=['Puntaje Promedio1'], inplace=True)
    summary_final['email'] = email
    cols = summary_final.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    summary_final = summary_final[cols]
    logger.info(summary_final.head())
    return summary_final.to_dict('records')



@app.callback(
    Output('scores_fig', 'figure'),
    [Input('scores_table', 'rows'),
     Input('scores_table', 'selected_row_indices')])

def update_figure(rows, selected_row_indices):
    dff = pd.DataFrame(rows)
    marker = {'color': ['#0074D9']*len(dff)}

    if len(selected_row_indices) == 0:
        last_index = 0
    else:
        last_index = selected_row_indices[0:][0]

    for i in (selected_row_indices or []):
        marker['color'][i] = '#FF851B'

    marker['color'][last_index] = '#10ac84'

    # CHANGE THE COLOR OF THE LAST INDEX
    cols = dff.columns.tolist()
    colsf=cols[0:-12]


    fig = plotly.tools.make_subplots(
        rows=3, cols=2, specs=[[{}, {}], [{'colspan': 2}, None], [{'colspan': 2}, None]],
        subplot_titles=('Puntaje : ' + dff['email'].iloc[last_index],'', 'Puntaje periodo actual', 'Puntaje acumulado'),
        shared_xaxes=False)

    fig.append_trace({
        'x': colsf,
        'y': dff[colsf].iloc[last_index],
        'type': 'bar',
        'hoverinfo':'text',
        'marker': {'color':'#10ac84'},
        'hovertext': '',
        'text': dff[colsf].iloc[last_index],
        'textposition':'inside',
        'textfont': {'size': ftxt_size , 'color': 'white'}


    }, 1, 1)

    fig.append_trace({

        'y': dff['Puntaje'],
        'type': 'bar',
        'text': '',
        'hoverinfo':'text',
        'hovertext':dff['email'],
        'marker': marker
    }, 2, 1)
    fig.append_trace({

        'y': dff['Puntaje Promedio'],
        'type': 'bar',
        'marker': marker,
        'text': '',
        'hoverinfo': 'text',
        'hovertext':dff['email'],
    }, 3, 1)
    fig['layout']['showlegend'] = False
    fig['layout']['height'] = 900
    fig['layout']['yaxis1'].update(title='Puntaje')
    fig['layout']['yaxis1'].update(tickvals=colsf)
    fig['layout']['yaxis1'].update(tickvals=colsf)
    fig['layout']['yaxis3'].update(title='Puntaje')
    fig['layout']['yaxis4'].update(title='Puntaje')
    fig['layout']['margin'] = {
        'l': 40,
        'r': 10,
        't': 60,
        'b': 200
    }

    return fig

@app.callback(Output('my-link', 'href'),
              [Input('scores_table', 'rows')])
def update_link(value):

    return '/dash/urlToDownload?value={}'.format(value)


@app.server.route('/dash/urlToDownload')
def download_csv():
    value = flask.request.args.get('value')
    #value = pd.DataFrame(value)
    # create a dynamic csv or file here using `StringIO`
    # (instead of writing to the file system)
    str_io = io.StringIO()
    str_io.write('You have selected {}'.format(value))
    mem = io.BytesIO()
    mem.write(str_io.getvalue().encode('utf-8'))
    mem.seek(0)
    str_io.close()
    return flask.send_file(mem,
                           mimetype='text/csv',
                           attachment_filename='downloadFile.csv',
                           as_attachment=True)

@app.callback(
    Output('scores_table', 'selected_row_indices'),
    [Input('scores_fig', 'clickData')],
    [State('scores_table', 'selected_row_indices')])
def update_selected_row_indices(clickData, selected_row_indices):
    if clickData:
        for point in clickData['points']:
            if point['pointNumber'] in selected_row_indices:
                selected_row_indices.remove(point['pointNumber'])
            else:
                selected_row_indices.insert(0, point['pointNumber'])
                #selected_row_indices.append(point['pointNumber'])
    return selected_row_indices



if __name__ == '__main__':
    app.run_server(debug=True)



