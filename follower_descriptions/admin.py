from django.contrib import admin
from . import models

admin.site.register(models.University)
admin.site.register(models.Graduate)
admin.site.register(models.Comment)
admin.site.register(models.Feedback)
admin.site.register(models.TaskStats)
admin.site.register(models.CeleryTasksRetrying)

