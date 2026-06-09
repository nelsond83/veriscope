import uuid
from django.db import models


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.OneToOneField(
        'reports.CreditReport', on_delete=models.CASCADE, related_name='subject'
    )
    full_name = models.CharField(max_length=255, blank=True)
    ssn = models.CharField(max_length=15, blank=True)
    ssn_last_four = models.CharField(max_length=4, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    in_file_since = models.DateField(null=True, blank=True)
    credit_score = models.PositiveIntegerField(null=True, blank=True)
    score_type = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name or f'Subject ({self.report.original_filename})'


class AlternateName(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='alternate_names')
    name = models.CharField(max_length=255)
    name_type = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class Address(models.Model):
    TYPE_CHOICES = [
        ('current', 'Current'),
        ('previous', 'Previous'),
        ('unknown', 'Unknown'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    address_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='unknown')
    reported_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f'{self.street}, {self.city}, {self.state} {self.zip_code}'.strip(', ')


class FinancialAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('auto_loan', 'Auto Loan'),
        ('mortgage', 'Mortgage'),
        ('student_loan', 'Student Loan'),
        ('personal_loan', 'Personal Loan'),
        ('collection', 'Collection'),
        ('medical', 'Medical'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('derogatory', 'Derogatory'),
        ('collection', 'In Collections'),
        ('charged_off', 'Charged Off'),
        ('unknown', 'Unknown'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='financial_accounts')
    creditor_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=100, blank=True)
    account_type = models.CharField(max_length=30, choices=ACCOUNT_TYPE_CHOICES, default='other')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown')
    balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    highest_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    account_address = models.CharField(max_length=255, blank=True)
    date_opened = models.DateField(null=True, blank=True)
    date_closed = models.DateField(null=True, blank=True)
    payment_status = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.creditor_name} — {self.get_account_type_display()}'
