from notifications.models import Notification


def create_notifications_application_accept(application):
    participant = application.vacancy
    text = f'Ваша заявка на роль {participant.title} в проекте {participant.project.title} одобрена'
    Notification.objects.create(user=application.applicant, text=text)
    remaining_applications = participant.applications.exclude(id=application.id)
    text = f'Ваша заявка на роль {participant.title} в проекте {participant.project.title} отклонена'
    for application in remaining_applications:
        Notification.objects.create(user=application.applicant, text=text)


def create_notification_application_reject(application):
    participant = application.vacancy
    text = f'Ваша заявка на роль {participant.title} в проекте {participant.project.title} отклонена'
    Notification.objects.create(user=application.applicant, text=text)


def create_notification_participant_clear(participant):
    text = f'Вы были удалены с роли {participant.title} в проекте {participant.project.title}'
    Notification.objects.create(user=participant.participant, text=text)
