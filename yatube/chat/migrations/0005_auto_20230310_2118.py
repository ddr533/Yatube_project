# Generated by Django 3.0 on 2023-03-10 14:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_auto_20230310_1628'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ('-date_added',)},
        ),
    ]
