from django.contrib import admin

from shop import models

admin.site.register(models.Category)
admin.site.register(models.Client)
admin.site.register(models.Dispatch)
admin.site.register(models.User)


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    readonly_fields = ('image_tg_id',)
