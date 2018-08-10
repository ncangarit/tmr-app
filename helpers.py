# Helper functions

import pandas as pd
import numpy as np
from pandasql import sqldf

import base64
import datetime
import io
import timeit
from datetime import datetime as dt
import logging
from tmr_logger import get_logger, get_console_handler,get_file_handler

import dash_html_components as html
import dash_table_experiments as dte
import colorlover as cl


from controls import PARAMS_COLS, DEFAULT_params, SEMAFORO_METAS, COLORS_TABLE, KPIS_HEADERS
from controls import TRANSPORT_TYPE, COMMUTE_MODE, RIDE_TYPE


# Things to remember:
# WHen groupinn by WEEK the date given is of the ending period

pd.options.mode.chained_assignment = None

logger = get_logger("Helpers")


COMMUNITIES1 = ['Citi Mobility Bogota', 'Colpatria', 'Try My Ride', 'UnBosque', 'Compensar', 'Equion', 'Connecta Colectiva', 'ServiEntrega Bogotá', 'MTS Bogota', 'Fontanar Bogotá', 'UNGRD', 'Isarco', 'Bancolombia Medellín', 'Orbis.Com', 'Bancolombia Bogotá', 'ISA', 'Grupo Exito Medellín', 'Comunidad Familia', 'Comunidad TCC', 'Itau', 'Grupo Exito Bogotá', 'ServiEntrega Medellín', 'Protección', 'Comfandi', 'TUYA']
COMMUNITIES1.sort()

#Calculate percentage rows in pandas


def calculate_total(row):
    result = result.rename(columns={'reg_users': 'registered users'})
    total = row['active users'] + row['width']
    return row['height']/total , row['width']/total

def calculate_pct(row):
    total = row['height'] + row['width']
    return row['height']/total , row['width']/total

# reusable components
def make_dash_table(df):
    ''' Return a dash definition of an HTML table for a Pandas dataframe '''
    table = []
    for index, row in df.iterrows():
        html_row = []
        for i in range(len(row)):
            html_row.append(html.Td([row[i]]))
        table.append(html.Tr(html_row))

    return table

#     row.append(html.Td(value, style=style))
# rows.append(html.Tr(row))
# html.Table(
#         # Header
#         [html.Tr([html.Th(col) for col in dataframe.columns])] +
#
#         # Body
#         rows)

def print_button():
    printButton = html.A(['Print PDF'],className="button no-print print",style={'position': "absolute", 'top': '-40', 'right': '0'})
    return printButton

# includes page/full view
def get_logo():
    logo = html.Div([

        html.Div([
            html.Img(src='http://logonoid.com/images/vanguard-logo.png', height='40', width='160')
        ], className="ten columns padded"),

        html.Div([
            dcc.Link('Full View   ', href='/full-view')
        ], className="two columns page-view no-print")

    ], className="row gs-header")
    return logo


def get_header():
    header = html.Div([

        html.Div([
            html.H5(
                'Vanguard 500 Index Fund Investor Shares')
        ], className="twelve columns padded")

    ], className="row gs-header gs-text-header")
    return header


def get_menu():
    menu = html.Div([

        dcc.Link('Overview   ', href='/overview', className="tab first"),

        dcc.Link('Price Performance   ', href='/price-performance', className="tab"),

        dcc.Link('Portfolio & Management   ', href='/portfolio-management', className="tab"),

        dcc.Link('Fees & Minimums   ', href='/fees', className="tab"),

        dcc.Link('Distributions   ', href='/distributions', className="tab"),

        dcc.Link('News & Reviews   ', href='/news-and-reviews', className="tab")

    ], className="row ")
    return menu


def filter_dataframe_date(df, start_date, end_date):
    dff = df[(df['date'] >= start_date) & (df['date'] < end_date)]
    return dff

def user_connections_type(users, rides, matches):

    start = timeit.default_timer()
    logger.info('user_connections_type')
    logger.info("Calculating summary for all connections/publications per ride type")


    # Check the commute mode and rides type
    logger.info("Summary publications")
    frequency = "M"
    rides['viajes'] =1
    f11 = rides.groupby(['driver_id', 'type']).resample(frequency).agg(dict(viajes='sum'))
    f11 = f11.reset_index(['driver_id','type'])
    f11 = f11.rename(columns={'driver_id': 'user_id'})
    f11['tipo_viaje'] = 'publicacion'
    f11['date'] = f11.index

    logger.info("Summary connections conductor")
    matches['viajes'] = 1
    f22 = matches.groupby(['driver_id', 'type']).resample(frequency).agg(dict(viajes='sum'))
    f22 = f22.reset_index(['driver_id', 'type'])
    f22 = f22.rename(columns={'driver_id': 'user_id'})
    f22['tipo_viaje'] = 'conductor'
    f22['date'] = f22.index

    logger.info("Summary connections pasajero")
    matches['viaje_pasajero'] = 1
    f33 = matches.groupby(['passenger_id', 'type']).resample(frequency).agg(dict(viajes='sum'))
    f33 = f33.reset_index(['passenger_id', 'type'])
    f33 = f33.rename(columns={'passenger_id': 'user_id'})
    f33['tipo_viaje'] = 'pasajero'
    f33['date'] = f33.index

    user_trip_type = pd.concat([f11, f22, f33])

    user_trip_type = pd.merge(user_trip_type,
                              users[['user_id', 'commute_mode', 'neighborhood', 'main_email', 'community']],
                              on='user_id', how='left')

    # Get the displaying axis
    user_trip_type['date'] = pd.to_datetime(user_trip_type['date'])
    user_trip_type.index = user_trip_type['date']
    #result.reg_users = result.reg_users.astype(int)
    #result.user_id = result.user_id.astype(int)


    if frequency in ['D']:
        user_trip_type['date']= user_trip_type['date'].dt.strftime('%Y-%m-%d')
    elif frequency in ['W', '2W']:
        user_trip_type['date'] = user_trip_type['date'].dt.strftime('%Y-%W')
    elif frequency in ['M','3M']:
        user_trip_type['date'] = user_trip_type['date'].dt.strftime('%Y-%m')
    else:
        user_trip_type['date'] = user_trip_type['date'].dt.strftime('%Y')

    stop = timeit.default_timer()
    logger.info(stop - start)

    return user_trip_type


    # conexiones1 = pd.merge(f22[['user_id', 'viaje_conductor', 'type']], f33[['viaje_pasajero', 'user_id', 'type']],
    #                        on=['user_id', 'date', 'type'], how='outer')
    #
    # conductor1 = pd.merge(f11[['user_id', 'publicaciones', 'type']], f22[['user_id', 'viaje_conductor', 'type']],
    #                       on=['user_id', 'date', 'type'], how='left')
    #
    # conductor = pd.merge(conductor1, users[['user_id', 'commute_mode', 'neighborhood', 'main_email', 'community']],
    #                      on='user_id', how='left')
    #
    # conexiones = pd.merge(conexiones1, users[['user_id', 'commute_mode', 'neighborhood', 'main_email', 'community']],
    #                       on='user_id', how='left')
    #
    # conexiones.fillna(0, inplace=True)
    # conductor.fillna(0, inplace=True)



def summary_user(users, rides, matches):
    # Create a summary at user level where we have user info and publications, rides, matches
    # Date given by groping is the END of the period
    logger.info('summary_user')
    logger.info("Calculating summary at user level, number of publications, trips as driver & passenger")

    frequency = "M"
    rides['publicaciones'] =1
    f1 = rides.groupby('driver_id').resample(frequency).agg(dict(publicaciones='sum'))
    f1 = f1.reset_index('driver_id')
    f1 = f1.rename(columns={'driver_id': 'user_id'})
    matches['viaje_conductor'] = 1
    f2 = matches.groupby('driver_id').resample(frequency).agg(dict(viaje_conductor='sum'))
    f2 = f2.reset_index('driver_id')
    f2 = f2.rename(columns={'driver_id': 'user_id'})
    matches['viaje_pasajero'] = 1
    f3 = matches.groupby('passenger_id').resample(frequency).agg(dict(viaje_pasajero='sum'))
    f3 = f3.reset_index('passenger_id')
    f3 = f3.rename(columns={'passenger_id': 'user_id'})


    # unir publicaciones y conexiones
    # Este analysis es mejor solo mensual crece expponencialmente
    conexiones1 = pd.merge(f2[['user_id', 'viaje_conductor']], f3[['viaje_pasajero', 'user_id']],
                           on=['user_id', 'date'], how='outer')
    conexiones1['date']=conexiones1.index
    conexiones1['date']=conexiones1['date'].dt.strftime('%Y-%m')

    conductor1 = pd.merge(f1[['user_id', 'publicaciones']], f2[['user_id', 'viaje_conductor']],
                          on=['user_id', 'date'], how='left')
    conductor1['date'] = conductor1.index
    conductor1['date'] = conductor1['date'].dt.strftime('%Y-%m')

    conductor = pd.merge(conductor1, users[['user_id', 'commute_mode', 'neighborhood', 'main_email', 'community']],
                         on='user_id', how='left')

    conexiones = pd.merge(conexiones1, users[['user_id', 'commute_mode', 'neighborhood', 'main_email', 'community']],
                          on='user_id', how='left')

    conexiones.fillna(0, inplace=True)
    conductor.fillna(0, inplace=True)

    conexiones.set_index = conexiones['date']
    conductor.set_index = conductor['date']


    return conexiones, conductor


# def filter_dataframe_column(df, community, start_date, end_date, column_name, column_type):
#
#     if column_type =='all':
#         dff = df[df['community'].isin(community) \
#                  & (df['date'] >= start_date) & (df['date'] < end_date)]
#         return dff
#     else:
#         if type(column_type) is str:
#             column_type = [column_type]
#             dff = df[df['community'].isin(community) \
#                  & (df['date'] >= start_date) & (df['date'] < end_date)
#                  & (df[column_name].isin(column_type))]
#        return dff


def filter_dataframe(df, community, start_date, end_date, type = 'all'):

    if type =='all':

        dff = df[df['community'].isin(community)\
              & (df['date'] >= start_date) & (df['date'] < end_date)]
    else:
        dff = df[df['community'].isin(community) \
                 & (df['date'] >= start_date) & (df['date'] < end_date)
                 & (df['type'] == type)]
    return dff


def active_users(rides, matches, community, start_date, end_date):

    # Active users are defined as the ones that have any type of
    # activity either published or connected

    # Filter rides
    rides_ff = rides[rides['community'].isin(community) \
             & (rides['date'] >= start_date) & (rides['date'] < end_date)]
    # Standarise column name
    rides_ff['user_type'] = 'published'
    rides_ff = rides_ff.rename(columns={'driver_id': 'user_id'})

    matches_ff = matches[matches['community'].isin(community) \
             & (matches['date'] >= start_date) & (matches['date'] < end_date)]

    matches_ff['user_type'] = 'connected'
    matches_ff = matches_ff.rename(columns={'passenger_id': 'user_id'})


    active_users = pd.concat([rides_ff[['user_id','ride_id','date', 'user_type']],matches_ff[['user_id','ride_id','date', 'user_type']] ])

    return active_users


def active_users_type(rides, matches, community, start_date, end_date):

    # Active users are defined as the ones that have any type of
    # activity either published or connected

    # Filter rides
    rides_ff = rides[rides['community'].isin(community) \
             & (rides['date'] >= start_date) & (rides['date'] < end_date)]
    # Standarise column name
    rides_ff['user_type'] = 'usuario publica'
    rides_ff = rides_ff.rename(columns={'driver_id': 'user_id'})

    matches_ff1 = matches[matches['community'].isin(community) \
             & (matches['date'] >= start_date) & (matches['date'] < end_date)]

    matches_ff2 = matches[matches['community'].isin(community) \
             & (matches['date'] >= start_date) & (matches['date'] < end_date)]


    matches_ff1['user_type'] = 'conductor conecta'
    matches_ff1 = matches_ff1.rename(columns={'driver_id': 'user_id'})

    matches_ff2['user_type'] = 'pasajero'
    matches_ff2 = matches_ff2.rename(columns={'passenger_id': 'user_id'})


    active_users = pd.concat([rides_ff[['user_id','ride_id','date', 'user_type','type']],
                              matches_ff1[['user_id','ride_id','date', 'user_type','type']],
                              matches_ff2[['user_id', 'ride_id', 'date', 'user_type', 'type']]])

    return active_users

def active_users_commute(users, rides, matches, community, start_date, end_date, drop_duplicates=True):

    # Active users are defined as the ones that have any type of
    # activity either published or connected

    # Filter rides
    rides_ff = rides[rides['community'].isin(community) \
             & (rides['date'] >= start_date) & (rides['date'] < end_date)]
    # Standarise column name
    rides_ff['user_type'] = 'usuario publica'
    rides_ff = rides_ff.rename(columns={'driver_id': 'user_id'})

    matches_ff1 = matches[matches['community'].isin(community) \
             & (matches['date'] >= start_date) & (matches['date'] < end_date)]

    matches_ff2 = matches[matches['community'].isin(community) \
             & (matches['date'] >= start_date) & (matches['date'] < end_date)]


    matches_ff1['user_type'] = 'conductor conecta'
    matches_ff1 = matches_ff1.rename(columns={'driver_id': 'user_id'})

    matches_ff2['user_type'] = 'pasajero'
    matches_ff2 = matches_ff2.rename(columns={'passenger_id': 'user_id'})



    active_users1 = pd.concat([rides_ff[['user_id','ride_id','date', 'user_type','type','community']],
                              matches_ff1[['user_id','ride_id','date', 'user_type','type','community']],
                              matches_ff2[['user_id', 'ride_id', 'date', 'user_type', 'type','community']]])

    users1 = users.copy(deep=True)
    users1.drop(columns=['community', 'new_id'], inplace=True)
    users1.drop_duplicates(inplace=True)

    if drop_duplicates:
    # Add the commute mode, copy users and drop duplicates

        active_users1.drop(columns=['ride_id','date'],inplace=True)
        active_users1.drop_duplicates(inplace=True)
        active_users = pd.merge(active_users1, users1[['commute_mode','neighborhood', 'main_email','user_id']], on='user_id', how='left')

    else:
         active_users = pd.merge(active_users1, users1[['commute_mode','neighborhood', 'main_email','user_id']], on='user_id', how='left')

    return active_users


def active_users_summary(users, rides, matches, community, params, start_date, end_date):
    '''
    Estimate the summary per person of the active users
    '''
    # Active users are defined as the ones that have any type of
    # activity either published or connected

    # Filter rides
    params_com = params[params['Comunidad'] == community[0]]

    rides_ff = rides[rides['community'].isin(community) \
                     & (rides['date'] >= start_date) & (rides['date'] < end_date)]

    if [params_com['Excluir hora almuerzo'] == 'SI']:
        rides_ff = rides_ff[(rides_ff['ride_hour'] < 11) | (rides_ff['ride_hour'] > 14)]

    if [params_com['Excluir fines de semana'] == 'SI']:
        rides_ff = rides_ff[rides_ff['ride_dow'].isin([2, 3, 4, 5, 6])]

    # Standarise column name
    rides_ff['user_type'] = 'usuario publica'
    rides_ff = rides_ff.rename(columns={'driver_id': 'user_id'})

    matches_ff1 = matches[matches['community'].isin(community) \
                          & (matches['date'] >= start_date) & (matches['date'] < end_date)]
    matches_ff2 = matches[matches['community'].isin(community) \
                          & (matches['date'] >= start_date) & (matches['date'] < end_date)]


    if [params_com['Excluir hora almuerzo'] == 'SI']:
        matches_ff1 = matches_ff1[(matches_ff1['ride_hour'] < 11) | (matches_ff1['ride_hour'] > 14)]
        matches_ff2 = matches_ff2[(matches_ff2['ride_hour'] < 11) | (matches_ff2['ride_hour'] > 14)]

    if [params_com['Excluir fines de semana'] == 'SI']:
        matches_ff1 = matches_ff1[matches_ff1['ride_dow'].isin([2, 3, 4, 5, 6])]
        matches_ff2 = matches_ff2[matches_ff2['ride_dow'].isin([2, 3, 4, 5, 6])]


    matches_ff1['user_type'] = 'conductor conecta'
    matches_ff1 = matches_ff1.rename(columns={'driver_id': 'user_id'})

    matches_ff2['user_type'] = 'pasajero'
    matches_ff2 = matches_ff2.rename(columns={'passenger_id': 'user_id'})

    active_users1 = pd.concat([rides_ff[['user_id', 'ride_id', 'date', 'user_type', 'type', 'community']],
                               matches_ff1[['user_id', 'ride_id', 'date', 'user_type', 'type', 'community']],
                               matches_ff2[['user_id', 'ride_id', 'date', 'user_type', 'type', 'community']]])

    users1 = users.copy(deep=True)
    users1.drop(columns=['community', 'new_id'], inplace=True)
    users1.drop_duplicates(inplace=True)

    act_users = pd.merge(active_users1, users1[['commute_mode', 'neighborhood', 'main_email', 'user_id']],
                                on='user_id', how='left')


    act_users['no'] = 1
    table = pd.pivot_table(act_users, index=["main_email", "user_type", 'type'], values=["no"], aggfunc=np.sum)
    table = table.unstack(['type', 'user_type']).fillna(0)
    table = table.stack(level=[0])
    table = table.reset_index()
    # Create dataframe with the final data
    summary = pd.DataFrame(columns = ['email', 'Puntaje', 'Puntaje Promedio', 'Pub carro', 'Con carro',
                                      'Pub bici', 'Con bici',
                                      'Pub caminata', 'Con caminata',
                                      'Pas carro', 'Pas bici', 'Pas caminata'])

    summary['email'] = table['main_email']

    for rid, val in RIDE_TYPE.items():
        col_name1 = 'Pub '+ val
        col_name2 = 'Con ' + val
        col_name3 = 'Pas ' + val

        # Set defaults, otherwise overwrite
        summary[col_name1] = 0
        summary[col_name2] = 0
        summary[col_name3] = 0


        if rid in table.columns:
            df = table[rid]

            if 'usuario publica' in df.columns:
                summary[col_name1] = df['usuario publica']

            if 'conductor conecta' in df.columns:
                summary[col_name2] = df['conductor conecta']

            if 'pasajero' in df.columns:
                summary[col_name3] = df['pasajero']

    puntaje = estimate_score(summary, params)

    return puntaje


def estimate_score(summary, params_com):
    score = summary['Pub carro'] * params_com['Publicación carro'][0] + \
            summary['Con carro'] * params_com['Conexión carro'][0] + \
            summary['Pub bici'] * params_com['Publicación bicicleta'][0] + \
            summary['Con bici'] * params_com['Conexión bicicleta'][0] + \
            summary['Pub caminata'] * params_com['Publicación caminante'][0] + \
            summary['Con caminata'] * params_com['Conexión caminante'][0] + \
            summary['Pas caminata'] * params_com['Pasajero'][0] + \
            summary['Pas carro'] * params_com['Pasajero'][0] + \
            summary['Pas bici'] * params_com['Pasajero'][0]

    summary['Puntaje'] = score

    return summary


def colormap_commute_mode():
    cmap = cl.scales[str(len(COMMUTE_MODE) + 2)]['qual']['Set1']
    if len(COMMUTE_MODE) !=6:
        logger.warning('More commute modes than expected. Check helpers colormap_commute_mode')
    if len(COMMUTE_MODE) > 5:
        cmap[5] = cmap[6]
        cmap[6] = cmap[7]

    return cmap[:-2]

# def migration_inital_transport(act_users):
#     ''' Estimate distribution of migratino from initial transport
#
#
#     '''
#     #act_users1 = act_users[['user_id','commute_mode']]
#     #act_users1.drop_duplicates(inplace=True)
#     result = act_users.groupby(['commute_mode'])['user_id'].nunique()
#
#     for i, val in COMMUTE_MODE.items():
#         act_users_by_type = act_users[act_users['commute_mode'] == i]
#         result = act_users_by_type.groupby(['type'])['user_id'].nunique()
#
#


def test():
    pysqldf = lambda q: sqldf(q, globals())
    q = """
    SELECT user_id, date, 'published' as user_type
    from rides_ff
    where(user_id not in
          (select driver_id from matches_ff))
    UNION
    SELECT user_id, date, 'passenger' as user_type
    FROM matches_ff
    UNION
    SELECT driver_id as user_id, date, 'driver' as user_type
    FROM matches_ff    
    """

    df = pysqldf(q)


def clean_df_parameters(df, COMMUNITIES):
    # Check that predefined columns are part of the DF and that each community
    # has a row with values, otherwise, removed the ones not part of the DB
    # and add default values for the
    df_clean = pd.DataFrame()
    cols_present = {}
    col_present_list = []
    msg =''
    ok = False
    df.columns = df.columns.str.lstrip()
    df.columns = df.columns.str.rstrip()
    for col, value in PARAMS_COLS.items():
        if col in df.columns:
            df_clean[col] = df[col]
            cols_present[col] = True
            col_present_list.append(True)
        else:
            cols_present[col] = False
            col_present_list.append(False)
            msg = '\n'.join([msg, 'Columna faltante:' +col])

    if all(col_present_list):
        ok = True

    df_clean = df_clean[df_clean['Comunidad'].isin(COMMUNITIES)]
    df_clean['DEFAULT_PARAMS'] = 'NO'

    # Check that all communities are present, if not then add default values
    for community in COMMUNITIES:
        if community in df['Comunidad'].values:
            logger.info('Reading parameters: ' + community)
            pass
        else:
            DEFAULT_params['Comunidad']=community
            logger.info('Default parameters: ' + community)
            df_clean = df_clean.append(DEFAULT_params, ignore_index=True)

    df_clean = df_clean.sort_values(by = ['Comunidad'], ascending=True)

    logger.info(msg)


    return df_clean, ok, msg

def parse_contents(contents, filename, date, COMMUNITIES):

    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif 'xlsx' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))

    except Exception as e:
        logger.error(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    # Check data Frame Columns
    df_clean, ok, msg = clean_df_parameters(df, COMMUNITIES)

    ok = True
    if ok == True:
        return html.Div([
            html.H5(filename),
            html.H6(datetime.datetime.fromtimestamp(date)),

            # Use the DataTable prototype component:
            # github.com/plotly/dash-table-experiments
            dte.DataTable(rows=df_clean.to_dict('records')),

            html.Hr(),  # horizontal line

            # For debugging, display the raw contents provided by the web browser
            html.Div('Raw Content'),
            html.Pre(contents[0:200] + '...', style={
                'whiteSpace': 'pre-wrap',
                'wordBreak': 'break-all'
            })
        ])
    else:
        logger.error(ok)
        return html.Div([
                msg
            ])


# file upload function
def parse_contents_simple(contents, filename, COMMUNITIES):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif 'xlsx' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))

    # Check data Frame Columns
        df_clean, ok, msg = clean_df_parameters(df, COMMUNITIES)

    except Exception as e:
        logger.error(e)
        return None

    return df_clean




def load_community_params(filename):
    # Load the parameters to score communities, based on the locallly saved copy
    pass


def load_summaries():
    connections_user_type = pd.read_csv('data/connections_user_type.csv')
    conexiones_user_sum = pd.read_csv('data/conexiones_user_sum.csv')
    publicaciones_user_sum = pd.read_csv('data/publicaciones_user_sum.csv')

    return connections_user_type, publicaciones_user_sum, conexiones_user_sum

def is_numeric(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def table_cell_style(value, SEMAFORO_METAS):
    style = {}
    if is_numeric(value):

        if value >= SEMAFORO_METAS['VERDE']:
            style = {
                'backgroundColor': COLORS_TABLE[0]['background'],
                'color': COLORS_TABLE[0]['text'],
                'font-size': '9pt',
                'align': ['center', 'center'],
                'line': {'color': '#506784'}
            }
        elif value <= SEMAFORO_METAS['ROJO']:
            style = {
                'backgroundColor': COLORS_TABLE[2]['background'],
                'color': COLORS_TABLE[2]['text'],
                'font-size': '9pt',
                'align': ['center', 'center'],
                'line': {'color': '#506784'}

            }
        else:
            style = { # yellow
                'backgroundColor': COLORS_TABLE[1]['background'],
                'color': COLORS_TABLE[1]['text'],
                'font-size': '9pt',
                'align': ['center', 'center'],
                'line': {'color': '#506784'}
            }

    return style

def make_kpi_table(score_card, max_rows=100):
    ''' Return a dash definition of an HTML table for a Pandas dataframe
        with a pre-defined cell style format
    '''

    rows = []
    style1 = {  # yellow
        'backgroundColor': COLORS_TABLE[1]['background'],
        'color': COLORS_TABLE[1]['text'],
        'font-size': '9pt',
        'align': ['center', 'center'],
        'line': {'color': '#fef0d9'}
    }

    for i in range(min(len(score_card), max_rows)):
        row = []
        for col in score_card.columns:
            if is_numeric(score_card.iloc[i][col]):
                value = round(score_card.iloc[i][col],1)
                style = table_cell_style(value, SEMAFORO_METAS)
                row.append(html.Td(value, style=style))
            else:
                row.append(html.Td(score_card.iloc[i][col],style=style1))
        rows.append(html.Tr(row))

    return html.Table(
        # Header
        [html.Tr([html.Th(col, style={'font-size': '9pt',
                                      'line': {'color': '#fef0d9'}}) for col in score_card.columns])] +

        # Body
        rows)


# reusable componenets
def make_dash_table(df):
    ''' Return a dash definition of an HTML table for a Pandas dataframe '''
    table = []
    for index, row in df.iterrows():
        html_row = []
        for i in range(len(row)):
            html_row.append(html.Td([row[i]]))
        table.append(html.Tr(html_row))
    return table


def estimate_kpis(users, rides, matches, communities, start_date, end_date, params_rows, by_com=True):
    """
    Function to estimate predefined KPIS.
    '% Usuarios registrados',
    '% Usuarios activos',
    '% Usuarios con parqueadero que publican',
    'Efectividad de uso (conexiones/publicaciones)'


    users: dataframe with users
    act_users: list of active users
    communities : list of communitities
    params_rows : rows table community paramters
    by_com: whether estimation row by row - individual communities or aggregated (depending where table is published)
    """

    # Individual: Parameter


    # Get parameters table

    params_community = pd.DataFrame(params_rows)

    # Read population from the table for the desired community
    # Sum over all populations



    if by_com == True:
        cols = ['Comunidad']
        [cols.append(kpi)for kpi in KPIS_HEADERS]
        score_card = pd.DataFrame(columns=cols)


        row_num = 0
        for com in communities:
            row = []
            # Get data such as poblacion & poblacion parqueadero
            poblacion = params_community[params_community['Comunidad'].isin([com])]['Población'].sum()
            poblacion_parqueadero = params_community[params_community['Comunidad'].isin([com])]['Población con parqueadero'].sum()

            # filter users and matches
            users_ff = users[users['community'].isin([com])
                             & (users['date'] >= start_date) & (users['date'] < end_date)]
            users_ff['reg_users'] = 1

            # Registered users
            reg_users = 100 * users_ff['reg_users'].sum() / poblacion

            # Get list of active users
            act_users = active_users(rides, matches, [com], start_date, end_date)

            # Usuarios activos
            no_us_activos = act_users['user_id'].nunique()
            usuarios_activos = 100 * no_us_activos/poblacion

            # Usuarios con parqueadero que publican
            no_us_publica = act_users[act_users['user_type'] == 'published']['user_id'].nunique()
            usuarios_publican = 100 * no_us_publica/poblacion_parqueadero

            # Efectividad de uso(conexiones / publicaciones)
            match_ff1 = matches[matches['community'].isin([com])
                                & (matches['date'] >= start_date) & (matches['date'] < end_date)]

            match_ff = match_ff1.drop_duplicates(subset=['ride_id', 'date'])
            match_ff['conexiones'] = 1

            rides_ff = rides[rides['community'].isin([com])
                             & (rides['date'] >= start_date) & (rides['date'] < end_date)]
            rides_ff['publicaciones'] = 1
            match_ff['conexiones'] = 1

            effectividad = 100 * match_ff['conexiones'].sum() / rides_ff['publicaciones'].sum()

            row = [com, reg_users,usuarios_activos,usuarios_publican, effectividad]

            score_card.loc[row_num] = row

            row_num = row_num + 1

    else:
        poblacion = params_community[params_community['Comunidad'].isin(communities)]['Población'].sum()
        poblacion_parqueadero = params_community[params_community['Comunidad'].isin(communities)][
            'Población con parqueadero'].sum()

        # filter users and matches
        users_ff = users[users['community'].isin(communities)
                         & (users['date'] >= start_date) & (users['date'] < end_date)]
        users_ff['reg_users'] = 1

        # Registered users
        reg_users = 100 * users_ff['reg_users'].sum() / poblacion

        # Usuarios activos
        act_users = active_users(rides, matches, communities, start_date, end_date)

        no_us_activos = act_users['user_id'].nunique()
        usuarios_activos = 100 * no_us_activos / poblacion

        # Usuarios con parqueadero que publican
        no_us_publica = act_users[act_users['user_type'] == 'published']['user_id'].nunique()
        usuarios_publican = 100 * no_us_publica / poblacion_parqueadero

        # Efectividad de uso(conexiones / publicaciones)
        match_ff1 = matches[matches['community'].isin(communities)
                           & (matches['date'] >= start_date) & (matches['date'] < end_date)]

        match_ff = match_ff1.drop_duplicates(subset=['ride_id', 'date'])
        match_ff['conexiones'] = 1

        rides_ff = rides[rides['community'].isin(communities)
                         & (rides['date'] >= start_date) & (rides['date'] < end_date)]
        rides_ff['publicaciones'] = 1
        match_ff['conexiones'] = 1

        effectividad = 100 * match_ff['conexiones'].sum() / rides_ff['publicaciones'].sum()

        row = [reg_users, usuarios_activos, usuarios_publican, effectividad]

        score_card = pd.DataFrame(columns=KPIS_HEADERS)

        score_card.loc[0] = row

    score_card.fillna(0, inplace=True)

    return score_card





def estimate_scores():
    pass