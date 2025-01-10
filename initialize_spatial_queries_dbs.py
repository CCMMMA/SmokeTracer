from pymongo import MongoClient
import psycopg2
from psycopg2 import sql
from pykml import parser
from pykml.factory import nsmap
import geopandas as gpd
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.wkt import dumps
from shapely.geometry.polygon import LinearRing

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
    create_table_query = sql.SQL("""
    CREATE TABLE IF NOT EXISTS comune (
        id INT PRIMARY KEY,
        nome_comune TEXT,
        box GEOMETRY(Polygon, 4326)
    )
    """)

    cur = client_postgresql.cursor()
    cur.execute(create_table_query)
    cur.close()
    client_postgresql.commit()

    geojson_file = gpd.read_file('SITRC_COMUNI_CAMPANIA.geojson')
    # polygons rappresenta un geodataframe di geopandas 
    polygons = geojson_file[geojson_file.geometry.type == 'Polygon']

    id = 0
    for i in range(0, len(polygons)-1):
        name = polygons.iloc[i]['COMUNE']
        polygon_z = polygons.iloc[i]['geometry']
        polygon_2d = Polygon([(x, y) for x, y, z in polygon_z.exterior.coords])

        # tolerance = 0.1  # Più alto è il valore, più semplice diventa la geometria
        # polygon_2d = polygon_2d.simplify(tolerance, preserve_topology=True)

        cur = client_postgresql.cursor()
        query = sql.SQL("INSERT INTO comune (id, nome_comune, box) VALUES (%s, %s, ST_GeomFromText(%s, 4326))")

        reduced_wkt = dumps(polygon_2d, rounding_precision=5)

        cur.execute(query, [id, name, reduced_wkt])
        id+=1
        print("[*] Insert : {}".format(name), flush=True)
        cur.close()
        client_postgresql.commit()



    '''
    geodataframe_commons = polygons['COMUNE']
    geodataframe_polygon = polygons['geometry']

    geodataframe_commons_dict = geodataframe_commons.to_dict()
    geodataframe_polygon_dict = geodataframe_polygon.to_dict()

    #TODO: if len(commons) == len(polygon)

    final_commons = []
    final_polygons = [] 

    for i in geodataframe_commons_dict:
        final_commons.append(geodataframe_commons[i])

    for i in geodataframe_polygon_dict:
        final_polygons.append(geodataframe_polygon_dict[i])


    id = 0

    for i in range(0, len(final_commons)):
        cur = client_postgresql.cursor()
        # query = sql.SQL("INSERT INTO comune (id, nome_comune, box) VALUES (%s, %s, ST_GeomFromText(%s))")
        query = sql.SQL("INSERT INTO comune (id, nome_comune, box) VALUES (%s, %s, ST_GeomFromText()(%s))")

        #TODO: trasformare il Polygon Z a Polygon 2D 
        #polygon_2d = Polygon([(x, y) for x, y, z in final_polygons[i].exterior.coords])
        
        srid = 4326
        polygon_2d = f"SRID={srid};POLYGON(({', '.join([f'{x} {y}' for x, y, z in final_polygons[i].exterior.coords])}))"

        print("{}".format(polygon_2d))

        cur.execute(query, [id, final_commons[i], polygon_2d])
        id+=1
        # print("[*] Insert : " + str(final_commons[i]) + " -- box : " + str(final_polygons[i]), flush=True)
        print("[*] Insert : {}".format(final_commons[i]), flush=True)
        cur.close()
        client_postgresql.commit()
    '''




    '''
    # per ogni riga del dataframe geopandas 
        # estrai nome comune 
        # estrai polygon Z
        # converti Polygon Z in Polygon 
        # aggiungi la riga alla tabella - id - nome_comune - polygon2D

    

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

        print("---------------------------------------------------------------------------------")
        print(str(polygon_wkt))
        print("---------------------------------------------------------------------------------")

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
    '''


    print("[*] Municipalities table created and populated", flush=True)    
    