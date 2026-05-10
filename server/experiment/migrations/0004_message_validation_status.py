from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0003_auto_20250801_1335'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagerecord',
            name='is_valid',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='messagerecord',
            name='validation_status',
            field=models.CharField(default='valid', max_length=20),
        ),
        migrations.AddField(
            model_name='messagerecord',
            name='meaningful_word_count',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='messagerecord',
            name='validation_error',
            field=models.TextField(blank=True, default=''),
        ),
    ]
