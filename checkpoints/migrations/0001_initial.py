# Generated by Django 5.0.2 on 2024-03-03 14:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0002_delete_checkpoint'),
    ]

    operations = [
        migrations.CreateModel(
            name='Checkpoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=30)),
                ('description', models.CharField(max_length=100)),
                ('deadline', models.DateField()),
                ('custom_id', models.IntegerField(null=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkpoints', to='projects.project')),
            ],
            options={
                'ordering': ['custom_id'],
            },
        ),
    ]
