from django.apps import AppConfig
import os
import sys
from django.conf import settings

class ExperimentConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'experiment'

    def ready(self):
        # Only run in the main process, not in management commands, migrations, etc.
        # The process lock in views.py will prevent multiple instances
        if 'runserver' in ' '.join(sys.argv):
            from .views import start_inactive_user_checker
            start_inactive_user_checker()
