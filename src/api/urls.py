from django.urls import include, path


urlpatterns = [
    path("", include("matches.urls")),
    path("", include("servers.urls")),
    path("", include("players.urls")),
    path("", include("guilds.urls")),
]
