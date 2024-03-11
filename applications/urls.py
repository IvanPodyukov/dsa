from django.urls import path

from applications import views

app_name = 'applications'

urlpatterns = [
    path('', views.ApplicationListView.as_view(), name='applications_list')
]
