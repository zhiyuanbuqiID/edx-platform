# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FacebookMotivationalPostConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('user_id', models.PositiveIntegerField()),
                ('course_run_id', models.CharField(max_length=255)),
                ('target_end_date', models.DateTimeField()),
                ('fb_user_id', models.CharField(max_length=255)),
                ('fb_access_token', models.CharField(max_length=255)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='facebookmotivationalpostconfig',
            unique_together=set([('course_run_id', 'user_id')]),
        ),
    ]
