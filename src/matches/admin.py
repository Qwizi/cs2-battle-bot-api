from django.contrib import admin

from matches.models import Map, Match, MapBan

# Register your models here.
admin.site.register(Match)
admin.site.register(Map)
admin.site.register(MapBan)
