# management/commands/test_inactivity.py
from django.core.management.base import BaseCommand
from Vault.management.commands.check_inactive_users import Command as CheckCommand

class Command(BaseCommand):
    help = 'Test inactivity feature immediately'
    
    def handle(self, *args, **options):
        # Run the check immediately
        CheckCommand().handle()
        self.stdout.write("Inactivity check completed")