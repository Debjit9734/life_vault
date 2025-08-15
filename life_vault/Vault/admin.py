from django.contrib import admin
from .models import LoginActivity
from .models import UploadedFile, Nominee
admin.site.register(LoginActivity)

# Register your models here.
@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'user', 'uploaded_at', 'file_type', 'file_size')
    search_fields = ('file', 'user__username')
    list_filter = ('file_type', 'uploaded_at')
    filter_horizontal = ('nominees',)


@admin.register(Nominee)
class NomineeAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'notifications')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('user',)
   
    #filter_horizontal = ('accessible_files', 'accessible_vault_items')

