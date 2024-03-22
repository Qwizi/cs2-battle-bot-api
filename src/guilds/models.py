from django.db import models
from prefix_id import PrefixIDField
from rest_framework_api_key.models import AbstractAPIKey

# Create your models here.


class Guild(models.Model):
    id = PrefixIDField(primary_key=True, prefix="guild")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
