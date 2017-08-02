# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-31 19:20
from __future__ import unicode_literals

from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations

from accounts.models import Organization


def create_mit_organization(apps, schema_editor, *args, **kwargs):
    db_alias = schema_editor.connection.alias
    # this creates the permissions prior to the post_save signals
    # on organization trying to use them
    emit_post_migrate_signal(2, False, db_alias)
    Organization.objects.create(
        name='MIT',
        url='https://lookit.mit.edu'
    )


def remove_mit_organization(*args, **kwargs):
    Organization.objects.filter(name='MIT').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '__latest__'),
        ('sites', '__latest__'),
        ('accounts', '0015_user_is_researcher'),
    ]

    operations = [
        migrations.RunPython(create_mit_organization, remove_mit_organization)
    ]