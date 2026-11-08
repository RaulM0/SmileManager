from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def send_patient_email(*, patient, user, subject, message):
    clinic_name = patient.clinic.name if patient.clinic_id else 'SmileManager'
    text=f'{message}\n\nAtentamente,\n{clinic_name}'
    html=render_to_string('emails/mensaje_paciente.html',{'asunto':subject,'mensaje':message,'paciente':patient,'user':user,'clinic_name':clinic_name})
    email=EmailMultiAlternatives(subject,text,settings.DEFAULT_FROM_EMAIL,[patient.email]); email.attach_alternative(html,'text/html')
    return email.send()
