from celery import shared_task
from django.core.mail import EmailMultiAlternatives

@shared_task
def send_async_email(subject, recipient_email, text_content, html_content):
    """
    Sends an email asynchronously using Celery.
    """
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=None, # Uses DEFAULT_FROM_EMAIL from settings
        to=[recipient_email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
