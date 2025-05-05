"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from django.conf.urls import url
from django.conf.urls.static import static
from experiment import views
from django.conf import settings

urlpatterns = [
    path('', views.home_view),
    path('ccw/admin/', admin.site.urls),

    # Include all experiment URLs
    path('ccw/api/', include('experiment.urls')),

    # Legacy URLs that haven't been moved yet
    path('ccw/api/create_subject', views.create_subject),
    path('ccw/api/update_demogra_survey', views.updateDemograSurvey),
    path('ccw/api/get_subject_info', views.get_subject_info),
    path('ccw/api/Update_pre_discussion_survey', views.Update_pre_discussion_survey),
    path('ccw/api/update_chat_status', views.update_chat_status),
    path('ccw/api/post_do_survey', views.post_do_survey),
    path('ccw/api/post_df_survey', views.post_df_survey),
    path('ccw/api/get_group_current_turn', views.get_group_current_turn),
    path('ccw/api/get_group_member_agreements', views.get_group_member_agreements),
    path('ccw/api/terminate_participation', views.terminate_participation),
    path('ccw/api/set_pair_end_time', views.set_pair_end_time),
    path('ccw/api/set_not_ready_to_pair', views.set_not_ready_to_pair),
    path('ccw/api/submit_to_prolific', views.submit_to_prolific)

]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# server/urls.py
from django.http import HttpResponse
urlpatterns += [
    path('ws/healthz', lambda r: HttpResponse('ok')),
]
