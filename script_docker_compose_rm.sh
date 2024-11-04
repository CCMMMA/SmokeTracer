#!/bin/bash

docker container rm -f container_FUMI2 container_postgres_FUMI2
docker image rm -f smoketracer-app smoketracer-db
