from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

class University(models.Model):
    uni_handle = models.CharField(max_length = 32, primary_key=True)
    last_refresh = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length = 1024, blank=True, null=True)

    def __str__(self):
        return self.uni_handle + ': ' + self.name

class Graduate(models.Model):
    id = models.BigIntegerField(primary_key=True)
    twitter_handle = models.CharField(max_length=128, default='')
    last_refresh = models.DateTimeField()
    description = models.CharField(max_length = 4096, default='')
    name = models.CharField(max_length = 128, default='')
    following = models.ManyToManyField(University)

    def __str__(self):
        return self.name


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, related_name="user")
    graduate = models.ForeignKey(Graduate)
    description = models.CharField(max_length=4096, default='')
    date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.description

class Feedback(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(User)
    description = models.CharField(max_length=4096, default='')


    def __str__(self):
        return self.description




# Defunct - remove at some point
class UniFollowers(models.Model):
    university = models.ForeignKey(University)
    graduate = models.ForeignKey(Graduate)

    def __str__(self):
        return self.university.uni_handle
