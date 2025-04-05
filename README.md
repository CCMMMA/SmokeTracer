# FUMI2
Fumi2 Parthenope Project


To build the containers :


Assuming you have a database initialization .sql file (with the superuser added inside)    


COMMANDS :    


docker compose up --build -d 
docker exec -it container_FUMI2 /bin/bash
python3 initialize_spatial_queries_dbs.py 
exit

