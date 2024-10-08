# Generated by Django 5.0.2 on 2024-04-08 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservation', '0008_bus_unique_migration_host_combination'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='bus',
            name='unique_migration_host_combination',
        ),
        migrations.AddConstraint(
            model_name='bus',
            constraint=models.UniqueConstraint(fields=('bus_name', 'date', 'time'), name='unique_bus_combination'),
        ),
    ]
