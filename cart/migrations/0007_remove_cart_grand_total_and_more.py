# Generated by Django 5.1.1 on 2024-11-08 13:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0006_cart_subtotal_after_discount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='grand_total',
        ),
        migrations.RemoveField(
            model_name='cart',
            name='subtotal_after_discount',
        ),
    ]
