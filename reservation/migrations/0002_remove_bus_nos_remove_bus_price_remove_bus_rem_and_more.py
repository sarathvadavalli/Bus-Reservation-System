# Generated by Django 5.0.2 on 2024-04-05 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservation', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bus',
            name='nos',
        ),
        migrations.RemoveField(
            model_name='bus',
            name='price',
        ),
        migrations.RemoveField(
            model_name='bus',
            name='rem',
        ),
        migrations.AddField(
            model_name='bus',
            name='capacity',
            field=models.IntegerField(default=30),
        ),
    ]
