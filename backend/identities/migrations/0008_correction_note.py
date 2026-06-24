from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('identities', '0007_correction_ddrun_corrections_snapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='correction',
            name='note',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.RemoveField(
            model_name='correction',
            name='field',
        ),
        migrations.RemoveField(
            model_name='correction',
            name='report_value',
        ),
        migrations.RemoveField(
            model_name='correction',
            name='correct_value',
        ),
        migrations.RemoveField(
            model_name='correction',
            name='issue_type',
        ),
        migrations.AlterModelOptions(
            name='correction',
            options={'ordering': ['bureau', '-created_at']},
        ),
    ]
