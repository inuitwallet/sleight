# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-21 13:08
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Balance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=10, max_digits=20)),
            ],
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=10, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='CurrencyPair',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='base_currency', to='sleight.Currency')),
                ('relative_currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relative_currency', to='sleight.Currency')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_amount', models.DecimalField(decimal_places=10, max_digits=20)),
                ('amount', models.DecimalField(decimal_places=10, max_digits=20)),
                ('price', models.DecimalField(decimal_places=10, max_digits=20)),
                ('order_type', models.CharField(choices=[('bid', 'Bid'), ('ask', 'Ask')], max_length=3)),
                ('state', models.CharField(choices=[('open', 'Open'), ('partial', 'Partial'), ('complete', 'Complete'), ('cancelled', 'Cancelled')], max_length=7)),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('pair', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order', to='sleight.CurrencyPair')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_key', models.UUIDField(default=uuid.uuid4)),
                ('api_secret', models.UUIDField(default=uuid.uuid4)),
                ('nonce', models.IntegerField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Trade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('amount', models.DecimalField(decimal_places=10, max_digits=20)),
                ('partial', models.BooleanField()),
                ('existing_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='existing_order', to='sleight.Order')),
                ('initiating_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='initiating_order', to='sleight.Order')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='currency',
            unique_together=set([('name', 'code')]),
        ),
        migrations.AddField(
            model_name='balance',
            name='currency',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sleight.Currency'),
        ),
        migrations.AddField(
            model_name='balance',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='currencypair',
            unique_together=set([('base_currency', 'relative_currency')]),
        ),
    ]
