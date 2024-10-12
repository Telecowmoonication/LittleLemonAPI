# Generated by Django 5.0.6 on 2024-09-14 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0010_rename_price_menuitem_unit_price_remove_order_total_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='logger',
            name='time_log',
        ),
        migrations.AddField(
            model_name='logger',
            name='end_time',
            field=models.TimeField(blank=True, help_text='Enter the end time (Logout time).', null=True),
        ),
        migrations.AddField(
            model_name='logger',
            name='start_time',
            field=models.TimeField(blank=True, help_text='Enter the start time (Login time).', null=True),
        ),
    ]
