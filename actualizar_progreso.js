        // Función para actualizar la barra de progreso
        async function actualizarProgresoDocumentos() {
            console.log('[DEBUG] Iniciando actualización de progreso...');
            // Mostrar estado de carga
            const progressBar = document.getElementById('globalProgressBar');
            const progressPercentage = document.getElementById('progressPercentage');
            
            if (progressBar && progressPercentage) {
                progressBar.classList.add('progress-bar-striped', 'progress-bar-animated');
                progressPercentage.textContent = 'Cargando...';
            }
            
            // Evitar múltiples solicitudes simultáneas
            if (appState.syncInProgress) {
                console.log('[DEBUG] Sincronización ya en progreso, omitiendo...');
                const cachedData = appState.getCachedData();
                if (cachedData) {
                    console.log('[DEBUG] Mostrando datos en caché mientras se completa la sincronización');
                    actualizarUIProgreso(cachedData.data);
                    return cachedData.data;
                }
                return null;
            }
            
            appState.syncInProgress = true;
            
            try {
                const expedienteId = '{{ expediente.id }}';
                if (!expedienteId) {
                    throw new Error('No se encontró el ID del expediente');
                }
                
                const url = `/expedientes/${expedienteId}/progreso-documentos/`;
                console.log('[DEBUG] Solicitando datos de progreso a:', url);
                
                // Obtener datos del servidor con timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 segundos de timeout
                
                const response = await fetch(url, {
                    signal: controller.signal,
                    headers: {
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    },
                    cache: 'no-store' // Evitar caché del navegador
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('[ERROR] Error en la respuesta del servidor:', {
                        status: response.status,
                        statusText: response.statusText,
                        response: errorText
                    });
                    throw new Error(`Error HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('[DEBUG] Datos de progreso recibidos:', data);
                
                // Validar estructura de datos
                if (!data || typeof data !== 'object') {
                    throw new Error('Respuesta del servidor no es un objeto JSON válido');
                }
                
                // Asegurar que los datos tengan el formato esperado
                const areas = Array.isArray(data.areas) ? data.areas : [];
                const areasCompletadas = areas.filter(a => a.completada).length;
                const totalAreas = areas.length || 1; // Evitar división por cero
                const porcentaje = Math.round((areasCompletadas / totalAreas) * 100);
                
                const datosProgreso = {
                    ...data,
                    areas: areas,
                    porcentaje_completo: data.porcentaje_completo || porcentaje,
                    areas_completadas: areasCompletadas,
                    total_areas: totalAreas
                };
                
                console.log(`[DEBUG] Progreso calculado: ${datosProgreso.porcentaje_completo}% (${areasCompletadas}/${totalAreas} áreas)`);
                
                // Actualizar caché local
                appState.cacheData(datosProgreso);
                
                // Actualizar la UI
                actualizarUIProgreso(datosProgreso);
                
                // Reiniciar contador de reintentos
                appState.retryCount = 0;
                
                return datosProgreso;
                
            } catch (error) {
                console.error('[ERROR] Error al actualizar el progreso:', error);
                
                // Reintentar si es posible
                if (appState.retryCount < appState.maxRetries) {
                    appState.retryCount++;
                    const delay = appState.retryDelay * appState.retryCount;
                    console.log(`[DEBUG] Reintentando (${appState.retryCount}/${appState.maxRetries}) en ${delay}ms...`);
                    
                    // Esperar antes de reintentar
                    await new Promise(resolve => setTimeout(resolve, delay));
                    return actualizarProgresoDocumentos();
                }
                
                // Si se agotaron los reintentos, mostrar datos en caché si existen
                const cachedData = appState.getCachedData();
                if (cachedData) {
                    console.log('[DEBUG] Usando datos en caché debido a error de conexión');
                    actualizarUIProgreso(cachedData.data);
                    return cachedData.data;
                }
                
                // Si no hay datos en caché, mostrar un mensaje de error
                if (progressBar && progressPercentage) {
                    progressBar.classList.remove('bg-success', 'bg-warning');
                    progressBar.classList.add('bg-danger');
                    progressBar.style.width = '100%';
                    progressPercentage.textContent = 'Error al cargar el progreso';
                    console.error('[ERROR] No hay datos en caché disponibles');
                }
                
                throw error;
                
            } finally {
                appState.syncInProgress = false;
                
                // Quitar animación de carga
                if (progressBar) {
                    progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
                }
            }
        }
