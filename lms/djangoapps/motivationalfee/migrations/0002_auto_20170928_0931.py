# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motivationalfee', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facebookmotivationalpostconfig',
            name='target_end_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
