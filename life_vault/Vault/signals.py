# signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
import user_agents
import requests
import json
from .models import LoginActivity

@receiver(user_logged_in)
def track_login(sender, request, user, **kwargs):
    # Get IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip_address = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    
    # Clean up IP address
    if ip_address:
        ip_address = ip_address.strip()
    
    # Device/browser detection code (keep existing)
    user_agent = user_agents.parse(request.META.get('HTTP_USER_AGENT', ''))
    # Extract device and browser information
    device = f"{user_agent.device.family} {user_agent.device.brand or ''} {user_agent.device.model or ''}".strip()
    browser = f"{user_agent.browser.family} {user_agent.browser.version_string or ''}".strip()
    
    # Enhanced location detection
    location = "Unknown"
    
    # Check for local/private IPs first
    if ip_address:
        if (ip_address.startswith('192.168.') or 
            ip_address.startswith('10.') or 
            ip_address.startswith('172.') or 
            ip_address == '127.0.0.1' or 
            ip_address == 'localhost'):
            location = "Local Network"
        else:
            # Try multiple geolocation services
            location = get_location_from_ip(ip_address)
    
    # Create login record
    LoginActivity.objects.create(
        user=user,
        ip_address=ip_address,
        device=device,
        browser=browser,
        location=location
    )

def get_location_from_ip(ip_address):
    """Try multiple geolocation services with fallbacks"""
    
    # Service 1: ip-api.com (free tier)
    try:
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}?fields=status,message,country,city,regionName,isp',
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'success':
            location_parts = []
            if data.get('city'):
                location_parts.append(data['city'])
            if data.get('regionName'):
                location_parts.append(data['regionName'])
            if data.get('country'):
                location_parts.append(data['country'])
            
            if location_parts:
                return ', '.join(location_parts)
            elif data.get('isp'):
                return f"{data['isp']} Network"
                
    except requests.exceptions.RequestException as e:
        print(f"ip-api.com failed: {e}")
    except (ValueError, KeyError) as e:
        print(f"ip-api.com response parsing failed: {e}")
    
    # Service 2: ipapi.co (backup service)
    try:
        response = requests.get(
            f'https://ipapi.co/{ip_address}/json/',
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get('error'):
            location_parts = []
            if data.get('city'):
                location_parts.append(data['city'])
            if data.get('region'):
                location_parts.append(data['region'])
            if data.get('country_name'):
                location_parts.append(data['country_name'])
            
            if location_parts:
                return ', '.join(location_parts)
                
    except requests.exceptions.RequestException as e:
        print(f"ipapi.co failed: {e}")
    except (ValueError, KeyError) as e:
        print(f"ipapi.co response parsing failed: {e}")
    
    # Fallback: Return IP address if all services fail
    return f"IP: {ip_address}"
