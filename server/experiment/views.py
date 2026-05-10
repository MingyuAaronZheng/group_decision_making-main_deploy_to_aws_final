# type: ignore
from django.http import HttpRequest, HttpResponse, JsonResponse  # type: ignore
from rest_framework.decorators import api_view  # type: ignore
from rest_framework.exceptions import PermissionDenied  # type: ignore
from .models import (
    Group, PostDOSurvey, Subject, MessageRecord, PostDFSurvey, 
    DemograSurvey, EarlyExit, PreDSurvey, TimeRecord, Feedback, AIDemograSurvey, EndFeedback, VideoQuizResponse
)
from django.db.models import Count  # type: ignore
from django.utils import timezone  # type: ignore
from datetime import datetime
import random
import json
import re
from .gpt import GPT
from django.db import transaction  # type: ignore
import logging
import time
from channels.layers import get_channel_layer  # type: ignore
from asgiref.sync import async_to_sync  # type: ignore
import threading
import os
from typing import List, Dict, Any, Optional, Set
from .models import NormalDemographicSurveyResponse

SUCCESS_CODE = "CHUZDXJH"
FAILED_ATTENTION_CODE = "C2ZILU9F"
GO_BACK_TERMINATE_CODE = "C3AXEIWP"
INACTIVE_TERMINATE_CODE = "C4ZJ8888"
FAILED_PAIRING_CODE = "C5ZJ8888"
EARLY_EXIT_CODE = "C6ZJ8888"
AI_TURN_PENDING_SENTINEL = -9999

FILLER_PHRASES = [
    "you know",
    "i mean",
]
FILLER_WORDS = {
    "um", "uh", "er", "ah", "like", "okay", "right", "well", "so",
    "anyway", "basically", "actually", "literally", "just",
}


def parse_json_field(value: Any, default: Any) -> Any:
    """Return native JSON values whether DRF supplied a string or parsed object."""
    if value is None or value == "":
        return default
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return value


def meaningful_word_count(message: str) -> int:
    normalized = (message or "").lower()
    normalized = re.sub(r"\b(can|won|don|isn|aren|wasn|weren|didn|doesn|couldn|shouldn|wouldn)'t\b", r"\1 not", normalized)
    normalized = re.sub(r"\b(i|you|we|they|he|she|it)'(m|re|ve|ll|d|s)\b", r"\1 \2", normalized)
    for phrase in FILLER_PHRASES:
        normalized = re.sub(rf"\b{re.escape(phrase)}\b", " ", normalized)
    tokens = re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", normalized)
    meaningful_tokens = {token for token in tokens if token not in FILLER_WORDS}
    return len(meaningful_tokens)


def validate_human_message(message: str, test: str = "N") -> Dict[str, Any]:
    count = meaningful_word_count(message)
    required = 3 if test == "Y" else 10
    accepted = count > required
    return {
        "accepted": accepted,
        "meaningful_word_count": count,
        "required_meaningful_words": required + 1,
        "message": "Message accepted" if accepted else "Your message must contain more than 10 meaningful unique words. Filler words and repeated words do not count."
    }


def required_speaker_ids(group: Group) -> Set[int]:
    required = {int(subject_id) for subject_id in group.member_ids.get("subject_ids", []) if int(subject_id) > 0}
    if group.group_participant_condition == 1:
        required.add(-3)
    elif group.group_participant_condition == 2:
        required.add(-4)
    if group.group_moderator_condition == 1:
        required.add(-2)
    return required


# Initialize logger
# Create logs directory if it doesn't exist

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'experiment', 'logs')
os.makedirs(log_dir, exist_ok=True)

# Set up log file with absolute path
today = datetime.today()
log_file_name = os.path.join(log_dir, f'views_{today.strftime("%Y%m%d")}.log')

# Clear any existing handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_name, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Get logger for this module
logger = logging.getLogger(__name__)
logger.info('=' * 50)
logger.info('Logging initialized')
logger.info(f'Log file: {log_file_name}')

# Create your views here.
def home_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
	return HttpResponse("<h1>Hello World</h1>")


# Additional imports for specific functions
from django.views.decorators.csrf import csrf_exempt  # type: ignore

@api_view(['GET'])
def health_check(request: HttpRequest) -> HttpResponse:
    return HttpResponse("OK")


@api_view(['POST'])
def create_subject(request: HttpRequest) -> JsonResponse:
    worker_id = request.POST.get('worker_id', None)
    study_id = request.POST.get('study_id', None)
    session_id = request.POST.get('session_id', None)
    test = request.POST.get('test', None)
    if test == 'Y':
        test_moderator_code = request.POST.get('test_moderator_code', None)
        test_participant_code = request.POST.get('test_participant_code', None)
        test_policy_number = request.POST.get('test_policy_number', None)
        test_turn_number = request.POST.get('test_turn_number', None)
    logger.info("worker_id: %s with study_id: %s and session_id: %s and test: %s", worker_id, study_id, session_id, test)
    if worker_id is not None:
        # This checks if there is NOT already a Subject in the database with the given worker_id, study_id, and session_id.
        # If such a Subject does not exist, the following block will execute to create a new Subject.
        if not Subject.objects.filter(worker_id=worker_id, study_id=study_id).exists():
            # Normal subject creation
            # participant_number_condition = random.choices([0, 1], weights=[3, 1])[0]
            # selected_indices = sample(range(12), 6)
            if test == 'Y':
                sub = Subject.objects.create(
                    worker_id=worker_id,
                    study_id=study_id,
                    session_id=session_id,
                    test=test,
                    test_moderator_code=test_moderator_code,
                    test_participant_code=test_participant_code,
                    test_policy_number=test_policy_number,
                    test_turn_number=test_turn_number
                )
                logger.info("test subject created: %s", sub._id)
            else:
                sub = Subject.objects.create(
                    worker_id=worker_id,
                    study_id=study_id,
                    session_id=session_id,
                    test=test
                )
                logger.info("normal subject created: %s", sub._id)
            time_record = TimeRecord.objects.create(
                subject_id=sub._id,
                StarEntrance_button_time=timezone.now()
            )
            logger.info(f"time_record created: {time_record.subject_id, time_record.StarEntrance_button_time}")
            return JsonResponse({
                "subject_id": sub._id,
                "success": True,
                # "participant_number_condition": sub.participant_number_condition
            })
        else:
            logger.info("Worker ID: %s already exists", worker_id)
            return JsonResponse({
                "success": False,
                "message": "Worker ID already exists"
            })


    raise PermissionDenied("Worker ID is missing")

@api_view(['POST'])
def update_normal_DemograSurvey(request: HttpRequest) -> JsonResponse:
    """
    Handle demographic survey submission and store responses in the new DemographicSurveyResponse model.
    """
    response_data = {}
    subject_id = request.POST.get('subject_id')

    if not subject_id:
        logger.error("Demographic survey submission failed: Missing subject_id")
        return JsonResponse({
            'success': False,
            'message': 'Missing subject_id'
        }, status=400)

    try:
        # Extract form data
        survey_data = {
            'subject_id': subject_id,
            'age_range': request.POST.get('ageRange'),
            'gender_selection': request.POST.get('genderSelection'),
            'income_range': request.POST.get('incomeRange'),
            'education_level': request.POST.get('educationLevel'),
            'ethnicity_selection': request.POST.get('ethnicitySelection'),
            'religion_affiliation': request.POST.get('religionAffiliation'),
            'political_affiliation': request.POST.get('politicalAffiliation'),
            'immigration_status': request.POST.get('immigrationStatus'),
            'social_media_reading_frequency': request.POST.get('socialMediaReadingFrequency'),
            'social_media_posting_frequency': request.POST.get('socialMediaPostingFrequency'),
        }

        # Handle JSON fields
        social_media_reading_platforms = request.POST.get('socialMediaReadingPlatforms')
        social_media_posting_platforms = request.POST.get('socialMediaPostingPlatforms')
        
        if social_media_reading_platforms:
            survey_data['social_media_reading_platforms'] = json.loads(social_media_reading_platforms)
        if social_media_posting_platforms:
            survey_data['social_media_posting_platforms'] = json.loads(social_media_posting_platforms)

        # Create new survey response
        survey = NormalDemographicSurveyResponse.objects.create(**survey_data)
        logger.info("Demographic survey record created for subject_id: %s", subject_id)

        # Update time record
        time_record = TimeRecord.objects.get(subject_id=subject_id)
        time_record.DemograSurvey_button_time = timezone.now()
        time_record.save()
        logger.info("Demographic survey time record updated for subject_id: %s", subject_id)

        return JsonResponse({
            'success': True,
            'message': 'Survey saved successfully'
        })

    except TimeRecord.DoesNotExist:
        logger.error("Time record not found for subject_id: %s", subject_id)
        return JsonResponse({
            'success': False,
            'message': 'Time record not found'
        }, status=404)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON data in survey submission for subject_id: %s - %s", subject_id, str(e))
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data in survey submission'
        }, status=400)
    except Exception as e:
        logger.error("Demographic survey submission failed for subject_id: %s - %s", subject_id, str(e), exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)



# Global variable to track if the background thread is running
inactive_check_thread = None
inactive_check_running = False
inactive_check_lock = threading.Lock()  # Thread lock for thread safety

# File-based lock to prevent multiple processes from running the checker
import fcntl
import os

class ProcessLock:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.fd = None

    def acquire(self) -> bool:
        self.fd = open(self.filename, 'w')
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            self.fd.close()
            return False

    def release(self) -> None:
        if self.fd:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                self.fd.close()
                os.remove(self.filename)
            except Exception:
                pass

# Create a global process lock
process_lock = ProcessLock('/tmp/gdm_inactive_checker.lock')

def start_inactive_user_checker() -> None:
    """Starts the background thread to check for inactive users"""
    global inactive_check_thread, inactive_check_running

    logger.debug(f"Attempting to start inactive user checker. Current state - running: {inactive_check_running}, thread: {inactive_check_thread}")

    # Try to acquire the process lock first
    if not process_lock.acquire():
        logger.debug("Another process is already running the inactive user checker")
        return

    try:
        with inactive_check_lock:  # Use a lock to prevent race conditions
            # Check if thread is already running and alive
            if inactive_check_running and inactive_check_thread and inactive_check_thread.is_alive():
                logger.debug("Inactive user checker is already running in this process")
                return

            # Set the flag before starting the thread to prevent race conditions
            inactive_check_running = True

            def check_inactive_loop():
                logger.info("Inactive user checker thread started")
                try:
                    while inactive_check_running:
                        try:
                            check_inactive_users()
                        except Exception as e:
                            logger.error(f"Error in inactive user check: {str(e)}")
                        time.sleep(20)  # Check every 20 seconds
                finally:
                    logger.info("Inactive user checker thread stopped")
                    # Release the process lock when the thread stops
                    process_lock.release()

            # Create and start the thread
            inactive_check_thread = threading.Thread(
                target=check_inactive_loop,
                daemon=True,
                name="InactiveUserChecker"
            )
            inactive_check_thread.start()
    except Exception as e:
        # If anything goes wrong, release the lock
        process_lock.release()
        logger.error(f"Failed to start inactive user checker: {str(e)}")


def check_inactive_users() -> None:
    
    logger.info("Running periodic inactive user check")
    mark_inactive_users()  # Step 1: Identify inactive users
    # users_to_repair = remove_inactive_users_from_groups(inactive_users)  # Step 2: Disband groups and collect active members
    # reassign_active_users(users_to_repair)  # Step 3: Re-pair remaining users from scratch
    
    # Also check for groups where all members have finished chat
    check_finished_chat_groups()

def check_finished_chat_groups() -> None:
    """Check active chatting groups and mark them as finished when all members have finished chat."""
    logger.info("Running finished chat groups check")
    finished_groups = mark_finished_chat_groups()
    logger.info(f"Marked {len(finished_groups)} groups as finished chatting")

def mark_finished_chat_groups() -> List[Group]:
    """
    Find active chatting groups where all members have finished_chat=True 
    and mark those groups as chatting=False.
    Returns a list of groups that were marked as finished.
    """
    logger.info("Checking for groups where all members have finished chat")
    
    # Find all active chatting groups
    active_chat_groups = Group.objects.filter(chatting=True)
    finished_groups = []
    
    for group in active_chat_groups:
        try:
            # Get member IDs from the group
            member_ids = group.member_ids.get('subject_ids', [])
            active_member_ids = group.activate_member_ids.get('subject_ids', [])
            if not active_member_ids:  # If group has no active members, mark it as not chatting
                logger.info(f"Group {group._id} has no active members, marking as not chatting")
                group.chatting = False
                group.save(update_fields=['chatting'])
                record_end_chat_time(group._id)
                finished_groups.append(group)
                continue
            
            # Get all subjects in this group
            group_subjects = Subject.objects.filter(_id__in=member_ids)
            
            # Check if all members have finished chat
            all_finished = all(subject.finished_chat for subject in group_subjects)
            
            if all_finished:
                logger.info(f"All members in group {group._id} have finished chat, marking group as finished")
                
                # Mark group as not chatting anymore
                group.chatting = False
                group.save(update_fields=['chatting'])
                
                # Record end chat time for this group
                record_end_chat_time(group._id)
                
                finished_groups.append(group)
                
        except Exception as e:
            logger.error(f"Error processing group {group._id} for finished chat check: {str(e)}")
            continue
    
    return finished_groups

def mark_inactive_users() -> List[Subject]:
    """
    Main function to find and process groups with inactive members.
    Returns a list of all processed users across all groups.
    """
    logger.info("Starting inactive user check")
    groups = find_groups_with_inactive_members()
    all_processed_users = []

    # Process each group with inactive members
    for group in groups:
        processed_users = process_inactive_members_in_group(group)
        all_processed_users.extend(processed_users)

    logger.info(f"Completed processing {len(all_processed_users)} inactive users: {all_processed_users} across {len(groups)} groups: {groups}")
    return all_processed_users

def find_groups_with_inactive_members() -> List[Group]:
    """
    Finds all active chat groups that have at least one inactive member.
    Returns a list of group objects that need to be processed.
    """
    logger.info("Finding groups with inactive members")

    # Find all active chatting groups
    active_chat_groups = Group.objects.filter(chatting=True)
    groups_with_inactive = []

    # Check each group for inactive members
    for group in active_chat_groups:
        member_ids = group.member_ids.get('subject_ids', [])
        if not member_ids:  # Skip groups with no members
            continue

        # Check if this group has any inactive members
        inactive_members = Subject.objects.filter(
            _id__in=member_ids,
            active=False,
            chatting=True
        )


        if inactive_members.exists():
            groups_with_inactive.append(group)

    logger.info(f"Found {len(groups_with_inactive)} groups: {groups_with_inactive} with inactive members")
    return groups_with_inactive

def process_inactive_members_in_group(group: Group) -> List[Subject]:
    """
    Processes all inactive members in a single group.
    Returns a list of processed user objects.
    """
    processed_users = []

    try:
        # Get member IDs from the group
        member_ids = group.member_ids.get('subject_ids', [])
        if not member_ids:
            return processed_users

        # Get all inactive members in this group
        inactive_members = Subject.objects.filter(
            _id__in=member_ids,
            active=False,
            chatting=True
        )

        logger.info(f"Group {group._id} has {len(inactive_members)} inactive members")

        for user in inactive_members:
            try:
                # Only process if user is still marked as chatting
                if user.chatting:
                    logger.info(f"Processing inactive user {user._id} in group {group._id}")

                    # Send notification to the group about this user
                    send_inactive_notification(group._id, user._id)

                    # Mark user as not chatting anymore
                    user.chatting = False
                    user.save(update_fields=['chatting'])
                    logger.info(f"Marked inactive user {user._id} as not chatting")

                    processed_users.append(user)

            except Exception as e:
                logger.error(f"Error processing inactive user {user._id}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error processing group {group._id}: {str(e)}")

    return processed_users

def send_inactive_notification(group_id: int, subject_id: int) -> None:
    """Sends a WebSocket notification when a user is marked as inactive."""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{group_id}",
            {
                "type": "chat_message",
                "message": {
                    "code": 132,  # Code for inactive user notification
                    "message": "Due to certain reasons, a group member has left the chat. However, the study will continue. Please click the button to proceed to the next survey."
                }
            }
        )
        logger.info(f"Sent inactive notification for subject {subject_id} in group {group_id}")
    except Exception as e:
        logger.error(f"Error sending inactive notification: {str(e)}")



@api_view(['POST'])
def pairing(request: HttpRequest) -> JsonResponse:
    """Pairs users into groups with different opinions on at least one shared statement."""

    try:
        subject_id = request.POST.get('subject_id', None)
        if subject_id is None:
            logger.info('Error: Missing subject_id')
            return JsonResponse({'success': False, 'message': 'Missing subject_id', 'has_capacity': False}, status=400)

        subject = Subject.objects.get(pk=subject_id)
        if subject.group_id != -1:
            group = Group.objects.get(pk=subject.group_id)
            group.refresh_from_db()
            logger.info("subject %s already in group %s", subject_id, group._id)
            if group.has_capacity and group.current_size < group.size:
                return JsonResponse({
                    'success': False,
                    'waiting_for_third_human': True,
                    'group_id': group._id,
                    'average_waiting_time': get_average_waiting_time()
                })
            return JsonResponse({
                'success': True,
                'group_id': group._id,
                'average_waiting_time': get_average_waiting_time()
            })

        # **Step 1: Check if an existing 2-person group needs a third participant**
        open_groups = Group.objects.filter(size=3, current_size=2, has_capacity=True)

        if open_groups:
            with transaction.atomic():
                group = Group.objects.select_for_update().filter(size=3, current_size=2, has_capacity=True).first()
                if group is None:
                    return JsonResponse({'success': False, 'message': 'Open group was filled by another request', 'average_waiting_time': get_average_waiting_time()})
                subject = Subject.objects.select_for_update().get(pk=subject_id)
                if subject.group_id != -1:
                    return JsonResponse({'success': False, 'message': 'Subject was assigned by another request', 'average_waiting_time': get_average_waiting_time()})
                # Add subject to the existing group
                group.member_ids['subject_ids'].append(subject._id)
                group.current_size += 1
                group.has_capacity = False  # Group is now full
                group.third_person_id = subject._id  # Mark this person as the third person
                logger.info("subject %s added to three-ppl group %s", subject_id, group._id)

                # Assign subject to this group
                subject.group_id = group._id
                subject.is_third_person = True  # Mark this subject as the third person
                group.random_third_person_prompt = random.choice([0, 1])
                subject.save()
                logger.info("subject %s as third person added to group %s", subject_id, group._id)

                # Since group is now full, assign avatar to subject
                assigned_avatars = assign_avatars_to_group(group)
                group.assigned_avatars = assigned_avatars
                group.save()
                logger.info("assigned avatars %s to group %s", assigned_avatars, group._id)
            return JsonResponse({
                'success': True,
                'group_id': group._id,
                'average_waiting_time': get_average_waiting_time()
            })

        # **Step 2: No 3-person group available, proceed with normal 2-person pairing**
        # Find all potential partners with opposing views on any statement
        potential_partners = []
        for partner in Subject.objects.filter(group_id=-1, ready_to_pair=True).exclude(_id=subject._id):
            different_opinions_index = get_different_opinions(subject, partner)
            if different_opinions_index is not None:
                potential_partners.append(partner)
                logger.info("subject %s added to potential partners list of subject %s", partner._id, subject_id)

        if not potential_partners:
            logger.info("no suitable partner found for subject %s", subject_id)
            return JsonResponse({'success': False, 'message': 'No suitable partner found','average_waiting_time': get_average_waiting_time()})

        # Randomly select one partner from those with opposing views
        random_match_partner = random.choice(potential_partners)
        logger.info("subject %s matched with subject %s", random_match_partner._id, subject_id)

        # Get the statements they disagree on for selecting chat topic
        different_opinions_index = get_different_opinions(subject, random_match_partner)
        logger.info("subject %s and subject %s disagree on statements %s", subject_id, random_match_partner._id, different_opinions_index)

        # **Step 3: Select a Statement for Discussion (Weighted Randomization)**
        statement_frequencies = get_statement_frequencies()
        available_statements = [idx for idx in different_opinions_index if idx in statement_frequencies]
        logger.info("available statements for discussion: %s", available_statements)
        if not available_statements:
            return JsonResponse({'success': False, 'message': 'No suitable statement found for discussion'})
        weights = [1 / (1 + statement_frequencies.get(idx, 0)) for idx in available_statements]
        chat_statement_idx = random.choices(available_statements, weights=weights)[0]
        logger.info("selected statement for discussion: %s", chat_statement_idx)

        # Assign `moderator_condition`
        # REAL: 50% chance for AI Moderator
        if subject.test == 'N':
            moderator_condition = random.choice([0,1])
            logger.info('Real moderator code: %s', moderator_condition)
        else:
            # TEST: Use fixed moderator code
            moderator_condition = subject.test_moderator_code
            logger.info('Test moderator code: %s', moderator_condition)
        # Assign `participant_condition` with equal probability
        # REAL: 2 human; 1 human + 1 Advocate AI; 1 human + 1 Dispute AI; 3 human
        if subject.test == 'N':
            participant_condition = random.choice([0,1,2,3])
            logger.info('Real participant code: %s', participant_condition)
        else:
            # TEST: Use fixed participant code
            participant_condition = subject.test_participant_code
            logger.info('Test participant code: %s', participant_condition)
        # **Step 4: Create a New Group**
        with transaction.atomic():
            subject = Subject.objects.select_for_update().get(pk=subject_id)
            random_match_partner = Subject.objects.select_for_update().get(pk=random_match_partner._id)
            if subject.group_id != -1 or random_match_partner.group_id != -1:
                return JsonResponse({'success': False, 'message': 'Pairing state changed; retry', 'average_waiting_time': get_average_waiting_time()})
            group = Group.objects.create(
                size=3 if participant_condition == 3 else 2,
                group_chat_statement_index=chat_statement_idx,
                group_moderator_condition=moderator_condition,
                group_participant_condition=participant_condition,
                current_size=0,
                current_turn=1
            )
            if participant_condition == 1 or participant_condition == 2:
                group.AI_participant_position = random.choice([0, 1])
                group.save(update_fields=['AI_participant_position'])
            logger.info('Group created with moderator condition: %s, participant condition: %s, AI participant position: %s, and chat statement index: %s', moderator_condition, participant_condition, group.AI_participant_position, chat_statement_idx)

            # Assign both users to the group
            group.member_ids['subject_ids'] = [subject._id, random_match_partner._id]
            group.current_size = 2
            assigned_avatars = None
            logger.info('Group %s member ids: %s', group._id, group.member_ids)
            # If the group needs a third member, keep it open
            if group.group_participant_condition == 3:
                group.has_capacity = True
                logger.info('Group %s has capacity and needs a third member', group._id)
            else:
                group.has_capacity = False  # Group is full
                logger.info('Group %s does not have capacity', group._id)
                # Since group is now full, assign avatar to subjects
                assigned_avatars = assign_avatars_to_group(group)


            group.save()

            # Update subjects
            subject.group_id = group._id
            random_match_partner.group_id = group._id
            logger.info('Subject %s and subject %s added to group %s', subject._id, random_match_partner._id, group._id)
            subject.save(update_fields=['group_id'])
            random_match_partner.save(update_fields=['group_id'])
            group.refresh_from_db()

            if assigned_avatars:
                group.assigned_avatars = assigned_avatars
                
                # If this is a group with AI participant, assign avatar for AI
                if group.group_participant_condition in [1, 2]:
                    try:
                        ai_avatar = assign_ai_participant_avatar(group)
                        group.assigned_avatars.append(ai_avatar)
                        logger.info('Added AI participant avatar %s to group %s', ai_avatar, group._id)
                    except Exception as e:
                        logger.error(f'Error assigning AI participant avatar: {str(e)}')
                        # Continue even if AI avatar assignment fails
                
                group.save()
                logger.info('Assigned avatars %s to group %s', group.assigned_avatars, group._id)
                return JsonResponse({
                    'success': True,
                    'group_id': group._id,
                    'average_waiting_time': get_average_waiting_time()
                })
        # if pair failed
        return JsonResponse({
            'success': False,
            'average_waiting_time': get_average_waiting_time()
        })

    except Subject.DoesNotExist:
        logger.info(f'Subject not found: {subject_id}')
        logger.error(f'Subject not found: {subject_id}')
        return JsonResponse({'success': False, 'message': 'Subject not found', 'has_capacity': False}, status=404)
    except Exception as e:
        logger.info(f'Error in pairing function: {str(e)}')
        logger.error(f'Error in pairing function: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'message': str(e), 'has_capacity': False}, status=500)

def get_average_waiting_time() -> float:
    try:
        time_records = TimeRecord.objects.filter(pair_end_time__isnull=False, pair_start_time__isnull=False)
        # print("REDIS_URL:", os.environ['REDIS_URL'])
        if not time_records.exists():
            logger.info('No time records found with valid pair_start_time and pair_end_time')
            return 10

        total_waiting_time = 0
        valid_records = 0

        for time_record in time_records:
            try:
                # Ensure both timestamps are valid
                if time_record.pair_end_time and time_record.pair_start_time:
                    # Calculate time difference in seconds
                    wait_time = (time_record.pair_end_time - time_record.pair_start_time).total_seconds()
                    # Only count positive and reasonable waiting times (less than 10 minutes)
                    if 0 <= wait_time < 600:
                        total_waiting_time += wait_time
                        valid_records += 1
            except Exception as e:
                logger.info(f'Error calculating waiting time for record {time_record._id}: {str(e)}')
                continue

        # Return average or default value
        if valid_records > 0:
            average = total_waiting_time / valid_records
            logger.info(f'Calculated average waiting time: {average} seconds from {valid_records} records')
            return average
        else:
            logger.info('No valid time records for calculation, returning default')
            return 10
    except Exception as e:
        logger.info(f'Error in get_average_waiting_time: {str(e)}')
        return 10

@api_view(['POST'])
def set_pipei(request: HttpRequest) -> JsonResponse:
    """Sets a subject's ready_to_pair status to True And record start pairing time."""
    subject_id = request.POST.get('subject_id', None)

    logger.info(f'Setting ready_to_pair to True for subject_id: {subject_id}')

    if subject_id is None:
        logger.info(f'Missing subject_id in set_pipei')
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
def set_pipei_end_time(request: HttpRequest) -> JsonResponse:
    """Sets a subject's ready_to_pair status to False And record end pairing time."""
    subject_id = request.POST.get('subject_id', None)

    if subject_id is None:
        logger.info(f'Missing subject_id in set_pipei_end_time')
        return JsonResponse({'success': False, 'message': 'Missing subject_id'}, status=400)

    try:
        time_record = TimeRecord.objects.get(subject_id=subject_id)
        time_record.pair_end_time = timezone.now()
        time_record.save()
        logger.info(f'End of Pairing time recorded for subject_id: {subject_id}')
        return JsonResponse({'success': True, 'message': 'Pairing time recorded'})
    except TimeRecord.DoesNotExist:
        logger.error(f'TimeRecord not found: {subject_id}')
        return JsonResponse({'success': False, 'message': 'TimeRecord not found'}, status=404)
    except Exception as e:
        logger.error(f'Error in set_pair_end_time function: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@api_view(['POST'])
def set_not_ready(request: HttpRequest) -> JsonResponse:
    """Sets a subject's ready_to_pair status to False And record end pairing time."""
    subject_id = request.POST.get('subject_id', None)

    if subject_id is None:
        logger.info(f'Missing subject_id in set_not_ready')
        return JsonResponse({'success': False, 'message': 'Missing subject_id'}, status=400)

    try:
        with transaction.atomic():
            subject = Subject.objects.select_for_update().get(pk=subject_id)
            subject.ready_to_pair = False
            if subject.group_id != -1:
                group = Group.objects.select_for_update().get(pk=subject.group_id)
                if group.has_capacity and not subject.chatting:
                    group.member_ids['subject_ids'] = [
                        int(id) for id in group.member_ids.get('subject_ids', [])
                        if int(id) != int(subject_id)
                    ]
                    group.activate_member_ids['subject_ids'] = [
                        int(id) for id in group.activate_member_ids.get('subject_ids', [])
                        if int(id) != int(subject_id)
                    ]
                    group.current_size = max(0, group.current_size - 1)
                    if group.current_size == 0:
                        group.has_capacity = False
                        group.is_activated = False
                    subject.group_id = -1
                    group.save(update_fields=['member_ids', 'activate_member_ids', 'current_size', 'has_capacity', 'is_activated'])
            subject.save()
        logger.info(f'Subject {subject_id} is not ready to pair')
        return JsonResponse({'success': True, 'message': 'Subject not ready to pair'})
    except Subject.DoesNotExist:
        logger.error(f'Subject not found: {subject_id}')
        return JsonResponse({'success': False, 'message': 'Subject not found'}, status=404)
    except Exception as e:
        logger.error(f'Error in set_not_ready_to_pair function: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)



def get_different_opinions(subject: Subject, partner: Subject) -> List[int]:
    """Returns all statement_ids where participants have opposing views."""
    different_opinions_index = []

    try:
        # Get PreDSurvey responses for both subjects
        survey1 = PreDSurvey.objects.get(subject_id=subject._id)
        survey2 = PreDSurvey.objects.get(subject_id=partner._id)

        responses1 = parse_json_field(survey1.responses, [])
        responses2 = parse_json_field(survey2.responses, [])
        # Map statement_id to agreement for both participants
        resp_dict1 = {item['statement_id']: item['agreement'] for item in responses1}
        resp_dict2 = {item['statement_id']: item['agreement'] for item in responses2}
        # Identify opposing views by statement_id
        for sid, agr1 in resp_dict1.items():
            agr2 = resp_dict2.get(sid)
            if agr2 is not None and agr1 * agr2 < 0:
                different_opinions_index.append(sid)
                logger.info(f"Statement {sid} has opposing views between subject {subject._id} and subject {partner._id}")
    except PreDSurvey.DoesNotExist:
        logger.info(f"PreDSurvey not found for subject {subject._id} or partner {partner._id}")
        return []
    except (ValueError, KeyError) as e:
        logger.info(f"Error in get_different_opinions: {e}")
    return different_opinions_index

def get_statement_frequencies() -> Dict[int, int]:
    """Counts how many times each statement has been selected for discussion and excludes those exceeding the threshold."""
    # Get all groups with a valid statement index
    groups = Group.objects.exclude(group_chat_statement_index=-1)
    if not groups.exists():
        logger.info("No groups found with valid chat statement index")
        return {idx: 0 for idx in range(6)}

    statement_counts = groups.values('group_chat_statement_index').annotate(count=Count('group_chat_statement_index'))
    count_dict = {idx: 0 for idx in range(6)}
    count_dict.update({entry['group_chat_statement_index']: entry['count'] for entry in statement_counts})

    # Determine dynamic threshold
    min_count = min(count_dict.values())
    max_count = max(count_dict.values())
    if min_count < 10:
        threshold = 10
        logger.info(f"Dynamic threshold set to {threshold} because min_count={min_count} and max_count={max_count}")
    elif min_count < 20:
        threshold = 20
        logger.info(f"Dynamic threshold set to {threshold} because min_count={min_count} and max_count={max_count}")
    elif min_count < 30:
        threshold = 30
        logger.info(f"Dynamic threshold set to {threshold} because min_count={min_count} and max_count={max_count}")
    elif min_count < 40:
        threshold = 40
        logger.info(f"Dynamic threshold set to {threshold} because min_count={min_count} and max_count={max_count}")
    else:
        logger.info("All policies reached the V2 maximum threshold of 40; no policy is available without protocol revision")
        return {}

    result = {idx: count for idx, count in count_dict.items() if count < threshold}
    logger.info(f"Statement frequencies: {result}")
    return result

def assign_ai_participant_avatar(group: Group) -> Dict[str, Any]:
    """Assigns a unique avatar to the AI participant in the group."""
    logger.info(f"Starting AI participant avatar assignment for group {group._id}")
    
    # Get all colors and animals
    all_colors = ['Red', 'Blue', 'Orange']
    all_animals = ['Tiger', 'Wolf', 'Elephant', 'Panda', 'Koala', 'Rabbit']
    
    # Get currently used colors and animals from group's assigned_avatars
    used_colors = set()
    used_animals = set()
    for avatar in group.assigned_avatars:
        used_colors.add(avatar['avatar_color'])
        used_animals.add(avatar['avatar_name'])
    
    # Get available colors and animals
    available_colors = [c for c in all_colors if c not in used_colors]
    available_animals = [a for a in all_animals if a not in used_animals]
    
    if not available_colors or not available_animals:
        logger.error(f"No available colors or animals for AI participant in group {group._id}")
        raise ValueError("No available avatars for AI participant")
    
    # Randomly select color and animal
    ai_color = random.choice(available_colors)
    ai_animal = random.choice(available_animals)
    
    # Set AI participant ID based on condition (1 = Advocating, 2 = Disputing)
    ai_participant_id = -3 if group.group_participant_condition == 1 else -4
    
    # Create avatar assignment for AI matching the expected format in ChatRoom.vue
    ai_avatar = {
        'subject_id': ai_participant_id,  # -3 for Advocating AI, -4 for Disputing AI
        'avatar_color': ai_color,         # Will be displayed in the chat room
        'avatar_name': ai_animal,         # Will be displayed in the chat room
        'is_ai': True                     # Additional flag for future use if needed
    }
    
    logger.info(f"Assigned AI participant avatar in group {group._id}: {ai_color} {ai_animal}")
    return ai_avatar

def assign_avatars_to_group(group: Group) -> List[Dict[str, Any]]:
    """Assigns unique avatars to all members of a group."""
    logger.info(f"Starting avatar assignment for group {group._id}")
    colors = ['Red', 'Blue', 'Orange']
    animals = ['Tiger', 'Wolf', 'Elephant', 'Panda', 'Koala', 'Rabbit']
    # colors = ['Purple', 'Green']
    # animals = ['Fox', 'Penguin']

    try:
        group_members = Subject.objects.filter(_id__in=group.member_ids['subject_ids'])

        # Shuffle to ensure randomness
        random.shuffle(colors)
        random.shuffle(animals)
        logger.info(f"Shuffled colors: {colors}")
        logger.info(f"Shuffled animals: {animals}")

        assigned_avatars = []
        for member in group_members:
            if colors and animals:
                color = colors.pop()
                animal = animals.pop()
                logger.info(f"Assigning to member {member._id}: {color} {animal}")
                member.avatar_color = color
                member.avatar_name = animal

                assigned_avatars.append({
                    'subject_id': member._id,
                    'avatar_color': color,
                    'avatar_name': animal
                })
                logger.info(f"Assigned avatar for member {member._id}: {color} {animal}")
                try:
                    with transaction.atomic():
                        member.save()
                        logger.info(f"Saved avatar for member {member._id}")

                        # Refresh and verify the update
                        member.refresh_from_db(fields=['avatar_color', 'avatar_name'])
                        logger.info(f"Verified update for member {member._id}: {member.avatar_color} {member.avatar_name}")

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
                logger.info(f"Recorded START chat time for subject {subject._id}: {time_record.start_chat_time}")
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
                logger.info(f"Recorded group END chat time for subject {subject._id}: {time_record.end_chat_time}")
                time_record.save(update_fields=['end_chat_time'])
    except Group.DoesNotExist:
        logger.error(f'Group {group_id} not found')
    except Exception as e:
        logger.error(f'Error recording end chat time: {str(e)}')

def record_end_chat_time_by_subject(subject_id: int) -> None:
    """Records the end time of a subject's chat session."""
    try:
        subject = Subject.objects.get(pk=subject_id)
        subject.chat_end_time = timezone.now()
        logger.info(f"Recorded subject END chat time for subject {subject_id}: {subject.chat_end_time}")
        subject.save(update_fields=['chat_end_time'])
    except Subject.DoesNotExist:
        logger.error(f'Subject not found: {subject_id}')
    except Exception as e:
        logger.error(f'Error recording end chat time: {str(e)}')

@api_view(['POST'])
def finish_chat(request: HttpRequest) -> JsonResponse:
    """Finish a chat session for a subject."""
    subject_id = request.POST.get('subject_id', None)
    if subject_id is None:
        logger.info(f'Missing subject_id in finish_chat')
        return JsonResponse({'success': False, 'message': 'Missing subject_id'}, status=400)
    try:
        subject = Subject.objects.get(pk=subject_id)
        subject.finished_chat = True
        subject.save()
        logger.info(f'Subject {subject_id} finished chat')
        record_end_chat_time_by_subject(subject_id)
        return JsonResponse({'success': True, 'message': 'Subject finished chat'}) 
    except Subject.DoesNotExist:
        logger.error(f'Subject {subject_id} not found')
        return JsonResponse({'success': False, 'message': 'Subject not found'}, status=404)
    except Exception as e:
        logger.error(f'Error finishing chat: {str(e)}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@api_view(['POST'])
def update_chat_status(request: HttpRequest) -> JsonResponse:
    """Update the 'chatting' status of a group and send welcome message if needed"""
    """ right now, this is only used for chatting = True"""
    try:
        group_id = request.POST.get('group_id')
        chatting = request.POST.get('chatting')

        if group_id is None or chatting is None:
            return JsonResponse({'error': 'Missing group_id or chatting field'}, status=400)

        logger.info(f"Updating chat status for group {group_id}: {chatting}")
        # Record start chat time if chat is starting
        if chatting:
            record_start_chat_time(group_id)
        else:
            record_end_chat_time(group_id)

        # Retrieve the group
        group = Group.objects.get(pk=group_id)
        group.chatting = chatting.lower() == 'true'
        group.save(update_fields=['chatting'])
        logger.info(f"Updated chat status for group {group_id}: {group.chatting}")

        # Update chatting status for all subjects in the group
        if chatting.lower() == 'true':
            subject_ids = group.member_ids.get('subject_ids', [])
            Subject.objects.filter(_id__in=subject_ids).update(chatting=chatting.lower() == 'true')
            logger.info(f"Updated chatting status for all subjects in group {group_id}: {group.chatting}")


        return JsonResponse({
            'message': 'Chat status updated successfully',
            'chatting': group.chatting
        })

    except Group.DoesNotExist:
        logger.error(f'Group {group_id} not found')
        return JsonResponse({'error': 'Group not found'}, status=404)
    except Exception as e:
        logger.error(f'Error updating chat status: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def update_system_message(request: HttpRequest) -> JsonResponse:
    """Store a custom GPT system prompt on the Group model."""
    group_id = request.data.get('group_id')
    text = request.data.get('system_message', '')
    try:
        g = Group.objects.get(pk=group_id)
        g.moderator_custom_system_message = text
        logger.info("custom_system_message updated: %s", g.moderator_custom_system_message)
        g.save()
        return JsonResponse({'ok': True})
    except Group.DoesNotExist:
        logger.error("Group %s not found", group_id)
        return JsonResponse({'ok': False, 'error': 'no such group'}, status=404)

@api_view(['GET'])
def get_system_message(request: HttpRequest) -> JsonResponse:
    """Retrieve the custom GPT system prompt for a group."""
    group_id = request.GET.get('group_id')
    try:
        group = Group.objects.get(pk=group_id)
        group.refresh_from_db()
        logger.info("custom_system_message retrieved: %s", group.moderator_custom_system_message)
        gpt = GPT(
                group_id=group_id,
                moderator_condition=group.group_moderator_condition,
                participant_condition=0
            )
        logger.info("gpt system_message: %s", gpt.get_system_message())
        return JsonResponse({'system_message': gpt.get_system_message()})
    except Group.DoesNotExist:
        logger.error("Group %s not found", group_id)
        return JsonResponse({'system_message': ''}, status=404)

def _broadcast_turn_update(group_id: int, current_turn: int) -> None:
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{group_id}",
        {
            "type": "chat_message",
            "message": {
                "code": 210,
                "current_turn": current_turn
            }
        }
    )


def record_message(subject_id: Optional[int] = None, group_id: Optional[int] = None, message: Optional[str] = None) -> Dict[str, Any]:
    """
    Records a message from a subject
    Args:
        subject_id: ID of the subject sending the message
        group_id: ID of the group the message belongs to
        message: The message content
    """
    try:
        subject_id = int(subject_id)
        group_id = int(group_id)
        message = message or ""
        should_generate_ai = False
        current_turn_str = "1"

        with transaction.atomic():
            group = Group.objects.select_for_update().get(pk=group_id)
            subject = Subject.objects.select_for_update().get(pk=subject_id)
            current_turn_str = str(group.current_turn)
            validation = validate_human_message(message, subject.test or "N")
            if not validation["accepted"]:
                invalid_record = MessageRecord.objects.create(
                    subject_id=subject_id,
                    group_id=group_id,
                    message=message,
                    turn_number=int(current_turn_str),
                    is_valid=False,
                    validation_status='invalid',
                    meaningful_word_count=validation["meaningful_word_count"],
                    validation_error=validation["message"]
                )
                return {
                    "success": False,
                    "error": "message_rejected_validation",
                    "message_record": {
                        "id": invalid_record._id,
                        "timestamp": invalid_record.time_stamp.isoformat(),
                        "turn_number": invalid_record.turn_number
                    },
                    **validation
                }
            if not subject.active:
                return {
                    "success": False,
                    "error": "inactive_terminate",
                    "message": "Inactive participants cannot submit chat messages."
                }

            message_record = MessageRecord.objects.create(
                subject_id=subject_id,
                group_id=group_id,
                message=message,
                turn_number=int(current_turn_str),
                is_valid=True,
                validation_status='valid',
                meaningful_word_count=validation["meaningful_word_count"]
            )
            logger.info("message saved: %s for subject %s in turn %s", message, subject_id, current_turn_str)

            if current_turn_str not in group.messages_turn:
                group.messages_turn[current_turn_str] = []
            if subject_id not in group.messages_turn[current_turn_str]:
                group.messages_turn[current_turn_str].append(subject_id)

            required = required_speaker_ids(group)
            current_turn_members = {int(id) for id in group.messages_turn[current_turn_str]}
            human_required = {id for id in required if id > 0}
            ai_required = {id for id in required if id < 0}
            should_generate_ai = human_required.issubset(current_turn_members) and (
                not ai_required or AI_TURN_PENDING_SENTINEL not in current_turn_members
            )
            if should_generate_ai and ai_required:
                group.messages_turn[current_turn_str].append(AI_TURN_PENDING_SENTINEL)
            group.save(update_fields=['messages_turn'])

        ai_speaker_ids: List[int] = []
        if should_generate_ai:
            ai_speaker_ids = send_turn_end_gpt_response(group_id, current_turn_str)

        turn_increased = False
        with transaction.atomic():
            group = Group.objects.select_for_update().get(pk=group_id)
            if str(group.current_turn) == current_turn_str:
                if current_turn_str not in group.messages_turn:
                    group.messages_turn[current_turn_str] = []
                group.messages_turn[current_turn_str] = [
                    int(id) for id in group.messages_turn[current_turn_str]
                    if int(id) != AI_TURN_PENDING_SENTINEL
                ]
                for ai_id in ai_speaker_ids:
                    if ai_id not in group.messages_turn[current_turn_str]:
                        group.messages_turn[current_turn_str].append(ai_id)

                required = required_speaker_ids(group)
                current_turn_members = {int(id) for id in group.messages_turn[current_turn_str]}
                if required.issubset(current_turn_members):
                    group.current_turn += 1
                    turn_increased = True
                    logger.info("Incrementing turn counter to %s", group.current_turn)
                group.save(update_fields=['messages_turn', 'current_turn'])
                if turn_increased:
                    _broadcast_turn_update(group_id, group.current_turn)

        return {
            "success": True,
            "turn_increased": turn_increased,
            "message_record": {
                "id": message_record._id,
                "timestamp": message_record.time_stamp.isoformat(),
                "turn_number": message_record.turn_number
            }
        }

    except Exception as e:
        logger.info('Error details: %s', str(e))
        logger.info('Group ID: %s', group_id)
        logger.info('Subject ID: %s', subject_id)
        logger.info('Message: %s', message)
        return {'success': False, 'error': 'server_unrecoverable_error', 'message': str(e)}

def send_turn_end_gpt_response(group_id: int, current_turn_str: str) -> List[int]:
    logger.info('Starting send_turn_end_gpt_response for group %s for turn %s', group_id, current_turn_str)
    ai_speaker_ids: List[int] = []
    # get group
    group = Group.objects.get(pk=group_id)

    # Get timestamp of the first message in the current turn
    first_message_timestamp = MessageRecord.objects.filter(
        group_id=group_id,
        turn_number=int(current_turn_str),
        is_valid=True
    ).values_list('time_stamp', flat=True).first()
    logger.info("first_message_timestamp in turn %s: %s", current_turn_str, first_message_timestamp)
    # Get messages from current turn
    current_message_records = MessageRecord.objects.filter(
        group_id=group_id,
        time_stamp__gte=first_message_timestamp,
        is_valid=True
    ).order_by('time_stamp')
    # Get messages from previous turns
    previous_message_records = MessageRecord.objects.filter(
        group_id=group_id,
        time_stamp__lt=first_message_timestamp,
        is_valid=True
    ).order_by('time_stamp')

    logger.info('Current messages in turn %s: %s', current_turn_str, current_message_records)
    logger.info('Previous messages in turn %s: %s', current_turn_str, previous_message_records)
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()
    try:
        # 1. First get participant AI response if condition requires it
        if group.group_participant_condition in [1, 2]:
            # Send typing notification: AI Participant started typing
            participant_id = -3 if group.group_participant_condition == 1 else -4
            
            # Get AI's assigned avatar from group
            ai_avatar = next((avatar for avatar in group.assigned_avatars if avatar['subject_id'] == participant_id), None)
            if not ai_avatar:
                logger.error(f"AI avatar not found for participant_id {participant_id} in group {group_id}")
                ai_avatar = {'avatar_name': 'AI Participant', 'avatar_color': ''}
            
            logger.info(f"Sending typing notification for AI Participant (avatar: {ai_avatar}) in turn {current_turn_str}")
            async_to_sync(channel_layer.group_send)(
                f"chat_{group_id}",
                {
                    'type': 'chat_message',
                    'message': {
                        'code': 203,
                        'typing_info': {
                            'subject_id': participant_id,
                            'avatar_name': ai_avatar['avatar_name']+ " (AI Participant)",
                            'avatar_color': ai_avatar['avatar_color'] ,
                            'is_typing': True
                        }
                    }
                }
            )
            participant_gpt = GPT(
                group_id=group_id,
                moderator_condition=0,  # Set to 0 to get only participant response
                participant_condition=group.group_participant_condition,
                AI_participant_position=group.AI_participant_position,
                current_message_records=format_message_records(current_message_records),
                previous_message_records=format_message_records(previous_message_records),
                turn_number=int(current_turn_str)
            )

            participant_gpt_response = participant_gpt.get_response()
            logger.info("participant_gpt_response: %s", participant_gpt_response)
            if participant_gpt_response and participant_gpt_response != "...":
                # Save participant AI response
                participant_id = -3 if group.group_participant_condition == 1 else -4
                gpt_participant_message = MessageRecord.objects.create(
                    subject_id=participant_id,
                    group_id=group_id,
                    message=participant_gpt_response,
                    turn_number=int(current_turn_str),
                    is_valid=True,
                    validation_status='valid'
                )
                logger.info("participant AI response saved: %s", participant_gpt_response)
                # Broadcast participant AI response first
                participant_gpt_response_response = json.loads(participant_gpt_response)['response']
                logger.info("broadcasting participant response content %s", participant_gpt_response_response)
                # Broadcast participant AI response with avatar info
                async_to_sync(channel_layer.group_send)(
                    f"chat_{group_id}",
                    {
                        'type': 'chat_message',
                        'message': {
                            "code": 201,
                            "message": {
                                "sender": {
                                    "subject_id": participant_id,
                                    "avatar_name": ai_avatar['avatar_name']+ " (AI Participant)",
                                    "avatar_color": ai_avatar['avatar_color'] ,
                                },
                                "content": participant_gpt_response_response,
                                "time_stamp": datetime.now().isoformat()
                            }
                        }
                    }
                )
                
                # Send typing notification: AI Participant stopped typing
                async_to_sync(channel_layer.group_send)(
                    f"chat_{group_id}",
                    {
                        "type": "chat_message",
                        "message": {
                            "code": 203,
                            "typing_info": {
                                "subject_id": participant_id,
                                "avatar_name": ai_avatar['avatar_name']+ " (AI Participant)",
                                "avatar_color": ai_avatar['avatar_color'] ,
                                "is_typing": False
                            }
                        }
                    }
                )
                # Add to current messages for moderator context
                current_message_records = list(current_message_records)
                current_message_records.append(gpt_participant_message)
                logger.info("adding gpt participant message")
                logger.info("current_message_records: %s", current_message_records)
                ai_speaker_ids.append(participant_id)
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
                            'avatar_name': "AI Moderator ",
                            'avatar_color': "",
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
                    turn_number=int(current_turn_str),
                    is_valid=True,
                    validation_status='valid'
                )
                logger.info("adding moderator response to MessageRecord")
                moderator_response_response = json.loads(moderator_response)['response']
                logger.info("broadcasting moderator response content %s", moderator_response_response)
                # Broadcast moderator response second
                async_to_sync(channel_layer.group_send)(
                    f"chat_{group_id}",
                    {
                        'type': 'chat_message',
                        'message': {
                            "code": 201,
                            "message": {
                                "sender": {
                                    "subject_id": -2,
                                    "avatar_name": "AI Moderator",
                                    "avatar_color": "",
                                },
                                "content": moderator_response_response,
                                "time_stamp": datetime.now().isoformat()
                            }
                        }
                    }
                )
                async_to_sync(channel_layer.group_send)(
                        f"chat_{group_id}",
                        {
                            "type": "chat_message",
                            "message": {
                                "code": 203,
                                "typing_info": {
                                    "subject_id": -2,
                                    "avatar_name": "AI Moderator",
                                    "avatar_color": "",
                                    "is_typing": False
                                }
                            }
                        }
                    )
                ai_speaker_ids.append(-2)
                

    except Exception as e:
        logger.info(f"Error in send_turn_end_gpt_response: %s", str(e))
        # You might want to log this error or handle it in a specific way
    return ai_speaker_ids


def format_message_records(message_records: Any) -> List[Dict[str, Any]]:
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
            if msg_record.subject_id == -2:  # AI Moderator
                formatted.append({
                    'content': msg_record.message,
                    'is_human': False,
                    'ai_role': get_ai_role(msg_record.subject_id),
                    'time_stamp': msg_record.time_stamp.timestamp()
                })
            else:  # AI Participant (-3 or -4)
                # Get the group to find AI's assigned avatar
                group = Group.objects.get(pk=msg_record.group_id)
                # "next" retrieves the first avatar in group.assigned_avatars where avatar['subject_id'] == msg_record.subject_id,
                # or returns None if no such avatar is found.
                ai_avatar = next((avatar for avatar in group.assigned_avatars 
                                if avatar['subject_id'] == msg_record.subject_id), None)
                
                if ai_avatar:
                    sender_name = f"{ai_avatar['avatar_color']} {ai_avatar['avatar_name']}" + " (AI Participant)"
                else:
                    sender_name = "AI Participant"
                    logger.error(f"AI avatar not found for participant_id {msg_record.subject_id} in group {msg_record.group_id}")
                
                formatted.append({
                    'content': msg_record.message,
                    'sender_name': sender_name,
                    'is_human': False,
                    'ai_role': get_ai_role(msg_record.subject_id),
                    'time_stamp': msg_record.time_stamp.timestamp()
                })
    logger.info("formatted message records: %s", formatted)
    return formatted

def get_ai_role(subject_id: int) -> str:
    """Get AI role based on subject ID"""
    if subject_id == -2:
        return "AI Moderator"
    elif subject_id == -3:
        return "Advocating AI Participant"
    elif subject_id == -4:
        return "Disputing AI Participant"
    return "AI"

def get_ai_subject_id(group: Group) -> int:
    """Get appropriate AI subject ID based on group conditions"""
    if group.group_moderator_condition == 1:
        return -2  # AI Moderator
    elif group.group_participant_condition == 1:
        return -3  # Advocating AI
    elif group.group_participant_condition == 2:
        return -4  # Disputing AI
    return -5  # Generic AI

def record_post_do_survey_submit_time(subject_id: int) -> None:
    time_record = TimeRecord.objects.get(subject_id=subject_id)
    time_record.PostDOSurvey_button_time = timezone.now()
    time_record.save()
    logger.info("PostDOSurvey_button_time updated for subject %s", subject_id)

@api_view(['POST'])
def post_do_survey(request: HttpRequest) -> JsonResponse:
    response_data = {}
    data = request.data  # Using request.data since we're sending json, not form data
    subject_id = data.get('subject_id', None)
    policy_responses = parse_json_field(data.get('policy_responses', []), [])
    conversation_quality = data.get('conversation_quality', None)
    conversation_responses = parse_json_field(data.get('conversation_responses', []), [])
    reciprocity_responses = parse_json_field(data.get('reciprocity_responses', []), [])

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
            logger.info("PostDOSurvey saved for subject %s", subject_id)

            response_data['success'] = True
            response_data['message'] = 'Survey saved successfully'
        except Exception as e:
            response_data['success'] = False
            response_data['message'] = f'Error saving survey: {str(e)}'
    else:
        response_data['success'] = False
        response_data['message'] = 'Missing subject_id'

    return JsonResponse(response_data)


def record_post_df_survey_submit_time(subject_id: int) -> None:
    time_record = TimeRecord.objects.get(subject_id=subject_id)
    time_record.PostDFSurvey_button_time = timezone.now()
    time_record.save()
    logger.info("PostDFSurvey_button_time updated for subject %s", subject_id)

@api_view(['POST'])
def post_df_survey(request: HttpRequest) -> JsonResponse:
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
            critical_thinking_responses=parse_json_field(data.get('critical_thinking_responses', []), []),
            used_ai_tool=data.get('used_ai_tool'),
            cost_responses=parse_json_field(data.get('cost_responses', []), [])
        )
        logger.info("PostDFSurvey created for subject %s", subject_id)

        # Add AI-specific responses if applicable
        if group.group_participant_condition > 0:  # Has AI participant
            survey.ai_participant_responses = parse_json_field(data.get('ai_participant_responses', []), [])
            logger.info("AI participant responses added for subject %s", subject_id)

        if group.group_moderator_condition == 1:  # Has AI moderator
            survey.ai_moderator_responses = parse_json_field(data.get('ai_moderator_responses', []), [])
            logger.info("AI moderator responses added for subject %s", subject_id)

        survey.save()
        logger.info("PostDFSurvey saved for subject %s", subject_id)

        # Mark subject as complete
        subject.is_complete = True
        subject.save()
        logger.info("Subject %s marked as complete", subject_id)

        response_data['success'] = True
        response_data['message'] = 'Survey saved successfully'

    except Subject.DoesNotExist:
        response_data['success'] = False
        response_data['message'] = 'Subject not found'
        logger.info("Subject %s not found in post_df_survey", subject_id)
    except Group.DoesNotExist:
        response_data['success'] = False
        response_data['message'] = 'Group not found'
        logger.info("Group %s not found in post_df_survey", subject_id)
    except Exception as e:
        response_data['success'] = False
        response_data['message'] = f'Error saving survey: {str(e)}'
        logger.info("Error saving survey: %s", str(e))
    logger.info("response_data: %s", response_data)
    return JsonResponse(response_data)



@api_view(['POST'])
def confirm_instructions(request: HttpRequest) -> JsonResponse:
    subject_id = request.POST.get('subject_id')
    group_id = request.POST.get('group_id')

    try:
        subject = Subject.objects.get(pk=subject_id)

        # Mark this subject as having confirmed instructions
        subject.confirmed_instructions = True
        subject.save()
        logger.info("Subject %s marked as confirmed instructions", subject_id)

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
        logger.info("Confirmation time recorded for subject %s", subject_id)

        # Notify via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{group_id}",
            {
                "type": "chat_message",
                "message": {
                    "code": 300,
                    "all_confirmed": all_confirmed
                }
            }
        )

        return JsonResponse({
            'success': True,
            'all_confirmed': all_confirmed
        })

    except (Subject.DoesNotExist, Group.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Subject or Group not found'
        })




@api_view(['POST'])
def Update_pre_discussion_survey(request: HttpRequest) -> JsonResponse:
    response_data = {}
    data = request.data
    subject_id = data.get('subject_id', None)
    suggestions = data.get('suggestions', '')
    responses = data.get('responses', [])

    if subject_id is not None:
        try:
            # Create survey record
            survey, created = PreDSurvey.objects.update_or_create(
                subject_id=subject_id,
                defaults={'responses': responses, 'suggestions': suggestions},

            )
            logger.info("PreDSurvey updated for subject %s", subject_id)

            time_record = TimeRecord.objects.get(subject_id=subject_id)
            time_record.PreDSurvey_button_time = timezone.now()
            time_record.save()
            logger.info("PreDSurvey_button_time updated for subject %s", subject_id)

            response_data['success'] = True
            response_data['message'] = 'Survey saved successfully'
        except Exception as e:
            response_data['success'] = False
            response_data['message'] = f'Error saving survey: {str(e)}'
            logger.info("Error saving survey: %s", str(e))
    else:
        response_data['success'] = False
        response_data['message'] = 'Missing subject_id'
        logger.info("Missing subject_id in Update_pre_discussion_survey")

    return JsonResponse(response_data)






@api_view(['POST'])
def get_group_member_agreements(request: HttpRequest) -> JsonResponse:
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
                responses = parse_json_field(survey.responses, [])
            except (PreDSurvey.DoesNotExist, ValueError, TypeError):
                responses = []
            agreement = None
            # build lookup and fetch agreement by statement_id
            if isinstance(responses, list):
                resp_dict = {item['statement_id']: item['agreement'] for item in responses}
                agreement = resp_dict.get(stmt_idx)
            logger.info("Agreement level of chat statement %s for subject %s: %s", stmt_idx, subject._id, agreement)
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
def terminate_participation(request: HttpRequest) -> JsonResponse:
    """Terminates a subject's participation in the study."""
    import logging
    import json
    from django.conf import settings
    import os
    from datetime import datetime

    # Set up logging
    log_dir = os.path.join(settings.BASE_DIR, 'server', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'termination_requests.log')

    # Configure logging to file
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    # Log the incoming request
    request_id = f"req_{int(datetime.now().timestamp() * 1000)}"
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')

    logging.info(f"[{request_id}] Received termination request. IP: {client_ip}, Headers: {dict(request.headers)}")

    subject_id = request.POST.get('subject_id', None)
    if subject_id is None:
        logging.error(f"[{request_id}] Missing subject_id in request")
        return JsonResponse({'success': False, 'message': 'Missing subject_id'}, status=400)

    logging.info(f"[{request_id}] Processing termination for subject_id: {subject_id}")

    try:
        with transaction.atomic():
            subject = Subject.objects.select_for_update().get(pk=subject_id)
            logging.info(f"[{request_id}] Found subject: {subject_id}, current active status: {subject.active}")

            if not subject.active and subject.status == 'inactive_terminate':
                logging.warning(f"[{request_id}] Subject {subject_id} was already inactive")
                return JsonResponse({'success': True, 'message': 'Subject was already inactive'})

            group_id = subject.group_id
            subject.active = False
            subject.chatting = False
            subject.status = 'inactive_terminate'
            subject.end_time = timezone.now()
            subject.save(update_fields=['active', 'chatting', 'status', 'end_time'])

            if group_id != -1:
                group = Group.objects.select_for_update().filter(pk=group_id).first()
                if group:
                    group.activate_member_ids['subject_ids'] = [
                        int(id) for id in group.activate_member_ids.get('subject_ids', [])
                        if int(id) != int(subject_id)
                    ]
                    group.save(update_fields=['activate_member_ids'])
        logging.info(f"[{request_id}] Successfully deactivated subject {subject_id}")

        return JsonResponse({'success': True, 'request_id': request_id})

    except Subject.DoesNotExist:
        logging.error(f"[{request_id}] Subject not found: {subject_id}")
        return JsonResponse({'success': False, 'message': 'Subject not found'}, status=404)
    except Exception as e:
        logging.error(f"[{request_id}] Error processing termination for {subject_id}: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@api_view(['POST'])
def client_logs(request: HttpRequest) -> JsonResponse:
    """
    Receives and stores client-side logs.
    Expected POST data:
    - logs: The log messages as a string
    - page: The page where the logs originated
    - timestamp: When the logs were sent
    """
    try:
        logs = request.POST.get('logs', '')
        page = request.POST.get('page', 'unknown')
        timestamp = request.POST.get('timestamp', '')

        if not logs:
            return JsonResponse({'success': False, 'message': 'No logs provided'}, status=400)

        # Save logs to file using our utility function
        from .logging_utils import save_client_logs
        success, message = save_client_logs({
            'logs': logs,
            'page': page,
            'timestamp': timestamp or datetime.now().isoformat()
        })

        if success:
            return JsonResponse({'success': True, 'message': message})
        else:
            return JsonResponse({'success': False, 'message': message}, status=500)

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@api_view(['POST'])
def submit_to_prolific(request: HttpRequest) -> JsonResponse:
    """Submits a subject's participation in the study to Prolific."""
    response_data = {}
    subject_id = request.POST.get('subject_id', None)
    status = request.POST.get('status', None)
    logger.info("submit_to_prolific: subject_id: %s, status: %s", subject_id, status)
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
        elif status == 'early_exit':
            code = EARLY_EXIT_CODE
        else:
            code = FAILED_ATTENTION_CODE
        # Update subject status and timestamps
        subject.end_time = timezone.now()
        subject.finished_at = timezone.now()  # Set finished_at timestamp
        subject.active = False
        subject.status = status
        if status == 'early_exit' or status == 'go_back_terminate' or status == 'inactive_terminate':
            reasons = request.POST.get('reasons', '[]')
            other = request.POST.get('other_reason', '')
            early_exit = EarlyExit.objects.create(subject_id=subject_id, status=status, early_exit_reasons=reasons, early_exit_other=other)
            early_exit.save()
        subject.save()
        prolific_url = f"https://app.prolific.co/submissions/complete?cc={code}"
        return JsonResponse({'success': True, 'prolific_url': prolific_url})
    raise PermissionDenied("Subject id is missing, please contact the requester.")

@api_view(['POST'])
def submit_end_feedback(request: HttpRequest) -> JsonResponse:
    """Receives and stores optional feedback from users at the end of the study."""
    subject_id = request.POST.get('subject_id', None)
    feedback_text = request.POST.get('feedback_text', '')
    if subject_id is None:
        return JsonResponse({'success': False, 'message': 'Missing subject_id'}, status=400)
    try:
        EndFeedback.objects.create(subject_id=subject_id, feedback_text=feedback_text)
        return JsonResponse({'success': True, 'message': 'Feedback submitted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@api_view(['POST'])
def check_finished_groups(request: HttpRequest) -> JsonResponse:
    """Manually trigger check for groups where all members have finished chat."""
    try:
        finished_groups = mark_finished_chat_groups()
        group_ids = [group._id for group in finished_groups]
        return JsonResponse({
            'success': True, 
            'message': f'Checked all active groups, marked {len(finished_groups)} as finished',
            'finished_group_ids': group_ids
        })
    except Exception as e:
        logger.error(f'Error in manual finished groups check: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@api_view(['POST'])
def updateAIDemograSurvey(request: HttpRequest) -> JsonResponse:
    response_data = {}
    subject_id = request.POST.get('subject_id', None)
    ai_tool_usage_frequency = request.POST.get('aiToolUsageFrequency', None)
    ai_attitude_selection = request.POST.get('aiAttitudeSelection', None)
    ai_in_music = request.POST.get('aiInMusic', None)
    ai_in_email = request.POST.get('aiInEmail', None)
    ai_in_home_devices = request.POST.get('aiInHomeDevices', None)
    ai_mental_capacity_responses = request.POST.get('aiMentalCapacityResponses', None)

    logger.info("AI survey response loaded for subject_id: %s", subject_id)
    
    # Validate required fields
    if not all([
        subject_id,
        ai_tool_usage_frequency,
        ai_attitude_selection,
        ai_in_music,
        ai_in_email,
        ai_in_home_devices,
        ai_mental_capacity_responses
    ]):
        logger.error("AI survey submission failed: Missing required fields")
        response_data['success'] = False
        response_data['message'] = 'Please complete all required fields'
        return JsonResponse(response_data, status=400)

    try:
        # Validate mental capacity responses
        mental_capacity_responses = json.loads(ai_mental_capacity_responses)
        if not isinstance(mental_capacity_responses, list) or len(mental_capacity_responses) != 6 or any(r is None for r in mental_capacity_responses):
            logger.error("AI survey submission failed: Invalid mental capacity responses format")
            response_data['success'] = False
            response_data['message'] = 'Invalid mental capacity responses'
            return JsonResponse(response_data, status=400)

        # Create AI survey record
        survey = AIDemograSurvey.objects.create(
            subject_id=subject_id,
            ai_tool_usage_frequency=ai_tool_usage_frequency,
            ai_attitude_selection=ai_attitude_selection,
            ai_in_music=ai_in_music,
            ai_in_email=ai_in_email,
            ai_in_home_devices=ai_in_home_devices,
            ai_mental_capacity_responses=ai_mental_capacity_responses
        )
        logger.info("AI survey record created for subject_id: %s", subject_id)

        # Update time record
        time_record = TimeRecord.objects.get(subject_id=subject_id)
        time_record.DemograSurvey_button_time = timezone.now()
        time_record.save()
        logger.info("AI survey time record updated for subject_id: %s", subject_id)

        response_data['success'] = True
        response_data['message'] = 'Survey saved successfully'
        return JsonResponse(response_data)
    except json.JSONDecodeError:
        logger.error("AI survey submission failed: Invalid JSON format for mental capacity responses", exc_info=True)
        response_data['success'] = False
        response_data['message'] = 'Invalid response format'
        return JsonResponse(response_data, status=400)
    except Exception as e:
        logger.error("AI survey record creation failed for subject_id: %s, error: %s", subject_id, str(e), exc_info=True)
        response_data['success'] = False
        response_data['message'] = str(e)
        return JsonResponse(response_data, status=500)

@api_view(['POST'])
def submit_video_quiz(request: HttpRequest) -> JsonResponse:
    """Save video quiz response"""
    response_data = {}
    data = request.POST
    subject_id = data.get('subject_id')
    answer = data.get('answer')

    logger.info("Received video quiz submission for subject %s with answer: %s", subject_id, answer)

    if subject_id is None or answer is None:
        logger.error("Missing required fields in video quiz submission. subject_id: %s, answer: %s", subject_id, answer)
        return JsonResponse({
            'success': False,
            'error': 'Missing required fields'
        }, status=400)

    try:
        # Check if subject exists
        if not Subject.objects.filter(_id=subject_id).exists():
            logger.error("Subject %s not found for video quiz submission", subject_id)
            return JsonResponse({
                'success': False,
                'error': 'Subject not found'
            }, status=404)

        # Create quiz response record
        quiz_response = VideoQuizResponse.objects.create(
            subject_id=subject_id,
            answer=answer
        )
        logger.info("Video quiz response saved successfully for subject %s", subject_id)

        response_data['success'] = True
        response_data['message'] = 'Quiz response saved successfully'
        return JsonResponse(response_data, status=200)

    except Exception as e:
        logger.error("Error saving video quiz response for subject %s: %s", subject_id, str(e), exc_info=True)
        response_data['success'] = False
        response_data['error'] = f'Error saving quiz response: {str(e)}'
        return JsonResponse(response_data, status=500)
