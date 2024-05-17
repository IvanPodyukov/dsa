from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    def handle(self, *args, **options):
        call_command('generateusers', 300)
        call_command('generateprojects', 500)
        call_command('generateratings', 2000)
        call_command('generateapplications', 1000)
        self.stdout.write(self.style.SUCCESS(f'Generated all data'))
