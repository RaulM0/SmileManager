from rest_framework.exceptions import ValidationError

SURFACES = {'mesial', 'oclusal', 'distal', 'lingual', 'vestibular'}
STATES = {'sin_registrar', 'sano', 'caries', 'restauracion', 'ausente', 'extraccion', 'protesis'}
SUMMARY = {'total_dientes', 'dientes_sanos', 'dientes_afectados', 'dientes_sin_registrar', 'superficies_caries', 'superficies_restauradas'}


def validate_odontogram(permanent, deciduous, summary):
    for dentition, quadrants, count in ((permanent, '1234', 8), (deciduous, '5678', 5)):
        if not isinstance(dentition, dict):
            raise ValidationError('La dentición debe ser un objeto.')
        for tooth, surfaces in dentition.items():
            if not isinstance(tooth, str) or len(tooth) != 2 or tooth[0] not in quadrants or tooth[1] not in '12345678'[:count]:
                raise ValidationError('Posición dental inválida.')
            if not isinstance(surfaces, dict) or set(surfaces) - SURFACES or any(not isinstance(v, str) or v not in STATES for v in surfaces.values()):
                raise ValidationError('Superficie o estado dental inválido.')
    if not isinstance(summary, dict) or set(summary) - SUMMARY or any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in summary.values()):
        raise ValidationError('Resumen de odontograma inválido.')
