# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-12 12:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('follower_descriptions', '0007_auto_20160312_1227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='university',
            name='name',
            field=models.CharField(max_length=1024, null=True),
        ),
    ]