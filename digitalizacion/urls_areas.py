from django.urls import path
from . import views_areas

app_name = 'areas'

urlpatterns = [
    # Gestión de áreas por tipo
    path('', views_areas.gestionar_areas_tipos, name='gestionar'),
    path('tipo/<str:tipo>/', views_areas.gestionar_areas_tipos, name='gestionar_tipo'),
    path('tipo/<str:tipo>/crear/', views_areas.crear_area_tipo, name='crear'),
    path('editar/<int:area_id>/', views_areas.editar_area, name='editar'),
    path('eliminar/<int:area_id>/', views_areas.eliminar_area, name='eliminar'),
    path('duplicar/<int:area_id>/', views_areas.duplicar_area, name='duplicar'),
    path('reordenar/<str:tipo>/', views_areas.reordenar_areas, name='reordenar'),
    
    # Gestión de campos personalizados
    path('campos/<int:area_id>/', views_areas.gestionar_campos_area, name='campos'),
    path('campos/<int:area_id>/crear/', views_areas.crear_campo_area, name='crear_campo'),
    path('campos/eliminar/<int:campo_id>/', views_areas.eliminar_campo_area, name='eliminar_campo'),
]
