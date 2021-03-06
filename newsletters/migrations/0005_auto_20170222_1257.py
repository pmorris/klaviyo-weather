# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-22 17:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('newsletters', '0004_auto_20170220_2318'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subscriberlocation',
            old_name='name',
            new_name='city',
        ),
        migrations.AddField(
            model_name='subscriberlocation',
            name='country',
            field=models.TextField(default='US', max_length=2),
        ),
        migrations.AddField(
            model_name='subscriberlocation',
            name='population',
            field=models.PositiveIntegerField(null=True, verbose_name='Last Known Population'),
        ),
        migrations.AddField(
            model_name='subscriberlocation',
            name='population_estimate',
            field=models.PositiveIntegerField(null=True, verbose_name='Estimated Population'),
        ),
        migrations.AddField(
            model_name='subscriberlocation',
            name='state_abv',
            field=models.TextField(default=django.utils.timezone.now, max_length=15),
            preserve_default=False,
        ),
    ]
