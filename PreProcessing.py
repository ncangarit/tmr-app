

#source dash_env/bin/activate


import pymysql
import pandas as pd
pymysql.install_as_MySQLdb()
import MySQLdb
import timeit
from pandasql import sqldf


from tmr_logger import get_logger, get_console_handler,get_file_handler

import logging

def load_data_csv():
    logger = get_logger("PreProcessing")
    logger.info("Loading Data")

    rides = pd.read_csv('data/rides.csv')
    matches = pd.read_csv('data/matches.csv')
    users = pd.read_csv('data/users.csv')

    users['date'] = pd.to_datetime(users['date'])
    matches['date'] = pd.to_datetime(matches['date'])
    rides['date'] = pd.to_datetime(rides['date'])

    rides.index = rides['date']
    matches.index = matches['date']
    users.index = users['date']

    return users, rides, matches


def load_data():
    # This needs to be migrated, perhaps AWS configuration manager?
    host="localhost"
    dbname="test"
    user="tmr"
    password="tmr2018"


    conn = pymysql.connect(host, user=user,
                               passwd=password, db=dbname)


    logger = get_logger("PreProcessing")
    logger.info("Loading Data")

    # Create variable for pandasql
    pysqldf = lambda q: sqldf(q, globals())

    # start = timeit.default_timer()
    # cursor = conn.cursor()
    # cursor.execute('select * from matches');
    # rows = cursor.fetchall()
    # matches = pd.DataFrame( [[ij for ij in i] for i in rows] )
    # stop = timeit.default_timer()
    #
    # print ("Cursor execute")
    # print(stop - start)

    cursor = conn.cursor()
    start = timeit.default_timer()

    # #----------------------------------------------
    # # Load users table, remove admin type users
    logger.info("Loading User Data")

    # Users can be associated to more than one community, if adding communities here users will have duplicated values
    # when using users later on, drop community column and drop duplicates

    # users = pd.read_sql('SELECT user_id, first_name, last_name, commute_mode, neighborhood, created_at as registration_date,\
    #                     main_email, \
    #                     CASE WHEN (user_id not in(select driver_id from rides)\
    #                                 AND user_id not in \
    #                                 (select user_id from passengers) ) THEN "REGISTERED"\
    #                                 ELSE "ACTIVE" END  AS user_type FROM users \
    #                     WHERE  type != "admin" AND validated_email=1 AND main_email NOT IN \
    #                         (SELECT main_email FROM (\
    #                             SELECT main_email , count(user_id) as dup FROM users GROUP BY 1 \
    #                                 HAVING dup>1) as a);', con=conn)

    cursor.execute("""
                SELECT a.user_id, a.first_name, a.last_name, a.commute_mode, a.neighborhood, a.created_at as date,
                        a.main_email, c.name as community,
                CASE WHEN (a.user_id not in(select driver_id from rides) AND a.user_id not in 
                (select user_id from passengers) ) THEN "REGISTERED"
                ELSE "ACTIVE" END AS user_type 
                FROM users as a
                LEFT JOIN user_communities as b
                ON a.user_id = b.user_id
                LEFT JOIN communities as c
                ON b.community_id = c.id
                WHERE  type != "admin" AND validated_email=1 AND main_email NOT IN 
                            (SELECT main_email FROM (
                                SELECT main_email , count(user_id) as dup FROM users GROUP BY 1 
                                    HAVING dup>1) as a);

    """)
    rows = cursor.fetchall()
    users = pd.DataFrame([[ij for ij in i] for i in rows])
    users.columns = ['user_id', 'first_name', 'last_name', 'commute_mode', 'neighborhood', 'date',
                     'main_email','community', 'user_type']

    # add new id
    users["new_id"] = users.index + 1
    users['date'] = pd.to_datetime(users['date'])
    users['reg_date_ym'] = users.date.dt.to_period('M')
    users.index = users['date']

    # #-----------------------------------------------
    # Look for duplicated users, remove from further queries, most likely these are all admin
    dup_users1 = pd.read_sql('SELECT user_id FROM users \
                            WHERE main_email IN \
                            (SELECT main_email FROM (\
                                SELECT main_email , count(user_id) as dup FROM users GROUP BY 1 \
                                    HAVING dup>1) as a);',con=conn)

    dup_users = dup_users1['user_id'].values.tolist()
    format_strings = ','.join(['%s'] * len(dup_users))

    # #------------------------------------------------
    # # Create the matches table, join with the rides, passengers and community
    # logger.info("Loading Matches Data")

    logger.info("Loading Matches Data")

    cursor.execute("""
    SELECT d.name as community, a.ride_id, a.date, b.hour, a.created_at as publication_date,  b.driver_id,
            c.user_id as passenger_id, coalesce(c.created_at, NULL) as match_date,
            b.type, b.seats, b.begin_location_gps,
            b.end_location_gps, b.distance_value,
            a.updated_at, c.updated_at AS pass_updated_at,
            YEAR(a.date) as ride_year, MONTH(a.date) as ride_month,
            WEEK(a.date) as ride_week, DAYOFWEEK(a.date) as ride_dow, DAY(a.date) as ride_day, HOUR(b.hour) as ride_hour
    FROM ride_dates AS a
    JOIN rides  AS b  ON a.ride_id = b.ride_id
    JOIN passengers as c
    ON a.ride_id = c.ride_id
    AND a.date = c.date
    JOIN communities as d
    ON b.community_id = d.id
    WHERE a.deleted_at IS NULL
    AND c.user_id not in (%s)
    """ % format_strings, tuple(dup_users));

    rows = cursor.fetchall()
    matches = pd.DataFrame( [[ij for ij in i] for i in rows] )

    # Add column names
    matches.columns = ['community','ride_id','date', 'hour', 'publication_date', 'driver_id', 'passenger_id',
                        'match_date', 'type','seats','begin_location_gps','end_location_gps','distance_value',
                       'updated_at','pass_updated_at', 'ride_year','ride_month','ride_week','ride_dow','ride_day', 'ride_hour']

    #Standarise date types
    matches['date'] =  pd.to_datetime(matches['date'])
    matches['publication_date'] = pd.to_datetime(matches['publication_date'])
    matches['match_date'] = pd.to_datetime(matches['match_date'])
    matches.index = matches['date']
    #df.resample('M').agg(dict(score='count'))

    #matches['ride'] = matches.date.dt.to_period('M')
    #matches['year_week'] = matches.date.dt.to_period('W')

    #
    #
    #-------------------------------------------
    # Get only valid and clean rides

    logger.info("Loading Rides Data")

    cursor.execute("""
    SELECT d.name as community, a.ride_id, a.date, b.hour, a.created_at as publication_date, b.driver_id,
                    b.type, b.seats, b.begin_location_gps, b.end_location_gps, b.distance_value,
                    a.updated_at, YEAR(a.date) as ride_year, MONTH(a.date) as ride_year,  
                    WEEK(a.date) as ride_week, DAYOFWEEK(a.date) as ride_dow, DAY(a.date) as ride_day, 
                    HOUR(b.hour) as ride_hour
    FROM ride_dates AS a
    JOIN rides  AS b  ON a.ride_id = b.ride_id
    JOIN communities as d
    ON b.community_id = d.id
    WHERE a.deleted_at IS NULL 
    AND b.driver_id not in (%s)
    """ % format_strings, tuple(dup_users));

    rows = cursor.fetchall()
    rides = pd.DataFrame( [[ij for ij in i] for i in rows])
    # Add column names
    rides.columns = ['community','ride_id','date', 'hour', 'publication_date', 'driver_id', 'type','seats',
                     'begin_location_gps','end_location_gps','distance_value',
                       'updated_at', 'ride_year','ride_month','ride_week','ride_dow','ride_day', 'ride_hour']


    #Standarise date types
    rides['date'] =  pd.to_datetime(rides['date'])
    rides.index = rides['date']

    rides['year_month'] = rides.date.dt.to_period('M')


    logger.info("Finish Loading Data")



    stop = timeit.default_timer()
    logger.info (stop - start)
    conn.close()


    #-------------------------------------------------------
    #df2 = users.groupby('commute_mode').resample("M").count()

    return users, rides, matches



#matches_day = matches.groupby(['community','ride_year','ride_month'])

#mujeres = pd.read_csv("/Users/natisangarita/TryMyRide/mujeres.csv")
#hombres = pd.read_csv("/Users/natisangarita/TryMyRide/hombres.csv")

#select iso_country, type, count(*) from airports group by iso_country, type order by iso_country, count(*) desc
#airports.groupby(['iso_country', 'type']).size().to_frame('size').reset_index().sort_values(['iso_country', 'size'], ascending=[True, False])