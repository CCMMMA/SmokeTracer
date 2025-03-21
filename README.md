# FUMI2
Fumi2 Parthenope Project


To build the containers :


docker compose up --build -d  
docker exec -it container_FUMI2 /bin/bash  
chmod +x initialize_spatial_queries_dbs.py  
python3 initialize_spatial_queries_dbs.py  
exit  

