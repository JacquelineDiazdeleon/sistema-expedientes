from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div
from crispy_forms.bootstrap import FormActions, Tab, TabHolder
from .models import (
    Documento, TipoDocumento, Departamento, Expediente, SolicitudRegistro, 
    RolUsuario, Mensaje, Chat, AreaTipoExpediente, ValorAreaExpediente
)






class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {'multiple': True}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        return files.get(name)

class MultipleFileField(forms.FileField):
    widget = MultipleFileInput
    
    def clean(self, data, initial=None):
        if data is None:
            return None
            
        if isinstance(data, (list, tuple)):
            return [super().clean(item, initial) for item in data if item]
            
        return super().clean(data, initial)

class ExpedienteForm(forms.ModelForm):
    """Formulario para crear y editar expedientes con áreas personalizadas"""
    # Campos básicos
    titulo = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Título del expediente (opcional)'
    )
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='Descripción del expediente (opcional)'
    )
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.filter(activo=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Departamento (opcional)'
    )
    giro = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Giro (opcional)'
    )
    
    class Meta:
        model = Expediente
        fields = [
            'tipo_expediente', 'subtipo_expediente', 'titulo', 'descripcion', 
            'departamento', 'giro', 'fuente_financiamiento', 'tipo_adquisicion', 
            'modalidad_monto'
        ]
        widgets = {
            'tipo_expediente': forms.HiddenInput(),
            'subtipo_expediente': forms.HiddenInput(),
            'modalidad_monto': forms.TextInput(attrs={'class': 'form-control'}),
            'fuente_financiamiento': forms.Select(attrs={'class': 'form-select'}),
            'tipo_adquisicion': forms.Select(attrs={'class': 'form-select'}),
            'giro': forms.TextInput(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'departamento': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        help_texts = {
            'titulo': 'Título del expediente (opcional)',
            'descripcion': 'Descripción del expediente (opcional)',
            'departamento': 'Departamento (opcional)',
            'giro': 'Giro (opcional)',
            'fuente_financiamiento': 'Fuente de financiamiento (opcional)',
            'tipo_adquisicion': 'Selecciona el tipo de adquisición',
            'modalidad_monto': 'Modalidad de monto (opcional)'
        }
        
    def get_areas_for_expediente(self):
        """
        Obtiene las áreas personalizadas para el tipo de expediente actual.
        
        Prioridad de búsqueda:
        1. Áreas específicas para el tipo y subtipo exacto
        2. Áreas para el tipo de expediente sin subtipo (generales)
        3. Áreas para el tipo de expediente con subtipo vacío (compatibilidad)
        """
        if not self.tipo_expediente:
            return []
        
        # Inicializar lista de áreas vacía
        areas_encontradas = []
        
        # 1. Buscar áreas específicas para el tipo y subtipo exacto
        areas_especificas = []
        if self.subtipo_expediente:
            # Normalizar el subtipo del expediente
            subtipo_exp = str(self.subtipo_expediente).strip().lower()
            
            # Lista de posibles formatos del subtipo para buscar
            subtipos_a_buscar = [subtipo_exp]
            
            # Si el subtipo no tiene prefijo 'licitacion_', agregar la versión con prefijo
            if self.tipo_expediente == 'licitacion' and not subtipo_exp.startswith('licitacion_'):
                subtipos_a_buscar.append(f'licitacion_{subtipo_exp}')
            
            # Si el subtipo tiene prefijo 'licitacion_', agregar la versión sin prefijo
            if self.tipo_expediente == 'licitacion' and subtipo_exp.startswith('licitacion_'):
                subtipos_a_buscar.append(subtipo_exp.replace('licitacion_', ''))
            
            # Buscar áreas con cualquiera de los formatos posibles
            # Eliminar duplicados de la lista de subtipos a buscar
            subtipos_a_buscar = list(set(subtipos_a_buscar))
            
            # Buscar áreas con cualquiera de los formatos posibles
            from django.db.models import Q
            areas_especificas = list(AreaTipoExpediente.objects.filter(
                tipo_expediente=self.tipo_expediente,
                subtipo_expediente__in=subtipos_a_buscar,
                activa=True
            ).order_by('orden'))
            
        # 2. Buscar áreas generales para el tipo de expediente (sin subtipo o con subtipo nulo/vacío)
        # Estas son áreas que aplican a todos los subtipos del tipo de expediente
        areas_generales = list(AreaTipoExpediente.objects.filter(
            tipo_expediente=self.tipo_expediente,
            activa=True
        ).filter(
            Q(subtipo_expediente__isnull=True) | Q(subtipo_expediente='')
        ).order_by('orden'))
        
        # 3. Combinar las áreas, priorizando las específicas sobre las generales
        # Usar un diccionario por ID para evitar duplicados (más eficiente)
        areas_dict = {}
        
        # Primero agregar áreas específicas (tienen prioridad)
        for area in areas_especificas:
            areas_dict[area.id] = area
        
        # Luego agregar áreas generales que no estén ya incluidas
        for area in areas_generales:
            if area.id not in areas_dict:
                areas_dict[area.id] = area
        
        # Convertir a lista
        areas_encontradas = list(areas_dict.values())
        
        # Si no se encontraron áreas, intentar con el tipo principal si es un subtipo
        if not areas_encontradas and ':' in self.tipo_expediente:
            tipo_principal = self.tipo_expediente.split(':', 1)[0]
            areas_tipo_principal = list(AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_principal,
                activa=True
            ).order_by('orden'))
            
            if areas_tipo_principal:
                # Solo agregar áreas que no estén ya en la lista
                for area in areas_tipo_principal:
                    if not any(a.nombre == area.nombre for a in areas_encontradas):
                        areas_encontradas.append(area)
        
        # Ordenar áreas por el campo 'orden' antes de devolverlas
        areas_encontradas = sorted(areas_encontradas, key=lambda x: x.orden)
        
        return areas_encontradas
        
    def __init__(self, *args, **kwargs):
        # Obtener el usuario y tipo/subtipo de expediente de los argumentos
        self.user = kwargs.pop('user', None)
        self.tipo_expediente = kwargs.pop('tipo_expediente', None)
        self.subtipo_expediente = kwargs.pop('subtipo_expediente', None)
        
        # Normalizar el subtipo si existe
        if self.subtipo_expediente:
            self.subtipo_expediente = str(self.subtipo_expediente).strip().lower()
        
        # Inicializar el formulario
        super().__init__(*args, **kwargs)
        
        # Importar el modelo Expediente aquí para evitar importación circular
        from .models import Expediente
        
        # Configurar las opciones para fuente_financiamiento y tipo_adquisicion
        self.fields['fuente_financiamiento'].choices = Expediente.FUENTE_CHOICES
        self.fields['tipo_adquisicion'].choices = Expediente.TIPO_ADQUISICION_CHOICES
        
        # NOTA: Las áreas NO se muestran en el formulario de creación de expedientes
        # Solo se usan en el detalle del expediente para subir documentos
        # Por lo tanto, NO creamos campos dinámicos aquí para evitar validaciones innecesarias
        self.areas = []
        
        # Establecer valores iniciales
        if self.tipo_expediente:
            self.fields['tipo_expediente'].initial = self.tipo_expediente
        if self.subtipo_expediente:
            self.fields['subtipo_expediente'].initial = self.subtipo_expediente
            
        # Configurar campo de archivos múltiples
        self.fields['archivos'] = MultipleFileField(
            required=False, 
            help_text='Puedes seleccionar múltiples archivos'
        )
        
        # Configurar valores iniciales
        if self.tipo_expediente == 'licitacion' and self.subtipo_expediente:
            # Para licitaciones, establecer el valor inicial según el subtipo
            if 'recurso_propio' in self.subtipo_expediente:
                self.fields['fuente_financiamiento'].initial = 'propio_municipal'
                self.fields['fuente_financiamiento'].widget.attrs['readonly'] = True
            elif 'fondo_federal' in self.subtipo_expediente:
                self.fields['fuente_financiamiento'].initial = 'federal'
                self.fields['fuente_financiamiento'].widget.attrs['readonly'] = True
        else:
            # Para otros tipos de expediente, establecer valores por defecto solo si no hay datos POST
            if not self.data:
                if 'fuente_financiamiento' not in self.initial:
                    self.fields['fuente_financiamiento'].initial = 'propio_municipal'
                if 'tipo_adquisicion' not in self.initial:
                    self.fields['tipo_adquisicion'].initial = 'bienes'
        
        # Configurar placeholders y clases CSS
        for field_name, field in self.fields.items():
            if field_name not in ['tipo_expediente', 'subtipo_expediente', 'archivos']:
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'
                
                if field_name == 'titulo':
                    field.widget.attrs['placeholder'] = 'Ingrese el título (opcional)'
                elif field_name == 'descripcion':
                    field.widget.attrs.update({
                        'placeholder': 'Ingrese una descripción (opcional)',
                        'rows': 3
                    })
                elif field_name == 'giro':
                    field.widget.attrs['placeholder'] = 'Ingrese el giro (opcional)'
                elif field_name == 'modalidad_monto':
                    field.widget.attrs['placeholder'] = 'Ingrese la modalidad de monto (opcional)'
        
        # Configurar el helper de crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}
        
        # Crear layout del formulario
        self.helper.layout = Layout(
            # Campos ocultos
            'tipo_expediente',
            'subtipo_expediente',
            
            # Campos visibles
            Row(
                Column('titulo', css_class='form-group col-md-6 mb-3'),
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
            'descripcion',
            
            # Botones de acción
            FormActions(
                Submit('submit', 'Guardar Expediente', css_class='btn btn-primary'),
                HTML('<a href="{% url \'expedientes:lista\' %}" class="btn btn-secondary ms-2">Cancelar</a>')
            )
        )
        
        # Filtrar solo departamentos activos
        self.fields['departamento'].queryset = Departamento.objects.filter(activo=True)

    def clean(self):
        cleaned_data = super().clean()
        
        # Determinar si es un envío real del formulario (solo cuando se presiona el botón de envío)
        is_form_submission = 'submit' in self.data
        
        # Si no es un envío del formulario, no validar campos obligatorios
        if not is_form_submission:
            return cleaned_data
            
        # NOTA: No validamos áreas aquí porque no se muestran en el formulario de creación
        # Las áreas se gestionan en el detalle del expediente, no en la creación
        
        # Mapeo de valores de opciones de selección a sus claves
        FUENTE_MAP = {
            'Propio municipal': 'propio_municipal',
            'Estatal': 'estatal',
            'Federal': 'federal'
        }
        
        TIPO_ADQUISICION_MAP = {
            'Bienes': 'bienes',
            'Servicios': 'servicios',
            'Arrendamientos': 'arrendamientos'
        }
        
        # Convertir valores de selección a sus claves correspondientes
        if 'fuente_financiamiento' in cleaned_data and cleaned_data['fuente_financiamiento']:
            valor = cleaned_data['fuente_financiamiento']
            if valor in FUENTE_MAP:
                cleaned_data['fuente_financiamiento'] = FUENTE_MAP[valor]
            elif valor not in dict(self.Meta.model.FUENTE_CHOICES).values():
                cleaned_data['fuente_financiamiento'] = None
        
        if 'tipo_adquisicion' in cleaned_data and cleaned_data['tipo_adquisicion']:
            valor = cleaned_data['tipo_adquisicion']
            if valor in TIPO_ADQUISICION_MAP:
                cleaned_data['tipo_adquisicion'] = TIPO_ADQUISICION_MAP[valor]
            elif valor not in dict(self.Meta.model.TIPO_ADQUISICION_CHOICES).values():
                cleaned_data['tipo_adquisicion'] = None
        
        # Asegurar que tipo_adquisicion tenga un valor por defecto
        if 'tipo_adquisicion' not in cleaned_data or not cleaned_data['tipo_adquisicion']:
            cleaned_data['tipo_adquisicion'] = 'bienes'
            
        # Asegurar que fuente_financiamiento tenga un valor por defecto si es requerido
        if 'fuente_financiamiento' not in cleaned_data or not cleaned_data['fuente_financiamiento']:
            cleaned_data['fuente_financiamiento'] = 'propio_municipal'
            
        # Convertir cadenas vacías a None para evitar problemas con campos opcionales
        for field in ['titulo', 'descripcion', 'giro', 'modalidad_monto']:
            if field in cleaned_data and (cleaned_data[field] == '' or cleaned_data[field] is None):
                cleaned_data[field] = None
                
        # Asegurarse de que el tipo_expediente esté presente
        tipo_expediente = cleaned_data.get('tipo_expediente')
        if not tipo_expediente and hasattr(self, 'tipo_expediente') and self.tipo_expediente:
            cleaned_data['tipo_expediente'] = self.tipo_expediente
        elif not tipo_expediente:
            raise forms.ValidationError({
                'tipo_expediente': 'El tipo de expediente es obligatorio.'
            })
            
        # Validar que el tipo de expediente sea uno de los permitidos
        if 'tipo_expediente' in cleaned_data and cleaned_data['tipo_expediente']:
            tipos_permitidos = dict(self.Meta.model.TIPO_CHOICES).keys()
            if cleaned_data['tipo_expediente'] not in tipos_permitidos:
                raise forms.ValidationError({
                    'tipo_expediente': 'Tipo de expediente no válido.'
                })
        
        # NOTA: No validar áreas aquí porque no se muestran en el formulario de creación
        # Las áreas se gestionan en el detalle del expediente, no en la creación
            
        
        # Verificar si hay errores de validación
        if is_form_submission and self.errors:
            logger.error(f"Errores de validación: {self.errors}")
                
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





class SolicitudRegistroForm(forms.ModelForm):
    """Formulario para solicitudes de registro"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña',
            'id': 'password'
        }),
        label='Contraseña *',
        help_text='Mínimo 8 caracteres'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu contraseña',
            'id': 'confirmPassword'
        }),
        label='Confirmar Contraseña *'
    )
    
    class Meta:
        model = SolicitudRegistro
        fields = [
            'nombres', 'apellidos', 'email_institucional', 
            'departamento', 'puesto', 'rol_solicitado'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa tu(s) nombre(s)',
                'id': 'nombres'
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa tus apellidos',
                'id': 'apellidos'
            }),
            'email_institucional': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@servicios.gob.mx',
                'id': 'emailInstitucional'
            }),
            'departamento': forms.Select(attrs={
                'class': 'form-select',
                'id': 'departamento'
            }),
            'puesto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu puesto o cargo',
                'id': 'puesto'
            }),

            'rol_solicitado': forms.Select(attrs={
                'class': 'form-select',
                'id': 'rolSolicitado'
            })
        }
        labels = {
            'nombres': 'Nombre(s) *',
            'apellidos': 'Apellidos *',
            'email_institucional': 'Correo Electrónico *',
            'departamento': 'Departamento',
            'puesto': 'Puesto',
            'rol_solicitado': 'Rol Solicitado *'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Incluir todos los roles disponibles (incluyendo administrador)
        self.fields['rol_solicitado'].queryset = RolUsuario.objects.all()
        self.fields['departamento'].queryset = Departamento.objects.filter(activo=True)
        
        # Hacer departamento y puesto opcionales
        self.fields['departamento'].required = False
        self.fields['puesto'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Las contraseñas no coinciden")
            
            if len(password) < 8:
                raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres")
        
        return cleaned_data


class LoginForm(forms.Form):
    """Formulario de login personalizado"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario o correo electrónico',
            'id': 'username'
        }),
        label='Usuario o Correo Electrónico'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
            'id': 'password'
        }),
        label='Contraseña'
    )


class MensajeForm(forms.ModelForm):
    """Formulario para enviar mensajes"""
    class Meta:
        model = Mensaje
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escribe tu mensaje aquí...',
                'style': 'resize: none;'
            })
        }


class ChatForm(forms.ModelForm):
    """Formulario para crear chats de grupo"""
    participantes = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Selecciona los participantes del grupo"
    )
    
    class Meta:
        model = Chat
        fields = ['nombre', 'participantes']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Excluir usuarios inactivos
        self.fields['participantes'].queryset = User.objects.filter(is_active=True)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'nombre',
            'participantes',
            FormActions(
                Submit('submit', 'Guardar Chat', css_class='btn-primary'),
                HTML('<a href="{% url \'digitalizacion:mensajeria\' %}" class="btn btn-secondary">Cancelar</a>')
            )
        )
