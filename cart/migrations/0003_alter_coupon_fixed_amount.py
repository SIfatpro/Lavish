# Generated by Django 5.1.1 on 2024-11-03 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0002_alter_coupon_fixed_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='fixed_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]