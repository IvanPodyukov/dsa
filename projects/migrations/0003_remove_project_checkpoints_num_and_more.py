# Generated by Django 5.0.2 on 2024-04-02 08:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0003_alter_application_vacancy'),
        ('projects', '0002_alter_project_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='checkpoints_num',
        ),
        migrations.RemoveField(
            model_name='project',
            name='participants_num',
        ),
        migrations.DeleteModel(
            name='Participant',
        ),
    ]