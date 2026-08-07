/* OSAT Tracer v2 — UI Helpers */

/* ── Sidebar toggle ── */
function toggleSidebar() {
  var sidebar = document.getElementById('main-sidebar');
  if (!sidebar) return;
  sidebar.classList.toggle('open');
  // Guardar estado
  try { localStorage.setItem('sidebar_open', sidebar.classList.contains('open')); } catch(e){}
}

document.addEventListener('DOMContentLoaded', function() {
  // Restaurar estado del sidebar
  try {
    if (localStorage.getItem('sidebar_open') === 'true') {
      var sb = document.getElementById('main-sidebar');
      if (sb) sb.classList.add('open');
    }
  } catch(e){}
});

/* ── Modal ── */
// El contenido de la página no hace scroll en <body> (el layout fija
// .app-shell a 100vh con overflow:hidden) sino en .main-content, que tiene
// su propio overflow-y:auto — bloquear solo document.body.style.overflow no
// evita que .main-content siga siendo scrolleable detrás del modal. Eso
// dejaba que listas con paginación (ej. Maquinaria) se pudieran desplazar
// por debajo del overlay mientras el modal seguía abierto, terminando
// superpuestas visualmente con él.
function _modalScrollContainer() {
  return document.querySelector('.main-content') || document.body;
}
function openModal(id) {
  var m = document.getElementById(id);
  if (m) { m.style.display = 'flex'; _modalScrollContainer().style.overflow = 'hidden'; }
}
function closeModal(id) {
  var m = document.getElementById(id);
  if (m) { m.style.display = 'none'; _modalScrollContainer().style.overflow = ''; }
}
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.style.display = 'none';
    _modalScrollContainer().style.overflow = '';
  }
});

/* ── Auto-refresh de dashboard ── Los dashboards de admin/supervisor son
   páginas renderizadas por Django (sin polling ni websockets), así que
   antes se quedaban "congeladas" hasta que alguien recargaba a mano —
   aunque los datos que muestran (semáforo KPI, órdenes activas, pasos
   completados hoy) sí se recalculan en vivo en cada request. Se recarga
   la página completa a intervalos en vez de hacer un refresco parcial vía
   AJAX porque son varias secciones independientes (kpis, semáforo, órdenes,
   alertas) y esta app no tiene un patrón de partial-render ya establecido
   para reutilizar. Se salta la recarga si la pestaña no está visible o si
   hay un modal abierto, para no interrumpir al usuario a media acción. */
function iniciarAutoRefreshDashboard(intervaloMs) {
  intervaloMs = intervaloMs || 30000;
  setInterval(function () {
    if (document.visibilityState !== 'visible') return;
    if (document.querySelector('.modal-overlay[style*="flex"]')) return;
    location.reload();
  }, intervaloMs);
}

/* ── Tabs ── */
function switchTab(tabId, btn, paneSelector) {
  paneSelector = paneSelector || '.tab-pane';
  var bar = btn.closest('.tab-bar');
  var container = bar ? bar.parentElement : document;
  container.querySelectorAll(paneSelector).forEach(function(p){ p.style.display = 'none'; });
  bar.querySelectorAll('.tab-btn').forEach(function(b){ b.classList.remove('active'); });
  var pane = document.getElementById(tabId);
  if (pane) pane.style.display = 'block';
  btn.classList.add('active');
}

/* ── Notificaciones ── Todas usan el mismo panel flotante a la derecha
   (antes había 3 estilos distintos: banner de ancho completo arriba,
   toast centrado abajo, y notif-dropdown a la derecha — ahora una sola
   clase visual y una sola duración estándar). */
var NOTIF_DURATION_MS = 6000;

function _notifStack() {
  var stack = document.querySelector('.report-notif-stack');
  if (!stack) {
    stack = document.createElement('div');
    stack.className = 'report-notif-stack';
    document.body.appendChild(stack);
  }
  return stack;
}

function _notifColor(type) {
  var colors = {success:'#16A85E', error:'#EF5350', warning:'#F5A623', info:'#009EAF'};
  return colors[type] || colors.success;
}

function showToast(message, type, duration) {
  type = type || 'success';
  duration = duration == null ? NOTIF_DURATION_MS : duration;
  var notif = document.createElement('div');
  notif.className = 'report-notif';
  notif.innerHTML =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="' + _notifColor(type) + '" stroke-width="2" style="flex-shrink:0;margin-top:2px;"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>' +
    '<div style="flex:1;min-width:0;"><div class="notif-title">' + message + '</div></div>' +
    '<button onclick="this.closest(\'.report-notif\').remove()" style="color:#A0AEC0;background:none;border:none;cursor:pointer;font-size:14px;flex-shrink:0;">&#10005;</button>';
  _notifStack().appendChild(notif);
  if (duration > 0) setTimeout(function(){ if (notif.parentNode) notif.remove(); }, duration);
}

/* ── Notificación de reporte (mismo panel, con botón "Ver") ── */
function showReportNotification(message, url, type) {
  type = type || 'success';
  var notif = document.createElement('div');
  notif.className = 'report-notif';
  notif.innerHTML =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="' + _notifColor(type) + '" stroke-width="2" style="flex-shrink:0;margin-top:2px;"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>' +
    '<div style="flex:1;min-width:0;">' +
      '<div class="notif-title">' + message + '</div>' +
      (url ? '<a class="report-notif-ver" href="' + url + '">Ver</a>' : '') +
    '</div>' +
    '<button onclick="this.closest(\'.report-notif\').remove()" style="color:#A0AEC0;background:none;border:none;cursor:pointer;font-size:14px;flex-shrink:0;">&#10005;</button>';
  _notifStack().appendChild(notif);
  setTimeout(function(){ if (notif.parentNode) notif.remove(); }, NOTIF_DURATION_MS);
}

/* ── Login: no dejar mandar el form con usuario o contraseña vacíos ──
   El form de login trae novalidate (para no depender del globo nativo del
   navegador, que no está en español ni sigue el diseño de la app) y este
   validador la reemplaza mostrando el mismo banner-error que ya se usa
   para los mensajes que manda el servidor. */
function validarLoginNoVacio(evt) {
  var usuario = document.getElementById('id_username');
  var password = document.getElementById('id_password');
  var aviso = document.getElementById('login-empty-error');
  var vacio = !usuario.value.trim() || !password.value.trim();
  if (aviso) aviso.style.display = vacio ? 'flex' : 'none';
  if (vacio && evt) evt.preventDefault();
  return !vacio;
}

/* ── Password toggle ── */
function togglePassword(inputId, btn) {
  var input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') { input.type = 'text'; btn.textContent = 'Ocultar'; }
  else { input.type = 'password'; btn.textContent = 'Ver'; }
}

/* ── Notif dropdown ── */
function toggleNotifDropdown() {
  var dd = document.getElementById('notif-dropdown');
  if (dd) dd.style.display = dd.style.display === 'none' ? 'block' : 'none';
}
document.addEventListener('click', function(e) {
  var dd = document.getElementById('notif-dropdown');
  if (dd && !dd.contains(e.target) && !e.target.closest('.topbar-bell')) {
    dd.style.display = 'none';
  }
});

/* ── Paso row (plantillas de procesos) ── */
var _pasoCount = 0;
function addPasoRow(listId) {
  _pasoCount++;
  var list = document.getElementById(listId);
  if (!list) return;
  var n = list.querySelectorAll('.paso-row').length + 1;
  var row = document.createElement('div');
  row.className = 'paso-row';
  row.style.cssText = 'display:flex;align-items:center;gap:8px;padding:8px 10px;background:var(--bg-app);border-radius:7px;border:1px solid var(--border-card);';
  row.innerHTML =
    '<span style="color:#546E7A;cursor:grab;padding:0 2px;">⠿</span>' +
    '<span style="background:var(--nav-item-bg);border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;color:#fff;flex-shrink:0;">'+n+'</span>' +
    '<input type="text" name="paso_'+_pasoCount+'" class="form-control" placeholder="Nombre del paso" style="flex:1;">' +
    '<button type="button" style="color:#EF5350;background:none;border:none;cursor:pointer;padding:4px;flex-shrink:0;" onclick="this.closest(\'.paso-row\').remove()">' +
      '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>' +
    '</button>';
  list.appendChild(row);
  row.querySelector('input').focus();
}

/* ── Paginación compacta con flechas < > (tablas de dashboard y listados) ──
   No usa Paginator de Django ni recarga la página: agrupa filas ya
   renderizadas en "páginas" del tamaño visual que ya tenía la tabla y
   muestra/oculta con display, con botones prev/next arriba a la derecha.
   Si hay menos filas que pageSize, los controles quedan ocultos —no
   tiene sentido mostrar flechas si no hay a dónde navegar.

   Convive con buscadores/filtros JS ya existentes (inventario, órdenes):
   en vez de que el filtro esconda filas directamente con style.display,
   debe marcarlas con row.dataset.filteredOut = 'true'/'' y llamar a
   pager.reset() — así el pager solo pagina sobre las filas que SÍ pasan
   el filtro, sin pelearse por quién controla el display de cada fila. */
function initRowPager(opts) {
  var tbody = typeof opts.tbody === 'string' ? document.querySelector(opts.tbody) : opts.tbody;
  var prevBtn = document.getElementById(opts.prevId);
  var nextBtn = document.getElementById(opts.nextId);
  var controls = opts.controlsId ? document.getElementById(opts.controlsId) : null;
  if (!tbody || !prevBtn || !nextBtn) return null;
  var pageSize = opts.pageSize || 5;
  var page = 0;

  function rows() {
    return Array.prototype.slice.call(tbody.querySelectorAll(opts.rowSelector || ':scope > tr'));
  }

  function render() {
    var all = rows();
    all.forEach(function (row) { if (row.dataset.filteredOut === 'true') row.style.display = 'none'; });
    var eligible = all.filter(function (row) { return row.dataset.filteredOut !== 'true'; });
    var totalPages = Math.max(1, Math.ceil(eligible.length / pageSize));
    if (page >= totalPages) page = totalPages - 1;
    if (page < 0) page = 0;
    eligible.forEach(function (row, i) {
      row.style.display = (i >= page * pageSize && i < (page + 1) * pageSize) ? '' : 'none';
    });
    prevBtn.disabled = page <= 0;
    nextBtn.disabled = page >= totalPages - 1;
    if (controls) controls.style.display = eligible.length > pageSize ? 'flex' : 'none';
  }

  prevBtn.addEventListener('click', function () { page--; render(); });
  nextBtn.addEventListener('click', function () { page++; render(); });
  render();

  return { render: render, reset: function () { page = 0; render(); } };
}

/* ── Paginación por columnas para la tabla de semáforo KPI ──
   Igual idea que initRowPager pero paginando COLUMNAS de línea de
   producción en vez de filas: la primera columna (nombre del KPI) y la
   última (Global) siempre quedan visibles; solo se pagina el bloque de
   columnas de línea intermedias, sincronizando header y cada fila del
   body por índice de columna. */
function initSemaforoPager(opts) {
  var table = typeof opts.table === 'string' ? document.querySelector(opts.table) : opts.table;
  var prevBtn = document.getElementById(opts.prevId);
  var nextBtn = document.getElementById(opts.nextId);
  if (!table || !prevBtn || !nextBtn) return null;
  var pageSize = opts.pageSize || 4;
  var page = 0;

  function middleCellsByColumn() {
    var headerRow = table.querySelector('thead tr');
    var ths = Array.prototype.slice.call(headerRow.children);
    var midCount = ths.length - 2; // menos KPI y Global
    var columns = [];
    for (var c = 1; c <= midCount; c++) {
      var cells = [ths[c]];
      table.querySelectorAll('tbody tr').forEach(function (tr) {
        cells.push(tr.children[c]);
      });
      columns.push(cells);
    }
    return columns;
  }

  function render() {
    var columns = middleCellsByColumn();
    var totalPages = Math.max(1, Math.ceil(columns.length / pageSize));
    if (page >= totalPages) page = totalPages - 1;
    if (page < 0) page = 0;
    columns.forEach(function (cells, i) {
      var visible = i >= page * pageSize && i < (page + 1) * pageSize;
      cells.forEach(function (cell) { if (cell) cell.style.display = visible ? '' : 'none'; });
    });
    prevBtn.style.display = columns.length > pageSize ? '' : 'none';
    nextBtn.style.display = columns.length > pageSize ? '' : 'none';
    prevBtn.disabled = page <= 0;
    nextBtn.disabled = page >= totalPages - 1;
  }

  prevBtn.addEventListener('click', function () { page--; render(); });
  nextBtn.addEventListener('click', function () { page++; render(); });
  render();

  return { render: render };
}
