import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('identities', '0006_identity_entity_id_ddrun'),
    ]

    operations = [
        migrations.AddField(
            model_name='ddrun',
            name='corrections_snapshot',
            field=models.JSONField(default=list),
        ),
        migrations.CreateModel(
            name='Correction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('bureau', models.CharField(choices=[('equifax', 'Equifax'), ('experian', 'Experian'), ('transunion', 'TransUnion')], max_length=20)),
                ('field', models.CharField(max_length=100)),
                ('report_value', models.CharField(blank=True, max_length=500)),
                ('correct_value', models.CharField(blank=True, max_length=500)),
                ('issue_type', models.CharField(choices=[('mismatch', 'Mismatch'), ('missing', 'Missing from Report'), ('partial', 'Partial Match'), ('not_on_file', 'Not on File'), ('other', 'Other')], default='other', max_length=20)),
                ('source', models.CharField(choices=[('auto', 'Auto-detected'), ('manual', 'Manual')], default='auto', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identity', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='corrections',
                    to='identities.identity',
                )),
            ],
            options={
                'ordering': ['bureau', 'field'],
            },
        ),
    ]
