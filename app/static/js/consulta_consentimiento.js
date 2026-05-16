// consulta_consentimiento.js


let ciudades = []; // [{id, nombre_ciudad}]
let consentimientoData = {}; // {nombre_ciudad: [empleados]}
let activaCiudadId = null;
let filtro = '';

document.addEventListener('DOMContentLoaded', function () {
    fetch('/api/consulta_consentimiento/listado')
        .then(r => r.json())
        .then(data => {
            if (!data.ok || !data.data) return;
            consentimientoData = data.data;
            // Convertir a estructura [{id, nombre_ciudad}]
            ciudades = Object.keys(consentimientoData).map((nombre, idx) => ({ id: idx + 1, nombre_ciudad: nombre }));
            activaCiudadId = ciudades.length ? ciudades[0].id : null;
            renderTabs();
            renderTabContent();
        });
    document.getElementById('epcSearchConsentimiento').addEventListener('input', function(e) {
        filtro = e.target.value.toLowerCase();
        renderTabContent();
    });
    document.getElementById('epcBtnClearConsentimiento').addEventListener('click', function() {
        document.getElementById('epcSearchConsentimiento').value = '';
        filtro = '';
        renderTabContent();
    });
});

function renderTabs() {
    const tabs = document.getElementById('epcTabsConsentimiento');
    tabs.innerHTML = '';
    if (!ciudades.length) {
        tabs.innerHTML = '<span style="color:#94a3b8;font-size:13px;padding:7px 8px;">Sin ciudades disponibles</span>';
        return;
    }
    ciudades.forEach(ciudad => {
        const count = consentimientoData[ciudad.nombre_ciudad] ? consentimientoData[ciudad.nombre_ciudad].length : 0;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'epc-tab' + (ciudad.id === activaCiudadId ? ' active' : '');
        btn.dataset.id = ciudad.id;
        btn.innerHTML = `${ciudad.nombre_ciudad} <span class='epc-badge'>${count}</span>`;
        btn.onclick = () => {
            activaCiudadId = ciudad.id;
            renderTabs();
            renderTabContent();
        };
        tabs.appendChild(btn);
    });
}

function renderTabContent() {
    const tabContent = document.getElementById('ciudadTabContentConsentimiento');
    tabContent.innerHTML = '';
    ciudades.forEach(ciudad => {
        const show = ciudad.id === activaCiudadId;
        const empleados = (consentimientoData[ciudad.nombre_ciudad] || []).filter(emp => {
            if (!filtro) return true;
            return (
                (emp.nombre_completo || '').toLowerCase().includes(filtro) ||
                (emp.rider_id || '').toString().includes(filtro) ||
                (emp.cod_activo || '').toString().includes(filtro) ||
                (emp.telefono || '').toString().includes(filtro)
            );
        });
        const content = document.createElement('div');
        content.className = `tab-pane fade${show ? ' show active' : ''}`;
        content.id = `content-consent-${ciudad.id}`;
        content.role = 'tabpanel';
        content.innerHTML = tablaConsentimiento(ciudad.nombre_ciudad, empleados);
        if (show) {
            tabContent.appendChild(content);
        }
    });
}

function tablaConsentimiento(ciudad, empleados) {
    let html = `<div style='font-weight:600;margin-bottom:8px;'>${ciudad} <span style='color:#888;font-weight:400;font-size:14px;'>${empleados.length} empleados</span></div>`;
    html += `<div class=\"table-responsive\"><table class=\"epc-table\">\n        <thead><tr>\n            <th>RIDER</th>\n            <th>COD. ACTIVO</th>\n            <th>NOMBRE COMPLETO</th>\n            <th>TELÉFONO</th>\n            <th>CONSENTIMIENTO</th>\n        </tr></thead><tbody>`;
    if (empleados.length === 0) {
        html += `<tr><td colspan=\"5\" style=\"text-align:center;color:#888;\">Sin empleados en esta ciudad</td></tr>`;
    } else {
        empleados.forEach(emp => {
            html += `<tr>\n                <td>${emp.rider_id || ''}</td>\n                <td>${emp.cod_activo || ''}</td>\n                <td>${emp.nombre_completo || ''}</td>\n                <td>${emp.telefono || ''}</td>\n                <td style=\"text-align:center;\">${emp.consentimiento ? '<span style=\"color:green;font-weight:bold;\">✔️</span>' : '<span style=\"color:red;font-weight:bold;\">❌</span>'}</td>\n            </tr>`;
        });
    }
    html += '</tbody></table></div>';
    return html;
}
