from django.http import HttpResponse
import pandas as pd
from Pacientes.models import Consulta, ImagenesClinicas, Paciente

def excel_response(rows, *, filename, sheet):
    frame=pd.DataFrame(list(rows))
    for column in frame.select_dtypes(include=['datetimetz']): frame[column]=frame[column].dt.tz_localize(None)
    response=HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'); response['Content-Disposition']=f'attachment; filename={filename}'
    with pd.ExcelWriter(response,engine='openpyxl') as writer: frame.to_excel(writer,sheet_name=sheet,index=False)
    return response

def export_patients(user):
    rows=Paciente.objects.filter(medico=user).values('id','nombre','appat','apmat','fecha_nacimiento','genero','telefono','email','estatus')
    return excel_response(rows,filename='Pacientes.xlsx',sheet='Pacientes')
def export_consultations(user):
    rows=Consulta.objects.filter(paciente__medico=user).values('paciente__nombre','paciente__appat','paciente__apmat','fecha_consulta','motivo_consulta','diagnostico','tratamiento','observaciones')
    return excel_response(rows,filename='Consultas.xlsx',sheet='Consultas')
def export_images(user):
    rows=ImagenesClinicas.objects.filter(paciente__medico=user).values('paciente','consulta','tipo_imagen','descripcion','imagen','fecha_subida')
    return excel_response(rows,filename='ImagenesClinicas.xlsx',sheet='ImagenesClinicas')
