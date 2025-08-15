from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from .forms import FileUploadForm
from .models import UploadedFile
import os
from django.shortcuts import get_object_or_404
from .forms import NomineeForm
from .models import Nominee
from django.http import JsonResponse
from django.core.mail import send_mail
from .models import EmailOTPDevice
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from .forms import SecureVaultForm
from .models import SecureVaultItem
import json
from .models import LoginActivity
from django.utils import timezone
from .forms import CustomUserCreationForm
from .forms import NomineeAssignmentForm
from django.db.models import Q
from .forms import UserProfileForm
from .models import UserProfile
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout as auth_logout


# Create your views here.
#@login_required(login_url='login')

@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('Dashbord2')

    if request.method == 'POST':


        email = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user is not None:
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('send_email_otp')  # Redirect to the OTP verification page

        else:
            print("Invalid Login credentials")
            return HttpResponse("Invalid login credentials")
    else:
        template = loader.get_template('Vault/login.html')
            
        return HttpResponse(template.render({}, request))
    

# Add these imports at the top
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

# Create a signup view

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('send_email_otp')  # Redirect to OTP verification
        else:
            # Handle form errors
            return render(request, 'Vault/sign_up.html', {'form': form})
    else:
        form = CustomUserCreationForm()
        return render(request, 'Vault/sign_up.html', {'form': form})

@never_cache
def Dashbord2(request):
    doc_count = UploadedFile.objects.filter(user=request.user).count()
    nominee_count = Nominee.objects.filter(user=request.user).count()
    nominees_all = Nominee.objects.filter(user=request.user)
    recent_uploads = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')[:3]
    recent_nominees = Nominee.objects.filter(user=request.user).order_by('-created_at')[:3]
    doc_percentage = min(100, (doc_count / 5) * 100) if doc_count > 0 else 0
    nominee_percentage = min(100, (nominee_count / 5) * 100) if nominee_count > 0 else 0
    doc_offset = 326.56 * (1 - doc_percentage / 100)
    nominee_offset = 326.56 * (1 - nominee_percentage / 100)
    context = {
        'user': request.user,
        'doc_count': doc_count,
        'nominee_count': nominee_count,
        'nominees_all': nominees_all,
        'recent_uploads': recent_uploads,
        'recent_nominees': recent_nominees,
        'doc_offset': doc_offset,
        'nominee_offset': nominee_offset,
    }
    return render(request, 'Vault/Dashbord2.html', context)



@login_required
@never_cache
def setting(request):
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('setting')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'user': request.user,
        'form': form,
        'profile_picture': profile.profile_picture.url if profile.profile_picture else None
    }
    
    return render(request, 'Vault/setting.html', context)


@never_cache
def document(request):
    user_files = UploadedFile.objects.filter(
        Q(user=request.user) | 
        Q(accessible_nominees_files__user=request.user)
    ).distinct().order_by('-uploaded_at')

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save(commit=False)
            file.user = request.user
            file_name = file.file.name
            file.file_type = os.path.splitext(file_name)[1].lower()
            file.file_size = f"{file.file.size / 1024:.2f} KB"
            file.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            return redirect('document')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = FileUploadForm()
    
    user_files = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    
    return render(request, 'Vault/document.html', {
        'form': form,
        'files': user_files
    })



@login_required
@never_cache
def delete_file(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    file.file.delete()  # Delete the file from storage
    file.delete()       # Delete the database record
    return redirect('document')

# views.py
from .forms import NomineeForm
from .models import Nominee

@never_cache
def nominee_setup(request):
    if request.method == 'POST':
        form = NomineeForm(request.POST)
        if form.is_valid():
            nominee = form.save(commit=False)
            nominee.user = request.user
            nominee.save()
            return redirect('nominee_setup')
    else:
        form = NomineeForm()
    
    nominees = Nominee.objects.filter(user=request.user)
    return render(request, 'Vault/nominee_setup.html', {
        'form': form,
        'nominees': nominees
    })

@never_cache
def delete_nominee(request, nominee_id):
    nominee = get_object_or_404(Nominee, id=nominee_id, user=request.user)
    nominee.delete()
    return redirect('nominee_setup')    


@never_cache
def security(request):
    mapping = {
            '1 Minute': 1,
            '1 Hour': 60,
            '1 Day': 1440,
            '1 Week': 10080,
            '1 Month': 43200
        }
    if request.method == 'POST' and 'set_policy' in request.POST:
        duration = request.POST.get('duration')
        
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.account_timeout_minutes = mapping.get(duration, 43200)
        profile.save()
        messages.success(request, 'Account timeout policy updated!')
        return redirect('security')
    # Get distinct trusted devices (last 5 unique devices)

    try:
        profile = UserProfile.objects.get(user=request.user)
        current_timeout = profile.account_timeout_minutes
    except UserProfile.DoesNotExist:
        current_timeout = 43200  # Default to 1 month if profile doesn't exist
    
    # Create reverse mapping for display
    timeout_mapping = {v: k for k, v in mapping.items()}
    current_policy = timeout_mapping.get(current_timeout, '1 Month')
    
    # Get trusted devices
    trusted_devices = LoginActivity.objects.filter(
        user=request.user
    ).values('device').distinct().order_by('-timestamp')[:5]
    
    context = {
        'user': request.user,
        'trusted_devices': trusted_devices,
        'current_policy': current_policy
    }
    return render(request, 'Vault/security.html', context)


@login_required
@never_cache
def send_email_otp(request):
    device, _ = EmailOTPDevice.objects.get_or_create(user=request.user, name='default')
    code = device.generate_otp()

    send_mail(
        'Your OTP Code',
        f'Your OTP code is: {code}',
        settings.DEFAULT_FROM_EMAIL,
        [request.user.email],
        fail_silently=False,
    )
    return redirect('verify_otp')

@login_required
@never_cache
def verify_otp(request):
    if request.method == 'POST':
        token = request.POST.get('otp')
        device = EmailOTPDevice.objects.filter(user=request.user, name='default').first()
        if device and device.verify_token(token):
            request.session['otp_verified'] = True
            return redirect('Dashbord2')  # success page
        messages.error(request, 'Invalid OTP')
    return render(request, 'Vault/verify_otp.html', {'user': request.user})

@never_cache
def email_otp_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.session.get('otp_verified'):
            return view_func(request, *args, **kwargs)
        return redirect('send_email_otp')
    return wrapper

# views.py
@never_cache
def edit_nominee(request, nominee_id):
    nominee = get_object_or_404(Nominee, id=nominee_id, user=request.user)
    if request.method == 'POST':
        form = NomineeForm(request.POST, instance=nominee)
        if form.is_valid():
            form.save()
            return redirect('nominee_setup')
    else:
        form = NomineeForm(instance=nominee)
    
    return render(request, 'Vault/edit_nominee.html', {'form': form, 'nominee': nominee})

@never_cache
def secure(request):
    vault_items = SecureVaultItem.objects.filter(Q(user=request.user) | Q(accessible_nominees_vault_items__user=request.user)).distinct().order_by('-updated_at')
    
    if request.method == 'POST':
        item_type = request.POST.get('item_type')
        name = request.POST.get('item_name')
        form_data = {}
        if item_type == 'password':
            form_data = {
                'service_name': request.POST.get('service_name'),
                'username': request.POST.get('username'),
                'password': request.POST.get('password'),
                'url': request.POST.get('url'),
                'notes': request.POST.get('notes'),
            }
        elif item_type == 'id':
            form_data = {
                'document_name': request.POST.get('document_name'),
                'document_type': request.POST.get('document_type'),
                'document_number': request.POST.get('document_number'),
                'expiration_date': request.POST.get('expiration_date'),
                'issuing_authority': request.POST.get('issuing_authority'),
                'additional_notes': request.POST.get('additional_notes'),
            }
        elif item_type == 'crypto':
            form_data = {
                'wallet_name': request.POST.get('wallet_name'),
                'crypto_type': request.POST.get('crypto_type'),
                'public_address': request.POST.get('public_address'),
                'private_key': request.POST.get('private_key'),
                'additional_notes': request.POST.get('additional_notes'),
            }
        elif item_type == 'bank':
            form_data = {
                'account_name': request.POST.get('account_name'),
                'bank_name': request.POST.get('bank_name'),
                'account_number': request.POST.get('account_number'),
                'routing_number': request.POST.get('routing_number'),
                'holder_name': request.POST.get('holder_name'),
                'additional_notes': request.POST.get('additional_notes'),
            }
        elif item_type == 'atm':
            form_data = {
                'card_nickname': request.POST.get('card_nickname'),
                'card_number': request.POST.get('card_number'),
                'expiration_date': request.POST.get('expiration_date'),
                'cvv': request.POST.get('cvv'),
                'pin': request.POST.get('pin'),
                'additional_notes': request.POST.get('additional_notes'),
            }
        elif item_type == 'other':
            form_data = {
                'item_name': request.POST.get('item_name'),
                'confidential_details': request.POST.get('confidential_details'),
                'additional_notes': request.POST.get('additional_notes'),
            }
        SecureVaultItem.objects.create(
            user=request.user,
            item_type=item_type,
            name=name,  # Will need to update HTML
            data=json.dumps(form_data)
        )
        
        messages.success(request, 'Item saved successfully!')
        return redirect('secure')

    return render(request, 'Vault/secure.html', {'user': request.user,'vault_items':vault_items})


# views.py
@login_required
@never_cache
def delete_vault_item(request, item_id):
    item = get_object_or_404(SecureVaultItem, id=item_id, user=request.user)
    item.delete()
    messages.success(request, 'Item deleted successfully!')
    return redirect('secure')


@login_required
@never_cache
def login_activity(request):
    # Get login activities for current user
    activities = LoginActivity.objects.filter(user=request.user).order_by('-timestamp')[:5]
    
    activity_list = []
    for activity in activities:
        # Calculate relative time
        time_diff = timezone.now() - activity.timestamp
        if time_diff.days > 0:
            time_str = f"{time_diff.days} days ago"
        elif time_diff.seconds >= 3600:
            hours = time_diff.seconds // 3600
            time_str = f"{hours} hours ago"
        else:
            minutes = time_diff.seconds // 60
            time_str = f"{minutes} minutes ago"
        
        # Map device to icon
        device_icon = "fas fa-desktop"
        if "mobile" in activity.device.lower():
            device_icon = "fas fa-mobile-alt"
        elif "tablet" in activity.device.lower():
            device_icon = "fas fa-tablet-alt"
        
        device_display = activity.device if activity.device else "Unknown Device"
        location_display = activity.location if activity.location else "Location not available"


        activity_list.append({
            'device': activity.device,
            'device_icon': device_icon,
            'location': activity.location,
            'time': time_str,
            'status': 'Successful'
        })
    
    return JsonResponse(activity_list, safe=False)

@login_required
@never_cache
def assign_to_nominee(request, nominee_id):
    nominee = get_object_or_404(Nominee, id=nominee_id, user=request.user)
   
    if request.method == 'POST':
        form = NomineeAssignmentForm(request.POST, user=request.user)
        if form.is_valid():
            selected_documents = form.cleaned_data['documents']
            selected_vault_items = form.cleaned_data['vault_items']

            nominee.accessible_files.set(selected_documents)
            nominee.accessible_vault_items.set(selected_vault_items)

            return redirect('nominee_setup')
        else:
            print("Form Errors:", form.errors) 

    else:
        form = NomineeAssignmentForm(
            user=request.user,
            initial={
                'documents': nominee.accessible_files.all(),
                'vault_items': nominee.accessible_vault_items.all()
            }
        )

    documents_exist = UploadedFile.objects.filter(user=request.user).exists()
    vault_items_exist = SecureVaultItem.objects.filter(user=request.user).exists()
    return render(request, 'vault/assign_to_nominee.html', {
        'form': form,
        'nominee': nominee,
        'documents_exist': documents_exist,
        'vault_items_exist': vault_items_exist,
        'form_errors': form.errors
    })


# Also ensure you have your other relevant views, e.g.:
@login_required
@never_cache
def document_list(request):
    documents = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    vault_items = SecureVaultItem.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'vault/document_list.html', {'documents': documents, 'vault_items': vault_items})

@login_required
@never_cache
def document_detail(request, pk):
    document = get_object_or_404(UploadedFile, pk=pk, user=request.user)
    
    return render(request, 'vault/document_detail.html', {'document': document})


def log_out(request):
    auth_logout(request)
    return redirect('login')  # Redirect to login page after logout


def test_email(request):
    send_mail(
        'Test Email',
        'This is a test email from LifeVault.',
        settings.DEFAULT_FROM_EMAIL,
        [request.user.email])
    return HttpResponse("Test email sent successfully.")


