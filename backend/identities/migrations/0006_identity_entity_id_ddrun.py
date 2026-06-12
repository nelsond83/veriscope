import random
import uuid
import django.db.models.deletion
from django.db import migrations, models


def assign_entity_ids(apps, schema_editor):
    Identity = apps.get_model('identities', 'Identity')
    used = set(Identity.objects.exclude(entity_id='').values_list('entity_id', flat=True))
    for identity in Identity.objects.filter(entity_id=''):
        for _ in range(200):
            eid = str(random.randint(10000, 99999))
            if eid not in used:
                used.add(eid)
                identity.entity_id = eid
                identity.save(update_fields=['entity_id'])
                break


class Migration(migrations.Migration):

    dependencies = [
        ('identities', '0005_remove_identityemail'),
        ('reports', '0001_initial'),
    ]

    operations = [
        # Step 1: add field without unique constraint so existing rows can have default ''
        migrations.AddField(
            model_name='identity',
            name='entity_id',
            field=models.CharField(blank=True, max_length=5, default=''),
            preserve_default=False,
        ),
        # Step 2: populate entity_id for all existing rows
        migrations.RunPython(assign_entity_ids, migrations.RunPython.noop),
        # Step 3: now safe to add unique + index
        migrations.AlterField(
            model_name='identity',
            name='entity_id',
            field=models.CharField(blank=True, db_index=True, max_length=5, unique=True),
        ),
        # Step 4: DDRun model
        migrations.CreateModel(
            name='DDRun',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('results_snapshot', models.JSONField(default=list)),
                ('identity', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dd_runs',
                    to='identities.identity',
                )),
                ('reports', models.ManyToManyField(
                    blank=True,
                    related_name='dd_runs',
                    to='reports.creditreport',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
