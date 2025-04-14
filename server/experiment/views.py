from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .models import Group, PostDOSurvey, Subject, MessageRecord, PostDFSurvey, PreDSurvey, DemograSurvey
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from random import sample
import random
import json as JSON
from decimal import *
from django.conf import settings
from django.db.models import F, Count
from django.utils import timezone
from django.db import transaction

# Create your views here.
def home_view(request,*args, **kwargs):
	return HttpResponse("<h1>Hello World</h1>")


from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
import random
from random import sample
from .models import Subject

@api_view(['POST'])
def create_subject(request):
    worker_id = request.POST.get('worker_id', None)
    study_id = request.POST.get('study_id', None)
    session_id = request.POST.get('session_id', None)

    if worker_id is not None:
        if not Subject.objects.filter(worker_id=worker_id).exists():
            # Normal subject creation
            # participant_number_condition = random.choices([0, 1], weights=[3, 1])[0]
            # selected_indices = sample(range(12), 6)

            sub = Subject.objects.create(
                worker_id=worker_id,
                study_id=study_id,
                session_id=session_id,
                # participant_number_condition=participant_number_condition
            )

            return JsonResponse({
                "subject_id": sub._id,
                "success": True,
                # "participant_number_condition": sub.participant_number_condition
            })
        else:
            return JsonResponse({
                "success": False,
                "message": "Worker ID already exists"
            })

    raise PermissionDenied("Worker ID is missing")

@api_view(['POST'])
def updateDemograSurvey(request):
	json = {}
	subject_id = request.POST.get('subject_id', None)
	age_range = request.POST.get('ageRange', None)
	gender_selection = request.POST.get('genderSelection', None)
	income_range = request.POST.get('incomeRange', None)
	education_level = request.POST.get('educationLevel', None)
	ethnicity_selection = request.POST.get('ethnicitySelection', None)
	religion_affiliation = request.POST.get('religionAffiliation', None)
	political_affiliation = request.POST.get('politicalAffiliation', None)
	immigration_status = request.POST.get('immigrationStatus', None)
	social_media_reading_frequency = request.POST.get('socialMediaReadingFrequency', None)
	social_media_posting_frequency = request.POST.get('socialMediaPostingFrequency', None)
	social_media_reading_platforms = request.POST.get('socialMediaReadingPlatforms', None)
	social_media_posting_platforms = request.POST.get('socialMediaPostingPlatforms', None)
	ai_tool_usage_frequency = request.POST.get('aiToolUsageFrequency', None)
	ai_attitude_selection = request.POST.get('aiAttitudeSelection', None)
	ai_in_music = request.POST.get('aiInMusic', None)  # Expecting JSON string for checkboxes
	ai_in_email = request.POST.get('aiInEmail', None)  # Expecting JSON string for checkboxes
	ai_in_home_devices = request.POST.get('aiInHomeDevices', None)  # Expecting JSON string for checkboxes
	ai_mental_capacity_responses = request.POST.get('aiMentalCapacityResponses', None)  # Expecting JSON string

	if subject_id != None:
		try:
			survey = DemograSurvey.objects.create(
				subject_id=subject_id,
				age_range=age_range,
				gender_selection=gender_selection,
				income_range=income_range,
				education_level=education_level,
				ethnicity_selection=ethnicity_selection,
				religion_affiliation=religion_affiliation,
				political_affiliation=political_affiliation,
				immigration_status=immigration_status,
				social_media_reading_frequency=social_media_reading_frequency,
				social_media_posting_frequency=social_media_posting_frequency,
				social_media_reading_platforms=JSON.loads(social_media_reading_platforms) if social_media_reading_platforms else [],
				social_media_posting_platforms=JSON.loads(social_media_posting_platforms) if social_media_posting_platforms else [],
				ai_tool_usage_frequency=ai_tool_usage_frequency,
				ai_attitude_selection=ai_attitude_selection,
				ai_in_music=ai_in_music,
				ai_in_email=ai_in_email,
				ai_in_home_devices=ai_in_home_devices,
				ai_mental_capacity_responses=ai_mental_capacity_responses
			)

			# Indicate successful creation in the JSON response
			json['success'] = True
			json['message'] = 'Survey saved successfully'
			return JsonResponse(json)
		except Exception as e:
			json['success'] = False
			json['message'] = str(e)
			return JsonResponse(json)
	else:
		# Handle the case where subject_id is missing
		json['success'] = False
		json['message'] = 'Missing subject_id'
		return JsonResponse(json)



@api_view(['POST'])
def heartbeat(request):
    """Updates the last active time of a subject and checks for inactive users"""
    subject_id = request.data.get('subject_id')

    try:
        subject = Subject.objects.get(pk=subject_id)
        subject.last_active_time = timezone.now()  # Update last active time
        subject.save()

        no_heartbeat_subjects()  # Identify inactive users

        return JsonResponse({'status': 'ok'})
    except Subject.DoesNotExist:
        return JsonResponse({'error': 'Subject not found'}, status=404)
    

def no_heartbeat_subjects():
    """Marks users as inactive if they haven't sent a heartbeat within 30 seconds."""
    time_threshold = timezone.now() - timedelta(seconds=30)  # 30 sec inactivity

    # Find inactive users
    inactive_users = Subject.objects.filter(last_active_time__lt=time_threshold, active=True)

    for user in inactive_users:
        user.active = False  # Mark user as inactive
        user.save()
    
    return inactive_users  # Return list of inactive users for further processing


@api_view(['POST'])
def terminate_participation(request):
    subject_id = request.POST.get('subject_id')
    try:
        subject = Subject.objects.get(pk=subject_id)
        subject.active = False
        subject.save()

        return JsonResponse({'status': 'ok'})
    except Subject.DoesNotExist:
        return JsonResponse({'error': 'Subject not found'}, status=404)


@api_view(['POST'])
def Update_pre_discussion_survey(request):
    json = {}
    data = request.data
    subject_id = data.get('subject_id', None)
    responses = data.get('responses', [])

    if subject_id is not None:
        try:
            # Create survey record
            survey = PreDSurvey.objects.create(
                subject_id=subject_id,
                responses=responses
            )

            json['success'] = True
            json['message'] = 'Survey saved successfully'
        except Exception as e:
            json['success'] = False
            json['message'] = f'Error saving survey: {str(e)}'
    else:
        json['success'] = False
        json['message'] = 'Missing subject_id'
    
    return JsonResponse(json)
