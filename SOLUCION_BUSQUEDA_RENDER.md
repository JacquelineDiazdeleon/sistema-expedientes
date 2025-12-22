# Solución para Búsqueda en Render

## Problema Identificado

La búsqueda de documentos no funciona en Render porque:

1. **El índice Whoosh se guarda en `media/whoosh_index/`**
2. **En Render, el sistema de archivos es efímero** - se pierde al reiniciar el contenedor
3. **El índice necesita recrearse** después de cada reinicio

## Soluciones

### Solución 1: Reindexar manualmente después del deploy

En Render, después de hacer deploy, ejecuta manualmente desde la consola de Render:

```bash
python manage.py indexar_documentos --reindexar
```

O solo indexar los últimos documentos:

```bash
python manage.py indexar_documentos --limite 50
```

### Solución 2: Indexación automática al subir documentos (YA IMPLEMENTADO)

El sistema ya indexa automáticamente cuando subes un documento nuevo. Esto funciona, pero solo para documentos nuevos.

### Solución 3: Agregar indexación periódica (Recomendado para producción)

Puedes crear un script que se ejecute periódicamente en Render usando un cron job o tarea programada.

## Comandos Útiles

### Verificar estado del índice

```bash
python manage.py shell
```

```python
from digitalizacion.search_utils import get_or_create_index
ix = get_or_create_index()
with ix.searcher() as searcher:
    print(f"Documentos indexados: {searcher.doc_count()}")
```

### Reindexar todos los documentos

```bash
python manage.py indexar_documentos --reindexar
```

### Reindexar solo los primeros 100

```bash
python manage.py indexar_documentos --limite 100
```

## Nota Importante

⚠️ **Limitación**: Solo se pueden indexar documentos que estén físicamente presentes en el servidor de Render. Si los archivos fueron descargados y eliminados (como está configurado en tu sistema), no podrán ser indexados porque Whoosh necesita acceso físico a los archivos PDF para extraer el texto.

## Recomendación

Para que la búsqueda funcione correctamente en producción:

1. **Indexar periódicamente**: Ejecutar el comando de indexación cada vez que se reinicie Render
2. **O cambiar la estrategia**: Si necesitas búsqueda persistente, considera usar un servicio de búsqueda externo como Elasticsearch o Algolia, o mantener los archivos en Render más tiempo antes de descargarlos

