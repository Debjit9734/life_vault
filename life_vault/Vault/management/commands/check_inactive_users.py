# check_inactive_users.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from Vault.models import User, UserProfile, Nominee, UploadedFile, SecureVaultItem
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import os

class Command(BaseCommand):
    help = 'Checks for inactive users and sends documents to nominees'
    
    def handle(self, *args, **options):
        users = User.objects.filter(is_active=True)
        now = timezone.now()
        
        for user in users:
            try:
                profile = UserProfile.objects.get(user=user)
                inactive_minutes = (now - profile.last_activity).total_seconds() // 60
                
                if inactive_minutes >= profile.account_timeout_minutes:
                    # Safely get email count (handles missing field)
                    try:
                        email_count = profile.inactivity_email_count
                    except AttributeError:
                        email_count = 0
                    
                    if email_count < 2:
                        self.stdout.write(f"Processing inactive user: {user.username} (email count: {email_count})")
                        self.send_to_nominees(user, profile)
            except UserProfile.DoesNotExist:
                continue
        self.stdout.write("Inactive users check completed")

    def send_to_nominees(self, user, profile):
        nominees = Nominee.objects.filter(user=user, notifications=True)
        now = timezone.now()
        
        for nominee in nominees:
            documents = nominee.accessible_files.all()
            vault_items = nominee.accessible_vault_items.all()
            
            if not documents.exists() and not vault_items.exists():
                continue
                
            # Calculate timeout period
            total_minutes = profile.account_timeout_minutes
            if total_minutes < 60:
                timeout_str = f"{total_minutes} minutes"
            elif total_minutes < 1440:
                timeout_str = f"{total_minutes // 60} hours"
            else:
                timeout_str = f"{total_minutes // 1440} days"
            
            context = {
                'user': user,
                'nominee': nominee,
                'documents': documents,
                'vault_items': vault_items,
                'timeout_str': timeout_str
            }
            
            # Create email
            subject = f"Important: Access to {user.username}'s LifeVault"
            text_content = render_to_string('Vault/email/nominee_access.txt', context)
            html_content = render_to_string('Vault/email/nominee_access.html', context)
            
            email = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [nominee.email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Attach documents
            for document in documents:
                file_path = document.file.path
                if os.path.exists(file_path):
                    try:
                        file_name = os.path.basename(file_path)
                        content_type = self.get_content_type(file_path)
                        
                        with open(file_path, 'rb') as file:
                            email.attach(file_name, file.read(), content_type)
                    except Exception as e:
                        self.stdout.write(f"Attachment error: {str(e)}")
            
            try:
                email.send()
                self.stdout.write(f"Sent email to {nominee.email}")
                
                # Update profile - handle case where fields might not exist
                try:
                    profile.inactivity_email_count += 1
                except AttributeError:
                    # If field doesn't exist, create it temporarily
                    profile.inactivity_email_count = 1
                    
                profile.last_inactivity_email = now
                profile.save()
                
            except Exception as e:
                self.stdout.write(f"Email failed: {str(e)}")

    def get_content_type(self, file_path):
        """Determine MIME type based on file extension"""
        extension = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain',
            '.zip': 'application/zip'
        }
        return mime_types.get(extension, 'application/octet-stream')