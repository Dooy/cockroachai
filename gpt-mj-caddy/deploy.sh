#!/bin/bash
set -e
docker compose pull
docker compose up -d --remove-orphans

#老板docker 下面的
# docker-compose pull
# docker-compose up -d --remove-orphans