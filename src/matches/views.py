from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.auth import BearerTokenAuthentication
from matches.models import (
    Map,
    Match,
)
from rest_framework import viewsets
from rest_framework.decorators import action

from matches.permissions import IsAuthor
from matches.serializers import (
    MapBanSerializer,
    MapSerializer,
    MatchConfigSerializer,
    MatchMapSelectedSerializer,
    MatchSerializer, CreateMatchSerializer, MatchBanMapSerializer, MatchPickMapSerializer, MatchPlayerJoin,
    MatchBanMapResultSerializer, MatchPickMapResultSerializer,
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
    queryset = Match.objects.all().order_by("created_at")
    serializer_class = MatchSerializer

    @extend_schema(
        request=CreateMatchSerializer,
        responses={201: MatchSerializer}

    )
    def create(self, request, *args, **kwargs):
        return create_match(request)

    @action(detail=True, methods=["POST"])
    def load(self, request, pk=None):
        return load_match(pk)

    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def webhook(self, request):
        return process_webhook(request)

    @extend_schema(
        request=MatchBanMapSerializer,
        responses={200: MatchBanMapResultSerializer}
    )
    @action(detail=True, methods=["POST"])
    def ban(self, request, pk):
        return ban_map(request, pk)

    @extend_schema(
        request=MatchPickMapSerializer,
        responses={200: MatchPickMapResultSerializer}
    )
    @action(detail=True, methods=["POST"])
    def pick(self, request, pk):
        return pick_map(request, pk)

    @action(detail=True, methods=["POST"])
    def recreate(self, request, pk):
        return recreate_match(request, pk)

    @action(detail=True, methods=["POST"])
    def shuffle(self, request, pk):
        return shuffle_teams(request, pk)

    @extend_schema(
        responses={200: MapBanSerializer}
    )
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

    @extend_schema(
        responses={200: MatchMapSelectedSerializer}
    )
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

    @extend_schema(
        request=MatchPlayerJoin,
        responses={200: MatchSerializer}
    )
    @action(detail=True, methods=["POST"])
    def join(self, request, pk):
        return join_match(request, pk)

    @extend_schema(
        responses={200: MatchConfigSerializer}
    )
    @action(detail=True, methods=["GET"], permission_classes=[IsAuthor], authentication_classes=[BearerTokenAuthentication])
    def config(self, request, pk):
        match = self.get_object()
        serializer = MatchConfigSerializer(data=match.get_config())
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        return Response(serializer.data, status=200)


class MapViewSet(viewsets.ModelViewSet):
    queryset = Map.objects.all().order_by("created_at")
    serializer_class = MapSerializer
