# Generated by Django 5.0.11 on 2025-05-09 19:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HR', '0017_role_managertype'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newrolerequest',
            name='RoleTypeCode',
        ),
        migrations.AddField(
            model_name='newrolerequest',
            name='RoleType',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='HR.constvalue', verbose_name='کد نوع سمت'),
        ),
        migrations.AlterField(
            model_name='newrolerequest',
            name='ManagerType',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='HR.constvalue', verbose_name='مدیر مربوطه'),
        ),
    ]
