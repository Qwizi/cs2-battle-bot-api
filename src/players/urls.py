from rest_framework import routers

from players.views import PlayerViewSet, TeamViewSet

router = routers.SimpleRouter()

router.register(r'players', PlayerViewSet)
router.register(r'teams', TeamViewSet)

urlpatterns = router.urls