from django.test import TestCase, RequestFactory
from experiment.models import Subject, Group, PreDSurvey
from experiment.views import get_group_member_agreement_levels

class GetGroupMemberAgreementLevelsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Create test group
        self.group = Group.objects.create(_id='test_group', group_chat_statement_index=0)
        # Create test subjects
        self.subject1 = Subject.objects.create(_id='subject1', group_id='test_group', avatar_name='Alice', avatar_color='red')
        self.subject2 = Subject.objects.create(_id='subject2', group_id='test_group', avatar_name='Bob', avatar_color='blue')
        # Create pre-discussion surveys
        PreDSurvey.objects.create(subject_id='subject1', responses=[{'agreement': 5}])
        PreDSurvey.objects.create(subject_id='subject2', responses=[{'agreement': 3}])

    def test_get_group_member_agreement_levels(self):
        # Call the view function
        response = get_group_member_agreement_levels('test_group')
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(len(response.json()['responses']), 2)
        # Check if responses contain expected avatar info and agreement levels
        expected_responses = [
            {'red Alice': 5},
            {'blue Bob': 3}
        ]
        self.assertEqual(response.json()['responses'], expected_responses)

    def test_get_group_member_agreement_levels_no_surveys(self):
        # Delete pre-discussion surveys
        PreDSurvey.objects.all().delete()
        # Call the view function
        response = get_group_member_agreement_levels('test_group')
        # Check the response
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['message'], 'No pre-discussion surveys found for group members')
