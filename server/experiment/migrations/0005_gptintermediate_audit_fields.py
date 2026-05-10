from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0004_message_validation_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='gptintermediate',
            name='model',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='gptintermediate',
            name='prompt_version',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='gptintermediate',
            name='system_prompt',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gptintermediate',
            name='input_message_set',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AddField(
            model_name='gptintermediate',
            name='raw_response',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gptintermediate',
            name='parsed_response',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AddField(
            model_name='gptintermediate',
            name='retry_count',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='gptintermediate',
            name='error_metadata',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
