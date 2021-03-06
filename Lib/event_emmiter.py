"""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Purpose: in this event_emitter module for sending email
author:  Sachin Shrikant Jadhav
since :  25-09-2019
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

"""

from django.core.mail import EmailMultiAlternatives

from django.conf import settings
from pymitter import EventEmitter

email_event = EventEmitter()


@email_event.on("account_activate_event")
def email_for_account_activate(message, recipient_list):
    """

    :param message: here we passing message for mail
    :param recipient_list: here we passing receiver mail
    :return:this function send the email

    """
    email_from = settings.EMAIL_HOST_USER
    subject = 'Thank you for registering to our site'
    # send_mail(subject, message, email_from, recipient_list)
    msg = EmailMultiAlternatives(subject=subject, from_email=email_from,
                                 to=recipient_list, body=message)
    msg.attach_alternative(message, "text/html")
    msg.send()


@email_event.on("reset_password_event")
def email_for_reset_password(message, recipient_list):
    """
    :param message: here we passing message for mail
    :param recipient_list: here we passing receiver mail
    :return:this function send the email
    """
    email_from = settings.EMAIL_HOST_USER
    subject = 'Reset your password'
    # send_mail(subject, message, email_from, recipient_list)
    msg = EmailMultiAlternatives(subject=subject, from_email=email_from,
                                 to=recipient_list, body=message)
    msg.attach_alternative(message, "text/html")
    msg.send()


@email_event.on("reminder_event")
def email_for_reset_password(message, recipient_list):
    """
    :param message: here we passing message for mail
    :param recipient_list: here we passing receiver mail
    :return:this function send the email
    """
    email_from = settings.EMAIL_HOST_USER
    subject = 'reminder for you'
    # send_mail(subject, message, email_from, recipient_list)
    msg = EmailMultiAlternatives(subject=subject, from_email=email_from,
                                 to=recipient_list, body=message)
    msg.attach_alternative(message, "text/html")
    msg.send()
