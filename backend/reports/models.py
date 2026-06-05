import uuid
from django.db import models


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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='reports/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    bureau = models.CharField(max_length=20, choices=BUREAU_CHOICES, default='unknown')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    case = models.ForeignKey(
        'cases.Case', on_delete=models.CASCADE,
        related_name='reports', null=True, blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    raw_text = models.TextField(blank=True)
    page_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.original_filename} ({self.get_bureau_display()}) — {self.get_status_display()}'
