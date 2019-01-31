# Generated by Django 2.1.5 on 2019-01-31 09:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0029_auto_20190109_1415'),
    ]

    operations = [
        migrations.AddField(
            model_name='subcategory',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='signals.SubCategory'),
        ),
        migrations.AlterField(
            model_name='subcategory',
            name='departments',
            field=models.ManyToManyField(null=True, to='signals.Department'),
        ),
        migrations.AlterField(
            model_name='subcategory',
            name='handling',
            field=models.CharField(blank=True, choices=[('A3DMC', 'A3DMC'), ('A3DEC', 'A3DEC'), ('A3WMC', 'A3WMC'), ('A3WEC', 'A3WEC'), ('I5DMC', 'I5DMC'), ('STOPEC', 'STOPEC'), ('KLOKLICHTZC', 'KLOKLICHTZC'), ('GLADZC', 'GLADZC'), ('A3DEVOMC', 'A3DEVOMC'), ('WS1EC', 'WS1EC'), ('WS2EC', 'WS2EC'), ('REST', 'REST')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='subcategory',
            name='main_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='sub_categories', to='signals.MainCategory'),
        ),
    ]
