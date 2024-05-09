#!/bin/bash
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Run migrations
python manage.py migrate

# Loading map fixtures
python manage.py loaddata maps

# Create superuser
python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME"
echo -e "${GREEN}Superuser ${RED}$DJANGO_SUPERUSER_USERNAME ${NC}created"

# Create the API key
API_KEY=$(python manage.py shell -c "from rest_framework_api_key.models import APIKey; api_key, key = APIKey.objects.create_key(name='cs2-battle-bot'); print(key);")
echo -e "${GREEN}Api key created: ${RED}$API_KEY${NC}. Put this key to the .env file as API_KEY variable. You will not be able to see it again."