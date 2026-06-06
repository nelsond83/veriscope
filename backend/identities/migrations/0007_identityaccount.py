import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('identities', '0006_gender_full_string'),
    ]

    operations = [
        migrations.CreateModel(
            name='IdentityAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('creditor_name', models.CharField(max_length=255)),
                ('account_type', models.CharField(blank=True, max_length=50)),
                ('account_number', models.CharField(blank=True, max_length=20)),
                ('status', models.CharField(blank=True, max_length=50)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('identity', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ref_accounts',
                    to='identities.identity',
                )),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
