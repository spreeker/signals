# Generated by Django 2.1.2 on 2018-10-23 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0024_subcategory_set_is_active_to_true'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subcategory',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
