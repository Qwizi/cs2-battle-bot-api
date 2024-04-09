#!/bin/bash

# RUN MIGRATIONS
echo "Running migrations"
docker compose exec app sh -c "cd src && python manage.py migrate"
echo "Migrations complete"
