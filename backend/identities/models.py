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
    full_name = models.CharField(max_length=255)
    ssn = models.CharField(max_length=11, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='identities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']
        verbose_name_plural = 'Identities'

    def __str__(self):
        return self.full_name

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


class IdentityEmail(models.Model):
    EMAIL_TYPE_CHOICES = [
        ('personal', 'Personal'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name='emails')
    address = models.CharField(max_length=254)
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPE_CHOICES, default='personal')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.address


class IdentityAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name='ref_accounts')
    creditor_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=50, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=50, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.creditor_name} {self.account_number}'


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
