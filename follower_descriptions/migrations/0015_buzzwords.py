# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-05-24 21:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('follower_descriptions', '0014_auto_20160418_1256'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuzzWords',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buzz_word', models.CharField(default='', max_length=128)),
            ],
        ),
    ]
