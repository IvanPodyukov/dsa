from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from notifications.mixins import NotificationIsForUserRequiredMixin
from notifications.models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    paginate_by = 5
    context_object_name = 'notifications'
    template_name = 'notifications/list.html'

    def get_queryset(self):
        return self.request.user.notifications.all().order_by('-timestamp')


class ReadAllNotificationsView(LoginRequiredMixin, View):
    def post(self, request):
        notifications = request.user.notifications.all()
        notifications.update(unread=False)
        return redirect(reverse('notifications:notifications_list'))


class UnreadAllNotificationsView(LoginRequiredMixin, View):
    def post(self, request):
        notifications = request.user.notifications.all()
        notifications.update(unread=True)
        return redirect(reverse('notifications:notifications_list'))


class ReadNotificationView(LoginRequiredMixin, NotificationIsForUserRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)
        notification.unread = False
        notification.save()
        return redirect(reverse('notifications:notifications_list'))


class UnreadNotificationView(LoginRequiredMixin, NotificationIsForUserRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)
        notification.unread = True
        notification.save()
        return redirect(reverse('notifications:notifications_list'))


class ClearAllNotificationsView(LoginRequiredMixin, View):
    def post(self, request):
        notifications = request.user.notifications.all()
        notifications.delete()
        return redirect(reverse('notifications:notifications_list'))


class ClearNotificationView(LoginRequiredMixin, NotificationIsForUserRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)
        notification.delete()
        return redirect(reverse('notifications:notifications_list'))
