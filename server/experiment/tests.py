from unittest.mock import patch

from django.test import Client, TestCase
from django.utils import timezone

from experiment.consumers import mark_ready_to_end
from experiment.models import GPTIntermediate, Group, MessageRecord, PreDSurvey, Subject, TimeRecord
from experiment.views import record_message


def create_subject(worker_id, **overrides):
    defaults = {
        'worker_id': worker_id,
        'study_id': 'study',
        'session_id': f'{worker_id}-session',
        'ready_to_pair': True,
        'test': 'Y',
        'test_moderator_code': 0,
        'test_participant_code': 0,
        'test_policy_number': 1,
        'test_turn_number': 4,
        'avatar_name': worker_id,
        'avatar_color': 'Blue',
    }
    defaults.update(overrides)
    return Subject.objects.create(**defaults)


def create_pre_survey(subject, agreement):
    PreDSurvey.objects.create(
        subject_id=subject._id,
        responses=[
            {'statement_id': 0, 'agreement': agreement, 'importance': 4},
            {'statement_id': 1, 'agreement': agreement, 'importance': 4},
            {'statement_id': 2, 'agreement': agreement, 'importance': 4},
            {'statement_id': 3, 'agreement': agreement, 'importance': 4},
            {'statement_id': 4, 'agreement': agreement, 'importance': 4},
            {'statement_id': 5, 'agreement': agreement, 'importance': 4},
        ]
    )


class MainProtocolTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_create_subject_requires_all_prolific_identifiers(self):
        response = self.client.post('/ccw/api/create_subject', {
            'worker_id': 'worker-only',
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'invalid_prolific_identity')
        self.assertEqual(Subject.objects.count(), 0)

    def test_human_only_turn_advancement_broadcasts_after_commit(self):
        subject_1 = create_subject('h1')
        subject_2 = create_subject('h2')
        group = Group.objects.create(
            size=2,
            current_size=2,
            has_capacity=False,
            group_participant_condition=0,
            group_moderator_condition=0,
            member_ids={'subject_ids': [subject_1._id, subject_2._id]},
            current_turn=1,
        )
        message_1 = 'alpha beta gamma delta speaker one'
        message_2 = 'alpha beta gamma delta speaker two'

        with patch('experiment.views._broadcast_turn_update') as broadcast, \
                patch('experiment.views.send_turn_end_gpt_response') as send_ai:
            result_1 = record_message(subject_1._id, group._id, message_1)
            group.refresh_from_db()
            self.assertTrue(result_1['success'])
            self.assertFalse(result_1['turn_increased'])
            self.assertEqual(group.current_turn, 1)
            broadcast.assert_not_called()
            send_ai.assert_not_called()

            result_2 = record_message(subject_2._id, group._id, message_2)
            group.refresh_from_db()
            self.assertTrue(result_2['success'])
            self.assertTrue(result_2['turn_increased'])
            self.assertEqual(result_2['new_turn'], 2)
            self.assertEqual(group.current_turn, 2)
            self.assertEqual(set(group.messages_turn['1']), {subject_1._id, subject_2._id})
            broadcast.assert_called_once_with(group._id, 2)
            send_ai.assert_not_called()

    def test_invalid_message_is_persisted_without_turn_advancement(self):
        subject_1 = create_subject('invalid-h1')
        subject_2 = create_subject('invalid-h2')
        group = Group.objects.create(
            size=2,
            current_size=2,
            has_capacity=False,
            group_participant_condition=0,
            group_moderator_condition=0,
            member_ids={'subject_ids': [subject_1._id, subject_2._id]},
            current_turn=1,
        )

        with patch('experiment.views._broadcast_turn_update') as broadcast:
            result = record_message(subject_1._id, group._id, 'um um um just like')

        group.refresh_from_db()
        record = MessageRecord.objects.get()
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'message_rejected_validation')
        self.assertFalse(record.is_valid)
        self.assertEqual(record.validation_status, 'invalid')
        self.assertEqual(group.current_turn, 1)
        self.assertEqual(group.messages_turn, {})
        broadcast.assert_not_called()

    def test_ai_speaker_ids_count_before_turn_advancement(self):
        subject_1 = create_subject('ai-h1')
        subject_2 = create_subject('ai-h2')
        group = Group.objects.create(
            size=2,
            current_size=2,
            has_capacity=False,
            group_participant_condition=1,
            group_moderator_condition=1,
            member_ids={'subject_ids': [subject_1._id, subject_2._id]},
            current_turn=1,
        )

        with patch('experiment.views.send_turn_end_gpt_response', return_value=[-3, -2]) as send_ai, \
                patch('experiment.views._broadcast_turn_update') as broadcast:
            result_1 = record_message(subject_1._id, group._id, 'alpha beta gamma delta human one')
            result_2 = record_message(subject_2._id, group._id, 'alpha beta gamma delta human two')

        group.refresh_from_db()
        self.assertTrue(result_1['success'])
        self.assertFalse(result_1['turn_increased'])
        self.assertTrue(result_2['success'])
        self.assertTrue(result_2['turn_increased'])
        self.assertEqual(result_2['new_turn'], 2)
        self.assertEqual(group.current_turn, 2)
        self.assertEqual(set(group.messages_turn['1']), {subject_1._id, subject_2._id, -3, -2})
        send_ai.assert_called_once_with(group._id, '1')
        broadcast.assert_called_once_with(group._id, 2)

    def test_ready_to_end_returns_fresh_all_ready_state(self):
        subjects = [create_subject(f'h{i}') for i in range(1, 4)]
        group = Group.objects.create(
            size=3,
            current_size=3,
            has_capacity=False,
            group_participant_condition=3,
            member_ids={'subject_ids': [subject._id for subject in subjects]},
        )

        first = mark_ready_to_end(group._id, subjects[0]._id)
        second = mark_ready_to_end(group._id, subjects[1]._id)
        third = mark_ready_to_end(group._id, subjects[2]._id)

        self.assertFalse(first['all_ready'])
        self.assertFalse(second['all_ready'])
        self.assertTrue(third['all_ready'])
        self.assertEqual(set(third['ready_members']), {subject._id for subject in subjects})

    def test_three_human_pairing_preserves_pending_group_until_third_arrives(self):
        subject_1 = create_subject('p1', test_participant_code=3)
        subject_2 = create_subject('p2', test_participant_code=3)
        create_pre_survey(subject_1, 3)
        create_pre_survey(subject_2, -3)

        response_1 = self.client.post('/ccw/api/pairing', {'subject_id': subject_1._id})
        response_2 = self.client.post('/ccw/api/pairing', {'subject_id': subject_2._id})
        data = response_1.json() if response_1.json().get('group_id') else response_2.json()
        group = Group.objects.get(pk=data['group_id'])

        self.assertEqual(group.current_size, 2)
        self.assertTrue(group.has_capacity)
        self.assertEqual(group.third_person_id, -1)

        subject_3 = create_subject('p3', test_participant_code=3)
        create_pre_survey(subject_3, -2)
        response_3 = self.client.post('/ccw/api/pairing', {'subject_id': subject_3._id})
        self.assertTrue(response_3.json()['success'])
        group.refresh_from_db()
        self.assertEqual(group.current_size, 3)
        self.assertFalse(group.has_capacity)
        self.assertEqual(group.third_person_id, subject_3._id)

    def test_test_mode_third_human_does_not_fill_different_condition_open_group(self):
        stale_group = Group.objects.create(
            size=3,
            current_size=2,
            has_capacity=True,
            group_participant_condition=3,
            group_moderator_condition=0,
            member_ids={'subject_ids': [101, 102]},
        )
        subject = create_subject('different-condition-third', test_moderator_code=1, test_participant_code=3)

        response = self.client.post('/ccw/api/pairing', {'subject_id': subject._id})

        self.assertFalse(response.json().get('success'))
        stale_group.refresh_from_db()
        self.assertEqual(stale_group.current_size, 2)
        self.assertEqual(stale_group.third_person_id, -1)

    def test_confirm_instructions_requires_all_three_humans(self):
        subjects = [create_subject(f'c{i}') for i in range(1, 4)]
        group = Group.objects.create(
            size=3,
            current_size=3,
            has_capacity=False,
            group_participant_condition=3,
            member_ids={'subject_ids': [subject._id for subject in subjects]},
        )
        for subject in subjects:
            TimeRecord.objects.create(subject_id=subject._id, StarEntrance_button_time=timezone.now())

        with patch('experiment.views._send_chat_group_message'):
            first = self.client.post('/ccw/api/confirm_instructions', {'subject_id': subjects[0]._id, 'group_id': group._id})
            second = self.client.post('/ccw/api/confirm_instructions', {'subject_id': subjects[1]._id, 'group_id': group._id})
            third = self.client.post('/ccw/api/confirm_instructions', {'subject_id': subjects[2]._id, 'group_id': group._id})

        self.assertFalse(first.json()['all_confirmed'])
        self.assertFalse(second.json()['all_confirmed'])
        self.assertTrue(third.json()['all_confirmed'])

    def test_gpt_intermediate_accepts_audit_fields(self):
        record = GPTIntermediate.objects.create(
            group_id=1,
            turn_number=1,
            model='gpt-4o-2024-08-06',
            prompt_version='prd-dvtp-v1',
            system_prompt='system',
            input_message_set={'messages': []},
            raw_response='{"response": "raw"}',
            parsed_response={'response': 'parsed'},
            retry_count=1,
            error_metadata={'error': 'none'},
        )

        record.refresh_from_db()
        self.assertEqual(record.model, 'gpt-4o-2024-08-06')
        self.assertEqual(record.parsed_response['response'], 'parsed')
