// Utilities for rider_operativo: list, create and populate selects
(function(){
window.RIDER = window.RIDER || {};

// Fetch rider_operativo rows for an empleado
async function fetchRidersByEmpleado(empleado_id){
    if(!empleado_id) return [];
    try{
        const res = await fetch('/api/rider_operativo?empleado_id=' + encodeURIComponent(empleado_id));
        if(!res.ok) return [];
        return await res.json();
    }catch(e){ console.warn('fetchRidersByEmpleado error', e); return []; }
}

// Populate a <select> with rider_operativo for an empleado
async function populateRiderSelect(selectId, empleado_id, opts = {}){
    const sel = document.getElementById(selectId);
    if(!sel) return;
    sel.innerHTML = '<option value="">-- seleccionar --</option>';
    const arr = await fetchRidersByEmpleado(empleado_id);
    arr.forEach(r => {
        const o = document.createElement('option');
        o.value = r.id;
        // display useful label: rider_id or cod_activo or fallback name
        o.textContent = (r.rider_id || r.cod_activo || r.id);
        sel.appendChild(o);
    });
    if(opts.onPopulated && typeof opts.onPopulated === 'function') opts.onPopulated(sel);
}

// Create a new rider_operativo row via backend (expects POST /api/rider_operativo)
async function createRider(payload){
    try{
        const res = await fetch('/api/rider_operativo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
        if(!res.ok){ const txt = await res.text(); throw new Error(txt || res.status); }
        return await res.json();
    }catch(e){ console.warn('createRider error', e); throw e; }
}

// Simple modal to add rider_operativo (injects into body if not present)
function ensureAddModal(){
    if(document.getElementById('modal_add_rider')) return;
    const modal = document.createElement('div');
    modal.id = 'modal_add_rider';
    modal.className = 'modal hidden';
    modal.innerHTML = `
        <div class="modal-dialog">
            <h3>Añadir Rider Operativo</h3>
            <div class="field"><label>Rider ID</label><input id="modal_rider_id"></div>
            <div class="field"><label>Código de Activo</label><input id="modal_cod_activo"></div>
            <div class="field"><label>Ciudad ID</label><input id="modal_ciudad_id"></div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
                <button type="button" class="btn secondary" id="modal_cancel_rider">Cancelar</button>
                <button type="button" class="btn" id="modal_save_rider">Guardar</button>
            </div>
        </div>`;
    document.body.appendChild(modal);
    document.getElementById('modal_cancel_rider').addEventListener('click', ()=>{ modal.classList.add('hidden'); });
    document.getElementById('modal_save_rider').addEventListener('click', async ()=>{
        const rider_id = (document.getElementById('modal_rider_id')||{}).value || null;
        const cod_activo = (document.getElementById('modal_cod_activo')||{}).value || '';
        const ciudad_id = (document.getElementById('modal_ciudad_id')||{}).value || null;
        const payload = { rider_id, cod_activo, ciudad_id, activo: true };
        try{
            const created = await createRider(payload);
            modal.classList.add('hidden');
            // dispatch event so other code can react (e.g., repopulate selects)
            document.dispatchEvent(new CustomEvent('rider:created', { detail: created }));
        }catch(e){ try{ if(window.showToast) window.showToast('Error creando Rider: ' + (e.message||e)); else console.warn('Error creando Rider: ' + (e.message||e)); }catch(ex){} }
    });
}

function openAddRiderModal(){ ensureAddModal(); const m = document.getElementById('modal_add_rider'); if(m) m.classList.remove('hidden'); }

// Auto-populate selects that have data-rider-for-empleado attribute
function autoAttach(){
    document.querySelectorAll('select[data-rider-for-empleado]').forEach(async sel=>{
        const empleadoId = sel.getAttribute('data-rider-for-empleado') || sel.dataset.empleadoId || null;
        if(!empleadoId){
            // try to read from a field id referenced
            const ref = sel.getAttribute('data-empleado-field');
            if(ref){ const el = document.getElementById(ref); if(el) empleadoId = el.value || el.dataset.empleadoId || null; }
        }
        if(empleadoId) await populateRiderSelect(sel.id, empleadoId);
        // repopulate when a new rider is created
        document.addEventListener('rider:created', async (ev)=>{ try{ if(empleadoId) await populateRiderSelect(sel.id, empleadoId); }catch(e){} });
    });
}

// expose
window.RIDER.fetchRidersByEmpleado = fetchRidersByEmpleado;
window.RIDER.populateRiderSelect = populateRiderSelect;
window.RIDER.createRider = createRider;
window.RIDER.openAddRiderModal = openAddRiderModal;

// --- Vehículos and asignaciones helpers ---
// Fetch vehicles list from backend (/api/vehiculos)
async function fetchVehiculos(){
    try{
        const res = await fetch('/api/vehiculos');
        if(!res.ok) return [];
        return await res.json();
    }catch(e){ console.warn('fetchVehiculos error', e); return []; }
}

// Populate a select with vehicles
async function populateVehiculoSelect(selectId, selected){
    const sel = document.getElementById(selectId);
    if(!sel) return;
    sel.innerHTML = '<option value="">-- seleccionar vehículo --</option>';
    const arr = await fetchVehiculos();
    arr.forEach(v=>{ const o = document.createElement('option'); o.value = v.id; o.textContent = v.nombre || v.name || `ID ${v.id}`; sel.appendChild(o); });
    if(selected) sel.value = String(selected);
}

// Fetch vehiculo_asignacion rows for a vehicle
async function fetchVehiculoAsignaciones(vehiculo_id){
    if(!vehiculo_id) return [];
    try{
        const res = await fetch('/api/vehiculo_asignaciones?vehiculo_id=' + encodeURIComponent(vehiculo_id));
        if(!res.ok) return [];
        return await res.json();
    }catch(e){ console.warn('fetchVehiculoAsignaciones error', e); return []; }
}

// expose vehiculo helpers
window.RIDER.fetchVehiculos = fetchVehiculos;
window.RIDER.populateVehiculoSelect = populateVehiculoSelect;
window.RIDER.fetchVehiculoAsignaciones = fetchVehiculoAsignaciones;

// initialize on DOM ready
if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', autoAttach); else autoAttach();

})();
