from rest_framework.permissions import BasePermission


class UserPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ['update', 'partial_update']:
            return request.user.is_authenticated and request.user == obj
        return request.user.is_authenticated

    def has_permission(self, request, view):
        return request.user.is_authenticated


class ProjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ['retrieve', 'checkpoints', 'participants', 'rate']:
            return request.user.is_authenticated
        return request.user.is_authenticated and obj.creator == request.user

    def has_permission(self, request, view):
        return request.user.is_authenticated


class ApplicationPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action == 'accept':
            return request.user.is_authenticated and obj.vacancy.project.creator == request.user
        return request.user.is_authenticated and (
                obj.applicant == request.user or obj.vacancy.project.creator == request.user)

    def has_permission(self, request, view):
        return request.user.is_authenticated


class ParticipantPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        check = request.user.is_authenticated
        if view.action in ['update', 'partial_update', 'applications']:
            return check and obj.project.creator == request.user
        if view.action == 'clear':
            return check and (obj.participant == request.user or obj.project.creator == request.user)
        return check

    def has_permission(self, request, view):
        return request.user.is_authenticated


class CheckpointPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve':
            return request.user.is_authenticated
        return request.user.is_authenticated and obj.project.creator == request.user

    def has_permission(self, request, view):
        return request.user.is_authenticated


class NotificationPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and obj.user == request.user

    def has_permission(self, request, view):
        return request.user.is_authenticated
