import uuid
from django.db import models


class DocumentTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    keywords = models.JSONField(default=list, blank=True)
    sample_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TemplateField(models.Model):
    FIELD_CHOICES = [
        ('full_name', 'Full Name'),
        ('ssn', 'SSN / Tax ID'),
        ('date_of_birth', 'Date of Birth'),
        ('address', 'Address'),
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('employer', 'Employer'),
        ('account_number', 'Account Number'),
        ('custom', 'Custom Field'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE, related_name='fields')
    field_name = models.CharField(max_length=50, choices=FIELD_CHOICES)
    custom_label = models.CharField(max_length=50, blank=True)
    regex_pattern = models.TextField()
    capture_group = models.PositiveSmallIntegerField(default=1)
    case_insensitive = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'field_name']

    def __str__(self):
        label = self.custom_label if self.field_name == 'custom' else self.field_name
        return f'{self.template.name} — {label}'
