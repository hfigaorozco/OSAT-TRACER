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
function openModal(id) {
  var m = document.getElementById(id);
  if (m) { m.style.display = 'flex'; document.body.style.overflow = 'hidden'; }
}
function closeModal(id) {
  var m = document.getElementById(id);
  if (m) { m.style.display = 'none'; document.body.style.overflow = ''; }
}
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.style.display = 'none';
    document.body.style.overflow = '';
  }
});

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

/* ── Toast ── */
function showToast(message, type, duration) {
  type = type || 'success'; duration = duration || 4000;
  var stack = document.querySelector('.toast-stack');
  if (!stack) {
    stack = document.createElement('div');
    stack.className = 'toast-stack';
    stack.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:200;display:flex;flex-direction:column;gap:8px;align-items:center;';
    document.body.appendChild(stack);
  }
  var colors = {success:'#16A85E',error:'#EF5350',warning:'#F5A623',info:'#009EAF'};
  var toast = document.createElement('div');
  toast.style.cssText = 'display:flex;align-items:center;gap:12px;padding:0 16px;height:48px;min-width:320px;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.4);font-size:13.5px;font-weight:500;background:#243040;border-left:3px solid '+(colors[type]||colors.success)+';color:#C4C5D0;';
  toast.innerHTML = '<span style="color:'+(colors[type]||colors.success)+';">●</span><span style="flex:1;">'+message+'</span><button onclick="this.closest(\'div\').remove()" style="color:#718096;font-size:16px;background:none;border:none;cursor:pointer;">✕</button>';
  stack.appendChild(toast);
  if (duration > 0) setTimeout(function(){ toast.remove(); }, duration);
}

/* ── Notificación de reporte (estilo notif-dropdown, arriba, con botón "Ver") ── */
function showReportNotification(message, url, type) {
  type = type || 'success';
  var stack = document.querySelector('.report-notif-stack');
  if (!stack) {
    stack = document.createElement('div');
    stack.className = 'report-notif-stack';
    document.body.appendChild(stack);
  }
  var colors = {success:'#16A85E',error:'#EF5350',warning:'#F5A623',info:'#009EAF'};
  var color = colors[type] || colors.success;
  var notif = document.createElement('div');
  notif.className = 'report-notif';
  notif.innerHTML =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="' + color + '" stroke-width="2" style="flex-shrink:0;margin-top:2px;"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>' +
    '<div style="flex:1;min-width:0;">' +
      '<div class="notif-title">' + message + '</div>' +
      (url ? '<a class="report-notif-ver" href="' + url + '">Ver</a>' : '') +
    '</div>' +
    '<button onclick="this.closest(\'.report-notif\').remove()" style="color:#A0AEC0;background:none;border:none;cursor:pointer;font-size:14px;flex-shrink:0;">&#10005;</button>';
  stack.appendChild(notif);
  setTimeout(function(){ if (notif.parentNode) notif.remove(); }, 12000);
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
