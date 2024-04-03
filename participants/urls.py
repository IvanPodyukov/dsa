from django.urls import path

from participants import views

app_name = 'participants'

urlpatterns = [
    path('<pk>/applications/', views.ParticipantApplicationsListView.as_view(),
         name='participant_applications_list'),
    path('<pk>/confirm-clear/', views.ParticipantConfirmClearView.as_view(),
         name='confirm_clear_participant'),
    path('<pk>/clear/', views.ParticipantClearView.as_view(),
         name='clear_participant'),
    path('<pk>/submit/', views.ParticipantSubmitView.as_view(), name='participant_submit'),
    path('<pk>/withdraw/', views.ParticipantWithdrawView.as_view(), name='participant_withdraw'),
    path('', views.MyParticipationsListView.as_view(), name='my_participations')
]
