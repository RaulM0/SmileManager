from itertools import islice
from django.conf import settings
from django.http import HttpResponse, JsonResponse
import pandas as pd
from Pacientes.models import Consulta, ImagenesClinicas, Paciente
from api.policies import scoped

def safe_cell(value):
    if isinstance(value, str) and value.lstrip(' \t\r\n').startswith(('=', '+', '-', '@')):
        return "'" + value
    return value

def excel_response(rows, *, filename, sheet):
    limit = settings.EXPORT_MAX_ROWS
    source = rows[:limit + 1].iterator(chunk_size=500) if hasattr(rows, 'iterator') else islice(rows, limit + 1)
    data = [{key: safe_cell(value) for key, value in row.items()} for row in source]
    if len(data) > limit:
        return JsonResponse({'detail': f'La exportación supera el límite de {limit} registros. Contacta al administrador.'}, status=413)
    frame=pd.DataFrame(data)
    for column in frame.select_dtypes(include=['datetimetz']): frame[column]=frame[column].dt.tz_localize(None)
    response=HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'); response['Content-Disposition']=f'attachment; filename={filename}'
    with pd.ExcelWriter(response,engine='openpyxl') as writer: frame.to_excel(writer,sheet_name=sheet,index=False)
    return response

def export_patients(user):
    rows=scoped(user, Paciente).values('id','nombre','appat','apmat','fecha_nacimiento','genero','telefono','email','estatus')
    return excel_response(rows,filename='Pacientes.xlsx',sheet='Pacientes')
def export_consultations(user):
    rows=scoped(user, Consulta).values('paciente__nombre','paciente__appat','paciente__apmat','fecha_consulta','motivo_consulta','diagnostico','tratamiento','observaciones')
    return excel_response(rows,filename='Consultas.xlsx',sheet='Consultas')
def export_images(user):
    rows=scoped(user, ImagenesClinicas).values('paciente','consulta','tipo_imagen','descripcion','imagen','fecha_subida')
    return excel_response(rows,filename='ImagenesClinicas.xlsx',sheet='ImagenesClinicas')
