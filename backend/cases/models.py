import uuid
from django.db import models
from django.contrib.auth.models import User


class Case(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_review', 'In Review'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cases')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ReferenceData(models.Model):
    SOURCE_CHOICES = [
        ('api', 'API'),
        ('csv', 'CSV Upload'),
        ('manual', 'Manual Entry'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='reference_data')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    label = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255, blank=True)
    ssn = models.CharField(max_length=11, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    raw_data = models.JSONField(default=dict)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name_plural = 'Reference Data'

    def __str__(self):
        return f'{self.label} ({self.case.name})'


class ComparisonResult(models.Model):
    MATCH_STATUS_CHOICES = [
        ('match', 'Match'),
        ('mismatch', 'Mismatch'),
        ('partial', 'Partial Match'),
        ('missing', 'Missing'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='comparisons')
    report = models.ForeignKey('reports.CreditReport', on_delete=models.CASCADE, related_name='comparisons')
    reference = models.ForeignKey(ReferenceData, on_delete=models.CASCADE, related_name='comparisons')
    field_name = models.CharField(max_length=100)
    report_value = models.CharField(max_length=500, blank=True)
    reference_value = models.CharField(max_length=500, blank=True)
    match_status = models.CharField(max_length=20, choices=MATCH_STATUS_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['field_name']

    def __str__(self):
        return f'{self.field_name}: {self.match_status}'
