from django.urls import path

from notifications import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notifications_list'),
    path('read/', views.ReadAllNotificationsView.as_view(), name='read_all_notifications'),
    path('unread/', views.UnreadAllNotificationsView.as_view(), name='unread_all_notifications'),
    path('<pk>/read/', views.ReadNotificationView.as_view(), name='read_notification'),
    path('<pk>/unread/', views.UnreadNotificationView.as_view(), name='unread_notification'),
    path('clear/', views.ClearAllNotificationsView.as_view(), name='clear_all_notifications'),
    path('<pk>/clear/', views.ClearNotificationView.as_view(), name='clear_notification')
]
