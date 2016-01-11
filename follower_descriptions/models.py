from __future__ import unicode_literals

from django.db import models

class University(models.Model):
    uni_handle = models.CharField(max_length = 32, primary_key=True)
    last_refresh = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.uni_handle

class Graduate(models.Model):
    id = models.BigIntegerField(primary_key=True)
    last_refresh = models.DateTimeField()
    description = models.CharField(max_length = 4096, default='')
    name = models.CharField(max_length = 128, default='')

    def __str__(self):
        return self.name

class UniFollowers(models.Model):
    university = models.ForeignKey(University)
    graduate = models.ForeignKey(Graduate)

