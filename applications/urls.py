from django.urls import path

from applications import views

app_name = 'applications'

urlpatterns = [
    path('<pk>/accept/', views.ApplicationAcceptView.as_view(),
         name='application_accept'),
    path('<pk>/reject/', views.ApplicationRejectView.as_view(),
         name='application_reject'),
    path('', views.ApplicationListView.as_view(), name='applications_list'),
]
