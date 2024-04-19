## CS2 Battle Bot API
Backend server for cs2 battle discord bot

[![Generate Client](https://github.com/Qwizi/cs2-battle-bot-api/actions/workflows/generate-schema.yml/badge.svg)](https://github.com/Qwizi/cs2-battle-bot-api/actions/workflows/generate-schema.yml)
[![Publish Backend Docker image](https://github.com/Qwizi/cs2-battle-bot-api/actions/workflows/docker.yml/badge.svg)](https://github.com/Qwizi/cs2-battle-bot-api/actions/workflows/docker.yml)
[![Tests](https://github.com/Qwizi/cs2-battle-bot-api/actions/workflows/test.yml/badge.svg)](https://github.com/Qwizi/cs2-battle-bot-api/actions/workflows/test.yml)


## Installation

### Docker

1. **Setting Up Docker**
Create a Docker network for the CS2 Battle Bot:

```shell
docker network create cs2-battle-bot-network
```
2. **Docker Compose Configuration**
Create a docker-compose.yml file with the following configuration:

```yaml
services:
  app:
    container_name: cs2_battle_bot_api
    image: qwizii/cs2-battle-bot-api:latest
    command: gunicorn cs2_battle_bot.wsgi:application --bind 0.0.0.0:8000
    ports:
      - "8003:8000"
    environment:
      - SECRET_KEY=django-insecure-#
      - DB_ENGINE=django.db.backends.postgresql
      - DB_HOST=db
      - DB_NAME=cs2_db
      - DB_USER=cs2_user
      - DB_PASSWORD=cs2_password
      - DB_PORT=5432
      - REDIS_URL=redis://redis:6379/0
      - HOST_URL=http://localhost:8003
      - DISCORD_CLIENT_ID=
      - DISCORD_CLIENT_SECRET=
      - DISCORD_REDIRECT_URI=http://localhost:8003/accounts/discord/callback
      - STEAM_API_KEY=
      - STEAM_REDIRECT_URI=https://localhost:8003/accounts/steam/callback
      - RCON_HOST=
      - RCON_PORT=
      - RCON_PASSWORD=
      - API_KEY=
    restart: always
    depends_on:
      - db
    networks:
      - cs2-battle-bot-network
  db:
    image: postgres:15.1
    container_name: cs2_battle_bot_db
    environment:
      - POSTGRES_DB=cs2_db
      - POSTGRES_USER=cs2_user
      - POSTGRES_PASSWORD=cs2_password
    restart: always
    expose:
      - "5435:5432"
    networks:
      - cs2-battle-bot-network
  redis:
    image: "redis:alpine"
    container_name: cs2_battle_bot_redis
    restart: always
    expose:
      - "6379:6379"
    networks:
      - cs2-battle-bot-network
networks:
  cs2-battle-bot-network:
    external: true
```
3. **Building and Running Containers**
Build and run the containers:
```shell
docker compose up -d --build
```
4. **Running Migrations**
Run migrations:
```shell
docker compose exec app python manage.py migrate
```
5. **Creating Super User**
Create a superuser:
```shell
docker compose exec app python manage.py createsuperuser
```
6. **Creating API Key**
   1. Access the admin panel at http://localhost:8003/admin/ using the superuser credentials.
   2. Navigate to the API Keys section.
   3. Click on the "Add" button to create a new API key, providing a name and expiration date.
   4. Save the API key.
   5. After completing the previous steps, you will see a message similar to the following in the admin panel:
   ![Api token](https://i.imgur.com/RrfuGNH.png)
   6. Update the API_KEY environment variable in your docker-compose.yml file with the new key.
   7. Rebuild the containers:
   ```shell
   docker compose up -d --build
   ```
7. **Add maps**:
Run fixture with maps
```shell
docker compose exec app python manage.py loaddata maps
```
