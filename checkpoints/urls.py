from django.urls import path

from checkpoints import views

app_name = 'checkpoints'

urlpatterns = [
    path('', views.CheckpointListView.as_view(), name='checkpoints_list')
]
