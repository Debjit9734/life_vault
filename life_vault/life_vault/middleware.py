from django.utils import timezone
from Vault.models import UserProfile


class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
    


# middleware.py
from django.utils import timezone
from Vault.models import UserProfile

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
             UserProfile.objects.update_or_create(
                user=request.user,
                defaults={'last_activity': timezone.now(),
                          'inactivity_email_count': 0 
                          }
                
            )
        return response