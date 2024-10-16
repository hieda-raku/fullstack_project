# database.py - 数据库交互模块
import psycopg2
from psycopg2 import sql
import logging

# 数据库连接参数（应安全地存储在配置文件中）
DB_PARAMS = {
    'dbname': 'sensor_data',
    'user': 'raku',
    'password': '970226',
    'host': 'localhost',
    'port': '5432'
}

# 将解析后的传感器数据存储到数据库中
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
        logging.error(f"将数据存储到数据库时失败: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()