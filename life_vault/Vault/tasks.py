# tasks.py
from celery import shared_task
from .management.commands.check_inactive_users import Command as CheckCommand

@shared_task
def check_inactive_users_task():
    CheckCommand().handle()