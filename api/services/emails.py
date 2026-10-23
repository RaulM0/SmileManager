from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def send_patient_email(*, patient, user, subject, message):
    text=f'{message}\n\nAtentamente,\nClínica Dental Sonrisa Perfecta 🦷'
    html=render_to_string('emails/mensaje_paciente.html',{'asunto':subject,'mensaje':message,'paciente':patient,'user':user})
    email=EmailMultiAlternatives(subject,text,settings.EMAIL_HOST_USER,[patient.email]); email.attach_alternative(html,'text/html'); email.send()
