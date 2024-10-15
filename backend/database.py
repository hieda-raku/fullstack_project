# database.py - Database Interaction Module
import psycopg2
from psycopg2 import sql
import logging

# Database connection parameters (should be stored securely in a config file)
DB_PARAMS = {
    'dbname': 'sensor_data',
    'user': 'username',
    'password': 'password',
    'host': 'localhost',
    'port': '5432'
}

# Store parsed sensor data into database
def store_sensor_data(station_id, vice_id, parsed_data):
    try:
        connection = psycopg2.connect(**DB_PARAMS)
        cursor = connection.cursor()
        
        for data in parsed_data:
            columns = data.keys()
            values = [data[column] for column in columns]
            insert_query = sql.SQL("INSERT INTO meteorological_data ({}) VALUES ({})").format(
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(values))
            )
            cursor.execute(insert_query, values)
        
        connection.commit()
    except Exception as e:
        logging.error(f"Failed to store data in the database: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()