from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'Deletes all entries from all models in the database'

    def handle(self, *args, **kwargs):
        for model in apps.get_models():
            model.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all database entries'))
