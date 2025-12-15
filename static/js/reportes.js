// Funcionalidad para la página de Reportes

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM cargado, iniciando reportes...');
    
    // Verificar que Chart.js esté disponible
    if (typeof Chart === 'undefined') {
        console.error('❌ Chart.js no está disponible');
        alert('Error: Chart.js no se cargó correctamente');
        return;
    }
    
    console.log('✅ Chart.js está disponible');
    
    // Inicializar gráficos
    inicializarGraficos();
    
    // Configurar eventos
    configurarEventos();
});

function inicializarGraficos() {
    console.log('📊 Inicializando tablas de reportes...');
    
    // Datos para las tablas (se pasan desde Django)
    const expedientesPorMesData = window.expedientesPorMesData || [];
    const expedientesPorTipoData = window.expedientesPorTipoData || [];
    const expedientesPorEstadoData = window.expedientesPorEstadoData || [];
    const usuariosActivosData = window.usuariosActivosData || [];
    
    console.log('📋 Datos recibidos:', {
        expedientesPorMesData,
        expedientesPorTipoData,
        expedientesPorEstadoData,
        usuariosActivosData
    });
    
    // Verificar que haya datos
    if (expedientesPorMesData.length === 0) {
        console.warn('⚠️ No hay datos de expedientes por mes');
    }
    if (expedientesPorTipoData.length === 0) {
        console.warn('⚠️ No hay datos de expedientes por tipo');
    }
    if (expedientesPorEstadoData.length === 0) {
        console.warn('⚠️ No hay datos de expedientes por estado');
    }
    if (usuariosActivosData.length === 0) {
        console.warn('⚠️ No hay datos de usuarios activos');
    }
    
    // Cargar datos en las tablas
    cargarTablaExpedientesPorTipo(expedientesPorTipoData);
    cargarTablaExpedientesPorEstado(expedientesPorEstadoData);
    cargarTablaExpedientesPorMes(expedientesPorMesData);
    cargarTablaUsuariosActivos(usuariosActivosData);
    
    console.log('🎉 Carga de tablas completada');
}

function crearGraficoPrueba() {
    console.log('🧪 Creando gráfico de prueba...');
    
    const canvasPrueba = document.getElementById('graficoPrueba');
    const estadoPrueba = document.getElementById('estadoGraficoPrueba');
    
    if (!canvasPrueba) {
        console.error('❌ No se encontró el canvas de prueba');
        return;
    }
    
    if (estadoPrueba) {
        estadoPrueba.innerHTML = '<small class="text-yellow-400">Creando gráfico de prueba...</small>';
    }
    
    try {
        new Chart(canvasPrueba, {
            type: 'bar',
            data: {
                labels: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo'],
                datasets: [{
                    label: 'Datos de Prueba',
                    data: [12, 19, 3, 5, 8],
                    backgroundColor: ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'],
                    borderWidth: 0,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#f4f4f5' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(156, 163, 175, 0.2)' }
                    },
                    y: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(156, 163, 175, 0.2)' }
                    }
                }
            }
        });
        
        console.log('✅ Gráfico de prueba creado exitosamente');
        if (estadoPrueba) {
            estadoPrueba.innerHTML = '<small class="text-green-400">✅ Gráfico de prueba creado exitosamente</small>';
        }
        
    } catch (error) {
        console.error('❌ Error creando gráfico de prueba:', error);
        if (estadoPrueba) {
            estadoPrueba.innerHTML = '<small class="text-red-400">❌ Error: ' + error.message + '</small>';
        }
    }
}

function crearGraficoPruebaReal() {
    console.log('🧪 Creando gráfico de prueba con datos reales...');
    
    const canvasPruebaReal = document.getElementById('graficoPruebaReal');
    const estadoPruebaReal = document.getElementById('estadoGraficoPruebaReal');
    
    if (!canvasPruebaReal) {
        console.error('❌ No se encontró el canvas de prueba real');
        return;
    }
    
    if (estadoPruebaReal) {
        estadoPruebaReal.innerHTML = '<small class="text-yellow-400">Creando gráfico con datos reales...</small>';
    }
    
    // Obtener datos reales de Django
    const expedientesPorTipoData = window.expedientesPorTipoData || [];
    
    console.log('📊 Datos reales para gráfico de prueba:', expedientesPorTipoData);
    
    if (expedientesPorTipoData.length === 0) {
        if (estadoPruebaReal) {
            estadoPruebaReal.innerHTML = '<small class="text-red-400">❌ No hay datos disponibles</small>';
        }
        return;
    }
    
    try {
        // Preparar datos para el gráfico
        const labels = expedientesPorTipoData.map(item => item.tipo_expediente || 'Sin Tipo');
        const data = expedientesPorTipoData.map(item => item.total);
        
        console.log('📋 Labels:', labels);
        console.log('📊 Data:', data);
        
        new Chart(canvasPruebaReal, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 2,
                    borderColor: '#1f2937'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#f4f4f5' }
                    }
                }
            }
        });
        
        console.log('✅ Gráfico de prueba con datos reales creado exitosamente');
        if (estadoPruebaReal) {
            estadoPruebaReal.innerHTML = '<small class="text-green-400">✅ Gráfico con datos reales creado exitosamente</small>';
        }
        
    } catch (error) {
        console.error('❌ Error creando gráfico de prueba con datos reales:', error);
        if (estadoPruebaReal) {
            estadoPruebaReal.innerHTML = '<small class="text-red-400">❌ Error: ' + error.message + '</small>';
        }
    }
}

function crearGraficoExpedientesPorMes(expedientesPorMesData, colors) {
    const expedientesPorMesChart = document.getElementById('expedientesPorMesChart');
    if (expedientesPorMesChart) {
        console.log('🎯 Creando gráfico de expedientes por mes');
        console.log('📊 Datos recibidos:', expedientesPorMesData);
        
        // Actualizar indicador de estado
        const estadoMes = document.getElementById('estadoGraficoMes');
        if (estadoMes) {
            estadoMes.innerHTML = '<small class="text-yellow-400">Creando gráfico...</small>';
        }
        
        try {
            // Verificar que haya datos
            if (!expedientesPorMesData || expedientesPorMesData.length === 0) {
                console.warn('⚠️ No hay datos para el gráfico de mes');
                if (estadoMes) {
                    estadoMes.innerHTML = '<small class="text-red-400">❌ No hay datos disponibles</small>';
                }
                return;
            }
            
            // Preparar datos para el gráfico
            const labels = expedientesPorMesData.map(item => item.mes);
            const data = expedientesPorMesData.map(item => item.total);
            
            console.log('📋 Labels para gráfico:', labels);
            console.log('📊 Data para gráfico:', data);
            
            new Chart(expedientesPorMesChart, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Expedientes',
                        data: data,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#f4f4f5' }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#9ca3af' },
                            grid: { color: 'rgba(156, 163, 175, 0.2)' }
                        },
                        y: {
                            ticks: { color: '#9ca3af' },
                            grid: { color: 'rgba(156, 163, 175, 0.2)' }
                        }
                    }
                }
            });
            console.log('✅ Gráfico de expedientes por mes creado exitosamente');
            
            // Actualizar indicador de estado
            if (estadoMes) {
                estadoMes.innerHTML = '<small class="text-green-400">✅ Gráfico creado exitosamente</small>';
            }
        } catch (error) {
            console.error('❌ Error creando gráfico de expedientes por mes:', error);
            
            // Actualizar indicador de estado con error
            if (estadoMes) {
                estadoMes.innerHTML = '<small class="text-red-400">❌ Error: ' + error.message + '</small>';
            }
        }
    } else {
        console.error('❌ No se encontró el canvas expedientesPorMesChart');
    }
}

function crearGraficoExpedientesPorTipo(expedientesPorTipoData, colors) {
    const expedientesPorTipoChart = document.getElementById('expedientesPorTipoChart');
    if (expedientesPorTipoChart) {
        console.log('🎯 Creando gráfico de expedientes por tipo');
        console.log('📊 Datos recibidos:', expedientesPorTipoData);
        
        // Actualizar indicador de estado
        const estadoTipo = document.getElementById('estadoGraficoTipo');
        if (estadoTipo) {
            estadoTipo.innerHTML = '<small class="text-yellow-400">Creando gráfico...</small>';
        }
        
        try {
            // Verificar que haya datos
            if (!expedientesPorTipoData || expedientesPorTipoData.length === 0) {
                console.warn('⚠️ No hay datos para el gráfico de tipo');
                if (estadoTipo) {
                    estadoTipo.innerHTML = '<small class="text-red-400">❌ No hay datos disponibles</small>';
                }
                return;
            }
            
            // Preparar datos para el gráfico
            const labels = expedientesPorTipoData.map(item => item.tipo_expediente || 'Sin Tipo');
            const data = expedientesPorTipoData.map(item => item.total);
            
            console.log('📋 Labels para gráfico:', labels);
            console.log('📊 Data para gráfico:', data);
            
            new Chart(expedientesPorTipoChart, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors.slice(0, expedientesPorTipoData.length),
                        borderWidth: 2,
                        borderColor: '#1f2937'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#f4f4f5' }
                        }
                    }
                }
            });
            console.log('✅ Gráfico de expedientes por tipo creado exitosamente');
            
            // Actualizar indicador de estado
            if (estadoTipo) {
                estadoTipo.innerHTML = '<small class="text-green-400">✅ Gráfico creado exitosamente</small>';
            }
        } catch (error) {
            console.error('❌ Error creando gráfico de expedientes por tipo:', error);
            
            // Actualizar indicador de estado con error
            if (estadoTipo) {
                estadoTipo.innerHTML = '<small class="text-red-400">❌ Error: ' + error.message + '</small>';
            }
        }
    } else {
        console.error('❌ No se encontró el canvas expedientesPorTipoChart');
    }
}

function crearGraficoExpedientesPorEstado(expedientesPorEstadoData, colors) {
    const expedientesPorEstadoChart = document.getElementById('expedientesPorEstadoChart');
    if (expedientesPorEstadoChart) {
        console.log('🎯 Creando gráfico de expedientes por estado');
        console.log('📊 Datos recibidos:', expedientesPorEstadoData);
        
        // Actualizar indicador de estado
        const estadoEstado = document.getElementById('estadoGraficoEstado');
        if (estadoEstado) {
            estadoEstado.innerHTML = '<small class="text-yellow-400">Creando gráfico...</small>';
        }
        
        try {
            // Verificar que haya datos
            if (!expedientesPorEstadoData || expedientesPorEstadoData.length === 0) {
                console.warn('⚠️ No hay datos para el gráfico de estado');
                if (estadoEstado) {
                    estadoEstado.innerHTML = '<small class="text-red-400">❌ No hay datos disponibles</small>';
                }
                return;
            }
            
            // Preparar datos para el gráfico
            const labels = expedientesPorEstadoData.map(item => item.estado_actual || 'Sin Estado');
            const data = expedientesPorEstadoData.map(item => item.total);
            
            console.log('📋 Labels para gráfico:', labels);
            console.log('📊 Data para gráfico:', data);
            
            new Chart(expedientesPorEstadoChart, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Expedientes',
                        data: data,
                        backgroundColor: colors.slice(0, expedientesPorEstadoData.length),
                        borderWidth: 0,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#9ca3af' },
                            grid: { color: 'rgba(156, 163, 175, 0.2)' }
                        },
                        y: {
                            ticks: { color: '#9ca3af' },
                            grid: { color: 'rgba(156, 163, 175, 0.2)' }
                        }
                    }
                }
            });
            console.log('✅ Gráfico de expedientes por estado creado exitosamente');
            
            // Actualizar indicador de estado
            if (estadoEstado) {
                estadoEstado.innerHTML = '<small class="text-green-400">✅ Gráfico creado exitosamente</small>';
            }
        } catch (error) {
            console.error('❌ Error creando gráfico de expedientes por estado:', error);
            
            // Actualizar indicador de estado con error
            if (estadoEstado) {
                estadoEstado.innerHTML = '<small class="text-red-400">❌ Error: ' + error.message + '</small>';
            }
        }
    } else {
        console.error('❌ No se encontró el canvas expedientesPorEstadoChart');
    }
}

function crearGraficoUsuariosActivos(usuariosActivosData, colors) {
    const usuariosActivosChart = document.getElementById('usuariosActivosChart');
    if (usuariosActivosChart) {
        console.log('🎯 Creando gráfico de usuarios activos');
        console.log('📊 Datos recibidos:', usuariosActivosData);
        
        // Actualizar indicador de estado
        const estadoUsuarios = document.getElementById('estadoGraficoUsuarios');
        if (estadoUsuarios) {
            estadoUsuarios.innerHTML = '<small class="text-yellow-400">Creando gráfico...</small>';
        }
        
        try {
            // Verificar que haya datos
            if (!usuariosActivosData || usuariosActivosData.length === 0) {
                console.warn('⚠️ No hay datos para el gráfico de usuarios');
                if (estadoUsuarios) {
                    estadoUsuarios.innerHTML = '<small class="text-red-400">❌ No hay datos disponibles</small>';
                }
                return;
            }
            
            // Preparar datos para el gráfico
            const labels = usuariosActivosData.map(item => item.username);
            const data = usuariosActivosData.map(item => item.total_expedientes);
            
            console.log('📋 Labels para gráfico:', labels);
            console.log('📊 Data para gráfico:', data);
            
            new Chart(usuariosActivosChart, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Expedientes Creados',
                        data: data,
                        backgroundColor: '#10b981',
                        borderWidth: 0,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#9ca3af' },
                            grid: { color: 'rgba(156, 163, 175, 0.2)' }
                        },
                        y: {
                            ticks: { color: '#9ca3af' },
                            grid: { color: 'rgba(156, 163, 175, 0.2)' }
                        }
                    }
                }
            });
            console.log('✅ Gráfico de usuarios activos creado exitosamente');
            
            // Actualizar indicador de estado
            if (estadoUsuarios) {
                estadoUsuarios.innerHTML = '<small class="text-green-400">✅ Gráfico creado exitosamente</small>';
            }
        } catch (error) {
            console.error('❌ Error creando gráfico de usuarios activos:', error);
            
            // Actualizar indicador de estado con error
            if (estadoUsuarios) {
                estadoUsuarios.innerHTML = '<small class="text-red-400">❌ Error: ' + error.message + '</small>';
            }
        }
    } else {
        console.error('❌ No se encontró el canvas usuariosActivosChart');
    }
}

// Función de prueba para verificar Chart.js
function probarChartJS() {
    console.log('🧪 Probando Chart.js...');
    
    // Verificar que Chart.js esté disponible
    if (typeof Chart === 'undefined') {
        alert('❌ Chart.js NO está disponible');
        console.error('Chart.js no está disponible');
        return;
    }
    
    console.log('✅ Chart.js está disponible');
    
    // Crear un gráfico de prueba simple
    const testCanvas = document.createElement('canvas');
    testCanvas.id = 'testChart';
    testCanvas.style.width = '100%';
    testCanvas.style.height = '200px';
    testCanvas.style.border = '1px solid #ccc';
    testCanvas.style.margin = '10px 0';
    
    // Insertar el canvas de prueba al inicio de la página
    const container = document.querySelector('.container-fluid');
    const testDiv = document.createElement('div');
    testDiv.innerHTML = '<h4 class="text-zinc-100">Gráfico de Prueba</h4>';
    testDiv.appendChild(testCanvas);
    container.insertBefore(testDiv, container.firstChild);
    
    // Crear gráfico de prueba
    try {
        new Chart(testCanvas, {
            type: 'bar',
            data: {
                labels: ['Enero', 'Febrero', 'Marzo', 'Abril'],
                datasets: [{
                    label: 'Datos de Prueba',
                    data: [12, 19, 3, 5],
                    backgroundColor: ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#f4f4f5' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(156, 163, 175, 0.2)' }
                    },
                    y: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(156, 163, 175, 0.2)' }
                    }
                }
            }
        });
        
        console.log('✅ Gráfico de prueba creado exitosamente');
        alert('✅ Chart.js funciona correctamente! Se creó un gráfico de prueba.');
        
        // Remover el gráfico de prueba después de 5 segundos
        setTimeout(() => {
            if (testDiv.parentNode) {
                testDiv.remove();
            }
        }, 5000);
        
    } catch (error) {
        console.error('❌ Error creando gráfico de prueba:', error);
        alert('❌ Error creando gráfico de prueba: ' + error.message);
    }
}

function configurarEventos() {
    // Selector de período
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remover clase active de todos los botones
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            // Agregar clase active al botón clickeado
            this.classList.add('active');
            
            const periodo = this.dataset.period;
            if (periodo !== 'personalizado') {
                actualizarFechasPorPeriodo(periodo);
            }
        });
    });
    
    // Actualizar filtros cuando cambien las fechas
    const fechaInicio = document.getElementById('fechaInicio');
    const fechaFin = document.getElementById('fechaFin');
    
    if (fechaInicio) {
        fechaInicio.addEventListener('change', function() {
            const fechaFinValue = fechaFin ? fechaFin.value : '';
            if (fechaFinValue) {
                recargarConFiltros(this.value, fechaFinValue);
            }
        });
    }
    
    if (fechaFin) {
        fechaFin.addEventListener('change', function() {
            const fechaInicioValue = fechaInicio ? fechaInicio.value : '';
            if (fechaInicioValue) {
                recargarConFiltros(fechaInicioValue, this.value);
            }
        });
    }
}

function actualizarFechasPorPeriodo(periodo) {
    const fechaInicio = document.getElementById('fechaInicio');
    const fechaFin = document.getElementById('fechaFin');
    
    if (!fechaInicio || !fechaFin) return;
    
    const hoy = new Date();
    let fechaInicioValue, fechaFinValue;
    
    switch (periodo) {
        case 'dia':
            fechaInicioValue = fechaFinValue = hoy.toISOString().split('T')[0];
            break;
        case 'semana':
            const inicioSemana = new Date(hoy);
            inicioSemana.setDate(hoy.getDate() - hoy.getDay());
            const finSemana = new Date(inicioSemana);
            finSemana.setDate(inicioSemana.getDate() + 6);
            fechaInicioValue = inicioSemana.toISOString().split('T')[0];
            fechaFinValue = finSemana.toISOString().split('T')[0];
            break;
        case 'mes':
            fechaInicioValue = new Date(hoy.getFullYear(), hoy.getMonth(), 1).toISOString().split('T')[0];
            fechaFinValue = hoy.toISOString().split('T')[0];
            break;
        case 'trimestre':
            const mesActual = hoy.getMonth();
            const trimestre = Math.floor(mesActual / 3);
            const inicioTrimestre = new Date(hoy.getFullYear(), trimestre * 3, 1);
            fechaInicioValue = inicioTrimestre.toISOString().split('T')[0];
            fechaFinValue = hoy.toISOString().split('T')[0];
            break;
        case 'semestre':
            const mesSemestre = hoy.getMonth();
            const semestre = Math.floor(mesSemestre / 6);
            const inicioSemestre = new Date(hoy.getFullYear(), semestre * 6, 1);
            fechaInicioValue = inicioSemestre.toISOString().split('T')[0];
            fechaFinValue = hoy.toISOString().split('T')[0];
            break;
        case 'año':
            fechaInicioValue = new Date(hoy.getFullYear(), 0, 1).toISOString().split('T')[0];
            fechaFinValue = hoy.toISOString().split('T')[0];
            break;
        case 'ultimos_7_dias':
            const inicio7Dias = new Date(hoy);
            inicio7Dias.setDate(hoy.getDate() - 7);
            fechaInicioValue = inicio7Dias.toISOString().split('T')[0];
            fechaFinValue = hoy.toISOString().split('T')[0];
            break;
        case 'ultimos_30_dias':
            const inicio30Dias = new Date(hoy);
            inicio30Dias.setDate(hoy.getDate() - 30);
            fechaInicioValue = inicio30Dias.toISOString().split('T')[0];
            fechaFinValue = hoy.toISOString().split('T')[0];
            break;
        case 'ultimos_90_dias':
            const inicio90Dias = new Date(hoy);
            inicio90Dias.setDate(hoy.getDate() - 90);
            fechaInicioValue = inicio90Dias.toISOString().split('T')[0];
            fechaFinValue = hoy.toISOString().split('T')[0];
            break;
        default:
            return;
    }
    
    fechaInicio.value = fechaInicioValue;
    fechaFin.value = fechaFinValue;
    
    // Recargar con nuevos filtros
    recargarConFiltros(fechaInicioValue, fechaFinValue);
}

function recargarConFiltros(fechaInicio, fechaFin) {
    const url = new URL(window.location);
    url.searchParams.set('fecha_inicio', fechaInicio);
    url.searchParams.set('fecha_fin', fechaFin);
    window.location.href = url.toString();
}

// Funciones de exportación
function exportarReporte(tipo, formato) {
    const fechaInicio = document.getElementById('fechaInicio')?.value || '';
    const fechaFin = document.getElementById('fechaFin')?.value || '';
    
    // Construir URL de exportación
    const baseUrl = window.location.origin + window.location.pathname.replace('/reportes/', '/reportes/exportar/');
    const params = new URLSearchParams({
        tipo: tipo,
        formato: formato
    });
    
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);
    
    const url = `${baseUrl}?${params.toString()}`;
    
    // Mostrar indicador de descarga
    mostrarIndicadorDescarga(tipo, formato);
    
    // Descargar archivo
    window.open(url, '_blank');
}

function exportarGrafico(tipo, formato) {
    const fechaInicio = document.getElementById('fechaInicio')?.value || '';
    const fechaFin = document.getElementById('fechaFin')?.value || '';
    
    // Construir URL de exportación
    const baseUrl = window.location.origin + window.location.pathname.replace('/reportes/', '/reportes/exportar-grafico/');
    const params = new URLSearchParams({
        tipo: tipo,
        formato: formato
    });
    
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);
    
    const url = `${baseUrl}?${params.toString()}`;
    
    // Mostrar indicador de descarga
    mostrarIndicadorDescarga(`gráfico ${tipo}`, formato);
    
    // Descargar archivo
    window.open(url, '_blank');
}

function exportarTabla(tipo, formato) {
    const fechaInicio = document.getElementById('fechaInicio')?.value || '';
    const fechaFin = document.getElementById('fechaFin')?.value || '';
    
    // Construir URL de exportación
    const baseUrl = window.location.origin + window.location.pathname.replace('/reportes/', '/reportes/exportar-tabla/');
    const params = new URLSearchParams({
        tipo: tipo,
        formato: formato
    });
    
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fechaFin', fechaFin);
    
    const url = `${baseUrl}?${params.toString()}`;
    
    // Mostrar indicador de descarga
    mostrarIndicadorDescarga(`tabla ${tipo}`, formato);
    
    // Descargar archivo
    window.open(url, '_blank');
}

function mostrarIndicadorDescarga(tipo, formato) {
    // Crear notificación de descarga
    const notificacion = document.createElement('div');
    notificacion.className = 'alert alert-info alert-dismissible fade show position-fixed';
    notificacion.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notificacion.innerHTML = `
        <i class="bi bi-download me-2"></i>
        Descargando reporte de ${tipo} en formato ${formato.toUpperCase()}...
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notificacion);
    
    // Remover notificación después de 3 segundos
    setTimeout(() => {
        if (notificacion.parentNode) {
            notificacion.remove();
        }
    }, 3000);
}

function aplicarFiltros() {
    const fechaInicio = document.getElementById('fechaInicio')?.value || '';
    const fechaFin = document.getElementById('fechaFin')?.value || '';
    
    if (fechaInicio && fechaFin) {
        recargarConFiltros(fechaInicio, fechaFin);
    } else {
        alert('Por favor selecciona ambas fechas para aplicar los filtros.');
    }
}

function limpiarFiltros() {
    const fechaInicio = document.getElementById('fechaInicio');
    const fechaFin = document.getElementById('fechaFin');
    
    if (fechaInicio && fechaFin) {
        // Establecer fechas por defecto (último mes)
        const hoy = new Date();
        const hace30Dias = new Date(hoy);
        hace30Dias.setDate(hoy.getDate() - 30);
        
        fechaInicio.value = hace30Dias.toISOString().split('T')[0];
        fechaFin.value = hoy.toISOString().split('T')[0];
        
        // Recargar con fechas por defecto
        recargarConFiltros(fechaInicio.value, fechaFin.value);
    }
}

function cargarTablaExpedientesPorTipo(expedientesPorTipoData) {
    const tabla = document.getElementById('tablaExpedientesPorTipo');
    if (!tabla) {
        console.error('❌ No se encontró la tabla expedientesPorTipo');
        return;
    }
    
    console.log('📊 Cargando tabla de expedientes por tipo:', expedientesPorTipoData);
    
    if (!expedientesPorTipoData || expedientesPorTipoData.length === 0) {
        tabla.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No hay datos disponibles</td></tr>';
        return;
    }
    
    // Calcular total para porcentajes
    const total = expedientesPorTipoData.reduce((sum, item) => sum + item.total, 0);
    
    let html = '';
    expedientesPorTipoData.forEach(item => {
        const porcentaje = total > 0 ? ((item.total / total) * 100).toFixed(1) : '0.0';
        html += `
            <tr>
                <td>${item.tipo_expediente || 'Sin Tipo'}</td>
                <td class="text-center">${item.total}</td>
                <td class="text-center">${porcentaje}%</td>
            </tr>
        `;
    });
    
    tabla.innerHTML = html;
    console.log('✅ Tabla de expedientes por tipo cargada');
}

function cargarTablaExpedientesPorEstado(expedientesPorEstadoData) {
    const tabla = document.getElementById('tablaExpedientesPorEstado');
    if (!tabla) {
        console.error('❌ No se encontró la tabla expedientesPorEstado');
        return;
    }
    
    console.log('📊 Cargando tabla de expedientes por estado:', expedientesPorEstadoData);
    
    if (!expedientesPorEstadoData || expedientesPorEstadoData.length === 0) {
        tabla.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No hay datos disponibles</td></tr>';
        return;
    }
    
    // Calcular total para porcentajes
    const total = expedientesPorEstadoData.reduce((sum, item) => sum + item.total, 0);
    
    let html = '';
    expedientesPorEstadoData.forEach(item => {
        const porcentaje = total > 0 ? ((item.total / total) * 100).toFixed(1) : '0.0';
        html += `
            <tr>
                <td>${item.estado_actual || 'Sin Estado'}</td>
                <td class="text-center">${item.total}</td>
                <td class="text-center">${porcentaje}%</td>
            </tr>
        `;
    });
    
    tabla.innerHTML = html;
    console.log('✅ Tabla de expedientes por estado cargada');
}

function cargarTablaExpedientesPorMes(expedientesPorMesData) {
    const tabla = document.getElementById('tablaExpedientesPorMes');
    if (!tabla) {
        console.error('❌ No se encontró la tabla expedientesPorMes');
        return;
    }
    
    console.log('📊 Cargando tabla de expedientes por mes:', expedientesPorMesData);
    
    if (!expedientesPorMesData || expedientesPorMesData.length === 0) {
        tabla.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No hay datos disponibles</td></tr>';
        return;
    }
    
    let html = '';
    expedientesPorMesData.forEach((item, index) => {
        let tendencia = '';
        if (index > 0) {
            const anterior = expedientesPorMesData[index - 1].total;
            const actual = item.total;
            if (actual > anterior) {
                tendencia = '<span class="text-success">↗️ Aumentó</span>';
            } else if (actual < anterior) {
                tendencia = '<span class="text-danger">↘️ Disminuyó</span>';
            } else {
                tendencia = '<span class="text-muted">→ Igual</span>';
            }
        } else {
            tendencia = '<span class="text-muted">-</span>';
        }
        
        html += `
            <tr>
                <td>${item.mes}</td>
                <td class="text-center">${item.total}</td>
                <td class="text-center">${tendencia}</td>
            </tr>
        `;
    });
    
    tabla.innerHTML = html;
    console.log('✅ Tabla de expedientes por mes cargada');
}

function cargarTablaUsuariosActivos(usuariosActivosData) {
    const tabla = document.getElementById('tablaUsuariosActivos');
    if (!tabla) {
        console.error('❌ No se encontró la tabla usuariosActivos');
        return;
    }
    
    console.log('📊 Cargando tabla de usuarios activos:', usuariosActivosData);
    
    if (!usuariosActivosData || usuariosActivosData.length === 0) {
        tabla.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No hay datos disponibles</td></tr>';
        return;
    }
    
    let html = '';
    usuariosActivosData.forEach((item, index) => {
        const ranking = index + 1;
        let rankingClass = '';
        if (ranking === 1) rankingClass = 'text-warning fw-bold';
        else if (ranking === 2) rankingClass = 'text-muted fw-bold';
        else if (ranking === 3) rankingClass = 'text-info fw-bold';
        
        html += `
            <tr>
                <td>${item.username}</td>
                <td class="text-center">${item.total_expedientes}</td>
                <td class="text-center ${rankingClass}">#${ranking}</td>
            </tr>
        `;
    });
    
    tabla.innerHTML = html;
    console.log('✅ Tabla de usuarios activos cargada');
}
