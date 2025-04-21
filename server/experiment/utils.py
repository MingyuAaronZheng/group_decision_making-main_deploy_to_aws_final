from django.http import JsonResponse
from .models import Subject, PreDSurvey, Group
import logging
import json

logger = logging.getLogger(__name__)

def get_group_member_agreement_levels(group_id):
    """Get group's pre-discussion responses with avatar info for gpt.py to generate system prompt"""
    try:
        # Get group members with their avatars
        group_members = Subject.objects.filter(group_id=group_id).values('_id', 'avatar_name', 'avatar_color')
        group = Group.objects.get(_id=group_id)
        chat_statement_index = group.group_chat_statement_index
        # Collect pre-discussion responses with avatar info
        combined_responses = {}
        for member in group_members:
            try:
                pre_survey = PreDSurvey.objects.get(subject_id=member['_id'])
                # Parse responses if it's a string
                if isinstance(pre_survey.responses, str):
                    try:
                        pre_survey.responses = json.loads(pre_survey.responses)
                    except json.JSONDecodeError:
                        logger.error(f'Failed to parse pre_survey.responses as JSON: {pre_survey.responses}')
                        continue
                if not isinstance(pre_survey.responses, list):
                    logger.error(f'pre_survey.responses is not a list: {pre_survey.responses}')
                    continue
                if chat_statement_index >= len(pre_survey.responses):
                    logger.error(f'chat_statement_index {chat_statement_index} is out of range for responses of length {len(pre_survey.responses)}')
                    continue
                response = pre_survey.responses[chat_statement_index]
                if not isinstance(response, dict):
                    logger.error(f'response at index {chat_statement_index} is not a dict: {response}')
                    continue
                agreement = response.get('agreement')
                combined_responses[member['avatar_color'] + ' ' + member['avatar_name']] = agreement
            except PreDSurvey.DoesNotExist:
                logger.warning(f'No pre-discussion survey found for subject {member["_id"]}')
                continue

        if not combined_responses:
            return JsonResponse({
                'success': False,
                'message': 'No pre-discussion surveys found for group members'
            }, status=404)

        return combined_responses
    except Exception as e:
        logger.exception(f'Error in get_group_member_agreement_levels: {e}')
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
