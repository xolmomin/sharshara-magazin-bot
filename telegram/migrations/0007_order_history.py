# Generated by Django 3.0.4 on 2020-04-03 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram', '0006_tguser_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='history',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
    ]