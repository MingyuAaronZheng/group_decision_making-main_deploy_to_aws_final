from django.urls import path
from . import views

urlpatterns = [
    # Auth & Setup
    path('create_subject', views.create_subject, name='create_subject'),
    path('heartbeat', views.heartbeat, name='heartbeat'),
    
    # Demographic Survey
    path('updateDemograSurvey', views.updateDemograSurvey, name='updateDemograSurvey'),

    # Pre-Discussion
    path('Update_pre_discussion_survey', views.Update_pre_discussion_survey, name='Update_pre_discussion_survey'),
    
    # Termination
    path('terminate_participation', views.terminate_participation, name='terminate_participation'),
] 