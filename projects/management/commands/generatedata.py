from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    def handle(self, *args, **options):
        call_command('flush')
        call_command('loaddata', 'interests.json')
        call_command('generateusers', 300)
        call_command('generateprojects', 50)
        call_command('generateratings', 2000)
        self.stdout.write(self.style.SUCCESS(f'Generated all data'))
