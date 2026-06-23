"""
OSAT Tracer — Views del frontend (datos falsos para probar templates)
Reemplaza esto con queries reales cuando el backend esté listo.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import json

# ── Contexto base compartido por todos ──────────────────────────
def _base_ctx(role='Administrador', unread=3):
    """Contexto mínimo que necesita el topbar y sidebar."""
    return {
        'user_role': role,
        'unread_count': unread,
        'recent_notifications': [
            {'titulo': 'Lote LOT-2026-0047 en Hold', 'tipo': 'hold', 'creada_en_display': 'hace 5 min', 'leida': False},
            {'titulo': 'Stock crítico: Resina EMC', 'tipo': 'critico', 'creada_en_display': 'hace 20 min', 'leida': False},
            {'titulo': 'Lote LOT-2026-0041 completado', 'tipo': 'exito', 'creada_en_display': 'hace 1h', 'leida': True},
        ],
        'breadcrumbs': [],
    }


# ════════════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════════════

def login_view(request):
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user:
            login(request, user)
            role = getattr(user, 'perfil', {}).get('rol', 'admin') if hasattr(user, 'perfil') else 'admin'
            if role == 'supervisor':
                return redirect('supervisor_dashboard')
            if role == 'operador':
                return redirect('operator_dashboard')
            return redirect('admin_dashboard')
        from django.contrib import messages
        messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'base/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ════════════════════════════════════════════════════════════════
# ADMIN
# ════════════════════════════════════════════════════════════════

def admin_organizacion(request):
    ctx = _base_ctx('Administrador', 3)
    ctx.update({
        'plantillas': [
            {'pk': 1, 'nombre': 'OSAT Estándar', 'descripcion': 'Proceso estándar de ensamblado OSAT', 'activo': True, 'pasos_count': 12},
            {'pk': 2, 'nombre': 'OSAT Express',  'descripcion': 'Proceso optimizado para entregas rápidas', 'activo': True, 'pasos_count': 8},
        ],
        'tipos_oblea': [
            {'pk': 1, 'codigo': 'OBL-8IN',  'nombre': 'Oblea 8 pulgadas 65nm',  'dies_maximos': 1200, 'activo': True},
            {'pk': 2, 'codigo': 'OBL-12IN', 'nombre': 'Oblea 12 pulgadas 28nm', 'dies_maximos': 3500, 'activo': True},
        ],
        'lineas': [
            {'pk': 1, 'nombre': 'Línea A', 'planta': 'Planta Norte', 'activo': True,  'proceso_asignado': 'OSAT Estándar'},
            {'pk': 2, 'nombre': 'Línea B', 'planta': 'Planta Norte', 'activo': True,  'proceso_asignado': 'OSAT Express'},
            {'pk': 3, 'nombre': 'Línea C', 'planta': 'Planta Sur',   'activo': False, 'proceso_asignado': None},
        ],
        'kpi_cards': [
            {
                'nombre': 'Yield', 'key': 'yield', 'unidad': '%',
                'verde': 95, 'amarillo': 85, 'rojo': 75,
                'label_verde': '≥ 95%', 'label_amarillo': '85 – 95%', 'label_rojo': '< 75%',
            },
            {
                'nombre': 'Throughput', 'key': 'throughput', 'unidad': '▲',
                'verde': 200, 'amarillo': 150, 'rojo': 100,
                'label_verde': '≥ 200und/hora', 'label_amarillo': '150 – 200und/hora', 'label_rojo': '< 100und/hora',
            },
            {
                'nombre': 'OEE', 'key': 'oee', 'unidad': '%',
                'verde': 85, 'amarillo': 70, 'rojo': 55,
                'label_verde': '≥ 85%', 'label_amarillo': '70 – 85%', 'label_rojo': '< 55%',
            },
        ],
        'breadcrumbs': [{'label': 'Organización', 'url': '/admin/organizacion/'}],
    })
    return render(request, 'admin/organizacion.html', ctx)


def admin_dashboard(request):
    ctx = _base_ctx('Administrador', 3)

    # Umbrales (en producción vendrían de la BD)
    th = {
        'yield':      {'verde': 95, 'amarillo': 85},
        'throughput': {'verde': 200, 'amarillo': 150},
        'oee':        {'verde': 85, 'amarillo': 70},
    }

    def semaforo_color(valor, tipo, unidad='%'):
        """Devuelve dict con bg, color y valor formateado."""
        t = th[tipo]
        if valor >= t['verde']:
            bg, color = '#D4EDDA', '#155724'
        elif valor >= t['amarillo']:
            bg, color = '#FFF3CD', '#856404'
        else:
            bg, color = '#F8D7DA', '#721C24'
        val_str = f"{valor:.1f}" if isinstance(valor, float) else str(valor)
        return {'bg': bg, 'color': color, 'valor': val_str, 'unidad': unidad}

    semaforo_kpi = [
        {
            'nombre': 'Yield',
            'celdas': [
                semaforo_color(94.2, 'yield'),
                semaforo_color(91.5, 'yield'),
                semaforo_color(88.3, 'yield'),
                semaforo_color(91.3, 'yield'),
            ]
        },
        {
            'nombre': 'Throughput',
            'celdas': [
                semaforo_color(210, 'throughput', ''),
                semaforo_color(185, 'throughput', ''),
                semaforo_color(95,  'throughput', ''),
                semaforo_color(163, 'throughput', ''),
            ]
        },
        {
            'nombre': 'OEE',
            'celdas': [
                semaforo_color(88.1, 'oee'),
                semaforo_color(82.4, 'oee'),
                semaforo_color(71.2, 'oee'),
                semaforo_color(80.6, 'oee'),
            ]
        },
    ]

    ordenes_activas = [
        {'numero': 'ORD-2026-042', 'proceso': 'OSAT Estándar', 'completados': 5, 'total': 8,  'pct': 63, 'estado': 'en_proceso'},
        {'numero': 'ORD-2026-043', 'proceso': 'OSAT Express',  'completados': 0, 'total': 5,  'pct': 0,  'estado': 'pendiente'},
        {'numero': 'ORD-2026-044', 'proceso': 'OSAT Estándar', 'completados': 2, 'total': 10, 'pct': 20, 'estado': 'en_proceso'},
    ]

    ctx.update({
        'kpi': {
            'cuentas': 24, 'empleados': 87, 'maquinas': 12,
            'lotes_hold': 3, 'lotes_hold_delta': '+5.2%',
        },
        'throughput_labels': ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
        'throughput_data':   [7200, 8100, 8900, 7800, 9200, 8500, 9800, 10200, 9500, 10800, 11200, 11800],
        'semaforo_kpi': semaforo_kpi,
        'ordenes_activas': ordenes_activas,
        'alertas_activas': [
            {'tipo': 'critico',     'descripcion': 'Stock crítico: Resina EMC',            'referencia': 'MAT-001',      'tiempo': 'hace 5 min'},
            {'tipo': 'hold',        'descripcion': 'Lote LOT-2026-047 en Hold',            'referencia': 'LOT-2026-047', 'tiempo': 'hace 20 min'},
            {'tipo': 'advertencia', 'descripcion': 'KPI Throughput bajo umbral — Línea C', 'referencia': 'Línea C',      'tiempo': 'hace 1h'},
        ],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/admin-dash/'}],
    })
    return render(request, 'admin/dashboard.html', ctx)


def admin_cuentas(request):
    ctx = _base_ctx('Administrador', 3)
    ctx.update({
        'cuentas': [
            {'pk': 1, 'user': _u('jgarcia', 'Juan García'), 'rol': 'admin', 'activo': True, 'fecha_contrato': '2024-01-15'},
            {'pk': 2, 'user': _u('mlopez', 'María López'), 'rol': 'supervisor', 'activo': True, 'fecha_contrato': '2024-03-01'},
            {'pk': 3, 'user': _u('ptorres', 'Pedro Torres'), 'rol': 'operador', 'activo': True, 'fecha_contrato': '2024-06-10'},
            {'pk': 4, 'user': _u('aruiz', 'Ana Ruiz'), 'rol': 'operador', 'activo': False, 'fecha_contrato': '2023-11-20'},
        ],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/admin-dash/'}, {'label': 'Cuentas', 'url': '/admin/cuentas/'}],
    })
    return render(request, 'admin/cuentas.html', ctx)


def admin_personal(request):
    ctx = _base_ctx('Administrador', 3)
    ctx.update({
        'empleados': [
            {'pk': 1, 'primer_nombre': 'Juan', 'apellido_paterno': 'García', 'apellido_materno': 'Mendoza', 'rfc': 'GAMJ900101ABC', 'rol': _obj('Operador'), 'estado': _obj('Activo'), 'fecha_contrato': '2024-01-15'},
            {'pk': 2, 'primer_nombre': 'María', 'apellido_paterno': 'López', 'apellido_materno': 'Ruiz', 'rfc': 'LORM850215DEF', 'rol': _obj('Supervisor'), 'estado': _obj('Activo'), 'fecha_contrato': '2024-03-01'},
            {'pk': 3, 'primer_nombre': 'Pedro', 'apellido_paterno': 'Torres', 'apellido_materno': 'Soto', 'rfc': 'TOSP920530GHI', 'rol': _obj('Operador'), 'estado': _obj('Inactivo'), 'fecha_contrato': '2023-11-20'},
        ],
        'roles_list': [_obj('Administrador'), _obj('Supervisor'), _obj('Operador')],
        'estados_empleado': [_estado('Activo', '#16A85E'), _estado('Inactivo', '#718096'), _estado('Suspendido', '#EF5350')],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/admin-dash/'}, {'label': 'Personal', 'url': '/admin/personal/'}],
    })
    return render(request, 'admin/personal.html', ctx)


def admin_maquinaria(request):
    ctx = _base_ctx('Administrador', 3)
    ctx.update({
        'maquinas': [
            {'pk': 1, 'id_maquina': 'MQ-001', 'tipo': _obj('Wire Bonder'), 'linea': _obj('Línea A'), 'estado': _obj('Disponible'), 'operador_actual': None, 'created_at': '2024-01-10'},
            {'pk': 2, 'id_maquina': 'MQ-002', 'tipo': _obj('Die Attach Machine'), 'linea': _obj('Línea A'), 'estado': _obj('Ocupada'), 'operador_actual': _empleado('Juan García'), 'created_at': '2024-01-10'},
            {'pk': 3, 'id_maquina': 'MQ-003', 'tipo': _obj('Dicing Saw'), 'linea': _obj('Línea B'), 'estado': _obj('Mantenimiento'), 'operador_actual': None, 'created_at': '2024-02-05'},
            {'pk': 4, 'id_maquina': 'MQ-004', 'tipo': _obj('Molding Press'), 'linea': _obj('Línea A'), 'estado': _obj('Disponible'), 'operador_actual': _empleado('Pedro Torres'), 'created_at': '2024-03-01'},
        ],
        'tipos_maquina': [_obj('Wire Bonder'), _obj('Die Attach Machine'), _obj('Dicing Saw'), _obj('Molding Press'), _obj('Laser Marker'), _obj('ATE Handler')],
        'estados_maquina': [_obj('Disponible'), _obj('Ocupada'), _obj('Mantenimiento'), _obj('Fuera de servicio')],
        'lineas': [_obj('Línea A'), _obj('Línea B'), _obj('Línea C')],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/admin-dash/'}, {'label': 'Maquinaria', 'url': '/admin/maquinaria/'}],
    })
    return render(request, 'admin/maquinaria.html', ctx)

def admin_inventario(request):
    ctx = _base_ctx('Administrador', 3)
    ctx.update({
        'piezas': [
            {'pk': 1, 'codigo': 'MAT-001', 'nombre': 'Resina EMC',         'descripcion': 'Compuesto epoxi para moldeo',  'stock': 0,    'stock_minimo': 50,  'linea': 'Línea A', 'operador': 'Juan Torres',  'fecha_registro': '2024-01-10'},
            {'pk': 2, 'codigo': 'MAT-002', 'nombre': 'Hilo de cobre 25µm', 'descripcion': 'Wire bonding copper wire',      'stock': 12,   'stock_minimo': 100, 'linea': 'Línea A', 'operador': 'Ana López',    'fecha_registro': '2024-01-15'},
            {'pk': 3, 'codigo': 'MAT-003', 'nombre': 'Adhesivo epoxi DAF', 'descripcion': 'Die attach film adhesive',      'stock': 280,  'stock_minimo': 50,  'linea': 'Línea B', 'operador': 'Sin asignar',  'fecha_registro': '2024-02-01'},
            {'pk': 4, 'codigo': 'MAT-004', 'nombre': 'Sustrato BGA 256',   'descripcion': 'Substrate 256-ball array',      'stock': 1500, 'stock_minimo': 200, 'linea': 'Línea B', 'operador': 'Sin asignar',  'fecha_registro': '2024-03-01'},
            {'pk': 5, 'codigo': 'MAT-005', 'nombre': 'Cinta UV dicing',    'descripcion': 'UV release dicing tape',        'stock': 45,   'stock_minimo': 30,  'linea': 'Línea C', 'operador': 'Sin asignar',  'fecha_registro': '2024-03-15'},
        ],
        'categorias': [],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/admin-dash/'}, {'label': 'Inventario', 'url': '/admin/inventario/'}],
    })
    return render(request, 'admin/inventario.html', ctx)


def admin_produccion(request):
    ctx = _base_ctx('Administrador', 3)

    ordenes = [
        {'pk': 1, 'numero': 'ORD-2026-042', 'proceso': 'OSAT Estándar', 'fecha_inicio': '2026-06-01', 'fecha_fin': '2026-06-15', 'total_lotes': 8,  'completados': 5, 'pct': 63, 'estado': 'en_proceso'},
        {'pk': 2, 'numero': 'ORD-2026-041', 'proceso': 'OSAT Estándar', 'fecha_inicio': '2026-05-20', 'fecha_fin': '2026-06-03', 'total_lotes': 6,  'completados': 6, 'pct': 100,'estado': 'aprobado'},
        {'pk': 3, 'numero': 'ORD-2026-040', 'proceso': 'OSAT Express',  'fecha_inicio': '2026-05-15', 'fecha_fin': '2026-05-25', 'total_lotes': 4,  'completados': 2, 'pct': 50, 'estado': 'rechazado'},
        {'pk': 4, 'numero': 'ORD-2026-043', 'proceso': 'OSAT Express',  'fecha_inicio': '2026-06-10', 'fecha_fin': '2026-06-20', 'total_lotes': 5,  'completados': 0, 'pct': 0,  'estado': 'pendiente'},
    ]

    lotes = [
        {
            'pk': 1, 'orden_pk': 1, 'folio': 'LOT-2026-001',
            'proceso': 'OSAT Estándar', 'fecha_inicio': '2026-06-01', 'fecha_fin': '2026-06-15',
            'total_pasos': 6, 'pasos_completados': 3, 'estado': 'en_proceso',
            'dies_iniciales': 1200, 'dies_activos': 1180, 'scrap': 20, 'yield_pct': 98.3,
            'etapas': [
                {'nombre': 'Recepción oblea', 'estado': 'aprobado', 'meta': 'Ana López · N/A · 08:00 → 08:30', 'detalle': None},
                {'nombre': 'Die Attach',      'estado': 'aprobado', 'meta': 'Juan Torres · MQ-001 · 08:35 → 10:15',
                 'detalle': {'defectos': ['2 dies mal posicionados'], 'materiales': ['Pasta conductora 15g']}},
                {'nombre': 'Wire Bonding',    'estado': 'en_curso',  'meta': 'Juan Torres · MQ-002 · 10:20 (en curso)', 'detalle': None},
                {'nombre': 'Encapsulado',     'estado': 'pendiente', 'meta': None, 'detalle': None},
                {'nombre': 'Marcado laser',   'estado': 'pendiente', 'meta': None, 'detalle': None},
                {'nombre': 'Inspección final','estado': 'pendiente', 'meta': None, 'detalle': None},
            ]
        },
        {
            'pk': 2, 'orden_pk': 1, 'folio': 'LOT-2026-002',
            'proceso': 'OSAT Estándar', 'fecha_inicio': '2026-06-02', 'fecha_fin': '2026-06-15',
            'total_pasos': 6, 'pasos_completados': 1, 'estado': 'en_proceso',
            'dies_iniciales': 1200, 'dies_activos': 1200, 'scrap': 0, 'yield_pct': 100,
            'etapas': [
                {'nombre': 'Recepción oblea', 'estado': 'aprobado', 'meta': 'Ana López · N/A · 09:00 → 09:30', 'detalle': None},
                {'nombre': 'Die Attach',      'estado': 'en_curso',  'meta': 'Pedro Torres · MQ-001 · 09:45 (en curso)', 'detalle': None},
                {'nombre': 'Wire Bonding',    'estado': 'pendiente', 'meta': None, 'detalle': None},
                {'nombre': 'Encapsulado',     'estado': 'pendiente', 'meta': None, 'detalle': None},
                {'nombre': 'Marcado laser',   'estado': 'pendiente', 'meta': None, 'detalle': None},
                {'nombre': 'Inspección final','estado': 'pendiente', 'meta': None, 'detalle': None},
            ]
        },
    ]

    plantillas = [
        {'pk': 1, 'nombre': 'OSAT Estándar'},
        {'pk': 2, 'nombre': 'OSAT Express'},
    ]

    ctx.update({
        'ordenes': ordenes,
        'lotes': lotes,
        'plantillas': plantillas,
        'ordenes_json': json.dumps(ordenes),
        'lotes_json': json.dumps(lotes),
        'breadcrumbs': [{'label': 'Producción', 'url': '/admin/produccion/'}],
    })
    return render(request, 'admin/produccion.html', ctx)


def admin_configuracion(request):
    ctx = _base_ctx('Administrador', 3)
    ctx.update({
        'kpi_configs': [],   # vacío = muestra los cards por defecto
        'tipos_defecto': [
            {'pk': 1, 'codigo': 'DEF-01', 'nombre': 'Wire bond desalineado', 'categoria': 'Visual', 'activo': True},
            {'pk': 2, 'codigo': 'DEF-02', 'nombre': 'Die mal posicionado', 'categoria': 'Dimensional', 'activo': True},
            {'pk': 3, 'codigo': 'DEF-03', 'nombre': 'Delamination', 'categoria': 'Mecánico', 'activo': True},
            {'pk': 4, 'codigo': 'DEF-04', 'nombre': 'Cortocircuito', 'categoria': 'Eléctrico', 'activo': True},
        ],
        'turnos': [
            {'pk': 1, 'nombre': 'Matutino', 'hora_inicio': '06:00', 'hora_fin': '14:00', 'dias_display': 'Lun–Vie', 'activo': True},
            {'pk': 2, 'nombre': 'Vespertino', 'hora_inicio': '14:00', 'hora_fin': '22:00', 'dias_display': 'Lun–Vie', 'activo': True},
            {'pk': 3, 'nombre': 'Nocturno', 'hora_inicio': '22:00', 'hora_fin': '06:00', 'dias_display': 'Lun–Vie', 'activo': False},
        ],
        'notif_configs': [],
        'estados_sistema': {},
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/admin-dash/'}, {'label': 'Configuración', 'url': '/admin/configuracion/'}],
    })
    return render(request, 'admin/configuracion.html', ctx)


def admin_notificaciones(request):
    return redirect('admin_dashboard')


def admin_reportes(request):
    return redirect('supervisor_reportes')


# ════════════════════════════════════════════════════════════════
# STUBS DE URLs que usan los templates (para que no exploten)
# ════════════════════════════════════════════════════════════════

def stub_post(request):
    """Recibe POSTs de formularios y redirige de vuelta."""
    ref = request.META.get('HTTP_REFERER', '/')
    return redirect(ref)


# ════════════════════════════════════════════════════════════════
# SUPERVISOR
# ════════════════════════════════════════════════════════════════

def supervisor_dashboard(request):
    ctx = _base_ctx('Supervisor', 2)
    ctx.update({
        'kpi': {'yield_pct': 94.2, 'throughput': 520, 'oee': 87.1},
        'kpi_thresholds': {
            'yield_verde': 90, 'yield_amarillo': 75,
            'throughput_verde': 500, 'throughput_amarillo': 350,
            'oee_verde': 85, 'oee_amarillo': 70,
        },
        'lotes_activos': [
            {'pk': 1, 'folio': 'LOT-2026-0047', 'orden': _orden('ORD-2026-012'), 'etapa_actual': _obj('Wire Bonding'), 'operador_actual': _empleado('Juan García'), 'tiempo_en_etapa': '1h 23min'},
            {'pk': 2, 'folio': 'LOT-2026-0048', 'orden': _orden('ORD-2026-012'), 'etapa_actual': _obj('Die Attach'), 'operador_actual': _empleado('Pedro Torres'), 'tiempo_en_etapa': '45min'},
            {'pk': 3, 'folio': 'LOT-2026-0049', 'orden': _orden('ORD-2026-013'), 'etapa_actual': _obj('Molding'), 'operador_actual': None, 'tiempo_en_etapa': '2h 10min'},
        ],
        'alertas': [
            {'tipo': 'critico', 'descripcion': 'Stock crítico: Resina EMC — 0 unidades', 'creada_en': _dt(), 'resuelta': False},
            {'tipo': 'advertencia', 'descripcion': 'Hilo de cobre 25µm bajo mínimo — 12 unidades', 'creada_en': _dt(), 'resuelta': False},
            {'tipo': 'advertencia', 'descripcion': 'Lote LOT-2026-0047 lleva más de 2h en Wire Bonding', 'creada_en': _dt(), 'resuelta': False},
        ],
        'alertas_activas_count': 3,
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/supervisor/'}],
    })
    return render(request, 'supervisor/dashboard.html', ctx)


def supervisor_ordenes(request):
    ctx = _base_ctx('Supervisor', 2)
    ctx.update({
        'ordenes': [
            {'pk': 1, 'numero': 'ORD-2026-012', 'proceso': _obj('Proceso WB-Standard'), 'prioridad': 'alta', 'fecha_inicio': '2026-05-01', 'fecha_fin': '2026-05-30', 'total_lotes': 10, 'lotes_completados': 7, 'pct_completados': 70, 'estado': 'activa'},
            {'pk': 2, 'numero': 'ORD-2026-013', 'proceso': _obj('Proceso WB-Standard'), 'prioridad': 'media', 'fecha_inicio': '2026-05-10', 'fecha_fin': '2026-06-10', 'total_lotes': 5, 'lotes_completados': 1, 'pct_completados': 20, 'estado': 'activa'},
            {'pk': 3, 'numero': 'ORD-2026-010', 'proceso': _obj('Proceso WB-Standard'), 'prioridad': 'baja', 'fecha_inicio': '2026-04-01', 'fecha_fin': '2026-04-30', 'total_lotes': 8, 'lotes_completados': 8, 'pct_completados': 100, 'estado': 'completada'},
        ],
        'procesos': [_obj('Proceso WB-Standard'), _obj('Proceso Flip Chip')],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/supervisor/'}, {'label': 'Órdenes', 'url': '/supervisor/ordenes/'}],
    })
    return render(request, 'supervisor/ordenes.html', ctx)


def supervisor_orden_detalle(request, pk=1):
    ctx = _base_ctx('Supervisor', 2)
    ctx.update({
        'orden': {'pk': pk, 'numero': f'ORD-2026-0{pk:02d}', 'proceso': _obj('Proceso WB-Standard'), 'prioridad': 'alta', 'fecha_inicio': '2026-05-01', 'fecha_fin': '2026-05-30', 'total_lotes': 3, 'lotes_completados': 1, 'lotes_en_proceso': 2, 'estado': 'activa'},
        'lotes': [
            {'pk': 1, 'folio': 'LOT-2026-0047', 'numero_oblea': 'WF-2026-001', 'dies_buenos': 480, 'etapa_actual': _obj('Wire Bonding'), 'estado': _obj('En proceso'), 'yield_pct': 96.5},
            {'pk': 2, 'folio': 'LOT-2026-0048', 'numero_oblea': 'WF-2026-002', 'dies_buenos': 500, 'etapa_actual': _obj('Die Attach'), 'estado': _obj('En proceso'), 'yield_pct': None},
            {'pk': 3, 'folio': 'LOT-2026-0041', 'numero_oblea': 'WF-2026-003', 'dies_buenos': 460, 'etapa_actual': _obj('Packing'), 'estado': _obj('Completado'), 'yield_pct': 94.1},
        ],
        'breadcrumbs': [{'label': 'Órdenes', 'url': '/supervisor/ordenes/'}, {'label': f'ORD-2026-0{pk:02d}', 'url': '#'}],
    })
    return render(request, 'supervisor/orden_detalle.html', ctx)


def supervisor_lotes(request):
    return redirect('supervisor_ordenes')


def supervisor_lote_detalle(request, pk=1):
    etapas = [
        {'nombre': 'Wafer Back Grinding', 'completado': True, 'activo': False, 'operador_nombre': 'Juan García', 'completado_en': _dt(), 'iniciado_en': _dt(), 'maquina': 'MQ-001', 'scrap': 2, 'yield_pct': 99.2, 'notas': 'Sin incidencias.'},
        {'nombre': 'Dicing', 'completado': True, 'activo': False, 'operador_nombre': 'Pedro Torres', 'completado_en': _dt(), 'iniciado_en': _dt(), 'maquina': 'MQ-003', 'scrap': 5, 'yield_pct': 98.9, 'notas': ''},
        {'nombre': 'Die Attach', 'completado': True, 'activo': False, 'operador_nombre': 'Juan García', 'completado_en': _dt(), 'iniciado_en': _dt(), 'maquina': 'MQ-002', 'scrap': 3, 'yield_pct': 99.4, 'notas': ''},
        {'nombre': 'Cure Oven', 'completado': True, 'activo': False, 'operador_nombre': 'Juan García', 'completado_en': _dt(), 'iniciado_en': _dt(), 'maquina': 'MQ-005', 'scrap': 0, 'yield_pct': 100, 'notas': ''},
        {'nombre': 'Wire Bonding', 'completado': False, 'activo': True, 'operador_nombre': 'Juan García', 'completado_en': None, 'iniciado_en': _dt(), 'tipo_maquina': 'Wire Bonder', 'descripcion': 'Conexión eléctrica por hilo de cobre 25µm'},
        {'nombre': 'Molding', 'completado': False, 'activo': False, 'operador_nombre': None, 'completado_en': None, 'iniciado_en': None},
        {'nombre': 'PMC Oven', 'completado': False, 'activo': False, 'operador_nombre': None, 'completado_en': None, 'iniciado_en': None},
        {'nombre': 'Laser Marking', 'completado': False, 'activo': False, 'operador_nombre': None, 'completado_en': None, 'iniciado_en': None},
        {'nombre': 'Final Test', 'completado': False, 'activo': False, 'operador_nombre': None, 'completado_en': None, 'iniciado_en': None},
        {'nombre': 'Packing', 'completado': False, 'activo': False, 'operador_nombre': None, 'completado_en': None, 'iniciado_en': None},
    ]
    ctx = _base_ctx('Supervisor', 2)
    ctx.update({
        'lote': {
            'pk': pk, 'folio': f'LOT-2026-00{pk:02d}',
            'orden': _orden('ORD-2026-012'),
            'estado': _obj('En proceso'),
            'dies_iniciales': 500, 'dies_activos': 490, 'scrap_total': 10, 'yield_pct': 96.5,
            'hold_motivo': '',
            'etapas': etapas,
            'etapa_activa': etapas[4],  # Wire Bonding activa
        },
        'tipos_defecto': [_obj('Wire bond desalineado'), _obj('Die mal posicionado'), _obj('Delamination')],
        'breadcrumbs': [{'label': 'Órdenes', 'url': '/supervisor/ordenes/'}, {'label': f'LOT-2026-00{pk:02d}', 'url': '#'}],
    })
    return render(request, 'supervisor/lote_detalle.html', ctx)


def supervisor_inventario(request):
    ctx = _base_ctx('Supervisor', 2)
    ctx.update({
        'piezas': [
            {'pk': 1, 'codigo': 'MAT-001', 'nombre': 'Resina EMC', 'descripcion': 'Compuesto epoxi para moldeo', 'stock': 0, 'stock_minimo': 50},
            {'pk': 2, 'codigo': 'MAT-002', 'nombre': 'Hilo de cobre 25µm', 'descripcion': 'Wire bonding copper wire', 'stock': 12, 'stock_minimo': 100},
            {'pk': 3, 'codigo': 'MAT-003', 'nombre': 'Adhesivo epoxi DAF', 'descripcion': 'Die attach film', 'stock': 280, 'stock_minimo': 50},
            {'pk': 4, 'codigo': 'MAT-004', 'nombre': 'Sustrato BGA 256', 'descripcion': 'Substrate 256-ball', 'stock': 1500, 'stock_minimo': 200},
        ],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/supervisor/'}, {'label': 'Inventario', 'url': '/supervisor/inventario/'}],
    })
    return render(request, 'supervisor/inventario.html', ctx)


def supervisor_reportes(request):
    ctx = _base_ctx('Supervisor', 2)
    ctx.update({
        'ordenes': [
            {'pk': 1, 'numero': 'ORD-2026-012', 'proceso': _obj('Proceso WB-Standard')},
            {'pk': 2, 'numero': 'ORD-2026-013', 'proceso': _obj('Proceso WB-Standard')},
        ],
        'reporte_orden': None,
        'reporte_inventario': [],
        'reporte_kpi': [],
        'todas_alertas': [
            {'tipo': 'critico', 'descripcion': 'Stock crítico: Resina EMC', 'referencia': 'MAT-001', 'creada_en': _dt(), 'resuelta_en': None, 'resuelta': False},
            {'tipo': 'advertencia', 'descripcion': 'KPI Yield por debajo del umbral — Línea B: 67%', 'referencia': 'KPI-YIELD', 'creada_en': _dt(), 'resuelta_en': _dt(), 'resuelta': True},
        ],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/supervisor/'}, {'label': 'Reportes', 'url': '/supervisor/reportes/'}],
    })
    return render(request, 'supervisor/reportes.html', ctx)


def supervisor_notificaciones(request):
    return redirect('supervisor_dashboard')


def supervisor_configuracion(request):
    return redirect('admin_configuracion')


def supervisor_inventario_entrada(request):
    return stub_post(request)


def supervisor_lote_hold(request, pk):
    return redirect('supervisor_lote_detalle', pk=pk)


def supervisor_lote_scrap(request, pk):
    return redirect('supervisor_lote_detalle', pk=pk)


def supervisor_lote_registrar(request):
    return stub_post(request)


def supervisor_ordenes_crear(request):
    return redirect('supervisor_ordenes')


# ════════════════════════════════════════════════════════════════
# OPERATOR
# ════════════════════════════════════════════════════════════════

def operator_dashboard(request):
    ctx = _base_ctx('Operador', 1)
    ctx.update({
        'actividades_recientes': [
            {'lote_pk': 1, 'folio': 'LOT-2026-0047', 'etapa_nombre': 'Wire Bonding', 'estado': 'En proceso', 'timestamp': _dt()},
            {'lote_pk': 3, 'folio': 'LOT-2026-0041', 'etapa_nombre': 'Packing', 'estado': 'Completado', 'timestamp': _dt()},
        ],
        'turno_activo': {'nombre': 'Turno Matutino', 'hora_inicio': '06:00', 'hora_fin': '14:00', 'linea': 'Línea A'},
        'search_error': None, 'lot_hold': None, 'lot_complete': None,
        'breadcrumbs': [{'label': 'Inicio', 'url': '/operator/'}],
    })
    return render(request, 'operator/dashboard.html', ctx)


def operator_mis_lotes(request):
    ctx = _base_ctx('Operador', 1)
    ctx.update({
        'mis_lotes': [
            {'pk': 1, 'folio': 'LOT-2026-0047', 'orden': _orden('ORD-2026-012'), 'etapa_actual': _obj('Wire Bonding'), 'estado': _obj('En proceso'), 'yield_pct': 96.5, 'ultima_actividad': _dt()},
            {'pk': 2, 'folio': 'LOT-2026-0048', 'orden': _orden('ORD-2026-012'), 'etapa_actual': _obj('Die Attach'), 'estado': _obj('Hold'), 'yield_pct': None, 'ultima_actividad': _dt()},
            {'pk': 3, 'folio': 'LOT-2026-0041', 'orden': _orden('ORD-2026-010'), 'etapa_actual': _obj('Packing'), 'estado': _obj('Completado'), 'yield_pct': 94.1, 'ultima_actividad': _dt()},
        ],
        'lotes_count': {'total': 3, 'en_proceso': 1, 'hold': 1},
        'breadcrumbs': [{'label': 'Inicio', 'url': '/operator/'}, {'label': 'Mis lotes', 'url': '/operator/mis-lotes/'}],
    })
    return render(request, 'operator/mis_lotes.html', ctx)


def operator_detalle_lote(request, pk=1):
    etapas = [
        {'nombre': 'Wafer Back Grinding', 'completado': True, 'activo': False, 'operador_nombre': 'Juan García', 'completado_en': _dt(), 'iniciado_en': _dt(), 'maquina': 'MQ-001', 'scrap': 2, 'yield_pct': 99.2, 'notas': ''},
        {'nombre': 'Dicing', 'completado': True, 'activo': False, 'operador_nombre': 'Pedro Torres', 'completado_en': _dt(), 'iniciado_en': _dt(), 'maquina': 'MQ-003', 'scrap': 5, 'yield_pct': 98.9, 'notas': ''},
        {'nombre': 'Die Attach', 'completado': True, 'activo': False, 'operador_nombre': 'Juan García', 'completado_en': _dt(), 'iniciado_en': _dt(), 'maquina': 'MQ-002', 'scrap': 3, 'yield_pct': 99.4, 'notas': 'Sin incidencias.'},
        {'nombre': 'Cure Oven', 'completado': True, 'activo': False, 'operador_nombre': 'Juan García', 'completado_en': _dt(), 'iniciado_en': _dt(), 'maquina': 'MQ-005', 'scrap': 0, 'yield_pct': 100, 'notas': ''},
        {'nombre': 'Wire Bonding', 'completado': False, 'activo': True, 'operador_nombre': None, 'completado_en': None, 'iniciado_en': _dt(), 'maquina': None, 'scrap': None, 'yield_pct': None, 'notas': ''},
        {'nombre': 'Molding', 'completado': False, 'activo': False, 'operador_nombre': None, 'completado_en': None, 'iniciado_en': None},
        {'nombre': 'PMC Oven', 'completado': False, 'activo': False, 'operador_nombre': None, 'completado_en': None, 'iniciado_en': None},
        {'nombre': 'Laser Marking', 'completado': False, 'activo': False, 'operador_nombre': None, 'completado_en': None, 'iniciado_en': None},
        {'nombre': 'Final Test', 'completado': False, 'activo': False, 'operador_nombre': None, 'completado_en': None, 'iniciado_en': None},
        {'nombre': 'Packing', 'completado': False, 'activo': False, 'operador_nombre': None, 'completado_en': None, 'iniciado_en': None},
    ]
    ctx = _base_ctx('Operador', 1)
    ctx.update({
        'lote': {
            'pk': pk, 'folio': f'LOT-2026-00{pk:02d}',
            'orden': _orden('ORD-2026-012'),
            'estado': _obj('En proceso'),
            'dies_iniciales': 500, 'dies_activos': 490, 'scrap_total': 10, 'yield_pct': 96.5,
            'hold_motivo': '',
            'etapas': etapas,
        },
        'breadcrumbs': [{'label': 'Mis lotes', 'url': '/operator/mis-lotes/'}, {'label': f'LOT-2026-00{pk:02d}', 'url': '#'}],
    })
    return render(request, 'operator/detalle_lote.html', ctx)


def operator_notificaciones(request):
    ctx = _base_ctx('Operador', 1)
    ctx.update({
        'notificaciones': [
            {'pk': 1, 'titulo': 'Lote LOT-2026-0047 en Hold', 'cuerpo': 'Anomalía detectada en el patrón de bonding. Contacta al supervisor antes de continuar.', 'tipo': 'hold', 'creada_en': _dt(), 'leida': False, 'referencia_tipo': 'Lote', 'referencia_valor': 'LOT-2026-0047', 'accion_url': '/operator/lote/1/', 'accion_label': 'Ver lote'},
            {'pk': 2, 'titulo': 'Stock crítico: Resina EMC', 'cuerpo': 'El stock de Resina EMC ha llegado a 0. La producción puede verse afectada.', 'tipo': 'critico', 'creada_en': _dt(), 'leida': False, 'referencia_tipo': 'Material', 'referencia_valor': 'MAT-001', 'accion_url': '', 'accion_label': ''},
            {'pk': 3, 'titulo': 'Lote LOT-2026-0041 completado', 'cuerpo': 'El lote LOT-2026-0041 completó todos los pasos del proceso exitosamente.', 'tipo': 'exito', 'creada_en': _dt(), 'leida': True, 'referencia_tipo': 'Lote', 'referencia_valor': 'LOT-2026-0041', 'accion_url': '/operator/lote/3/', 'accion_label': 'Ver lote'},
        ],
        'notificacion_activa': None,
        'breadcrumbs': [{'label': 'Inicio', 'url': '/operator/'}, {'label': 'Notificaciones', 'url': '/operator/notificaciones/'}],
    })
    return render(request, 'operator/notificaciones.html', ctx)


def operator_perfil(request):
    return redirect('operator_dashboard')


def operator_buscar_lote(request):
    return redirect('operator_dashboard')


def operator_marcar_todas_leidas(request):
    return redirect('operator_notificaciones')


# ════════════════════════════════════════════════════════════════
# STUBS — URLs que los templates intentan resolver con {% url %}
# ════════════════════════════════════════════════════════════════

def admin_cuentas_crear(request): return stub_post(request)
def admin_personal_crear(request): return stub_post(request)
def admin_maquinaria_crear(request): return stub_post(request)
def admin_inventario_crear(request): return stub_post(request)
def admin_inventario_movimiento(request): return stub_post(request)
def admin_produccion_plantilla_crear(request): return stub_post(request)
def admin_config_kpi_save(request): return stub_post(request)
def admin_config_turno_crear(request): return stub_post(request)
def admin_config_defecto_crear(request): return stub_post(request)
def admin_config_change_password(request): return stub_post(request)


# ════════════════════════════════════════════════════════════════
# HELPERS — objetos falsos para simular modelos Django
# ════════════════════════════════════════════════════════════════

class _FakeObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        return getattr(self, 'nombre', getattr(self, 'username', ''))

    # Para que timesince funcione
    def strftime(self, fmt):
        return '10:30'


def _obj(nombre):
    return _FakeObj(pk=1, nombre=nombre)


def _u(username, fullname):
    parts = fullname.split()
    obj = _FakeObj(pk=1, username=username, first_name=parts[0], last_name=' '.join(parts[1:]))
    obj.get_full_name = lambda: fullname
    return obj


def _empleado(nombre):
    parts = nombre.split()
    return _FakeObj(pk=1, primer_nombre=parts[0], apellido_paterno=parts[1] if len(parts) > 1 else '', apellido_materno='')


def _orden(numero):
    return _FakeObj(pk=1, numero=numero)


def _estado(nombre, color='#16A85E'):
    return _FakeObj(pk=1, nombre=nombre, color=color)


def _dt():
    """Objeto fecha falso compatible con |date y |timesince."""
    from datetime import datetime, timezone
    return datetime(2026, 5, 16, 10, 30, tzinfo=timezone.utc)



def admin_organizacion_plantilla_crear(request): return stub_post(request)
def admin_organizacion_plantilla_editar(request, pk): return stub_post(request)
def admin_organizacion_oblea_crear(request): return stub_post(request)
def admin_organizacion_linea_crear(request): return stub_post(request)
