#!/bin/bash
echo "Building the project"
docker compose up -d --build
echo "Project is running"

# Run migrations
echo "Running migrations"
docker compose exec app sh -c "cd src && python manage.py migrate"
echo "Migrations complete"

# Loading map fixtures
echo "Loading map fixtures"
docker compose exec app sh -c "cd src && python manage.py loaddata maps"
echo "Map fixtures loaded"

echo "Creating superuser"
# Create superuser
SUPER_USER=$(docker compose exec app sh -c "cd src && python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); user = User.objects.create_superuser('admin', 'admin@myproject.com', 'password'); print(user);\"")
echo "Superuser $SUPER_USER created"

echo "Creating API key"
# Create the API key
API_KEY=$(docker compose exec app sh -c "cd src && python manage.py shell -c \"from rest_framework_api_key.models import APIKey; api_key, key = APIKey.objects.create_key(name='cs2-battle-bot'); print(key);\"")
echo "Api key created: $API_KEY"