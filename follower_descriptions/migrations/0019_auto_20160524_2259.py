# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-05-24 22:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('follower_descriptions', '0018_merge'),
    ]

    operations = [
        migrations.RenameField(
            model_name='buzzwords',
            old_name='hits',
            new_name='count',
        ),
    ]