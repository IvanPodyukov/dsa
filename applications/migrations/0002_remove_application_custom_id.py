# Generated by Django 5.0.2 on 2024-04-02 08:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='application',
            name='custom_id',
        ),
    ]