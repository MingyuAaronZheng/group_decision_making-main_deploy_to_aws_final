# type: ignore
from django.urls import path
from . import views

urlpatterns = [
    # Auth & Setup
    path('create_subject', views.create_subject, name='create_subject'),
    # Custom GPT system message endpoints
    path('update_system_message', views.update_system_message, name='update_system_message'),
    path('get_system_message', views.get_system_message, name='get_system_message'),

    # Demographic Survey
    path('updateAIDemograSurvey', views.updateAIDemograSurvey, name='updateAIDemograSurvey'),
    path('update_normal_DemograSurvey', views.update_normal_DemograSurvey, name='update_normal_DemograSurvey'),

    # Pre-Discussion
    path('Update_pre_discussion_survey', views.Update_pre_discussion_survey, name='Update_pre_discussion_survey'),
    path('confirm_instructions', views.confirm_instructions, name='confirm_instructions'),
    path('pairing', views.pairing, name='pairing'),
    path('set_pipei', views.set_pipei, name='set_pipei'),
    path('set-not-ready', views.set_not_ready, name='set_not_ready'),
    path('set_pipei_end_time', views.set_pipei_end_time, name='set_pipei_end_time'),

    # Discussion
    path('update_chat_status', views.update_chat_status, name='update_chat_status'),
    path('record_message', views.record_message, name='record_message'),
    path('finish_chat', views.finish_chat, name='finish_chat'),
    path('check_finished_groups', views.check_finished_groups, name='check_finished_groups'),

    # Post-Discussion
    path('post_do_survey', views.post_do_survey, name='post_do_survey'),
    path('post_df_survey', views.post_df_survey, name='post_df_survey'),
    path('submit_video_quiz/', views.submit_video_quiz, name='submit_video_quiz'),
    path('get_group_member_agreements', views.get_group_member_agreements, name='get_group_member_agreements'),

    # Activity termination
    path('terminate_participation', views.terminate_participation, name='terminate_participation'),
    path('client_logs', views.client_logs, name='client_logs'),

    # Debug endpoints
    path('submit_to_prolific', views.submit_to_prolific, name='submit_to_prolific'),

    # Feedback endpoint
    # The first string in the path() function ('submit_feedback') defines the URL pattern that will be matched.
    # For example, this will match requests to /submit_feedback on your server.
    # The "name" argument assigns a unique identifier to this URL pattern for use in reverse lookups and templates.
    path('submit_feedback', views.submit_end_feedback, name='submit_feedback'),

    # Health check for ALB
    path('health/', views.health_check, name='health'),
    
]