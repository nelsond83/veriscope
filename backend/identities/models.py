import random
import uuid
from django.db import models
from django.contrib.auth.models import User


class Identity(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_id = models.CharField(max_length=5, unique=True, blank=True, db_index=True)
    full_name = models.CharField(max_length=255)
    ssn = models.CharField(max_length=11, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    FICO_RANGE_CHOICES = [
        ('800-850', '800-850 (Exceptional)'),
        ('740-799', '740-799 (Very Good)'),
        ('670-739', '670-739 (Good)'),
        ('580-669', '580-669 (Fair)'),
        ('300-579', '300-579 (Poor)'),
    ]
    notes = models.TextField(blank=True)
    expected_fico_range = models.CharField(max_length=10, blank=True, choices=FICO_RANGE_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='identities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']
        verbose_name_plural = 'Identities'

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.entity_id:
            for _ in range(100):
                eid = str(random.randint(10000, 99999))
                if not Identity.objects.filter(entity_id=eid).exists():
                    self.entity_id = eid
                    break
            else:
                self.entity_id = str(random.randint(10000, 99999))
        super().save(*args, **kwargs)

    @property
    def dd_status(self):
        results = self.comparisons.all()
        if not results.exists():
            return 'pending'
        statuses = set(results.values_list('match_status', flat=True))
        if 'mismatch' in statuses:
            return 'flagged'
        if 'partial' in statuses:
            return 'review'
        return 'clear'


class IdentityAddress(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('current', 'Current'),
        ('previous', 'Previous'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default='current')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.street}, {self.city}, {self.state} {self.zip_code}'.strip(', ')


class IdentityNameVariation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name='name_variations')
    name = models.CharField(max_length=255)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class IdentityPhone(models.Model):
    PHONE_TYPE_CHOICES = [
        ('mobile', 'Mobile'),
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name='phones')
    number = models.CharField(max_length=20)
    phone_type = models.CharField(max_length=20, choices=PHONE_TYPE_CHOICES, default='mobile')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.number



class IdentityAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name='ref_accounts')
    creditor_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=50, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=50, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    highest_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date_opened = models.DateField(null=True, blank=True)
    account_address = models.CharField(max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.creditor_name} {self.account_number}'


class DDRun(models.Model):
    """Archived snapshot of a completed DD — preserved when the user clears active results."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name='dd_runs')
    created_at = models.DateTimeField(auto_now_add=True)
    results_snapshot = models.JSONField(default=list)
    corrections_snapshot = models.JSONField(default=list)
    reports = models.ManyToManyField('reports.CreditReport', blank=True, related_name='dd_runs')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'DD Run {self.created_at:%Y-%m-%d} — {self.identity}'

    @property
    def dd_status(self):
        statuses = {r['match_status'] for r in self.results_snapshot}
        if 'mismatch' in statuses:
            return 'flagged'
        if 'partial' in statuses:
            return 'review'
        if statuses:
            return 'clear'
        return 'pending'


class Correction(models.Model):
    """Editable correction line for a specific bureau, shown/edited on the identity detail page
    and included in the per-bureau corrections export. Seeded from ComparisonResult issues but
    independently editable, addable, and deletable by the user."""
    BUREAU_CHOICES = [
        ('equifax', 'Equifax'),
        ('experian', 'Experian'),
        ('transunion', 'TransUnion'),
    ]
    SOURCE_CHOICES = [
        ('auto', 'Auto-detected'),
        ('manual', 'Manual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name='corrections')
    bureau = models.CharField(max_length=20, choices=BUREAU_CHOICES)
    note = models.CharField(max_length=500, blank=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='auto')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['bureau', '-created_at']

    def __str__(self):
        return f'Correction for {self.identity} [{self.bureau}]'


class ComparisonResult(models.Model):
    MATCH_STATUS_CHOICES = [
        ('match', 'Match'),
        ('mismatch', 'Mismatch'),
        ('partial', 'Partial Match'),
        ('missing', 'Missing'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name='comparisons')
    report = models.ForeignKey('reports.CreditReport', on_delete=models.CASCADE, related_name='comparisons')
    field_name = models.CharField(max_length=100)
    identity_value = models.CharField(max_length=500, blank=True)
    report_value = models.CharField(max_length=500, blank=True)
    match_status = models.CharField(max_length=20, choices=MATCH_STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['field_name']
        unique_together = [('identity', 'report', 'field_name')]

    def __str__(self):
        return f'{self.field_name}: {self.match_status}'
