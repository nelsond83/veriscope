import uuid
from datetime import date
from django.db import models
from django.contrib.auth.models import User


class MonitoringBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=200, blank=True)
    run_date = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-run_date', '-created_at']

    def __str__(self):
        return self.label or str(self.run_date)


class CreditReport(models.Model):
    BUREAU_CHOICES = [
        ('equifax', 'Equifax'),
        ('experian', 'Experian'),
        ('transunion', 'TransUnion'),
        ('unknown', 'Unknown'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('parsing', 'Parsing'),
        ('parsed', 'Parsed'),
        ('failed', 'Failed'),
    ]
    CONFIDENCE_CHOICES = [
        ('ssn', 'SSN Match'),
        ('ssn_last4_name', 'SSN Last-4 + Name'),
        ('name_dob', 'Name + DOB'),
        ('manual', 'Manual'),
        ('', 'Unmatched'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='reports/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    bureau = models.CharField(max_length=20, choices=BUREAU_CHOICES, default='unknown')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    identity = models.ForeignKey(
        'identities.Identity', on_delete=models.SET_NULL,
        related_name='reports', null=True, blank=True,
    )
    batch = models.ForeignKey(
        MonitoringBatch, on_delete=models.SET_NULL,
        related_name='reports', null=True, blank=True,
    )
    match_confidence = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    raw_text = models.TextField(blank=True)
    page_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.original_filename} ({self.get_bureau_display()}) — {self.get_status_display()}'
