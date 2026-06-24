from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('identities', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='correction',
            name='source',
        ),
    ]
