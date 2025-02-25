from django.contrib import admin
from .models import Subject, Group, MessageRecord

# Register your models here.
admin.site.register(Subject)
admin.site.register(Group)
admin.site.register(MessageRecord)
