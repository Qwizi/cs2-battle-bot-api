from django.http import HttpResponsePermanentRedirect
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from servers.models import Server
from servers.serializers import ServerSerializer


class CustomSchemeRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = ["steam"]


class ServerViewSet(viewsets.ModelViewSet):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer

    @action(detail=True, methods=["GET"], permission_classes=[AllowAny])
    def join(self, request, pk=None):
        server = self.get_object()
        return CustomSchemeRedirect(server.get_join_link())
