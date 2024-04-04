from rest_framework import viewsets
from servers.models import Server
from servers.serializers import ServerSerializer

class ServerViewSet(viewsets.ModelViewSet):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
        

