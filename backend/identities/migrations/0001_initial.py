import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Identity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('entity_id', models.CharField(blank=True, db_index=True, max_length=5, unique=True)),
                ('full_name', models.CharField(max_length=255)),
                ('ssn', models.CharField(blank=True, max_length=11)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('gender', models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('unknown', 'Unknown')], max_length=10)),
                ('notes', models.TextField(blank=True)),
                ('expected_fico_range', models.CharField(blank=True, choices=[('800-850', '800-850 (Exceptional)'), ('740-799', '740-799 (Very Good)'), ('670-739', '670-739 (Good)'), ('580-669', '580-669 (Fair)'), ('300-579', '300-579 (Poor)')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='identities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Identities',
                'ordering': ['full_name'],
            },
        ),
        migrations.CreateModel(
            name='IdentityAddress',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('street', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=50)),
                ('zip_code', models.CharField(blank=True, max_length=10)),
                ('address_type', models.CharField(choices=[('current', 'Current'), ('previous', 'Previous'), ('other', 'Other')], default='current', max_length=20)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('identity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='identities.identity')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='IdentityNameVariation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('note', models.CharField(blank=True, max_length=200)),
                ('identity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='name_variations', to='identities.identity')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='IdentityPhone',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('number', models.CharField(max_length=20)),
                ('phone_type', models.CharField(choices=[('mobile', 'Mobile'), ('home', 'Home'), ('work', 'Work'), ('other', 'Other')], default='mobile', max_length=20)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('identity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phones', to='identities.identity')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='IdentityAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('creditor_name', models.CharField(max_length=255)),
                ('account_type', models.CharField(blank=True, max_length=50)),
                ('account_number', models.CharField(blank=True, max_length=20)),
                ('status', models.CharField(blank=True, max_length=50)),
                ('balance', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('credit_limit', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('highest_balance', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('monthly_payment', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('date_opened', models.DateField(blank=True, null=True)),
                ('account_address', models.CharField(blank=True, max_length=255)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('identity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ref_accounts', to='identities.identity')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='DDRun',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('results_snapshot', models.JSONField(default=list)),
                ('corrections_snapshot', models.JSONField(default=list)),
                ('identity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dd_runs', to='identities.identity')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Correction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('bureau', models.CharField(choices=[('equifax', 'Equifax'), ('experian', 'Experian'), ('transunion', 'TransUnion')], max_length=20)),
                ('note', models.CharField(blank=True, max_length=500)),
                ('source', models.CharField(choices=[('auto', 'Auto-detected'), ('manual', 'Manual')], default='auto', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='corrections', to='identities.identity')),
            ],
            options={
                'ordering': ['bureau', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ComparisonResult',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('field_name', models.CharField(max_length=100)),
                ('identity_value', models.CharField(blank=True, max_length=500)),
                ('report_value', models.CharField(blank=True, max_length=500)),
                ('match_status', models.CharField(choices=[('match', 'Match'), ('mismatch', 'Mismatch'), ('partial', 'Partial Match'), ('missing', 'Missing')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('identity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comparisons', to='identities.identity')),
            ],
            options={
                'ordering': ['field_name'],
            },
        ),
    ]
