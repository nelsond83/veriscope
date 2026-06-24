import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
        ('identities', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='comparisonresult',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comparisons', to='reports.creditreport'),
        ),
        migrations.AddField(
            model_name='ddrun',
            name='reports',
            field=models.ManyToManyField(blank=True, related_name='dd_runs', to='reports.creditreport'),
        ),
        migrations.AlterUniqueTogether(
            name='comparisonresult',
            unique_together={('identity', 'report', 'field_name')},
        ),
    ]
