from django.urls import path
from . import views
from .views import signup_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.login_view, name='login'),
    path("Dashbord2/", views.Dashbord2, name="Dashbord2"),
    path("setting/", views.setting, name="setting"),
    path("document/", views.document, name="document"),
    path("delete_file/<int:file_id>/", views.delete_file, name="delete_file"),
    path("nominee_setup/", views.nominee_setup, name="nominee_setup"),
    path("delete_nominee/<int:nominee_id>/", views.delete_nominee, name="delete_nominee"),
    path("security/", views.security, name="security"),
    path("verify_otp", views.verify_otp, name="verify_otp"),
    path("send_email_otp/", views.send_email_otp, name="send_email_otp"),
    path("sign_up/", signup_view, name="sign_up"),
    path("secure/", views.secure, name="secure"),  # New path for secure view
    path("edit_nominee/<int:nominee_id>/", views.edit_nominee, name="edit_nominee"),
    path("login_activity/", views.login_activity, name="login_activity"),
    path("change-password/", 
         auth_views.PasswordChangeView.as_view(
             template_name='Vault/change_password.html',
             success_url = '/change-password/done/'
         ), 
         name='change_password'),
    path('change-password/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='Vault/change_password_done.html'
         ), 
         name='password_change_done'),

    path("assign_to_nominee/<int:nominee_id>/", views.assign_to_nominee, name="assign_to_nominee"),
    path("logout/", views.log_out, name="logout"),
]
