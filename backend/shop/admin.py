from django.contrib import admin

from shop import models

admin.site.register(models.Client)
admin.site.register(models.Category)
admin.site.register(models.Product)
admin.site.register(models.User)
