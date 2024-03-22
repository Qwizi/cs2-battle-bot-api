from rest_framework.response import Response
from matches.models import (
    Map,
    Match,
)
from rest_framework import viewsets
from rest_framework.decorators import action

from matches.serializers import (
    MapBanSerializer,
    MapSerializer,
    MatchConfigSerializer,
    MatchMapSelectedSerializer,
    MatchSerializer,
)
from matches.utils import (
    ban_map,
    create_match,
    join_match,
    load_match,
    pick_map,
    process_webhook,
    recreate_match,
    shuffle_teams,
)


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

    def create(self, request, *args, **kwargs):
        return create_match(request)

    @action(detail=True, methods=["POST"])
    def load(self, request, pk=None):
        return load_match(pk)

    @action(detail=False, methods=["POST"])
    def webhook(self, request):
        return process_webhook(request)

    @action(detail=True, methods=["POST"])
    def map_ban(self, request, pk):
        return ban_map(request, pk)

    @action(detail=True, methods=["POST"])
    def map_pick(self, request, pk):
        return pick_map(request, pk)

    @action(detail=True, methods=["POST"])
    def recreate(self, request, pk):
        return recreate_match(request, pk)

    @action(detail=True, methods=["POST"])
    def shuffle_teams(self, request, pk):
        return shuffle_teams(request, pk)

    @action(detail=True, methods=["GET"])
    def bans(self, request, pk):
        match: Match = self.get_object()
        queryset = match.map_bans.all().order_by("-created_at")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MapBanSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MapBanSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["GET"])
    def picks(self, request, pk):
        match: Match = self.get_object()
        queryset = match.map_picks.all().order_by("-created_at")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MatchMapSelectedSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MatchMapSelectedSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def join(self, request, pk):
        return join_match(request, pk)

    @action(detail=True, methods=["GET"])
    def config(self, request, pk):
        match = self.get_object()
        serializer = MatchConfigSerializer(data=match.get_config())
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        return Response(serializer.data, status=200)


class MapViewSet(viewsets.ModelViewSet):
    queryset = Map.objects.all()
    serializer_class = MapSerializer
