from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML
from crispy_forms.bootstrap import FormActions
from .models import Documento, TipoDocumento, Departamento, Expediente


class ExpedienteForm(forms.ModelForm):
    """Formulario para crear y editar expedientes"""
    
    class Meta:
        model = Expediente
        fields = [
            'numero_expediente', 'titulo', 'descripcion', 'tipo_expediente',
            'departamento', 'giro', 'fuente_financiamiento', 'tipo_adquisicion',
            'modalidad_monto', 'fecha_expediente', 'fecha_vencimiento', 
            'palabras_clave', 'observaciones', 'confidencial'
        ]
        widgets = {
            'fecha_expediente': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'palabras_clave': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Palabras clave separadas por comas'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('numero_expediente', css_class='form-group col-md-6 mb-3'),
                Column('titulo', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('tipo_expediente', css_class='form-group col-md-6 mb-3'),
                Column('departamento', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('giro', css_class='form-group col-md-6 mb-3'),
                Column('fuente_financiamiento', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('tipo_adquisicion', css_class='form-group col-md-6 mb-3'),
                Column('modalidad_monto', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('fecha_expediente', css_class='form-group col-md-6 mb-3'),
                Column('fecha_vencimiento', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('confidencial', css_class='form-group col-md-12 mb-3'),
                css_class='form-row'
            ),
            Field('descripcion', css_class='mb-3'),
            Field('palabras_clave', css_class='mb-3'),
            Field('observaciones', css_class='mb-3'),
            FormActions(
                Submit('submit', 'Guardar Expediente', css_class='btn btn-primary'),
                HTML('<a href="{% url "digitalizacion:lista_documentos" %}" class="btn btn-secondary ms-2">Cancelar</a>')
            )
        )

        # Filtrar solo elementos activos
        self.fields['departamento'].queryset = Departamento.objects.filter(activo=True)

    def clean_numero_expediente(self):
        numero_expediente = self.cleaned_data['numero_expediente']
        
        # Verificar que el número de expediente sea único
        if self.instance.pk:
            # Edición - excluir el expediente actual
            if Expediente.objects.filter(numero_expediente=numero_expediente).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Ya existe un expediente con este número.')
        else:
            # Creación - verificar que no exista
            if Expediente.objects.filter(numero_expediente=numero_expediente).exists():
                raise ValidationError('Ya existe un expediente con este número.')
        
        return numero_expediente

    def clean(self):
        cleaned_data = super().clean()
        fecha_expediente = cleaned_data.get('fecha_expediente')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')
        
        # Verificar que la fecha de vencimiento sea posterior a la fecha del expediente
        if fecha_expediente and fecha_vencimiento:
            if fecha_vencimiento < fecha_expediente:
                raise ValidationError('La fecha de vencimiento no puede ser anterior a la fecha del expediente.')
        
        return cleaned_data


class DocumentoForm(forms.ModelForm):
    """Formulario para crear y editar documentos (legacy)"""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('digitalizado', 'Digitalizado'),
        ('verificado', 'Verificado'),
        ('archivado', 'Archivado'),
        ('rechazado', 'Rechazado'),
    ]

    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    estado = forms.ChoiceField(choices=ESTADO_CHOICES, required=False)
    prioridad = forms.ChoiceField(choices=PRIORIDAD_CHOICES, required=False)
    
    class Meta:
        model = Documento
        fields = [
            'numero_documento', 'titulo', 'descripcion', 'tipo_documento',
            'departamento', 'giro', 'fuente_financiamiento', 'tipo_adquisicion',
            'modalidad_monto', 'archivo_digital',
            'fecha_documento', 'fecha_vencimiento', 'palabras_clave',
            'observaciones', 'confidencial'
        ]
        widgets = {
            'fecha_documento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'palabras_clave': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Palabras clave separadas por comas'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'archivo_digital': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.tiff'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('numero_documento', css_class='form-group col-md-6 mb-3'),
                Column('titulo', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('tipo_documento', css_class='form-group col-md-6 mb-3'),
                Column('departamento', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('estado', css_class='form-group col-md-4 mb-3'),
                Column('prioridad', css_class='form-group col-md-4 mb-3'),
                Column('confidencial', css_class='form-group col-md-4 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('fecha_documento', css_class='form-group col-md-6 mb-3'),
                Column('fecha_vencimiento', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('descripcion', css_class='mb-3'),
            Field('archivo_digital', css_class='mb-3'),
            Field('palabras_clave', css_class='mb-3'),
            Field('observaciones', css_class='mb-3'),
            FormActions(
                Submit('submit', 'Guardar Documento', css_class='btn btn-primary'),
                HTML('<a href="{% url "digitalizacion:lista_documentos" %}" class="btn btn-secondary ms-2">Cancelar</a>')
            )
        )

        # Filtrar solo elementos activos
        self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(activo=True)
        self.fields['departamento'].queryset = Departamento.objects.filter(activo=True)

    def clean_numero_documento(self):
        numero_documento = self.cleaned_data['numero_documento']
        
        # Verificar que el número de documento sea único
        if self.instance.pk:
            # Edición - excluir el documento actual
            if Documento.objects.filter(numero_documento=numero_documento).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Ya existe un documento con este número.')
        else:
            # Creación - verificar que no exista
            if Documento.objects.filter(numero_documento=numero_documento).exists():
                raise ValidationError('Ya existe un documento con este número.')
        
        return numero_documento

    def clean_archivo_digital(self):
        archivo = self.cleaned_data.get('archivo_digital')
        
        if archivo:
            # Verificar tamaño del archivo (máximo 50MB)
            if archivo.size > 50 * 1024 * 1024:
                raise ValidationError('El archivo no puede ser mayor a 50MB.')
            
            # Verificar extensión
            extensiones_permitidas = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.tiff', '.gif']
            nombre_archivo = archivo.name.lower()
            
            if not any(nombre_archivo.endswith(ext) for ext in extensiones_permitidas):
                raise ValidationError(
                    f'Tipo de archivo no permitido. Extensiones permitidas: {", ".join(extensiones_permitidas)}'
                )
        
        return archivo

    def clean(self):
        cleaned_data = super().clean()
        fecha_documento = cleaned_data.get('fecha_documento')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')
        
        # Verificar que la fecha de vencimiento sea posterior a la fecha del documento
        if fecha_documento and fecha_vencimiento:
            if fecha_vencimiento < fecha_documento:
                raise ValidationError('La fecha de vencimiento no puede ser anterior a la fecha del documento.')
        
        return cleaned_data


class TipoDocumentoForm(forms.ModelForm):
    """Formulario para tipos de documento"""
    
    class Meta:
        model = TipoDocumento
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('nombre', css_class='mb-3'),
            Field('descripcion', css_class='mb-3'),
            Field('activo', css_class='mb-3'),
            FormActions(
                Submit('submit', 'Guardar Tipo de Documento', css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary ms-2" data-bs-dismiss="modal">Cancelar</button>')
            )
        )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        
        if self.instance.pk:
            # Edición - excluir el tipo actual
            if TipoDocumento.objects.filter(nombre=nombre).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Ya existe un tipo de documento con este nombre.')
        else:
            # Creación - verificar que no exista
            if TipoDocumento.objects.filter(nombre=nombre).exists():
                raise ValidationError('Ya existe un tipo de documento con este nombre.')
        
        return nombre


class DepartamentoForm(forms.ModelForm):
    """Formulario para departamentos"""
    
    class Meta:
        model = Departamento
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('nombre', css_class='mb-3'),
            Field('descripcion', css_class='mb-3'),
            Field('activo', css_class='mb-3'),
            FormActions(
                Submit('submit', 'Guardar Departamento', css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary ms-2" data-bs-dismiss="modal">Cancelar</button>')
            )
        )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        
        if self.instance.pk:
            # Edición - excluir el departamento actual
            if Departamento.objects.filter(nombre=nombre).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Ya existe un departamento con este nombre.')
        else:
            # Creación - verificar que no exista
            if Departamento.objects.filter(nombre=nombre).exists():
                raise ValidationError('Ya existe un departamento con este nombre.')
        
        return nombre


class BusquedaAvanzadaForm(forms.Form):
    """Formulario para búsqueda avanzada de documentos"""
    
    numero_documento = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de documento'})
    )
    titulo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del documento'})
    )
    tipo_documento = forms.ModelChoiceField(
        queryset=TipoDocumento.objects.filter(activo=True),
        required=False,
        empty_label="Todos los tipos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.filter(activo=True),
        required=False,
        empty_label="Todos los departamentos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Documento.ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    prioridad = forms.ChoiceField(
        choices=[('', 'Todas las prioridades')] + Documento.PRIORIDAD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    palabras_clave = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Palabras clave'})
    )
    confidencial = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('numero_documento', css_class='form-group col-md-6 mb-3'),
                Column('titulo', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('tipo_documento', css_class='form-group col-md-6 mb-3'),
                Column('departamento', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('estado', css_class='form-group col-md-4 mb-3'),
                Column('prioridad', css_class='form-group col-md-4 mb-3'),
                Column('confidencial', css_class='form-group col-md-4 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('fecha_desde', css_class='form-group col-md-6 mb-3'),
                Column('fecha_hasta', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('palabras_clave', css_class='mb-3'),
            FormActions(
                Submit('submit', 'Buscar', css_class='btn btn-primary'),
                HTML('<button type="reset" class="btn btn-secondary ms-2">Limpiar</button>')
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise ValidationError('La fecha inicial no puede ser posterior a la fecha final.')
        
        return cleaned_data


