from django import forms
from .models import EstudioComparativo

class EstudioComparativoForm(forms.ModelForm):
    class Meta:
        model = EstudioComparativo
        fields = [
            'fecha_inicio', 
            'diagnostico', 
            'observaciones',
            'antes_oclusal_superior', 
            'antes_lateral_izquierda',
            'antes_frontal', 
            'antes_lateral_derecha', 
            'antes_oclusal_inferior',
            'despues_perfil', 
            'despues_semiperfil',
            'despues_retrato_frontal', 
            'despues_retrato_sonrisa'
        ]
        
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'fecha_inicio'
            }),
            'diagnostico': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'diagnostico',
                'placeholder': 'Ej: Maloclusión Clase II'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'observaciones',
                'rows': 3,
                'placeholder': 'Notas adicionales sobre el caso...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer que las imágenes "después" NO sean requeridas
        self.fields['despues_perfil'].required = False
        self.fields['despues_semiperfil'].required = False
        self.fields['despues_retrato_frontal'].required = False
        self.fields['despues_retrato_sonrisa'].required = False
        
        # Las imágenes "antes" SÍ son requeridas (solo si es nuevo estudio)
        if not self.instance.pk:  # Si es nuevo
            self.fields['antes_oclusal_superior'].required = True
            self.fields['antes_lateral_izquierda'].required = True
            self.fields['antes_frontal'].required = True
            self.fields['antes_lateral_derecha'].required = True
            self.fields['antes_oclusal_inferior'].required = True