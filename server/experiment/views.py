from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from .models import Group, PostDOSurvey, Subject, Group, MessageRecord, PostDFSurvey, PostDOSurvey, DemograSurvey
from .models import PreDSurvey
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta
from random import sample
import random
import json
from decimal import *
from .gpt import GPT
from django.db import connection, transaction
import logging
from datetime import datetime
from django.views.decorators.csrf import ensure_csrf_cookie


SUCCESS_CODE = "CVGW5BEE"
FAILED_ATTENTION_CODE = "C2ZILU9F"
GO_BACK_TERMINATE_CODE = "C3AXEIWP"
INACTIVE_TERMINATE_CODE = "C4ZJ8888"
FAILED_PAIRING_CODE = "C5ZJ8888"


# Initialize logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('experiment/logs/views.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

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

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
import random
from .models import Subject, Group, TimeRecord

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
                session_id=session_id
            )
            time_record = TimeRecord.objects.create(
                subject_id=sub._id,
                StarEntrance_button_time=timezone.now()
            )
            logger.info(f"time_record created: {time_record.subject_id, time_record.start_chat_time}")
            logger.info(f"time_record created: {time_record.subject_id, time_record.end_chat_time}")
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
    response_data = {}
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
    ai_in_music = request.POST.get('aiInMusic', None)  # Expecting json string for checkboxes
    ai_in_email = request.POST.get('aiInEmail', None)  # Expecting json string for checkboxes
    ai_in_home_devices = request.POST.get('aiInHomeDevices', None)  # Expecting json string for checkboxes
    ai_mental_capacity_responses = request.POST.get('aiMentalCapacityResponses', None)  # Expecting json string

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
                social_media_reading_platforms=json.loads(social_media_reading_platforms) if social_media_reading_platforms else [],
                social_media_posting_platforms=json.loads(social_media_posting_platforms) if social_media_posting_platforms else [],
                ai_tool_usage_frequency=ai_tool_usage_frequency,
                ai_attitude_selection=ai_attitude_selection,
                ai_in_music=ai_in_music,
                ai_in_email=ai_in_email,
                ai_in_home_devices=ai_in_home_devices,
                ai_mental_capacity_responses=ai_mental_capacity_responses
            )

            time_record = TimeRecord.objects.get(subject_id=subject_id)
            time_record.DemograSurvey_button_time = timezone.now()
            time_record.save()

            response_data['success'] = True
            response_data['message'] = 'Survey saved successfully'
            return JsonResponse(response_data)
        except Exception as e:
            response_data['success'] = False
            response_data['message'] = str(e)
            return JsonResponse(response_data)
    else:
		# Handle the case where subject_id is missing
        response_data['success'] = False
        response_data['message'] = 'Missing subject_id'
        return JsonResponse(response_data)



@api_view(['POST'])
def heartbeat(request):
    """Updates the last active time of a subject and checks for inactive users"""
    subject_id = request.data.get('subject_id')

    try:
        subject = Subject.objects.get(pk=subject_id)
        subject.last_active_time = timezone.now()  # Update last active time
        subject.save()

        check_inactive_users()  # This will check inactive users **every time** a heartbeat is received.

        return JsonResponse({'status': 'ok'})
    except Subject.DoesNotExist:
        return JsonResponse({'error': 'Subject not found'}, status=404)

def check_inactive_users():
    """Handles inactive users by marking them, disbanding their groups, and re-pairing active members."""
    inactive_users = mark_inactive_users()  # Step 1: Identify inactive users
    # users_to_repair = remove_inactive_users_from_groups(inactive_users)  # Step 2: Disband groups and collect active members
    # reassign_active_users(users_to_repair)  # Step 3: Re-pair remaining users from scratch

def mark_inactive_users():
    """Marks users as inactive if they haven't sent a heartbeat within 30 seconds."""
    time_threshold = timezone.now() - timedelta(seconds=30)  # 30 sec inactivity

    # Find inactive users
    inactive_users = Subject.objects.filter(last_active_time__lt=time_threshold, active=True)

    for user in inactive_users:
        user.active = False  # Mark user as inactive
        user.save()

    return inactive_users  # Return list of inactive users for further processing

def remove_inactive_users_from_groups(inactive_users):
    """Disbands groups with inactive users and prepares active users for re-pairing."""
    users_to_repair = []  # Collect all active users from disbanded groups

    for user in inactive_users:
        if user.group_id != -1:  # Only process users who were in a group
            try:
                group = Group.objects.get(pk=user.group_id)

                # Disband the group: Extract all active users
                for member_id in group.member_ids['subject_ids']:
                    member = Subject.objects.get(pk=member_id)
                    if member.active:  # Collect only active users for re-pairing
                        users_to_repair.append(member._id)  # Use _id instead of subject_id
                        member.group_id = -1  # Mark them as unassigned
                        member.save()

            except Group.DoesNotExist:
                pass  # Ignore if group doesn't exist

    return users_to_repair  # Return list of active users to be re-paired





@api_view(['POST'])
def pairing(request):
    """Pairs users into groups with different opinions on at least one shared statement."""
    subject_id = request.POST.get('subject_id', None)


    if subject_id is None:
        logger.info('Error: Missing subject_id')
        return JsonResponse({'success': False, 'message': 'Missing subject_id', 'has_capacity': False}, status=400)

    try:

        subject = Subject.objects.get(pk=subject_id)
        if subject.group_id != -1:
            group = Group.objects.get(pk=subject.group_id)
            group.refresh_from_db()
            return JsonResponse({
                'success': True,
                'group_id': group._id,
                'group_capacity': group.size,
                'moderator_condition': group.group_moderator_condition,
                'participant_condition': group.group_participant_condition,
                'chat_statement_indx': group.group_chat_statement_index,
                'assigned_avatars': group.assigned_avatars,  # Assign avatar to subject
                'is_third_person': False,
                'average_waiting_time': get_average_waiting_time(),
                'has_capacity': group.has_capacity
            })

        # **Step 1: Check if an existing 2-person group needs a third participant**
        open_groups = Group.objects.filter(size=3, current_size=2, has_capacity=True)

        if open_groups:
            group = open_groups[0]
            with transaction.atomic():
                # Add subject to the existing group
                group.member_ids['subject_ids'].append(subject._id)
                group.current_size += 1
                group.has_capacity = False  # Group is now full
                group.third_person_id = subject._id  # Mark this person as the third person


                # Assign subject to this group
                subject.group_id = group._id
                subject.is_third_person = True  # Mark this subject as the third person
                subject.random_third_person_prompt = random.choice([0, 1])
                subject.save()

                # Since group is now full, assign avatar to subject
                assigned_avatars = assign_avatars_to_group(group)
                group.assigned_avatars = assigned_avatars
                group.save()
            return JsonResponse({
                'success': True,
                'group_id': group._id,
                'group_capacity': group.size,
                'moderator_condition': group.group_moderator_condition,
                'participant_condition': group.group_participant_condition,
                'chat_statement_indx': group.group_chat_statement_index,
                'assigned_avatars': assigned_avatars,  # Assign avatar to subject
                'is_third_person': True,  # Tell frontend this is the third person
                'average_waiting_time': get_average_waiting_time(),
                'has_capacity': group.has_capacity,  # Now False
                'random_third_person_prompt': subject.random_third_person_prompt
            })

        # **Step 2: No 3-person group available, proceed with normal 2-person pairing**
        # Find all potential partners with opposing views on any statement
        potential_partners = []
        for partner in Subject.objects.filter(group_id=-1, ready_to_pair=True).exclude(_id=subject._id):
            different_opinions_index = get_different_opinions(subject, partner)
            if different_opinions_index is not None:
                potential_partners.append(partner)

        if not potential_partners:
            return JsonResponse({'success': False, 'message': 'No suitable partner found','average_waiting_time': get_average_waiting_time()})

        # Randomly select one partner from those with opposing views
        random_match_partner = random.choice(potential_partners)

        # Get the statements they disagree on for selecting chat topic
        different_opinions_index = get_different_opinions(subject, random_match_partner)

        # **Step 3: Select a Statement for Discussion (Weighted Randomization)**
        statement_frequencies = get_statement_frequencies()
        available_statements = [idx for idx in different_opinions_index if idx in statement_frequencies]
        if not available_statements:
            return JsonResponse({'success': False, 'message': 'No suitable statement found for discussion'})
        weights = [1 / (1 + statement_frequencies.get(idx, 0)) for idx in available_statements]
        chat_statement_idx = random.choices(available_statements, weights=weights)[0]

        # Assign `moderator_condition`
        # moderator_condition = random.choice([0, 1])  # 50% chance for AI Moderator
        moderator_condition = random.choice([0])  # A Moderator for TEST
        # Assign `participant_condition` with equal probability
        # participant_condition = random.choice([0, 1, 2, 3])
        participant_condition = random.choice([1]) # Only 3-person group with AI Participant for TEST

        # **Step 4: Create a New Group**
        with transaction.atomic():
            group = Group.objects.create(
                size=3 if participant_condition == 3 else 2,
                group_chat_statement_index=chat_statement_idx,
                group_moderator_condition=moderator_condition,
                group_participant_condition=participant_condition,
                current_size=0
            )

            # Assign both users to the group
            group.member_ids['subject_ids'] = [subject._id, random_match_partner._id]
            group.current_size = 2
            assigned_avatars = None
            # If the group needs a third member, keep it open
            if group.group_participant_condition == 3:
                group.has_capacity = True
            else:
                group.has_capacity = False  # Group is full
                # Since group is now full, assign avatar to subjects
                assigned_avatars = assign_avatars_to_group(group)

            group.save()

            # Update subjects
            subject.group_id = group._id
            random_match_partner.group_id = group._id
            subject.save(update_fields=['group_id'])
            random_match_partner.save(update_fields=['group_id'])
            group.refresh_from_db()

        if assigned_avatars:
            group.assigned_avatars = assigned_avatars
            group.save()
            return JsonResponse({
                'success': True,
                'group_id': group._id,
                'group_capacity': group.size,
                'moderator_condition': group.group_moderator_condition,
                'participant_condition': group.group_participant_condition,
                'chat_statement_indx': group.group_chat_statement_index,
                'assigned_avatars': assigned_avatars,
                'average_waiting_time': get_average_waiting_time(),
                'is_third_person': False,
                'has_capacity': group.has_capacity  # Ensures frontend correctly handles redirection
            })
        # if pair failed
        return JsonResponse({
            'success': False,
            'group_id': -100,
            'group_capacity': -100,
            'moderator_condition': -100,
            'participant_condition': -100,
            'chat_statement_indx': -100,
            'average_waiting_time': get_average_waiting_time(),
            'is_third_person': False,
            'has_capacity': True
        })

    except Subject.DoesNotExist:
        logger.info(f'Subject not found: {subject_id}')
        logger.error(f'Subject not found: {subject_id}')
        return JsonResponse({'success': False, 'message': 'Subject not found', 'has_capacity': False}, status=404)
    except Exception as e:
        logger.info(f'Error in pairing function: {str(e)}')
        logger.error(f'Error in pairing function: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'message': str(e), 'has_capacity': False}, status=500)

def get_average_waiting_time():
    time_records = TimeRecord.objects.filter(pair_end_time__isnull=False, pair_start_time__isnull=False)
    total_waiting_time = sum((time_record.pair_end_time - time_record.pair_start_time).total_seconds() for time_record in time_records)
    return total_waiting_time / len(time_records) if len(time_records) > 0 else 10


@api_view(['POST'])
def set_ready_to_pair(request):
    """Sets a subject's ready_to_pair status to True And record start pairing time."""
    subject_id = request.POST.get('subject_id', None)

    logger.info(f'Setting ready_to_pair to True for subject_id: {subject_id}')

    if subject_id is None:
        return JsonResponse({'success': False, 'message': 'Missing subject_id'}, status=400)

    try:


        subject = Subject.objects.get(pk=subject_id)
        subject.ready_to_pair = True
        subject.save()
        # Record start pairing time
        time_record = TimeRecord.objects.get(subject_id=subject_id)
        time_record.pair_start_time = timezone.now()
        time_record.save()

        return JsonResponse({'success': True, 'message': 'Subject ready to pair'})
    except Subject.DoesNotExist:
        logger.error(f'Subject not found: {subject_id}')
        return JsonResponse({'success': False, 'message': 'Subject not found'}, status=404)
    except Exception as e:
        logger.error(f'Error in set_ready_to_pair function: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@api_view(['POST'])
def set_not_ready_to_pair(request):
    """Sets a subject's ready_to_pair status to False And record end pairing time."""
    subject_id = request.POST.get('subject_id', None)

    logger.info(f'Setting ready_to_pair to False for subject_id: {subject_id}')

    if subject_id is None:
        return JsonResponse({'success': False, 'message': 'Missing subject_id'}, status=400)

    try:
        subject = Subject.objects.get(pk=subject_id)
        subject.ready_to_pair = False
        subject.save()
        # Record end pairing time
        time_record = TimeRecord.objects.get(subject_id=subject_id)
        time_record.pair_end_time = timezone.now()
        time_record.save()

        return JsonResponse({'success': True, 'message': 'Subject not ready to pair'})
    except Subject.DoesNotExist:
        logger.error(f'Subject not found: {subject_id}')
        return JsonResponse({'success': False, 'message': 'Subject not found'}, status=404)
    except Exception as e:
        logger.error(f'Error in set_not_ready_to_pair function: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def get_different_opinions(subject, partner):
    """Returns all statement_ids where participants have opposing views."""
    different_opinions_index = []

    try:
        # Get PreDSurvey responses for both subjects
        survey1 = PreDSurvey.objects.get(subject_id=subject._id)
        survey2 = PreDSurvey.objects.get(subject_id=partner._id)

        responses1 = json.loads(survey1.responses)
        responses2 = json.loads(survey2.responses)
        # Map statement_id to agreement for both participants
        resp_dict1 = {item['statement_id']: item['agreement'] for item in responses1}
        resp_dict2 = {item['statement_id']: item['agreement'] for item in responses2}
        # Identify opposing views by statement_id
        for sid, agr1 in resp_dict1.items():
            agr2 = resp_dict2.get(sid)
            if agr2 is not None and agr1 * agr2 < 0:
                different_opinions_index.append(sid)
    except PreDSurvey.DoesNotExist:
        return []
    except (ValueError, KeyError) as e:
        logger.info(f"Error in get_different_opinions: {e}")
    return different_opinions_index

def get_statement_frequencies():
    """Counts how many times each statement has been selected for discussion and excludes those exceeding the threshold."""
    # Get all groups with a valid statement index
    groups = Group.objects.exclude(group_chat_statement_index=-1)
    if not groups.exists():
        return {idx: 0 for idx in range(6)}

    # Get counts for statements that have been discussed
    statement_counts = groups.values('group_chat_statement_index').annotate(count=Count('group_chat_statement_index'))
    count_dict = {entry['group_chat_statement_index']: entry['count'] for entry in statement_counts}

    # Determine dynamic threshold
    min_count = min(count_dict.values())
    max_count = max(count_dict.values())
    if min_count < 10 and max_count <= 10:
        # threshold = 10
        threshold = 10000 # a large number for TEST
    elif min_count >= 10 and min_count < 20 and max_count <= 20:  # Only increase threshold if all counts >= 10
        threshold = 20
    elif min_count >= 20 and min_count < 30 and max_count <= 30:  # Only increase threshold if all counts >= 20
        threshold = 30
    elif min_count >= 30 and min_count < 40 and max_count <= 40:  # Only increase threshold if all counts >= 30
        threshold = 4000
    else:
        threshold = 40000

    # Include all statements from 0 to 5, defaulting to 0 for those not in count_dict
    result = {idx: count_dict.get(idx, 0) for idx in range(6) if count_dict.get(idx, 0) < threshold}
    return result

def assign_avatars_to_group(group):
    """Assigns unique avatars to all members of a group."""
    colors = ['Red', 'Blue', 'Green', 'Purple', 'Orange', 'Yellow']
    animals = ['Fox', 'Penguin', 'Tiger', 'Wolf', 'Elephant', 'Panda', 'Koala', 'Rabbit']

    try:
        group_members = Subject.objects.filter(_id__in=group.member_ids['subject_ids'])

        # Shuffle to ensure randomness
        random.shuffle(colors)
        random.shuffle(animals)

        assigned_avatars = []
        for member in group_members:
            if colors and animals:
                color = colors.pop()
                animal = animals.pop()
                member.avatar_color = color
                member.avatar_name = animal

                assigned_avatars.append({
                    'subject_id': member._id,
                    'avatar_color': color,
                    'avatar_name': animal
                })

                try:
                    with transaction.atomic():
                        member.save()

                        # Refresh and verify the update
                        member.refresh_from_db(fields=['avatar_color', 'avatar_name'])

                except Exception as e:
                    logger.error(f'Database update failed for subject {member._id}: {str(e)}')
                    raise

        return assigned_avatars

    except Exception as e:
        logger.error(f'Error in assign_avatars_to_group: {str(e)}')
        raise


def record_start_chat_time(group_id: int) -> None:
    """Records the start time of a group's chat session."""
    try:
        group = Group.objects.get(pk=group_id)
        subjects = Subject.objects.filter(_id__in=group.member_ids['subject_ids'])
        for subject in subjects:
            time_record = TimeRecord.objects.get(subject_id=subject._id)
            if time_record.start_chat_time is None:
                time_record.start_chat_time = timezone.now()
                time_record.save(update_fields=['start_chat_time'])
    except Group.DoesNotExist:
        logger.error(f'Group {group_id} not found')
    except Exception as e:
        logger.error(f'Error recording start chat time: {str(e)}')

def record_end_chat_time(group_id: int) -> None:
    """Records the end time of a group's chat session."""
    try:
        group = Group.objects.get(pk=group_id)
        subjects = Subject.objects.filter(_id__in=group.member_ids['subject_ids'])
        for subject in subjects:
            time_record = TimeRecord.objects.get(subject_id=subject._id)
            if time_record.end_chat_time is None:
                time_record.end_chat_time = timezone.now()
                time_record.save(update_fields=['end_chat_time'])
    except Group.DoesNotExist:
        logger.error(f'Group {group_id} not found')
    except Exception as e:
        logger.error(f'Error recording end chat time: {str(e)}')

@api_view(['POST'])
def update_chat_status(request):
    """Update the 'chatting' status of a group and send welcome message if needed"""
    try:
        group_id = request.POST.get('group_id')
        chatting = request.POST.get('chatting')

        if group_id is None or chatting is None:
            return JsonResponse({'error': 'Missing group_id or chatting field'}, status=400)

        # Record start chat time if chat is starting
        if chatting:
            record_start_chat_time(group_id)
        else:
            record_end_chat_time(group_id)

        # Retrieve the group
        group = Group.objects.get(pk=group_id)
        group.chatting = bool(chatting)
        group.save(update_fields=['chatting'])

        # No longer needed: Send welcome message if chat is starting and hasn't been sent before
        # if group.chatting and not group.chat_started and group.group_moderator_condition == 1:
        #     # Create message record
        #     welcome_msg = MessageRecord.objects.create(
        #         subject_id=-2,  # AI Moderator ID
        #         group_id=group_id,
        #         message="Welcome to the discussion. For each of you, please briefly explain your position to start!"
        #     )

        #     # Send WebSocket message
        #     from channels.layers import get_channel_layer
        #     from asgiref.sync import async_to_sync

        #     channel_layer = get_channel_layer()
        #     async_to_sync(channel_layer.group_send)(
        #         f"chat_{group_id}",
        #         {
        #             "type": "chat.message",
        #             "message": {
        #                 "code": 201,
        #                 "message": {
        #                     "sender": {
        #                         "subject_id": -2  # AI Moderator ID
        #                     },
        #                     "content": welcome_msg.message,
        #                     "timestamp": welcome_msg.time_stamp.isoformat()
        #                 }
        #             }
        #         }
        #     )

        #     group.chat_started = True

        return JsonResponse({
            'message': 'Chat status updated successfully',
            'chatting': group.chatting
        })

    except Group.DoesNotExist:
        return JsonResponse({'error': 'Group not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)










def record_message(request):
    """Record a message and update turn tracking"""
    try:
        subject_id = int(request.get('subject_id'))
        group_id = int(request.get('group_id'))
        message = request.get('message')



        # get the group and the current turn number
        group = Group.objects.get(pk=group_id)
        current_turn_str = str(group.current_turn)  # Convert to string for json dict key
        logger.info("current_turn_str: %s", current_turn_str)

        # Save message record with current turn number
        MessageRecord.objects.create(
            subject_id=subject_id,
            group_id=group_id,
            message=message,
            turn_number=int(current_turn_str)
        )
        logger.info("message saved: %s for subject %s in turn %s", message, subject_id, current_turn_str)
        # * track who sent message in current turn
        # Initialize messages_turn for current turn if needed
        if current_turn_str not in group.messages_turn:
            group.messages_turn[current_turn_str] = []
            logger.info("Initializing messages_turn for current turn: %s", current_turn_str)
        # Add subject to current turn if they haven't sent a message yet
        if subject_id not in group.messages_turn[current_turn_str]:
            group.messages_turn[current_turn_str].append(subject_id)
            group.save(update_fields=['messages_turn'])
            logger.info("group.messages_turn %s: %s", current_turn_str, group.messages_turn[current_turn_str])
            logger.info("Adding subject %s to turn %s", subject_id, current_turn_str)


        # * Upadte turn number if all members have sent a message this turn and send turn end GPT response
        # Check if all members have sent a message this turn
        all_members = set(int(id) for id in group.member_ids['subject_ids'])
        current_turn_members = set(int(id) for id in group.messages_turn[current_turn_str])
        logger.info("all_members: %s", all_members)
        logger.info("current_turn_members: %s", current_turn_members)
        response_data = {'success': True, 'turn_increased': False}
        # If all members have sent a message this turn, send turn end GPT response and increment turn counter
        if all_members == current_turn_members:
            send_turn_end_gpt_response(group_id, current_turn_str)
            # Increment turn counter
            group.current_turn += 1
            group.save(update_fields=['current_turn'])
            logger.info("Incrementing turn counter to %s", group.current_turn)
            response_data['turn_increased'] = True


    except Exception as e:
        logger.info('Error details: %s', str(e))
        logger.info('Request data: %s', request)
        logger.info('Group ID: %s', group_id)
        logger.info('Subject ID: %s', subject_id)
        logger.info('Message: %s', message)
        return JsonResponse({'error': str(e)}, status=500)

def send_turn_end_gpt_response(group_id, current_turn_str):
    logger.info('Starting send_turn_end_gpt_response')
    logger.info('Group ID: %s', group_id)
    logger.info('Current turn str: %s', current_turn_str)
    # get group
    group = Group.objects.get(pk=group_id)

    # Get timestamp of the first message in the current turn
    first_message_timestamp = MessageRecord.objects.filter(
        group_id=group_id,
        turn_number=int(current_turn_str)
    ).values_list('time_stamp', flat=True).first()
    logger.info("first_message_timestamp: %s", first_message_timestamp)
    # Get messages from current turn
    current_message_records = MessageRecord.objects.filter(
        group_id=group_id,
        time_stamp__gte=first_message_timestamp
    ).order_by('time_stamp')
    # Get messages from previous turns
    previous_message_records = MessageRecord.objects.filter(
        group_id=group_id,
        time_stamp__lt=first_message_timestamp
    ).order_by('time_stamp')

    logger.info('Current messages: %s', current_message_records)
    logger.info('Previous messages: %s', previous_message_records)
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()
    try:
        # 1. First get participant AI response if condition requires it
        if group.group_participant_condition in [1, 2]:
            # Send typing notification: AI Participant started typing
            participant_id = -3 if group.group_participant_condition == 1 else -4
            async_to_sync(channel_layer.group_send)(
                f"chat_{group_id}",
                {
                    'type': 'chat_message',
                    'message': {
                        'code': 203,
                        'typing_info': {
                            'subject_id': participant_id,
                            'avatar_name': 'AI Participant',
                            'avatar_color': '',
                            'is_typing': True
                        }
                    }
                }
            )
            participant_gpt = GPT(
                group_id=group_id,
                moderator_condition=0,  # Set to 0 to get only participant response
                participant_condition=group.group_participant_condition,
                current_message_records=format_message_records(current_message_records),
                previous_message_records=format_message_records(previous_message_records),
                turn_number=int(current_turn_str)
            )

            participant_gpt_response = participant_gpt.get_response()

            if participant_gpt_response and participant_gpt_response != "...":
                # Save participant AI response
                participant_id = -3 if group.group_participant_condition == 1 else -4
                gpt_participant_message = MessageRecord.objects.create(
                    subject_id=participant_id,
                    group_id=group_id,
                    message=participant_gpt_response,
                    turn_number=int(current_turn_str)
                )

                # Broadcast participant AI response first
                participant_gpt_response_response = json.loads(participant_gpt_response)['response']
                logger.info("broadcasting participant response %s", participant_gpt_response_response)

                print("broadcasting participant response")
                async_to_sync(channel_layer.group_send)(
                    f"chat_{group_id}",
                    {
                        'type': 'chat_message',
                        'message': {
                            "code": 201,
                            "message": {
                                "sender": {
                                    "subject_id": participant_id
                                },
                                "content": participant_gpt_response_response,
                                "time_stamp": datetime.now().isoformat()
                            }
                        }
                    }
                )
                # Send typing notification: AI Participant stopped typing
                print("AI Participant stopped typing")
                async_to_sync(channel_layer.group_send)(
                    f"chat_{group_id}",
                    {
                        'type': 'chat_message',
                        'message': {
                            'code': 203,
                            'typing_info': {
                                'subject_id': participant_id,
                                'avatar_name': 'AI Participant',
                                'avatar_color': '',
                                'is_typing': False
                            }
                        }
                    }
                )
                # Add to current messages for moderator context
                current_message_records = list(current_message_records)
                current_message_records.append(gpt_participant_message)
                logger.info("adding gpt participant message")
                logger.info("current_message_records: %s", current_message_records)
        # 2. Then get moderator response if condition requires it
        if group.group_moderator_condition == 1:
            logger.info("Getting moderator response")
            # Send typing notification: AI Moderator started typing
            async_to_sync(channel_layer.group_send)(
                f"chat_{group_id}",
                {
                    'type': 'chat_message',
                    'message': {
                        'code': 203,
                        'typing_info': {
                            'subject_id': -2,
                            'avatar_name': 'AI Moderator',
                            'avatar_color': '',
                            'is_typing': True
                        }
                    }
                }
            )
            moderator_gpt = GPT(
                group_id=group_id,
                moderator_condition=1,
                participant_condition=0,  # Set to 0 to get only moderator response
                current_message_records=format_message_records(current_message_records),
                previous_message_records=format_message_records(previous_message_records),
                turn_number=int(current_turn_str)
            )

            moderator_response = moderator_gpt.get_response()

            logger.info("Moderator GPT response: %s", moderator_response)
            if moderator_response and moderator_response != "...":
                # Save moderator response
                MessageRecord.objects.create(
                    subject_id=-2,  # Moderator ID
                    group_id=group_id,
                    message=moderator_response,
                    turn_number=int(current_turn_str)
                )
                logger.info("adding moderator response to MessageRecord")
                moderator_response_response = json.loads(moderator_response)['response']
                logger.info("broadcasting moderator response %s", moderator_response_response)
                # Broadcast moderator response second
                async_to_sync(channel_layer.group_send)(
                    f"chat_{group_id}",
                    {
                        'type': 'chat_message',
                        'message': {
                            "code": 201,
                            "message": {
                                "sender": {
                                    "subject_id": -2
                                },
                                "content": moderator_response_response,
                                "time_stamp": datetime.now().isoformat()
                            }
                        }
                    }
                )
                # Send typing notification: AI Moderator stopped typing
                async_to_sync(channel_layer.group_send)(
                    f"chat_{group_id}",
                    {
                        'type': 'chat_message',
                        'message': {
                            'code': 203,
                            'typing_info': {
                                'subject_id': -2,
                                'avatar_name': 'AI Moderator',
                                'avatar_color': '',
                                'is_typing': False
                            }
                        }
                    }
                )

    except Exception as e:
        logger.info(f"Error in send_turn_end_gpt_response: %s", str(e))
        # You might want to log this error or handle it in a specific way


def format_message_records(message_records):
    """Format messages for GPT input"""
    logger.info("formatting message records")
    formatted = []
    for msg_record in message_records:
        if msg_record.subject_id > 0:  # Human message
            subject = Subject.objects.get(pk=msg_record.subject_id)
            formatted.append({
                'content': msg_record.message,
                'sender_name': f"{subject.avatar_color} {subject.avatar_name}",
                'is_human': True,
                'time_stamp': msg_record.time_stamp.timestamp()
            })
        else:  # AI message
            formatted.append({
                'content': msg_record.message,
                'is_human': False,
                'ai_role': get_ai_role(msg_record.subject_id),
                'time_stamp': msg_record.time_stamp.timestamp()
            })
    logger.info("formatted message records: %s", formatted)
    return formatted

def get_ai_role(subject_id):
    """Get AI role based on subject ID"""
    if subject_id == -2:
        return "AI Moderator"
    elif subject_id == -3:
        return "Advocating AI Participant"
    elif subject_id == -4:
        return "Disputing AI Participant"
    return "AI"

def get_ai_subject_id(group):
    """Get appropriate AI subject ID based on group conditions"""
    if group.group_moderator_condition == 1:
        return -2  # AI Moderator
    elif group.group_participant_condition == 1:
        return -3  # Advocating AI
    elif group.group_participant_condition == 2:
        return -4  # Disputing AI
    return -5  # Generic AI

def record_post_do_survey_submit_time(subject_id):
    time_record = TimeRecord.objects.get(subject_id=subject_id)
    time_record.PostDOSurvey_button_time = timezone.now()
    time_record.save()

@api_view(['POST'])
def post_do_survey(request):
    response_data = {}
    data = request.data  # Using request.data since we're sending json, not form data
    subject_id = data.get('subject_id', None)
    policy_responses = data.get('policy_responses', [])
    conversation_quality = data.get('conversation_quality', None)
    conversation_responses = data.get('conversation_responses', [])
    reciprocity_responses = data.get('reciprocity_responses', [])

    if subject_id is not None:
        try:
            # Record submit time
            record_post_do_survey_submit_time(subject_id)

            # Create the survey record
            survey = PostDOSurvey.objects.create(
                subject_id=subject_id,
                policy_responses=policy_responses,
                conversation_quality=conversation_quality,
                conversation_responses=conversation_responses,
                reciprocity_responses=reciprocity_responses
            )

            response_data['success'] = True
            response_data['message'] = 'Survey saved successfully'
        except Exception as e:
            response_data['success'] = False
            response_data['message'] = f'Error saving survey: {str(e)}'
    else:
        response_data['success'] = False
        response_data['message'] = 'Missing subject_id'

    return JsonResponse(response_data)


def record_post_df_survey_submit_time(subject_id):
    time_record = TimeRecord.objects.get(subject_id=subject_id)
    time_record.PostDFSurvey_button_time = timezone.now()
    time_record.save()


@api_view(['POST'])
def post_df_survey(request):
    """Save final post-discussion survey"""
    response_data = {}
    data = request.data
    subject_id = data.get('subject_id')
    print(subject_id)
    print(data)
    if subject_id is None:
        return JsonResponse({
            'success': False,
            'message': 'Missing subject_id'
        })

    try:
        # Get group info for AI condition checks
        subject = Subject.objects.get(pk=subject_id)
        group = Group.objects.get(pk=subject.group_id)

        # Record submit time
        record_post_df_survey_submit_time(subject_id)

        # Create PostDFSurvey record
        survey = PostDFSurvey.objects.create(
            subject_id=subject_id,
            reflection=data.get('reflection'),
            attention_check_1=data.get('attention_check_1'),
            attention_check_2=data.get('attention_check_2'),
            critical_thinking_responses=data.get('critical_thinking_responses', []),
            used_ai_tool=data.get('used_ai_tool'),
            cost_responses=data.get('cost_responses', [])
        )

        # Add AI-specific responses if applicable
        if group.group_participant_condition > 0:  # Has AI participant
            survey.ai_participant_responses = data.get('ai_participant_responses', [])

        if group.group_moderator_condition == 1:  # Has AI moderator
            survey.ai_moderator_responses = data.get('ai_moderator_responses', [])

        survey.save()

        # Mark subject as complete
        subject.is_complete = True
        subject.save()

        response_data['success'] = True
        response_data['message'] = 'Survey saved successfully'

    except Subject.DoesNotExist:
        response_data['success'] = False
        response_data['message'] = 'Subject not found'
    except Group.DoesNotExist:
        response_data['success'] = False
        response_data['message'] = 'Group not found'
    except Exception as e:
        response_data['success'] = False
        response_data['message'] = f'Error saving survey: {str(e)}'
    print(response_data)
    return JsonResponse(response_data)



@api_view(['POST'])
def confirm_instructions(request):
    subject_id = request.POST.get('subject_id')
    group_id = request.POST.get('group_id')

    try:
        subject = Subject.objects.get(pk=subject_id)

        # Mark this subject as having confirmed instructions
        subject.confirmed_instructions = True
        subject.save()

        # Check if all third persons in the group have confirmed
        third_persons = Subject.objects.filter(
            group_id=group_id,
            is_third_person=True
        )

        all_confirmed = all(p.confirmed_instructions for p in third_persons)

        # Record confirmation time
        time_record = TimeRecord.objects.get(subject_id=subject_id)
        time_record.confirm_instructions_time = timezone.now()
        time_record.save()

        return JsonResponse({
            'success': True,
            'all_confirmed': all_confirmed
        })

    except (Subject.DoesNotExist, Group.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Subject or Group not found'
        })


def group_assign_condition(participant_number_condition):
    selected_indices = sample(range(12), 6)
    moderator_condition = random.choices([0,1], weights=[0.5, 0.5], k = 1)[0]
    if participant_number_condition == 0:
        participant_condition = random.choice([0,1,2])
    else:
        participant_condition = 3

    return selected_indices, moderator_condition, participant_condition



@api_view(['POST'])
def Update_pre_discussion_survey(request):
    response_data = {}
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

            time_record = TimeRecord.objects.get(subject_id=subject_id)
            time_record.PreDSurvey_button_time = timezone.now()
            time_record.save()

            response_data['success'] = True
            response_data['message'] = 'Survey saved successfully'
        except Exception as e:
            response_data['success'] = False
            response_data['message'] = f'Error saving survey: {str(e)}'
    else:
        response_data['success'] = False
        response_data['message'] = 'Missing subject_id'

    return JsonResponse(response_data)




@api_view(['POST'])
def get_subject_info(request):
    worker_id = request.POST.get('worker_id', None)
    study_id = request.POST.get('study_id', None)
    session_id = request.POST.get('session_id', None)

    # print(worker_id)

    if worker_id != None:
        if len(Subject.objects.filter(worker_id = worker_id)) == 0:
            raise PermissionDenied("We could not find your information in the server, please make sure you have passed the qualification.")
        else:
            sub = Subject.objects.filter(worker_id = worker_id)[0]
            if sub.is_qualified == False:
                raise PermissionDenied("We could not find your information in the server, please make sure you have passed the qualification.")
            if sub.start_time != None:
                raise PermissionDenied("You can take this HIT only once.")

            sub.assignment_id = study_id
            sub.hit_id = session_id
            sub.start_time = datetime.now()

            sub.save()

            response_data = {
                "subject_id": sub._id,
                "success": True
            }
            return JsonResponse(response_data)
    raise PermissionDenied("We could not find your information in the server, please make sure you have passed the qualification.")


@api_view(['GET'])
def debug_pre_discussion_surveys(request):
    """Debug endpoint to check all pre-discussion surveys."""
    try:
        surveys = PreDSurvey.objects.all()
        survey_data = []

        for survey in surveys:
            try:
                responses = survey.responses if isinstance(survey.responses, list) else []
                survey_data.append({
                    'subject_id': survey.subject_id,
                    'responses': responses
                })
            except json.JSONDecodeError:
                survey_data.append({
                    'subject_id': survey.subject_id,
                    'responses': 'Invalid JSON',
                    'raw_responses': survey.responses
                })

        return JsonResponse({
            'success': True,
            'count': len(survey_data),
            'surveys': survey_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



@api_view(['POST'])
def get_group_current_turn(request):
    """Retrieves the current turn of a group."""
    group_id = request.POST.get('group_id', None)

    if group_id is None:
        return JsonResponse({'success': False, 'message': 'Missing group_id'}, status=400)

    try:
        group = Group.objects.get(pk=group_id)
        return JsonResponse({'success': True, 'current_turn': group.current_turn})
    except Group.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Group not found'}, status=404)
    except Exception as e:
        logger.error(f'Error in get_group_current_turn function: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@api_view(['POST'])
def get_group_member_agreements(request):
    """Return group members' avatar name and their agreement level on the chat statement."""
    group_id = request.POST.get('group_id', None)
    try:
        group = Group.objects.get(pk=group_id)
        stmt_idx = group.group_chat_statement_index
        members = []
        for member_id in group.member_ids.get('subject_ids', []):
            subject = Subject.objects.get(pk=member_id)
            # Retrieve pre-discussion survey responses
            try:
                survey = PreDSurvey.objects.get(subject_id=subject._id)
                responses = json.loads(survey.responses)
            except (PreDSurvey.DoesNotExist, ValueError, TypeError):
                responses = []
            agreement = None
            # build lookup and fetch agreement by statement_id
            if isinstance(responses, list):
                resp_dict = {item['statement_id']: item['agreement'] for item in responses}
                agreement = resp_dict.get(stmt_idx)
            members.append({
                'subject_id': subject._id,
                'avatar_color': subject.avatar_color,
                'avatar_name': subject.avatar_name,
                'agreement_level': agreement
            })
        return JsonResponse({'members': members})
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Group not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in get_group_member_agreements: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def terminate_participation(request):
    subject_id = request.POST.get('subject_id', None)
    if subject_id is None:
        return JsonResponse({'success': False, 'message': 'Missing subject_id'}, status=400)
    try:
        # TODO: Implement termination logic
        return JsonResponse({'success': True})
    except Subject.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Subject not found'}, status=404)


@api_view(['POST'])
def submit_to_prolific(request):
    json = {}
    subject_id = request.POST.get('subject_id', None)
    status = request.POST.get('status', None)
    if subject_id != None:
        subject = Subject.objects.get(pk=subject_id)
        # Map status to Prolific completion codes
        if status == 'success':
            code = SUCCESS_CODE
        elif status == 'failed_attention':
            code = FAILED_ATTENTION_CODE
        elif status == 'go_back_terminate':
            code = GO_BACK_TERMINATE_CODE
        elif status == 'inactive_terminate':
            code = INACTIVE_TERMINATE_CODE
        elif status == 'failed_pairing':
            code = FAILED_PAIRING_CODE
        else:
            code = FAILED_ATTENTION_CODE
        # Update subject status and timestamps
        subject.end_time = timezone.now()
        subject.active = False
        subject.status = status
        subject.save()
        prolific_url = f"https://app.prolific.co/submissions/complete?cc={code}"
        return JsonResponse({'success': True, 'prolific_url': prolific_url})
    raise PermissionDenied("Subject id is missing, please contact the requester.")