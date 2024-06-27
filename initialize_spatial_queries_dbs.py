from pymongo import MongoClient
import psycopg2
from psycopg2 import sql
from pykml import parser
from pykml.factory import nsmap

if __name__ == '__main__':

    conn_params = {
        "host": "db",
        "database": "citizix_db",
        "user": "citizix_user",
        "password": "S3cret",
    }

    client_postgresql = psycopg2.connect(**conn_params)

    client_mongodb = MongoClient("mongodb://db_mongo:27017/")

    # create a table with 2 fields : long_name (text) - box (geometry-polygon - projection 4326)
    cur = client_postgresql.cursor()

    create_table_query = sql.SQL("""
    CREATE TABLE IF NOT EXISTS comune (
        id INT PRIMARY KEY,
        nome_comune TEXT,
        box GEOMETRY(Polygon, 4326)
    )
    """)

    cur.execute(create_table_query)
    cur.close()
    client_postgresql.commit()

    # extracting collection places from MONGODB
    db = client_mongodb['test-db']
    collection = db['places']
    places = collection.find()

    id_test = 0

    for place in places:

        # step 1 : extracting name and bounding box form 'places' collection from mongodb
        long_name = place['long_name']['it']
        bounding_box = place['bbox']

        # step 2
        # create a new tupla with long_name and bounding_box extracted
        # insert the new tupla into the table in postgresql
        polygon_wkt = f"POLYGON(({', '.join([f'{x} {y}' for x, y in bounding_box['coordinates']])}))"
        cur = client_postgresql.cursor()
        query = sql.SQL("INSERT INTO comune (id, nome_comune, box) VALUES (%s, %s, ST_GeomFromText(%s))")
        # if long_name == "Comune di Valverde" or long_name == "Comune di Calliano":
        #    pass
        # else:
        cur.execute(query, [id_test, long_name, polygon_wkt])
        id_test+=1
        print("[*] Insert : " + long_name + " -- box : " + str(bounding_box['coordinates']), flush=True)
        cur.close()
        client_postgresql.commit()

    print("[*] Municipalities table created and populated", flush=True)    