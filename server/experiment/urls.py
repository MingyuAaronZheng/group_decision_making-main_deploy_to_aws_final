from django.urls import path
from . import views

urlpatterns = [
    # Auth & Setup
    path('create_subject', views.create_subject, name='create_subject'),

    # Demographic Survey
    path('updateDemograSurvey', views.updateDemograSurvey, name='updateDemograSurvey'),

    # Pre-Discussion
    path('Update_pre_discussion_survey', views.Update_pre_discussion_survey, name='Update_pre_discussion_survey'),
    path('get_group_current_turn', views.get_group_current_turn, name='get_group_current_turn'),
    path('confirm_instructions', views.confirm_instructions, name='confirm_instructions'),
    path('pairing', views.pairing, name='pairing'),
    path('set_ready_to_pair', views.set_ready_to_pair, name='set_ready_to_pair'),
    path('set_not_ready_to_pair', views.set_not_ready_to_pair, name='set_not_ready_to_pair'),

    # Discussion
    path('update_chat_status', views.update_chat_status, name='update_chat_status'),
    path('record_message', views.record_message, name='record_message'),

    # Post-Discussion
    path('post_do_survey', views.post_do_survey, name='post_do_survey'),
    path('post_df_survey', views.post_df_survey, name='post_df_survey'),
    path('get_group_member_agreements', views.get_group_member_agreements, name='get_group_member_agreements'),

    # activity check
    path('heartbeat', views.heartbeat, name='heartbeat'),
    path('terminate_participation', views.terminate_participation, name='terminate_participation'),

    # Debug endpoints
    path('debug_pre_discussion_surveys', views.debug_pre_discussion_surveys, name='debug_pre_discussion_surveys'),
    path('submit_to_prolific', views.submit_to_prolific, name='submit_to_prolific')
]