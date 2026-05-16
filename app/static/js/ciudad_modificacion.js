function qse(id){ return document.getElementById(id); }
function valueEdit(id){ return (qse(id)?.value || '').trim(); }
function toIntOrNullEdit(id){
    const value = valueEdit(id);
    if(!value) return null;
    const parsed = parseInt(value, 10);
    return Number.isNaN(parsed) ? null : parsed;
}

function setOptions(select, items, config){
    if(!select) return;
    const placeholder = config?.placeholder || 'Selecciona una opción';
    const valueKey = config?.valueKey || 'name';
    const labelKey = config?.labelKey || 'name';
    select.innerHTML = '';

    const emptyOption = document.createElement('option');
    emptyOption.value = '';
    emptyOption.textContent = placeholder;
    select.appendChild(emptyOption);

    for(const item of items || []){
        const option = document.createElement('option');
        if(typeof item === 'string'){
            option.value = item;
            option.textContent = item;
        } else {
            option.value = item[valueKey];
            option.textContent = item[labelKey];
            if(item.code !== undefined){ option.dataset.code = String(item.code); }
        }
        select.appendChild(option);
    }

    try{ select.selectedIndex = 0; }catch(e){}
}

function ensureSelectValueVisible(select, value, fallbackPrefix){
    if(!select) return;
    const normalized = value == null ? '' : String(value);
    if(!normalized){
        try{ select.selectedIndex = 0; }catch(e){}
        return;
    }

    const existing = Array.from(select.options || []).some(function(opt){ return opt.value === normalized; });
    if(!existing){
        const option = document.createElement('option');
        option.value = normalized;
        option.textContent = (fallbackPrefix || 'ID actual') + ': ' + normalized;
        select.appendChild(option);
    }
    select.value = normalized;
}

async function fetchJsonEdit(url, options){
    const res = await fetch(url, options);
    if(!res.ok){
        throw new Error('HTTP ' + res.status);
    }
    return res.json();
}

function showStatusEdit(message, timeout){
    const status = qse('ciudadEditStatus');
    if(!status) return;
    status.textContent = message;
    if(timeout){
        setTimeout(function(){
            try{ status.textContent = ''; }catch(e){}
        }, timeout);
    }
}

async function loadCiudades(){
    const selector = qse('ciudad_selector');
    setOptions(selector, [], {placeholder: 'Cargando ciudades...'});
    const ciudades = await fetchJsonEdit('/api/ciudades');

    const normalized = (ciudades || []).map(function(item){
        const id = item?.id;
        const name = item?.name || item?.nombre || item?.municipio || ('Ciudad #' + id);
        return { id: id, name: name };
    }).filter(function(item){ return item.id !== undefined && item.id !== null; });

    setOptions(selector, normalized, {
        placeholder: 'Selecciona una ciudad',
        valueKey: 'id',
        labelKey: 'name'
    });
}

async function loadComunidadesEdit(){
    const comunidadSelect = qse('comunidad_autonoma_edit');
    const provinciasSelect = qse('provincia_edit');
    const municipiosSelect = qse('municipio_edit');

    setOptions(comunidadSelect, [], {placeholder: 'Cargando comunidades...'});
    if(provinciasSelect){
        provinciasSelect.disabled = true;
        setOptions(provinciasSelect, [], {placeholder: 'Selecciona primero una comunidad'});
    }
    if(municipiosSelect){
        municipiosSelect.disabled = true;
        setOptions(municipiosSelect, [], {placeholder: 'Selecciona primero una provincia'});
    }

    const comunidades = await fetchJsonEdit('/api/ciudades/geo/comunidades');
    setOptions(comunidadSelect, comunidades, {placeholder: 'Selecciona una comunidad autónoma'});
}

async function loadProvinciasEdit(comunidad){
    const provinciasSelect = qse('provincia_edit');
    const municipiosSelect = qse('municipio_edit');
    if(!provinciasSelect) return;

    provinciasSelect.disabled = true;
    setOptions(provinciasSelect, [], {placeholder: comunidad ? 'Cargando provincias...' : 'Selecciona primero una comunidad'});
    if(municipiosSelect){
        municipiosSelect.disabled = true;
        setOptions(municipiosSelect, [], {placeholder: 'Selecciona primero una provincia'});
    }

    if(!comunidad) return;

    const provincias = await fetchJsonEdit('/api/ciudades/geo/provincias?comunidad=' + encodeURIComponent(comunidad));
    setOptions(provinciasSelect, provincias, {
        placeholder: 'Selecciona una provincia',
        valueKey: 'name',
        labelKey: 'name'
    });
    provinciasSelect.disabled = false;
}

async function loadMunicipiosEdit(provinceCode){
    const municipiosSelect = qse('municipio_edit');
    if(!municipiosSelect) return;

    municipiosSelect.disabled = true;
    setOptions(municipiosSelect, [], {placeholder: provinceCode ? 'Cargando municipios...' : 'Selecciona primero una provincia'});
    if(!provinceCode) return;

    const municipios = await fetchJsonEdit('/api/ciudades/geo/municipios?provincia_codigo=' + encodeURIComponent(provinceCode));
    setOptions(municipiosSelect, municipios, {placeholder: 'Selecciona un municipio'});
    municipiosSelect.disabled = false;
}

async function loadResponsablesOpEdit(){
    const select = qse('id_op_edit');
    if(!select) return;
    select.disabled = true;
    setOptions(select, [], {placeholder: 'Cargando responsables...'});

    const responsables = await fetchJsonEdit('/api/ciudades/usuarios-operaciones?departamento_id=2');
    setOptions(select, responsables, {
        placeholder: 'Selecciona responsable de operaciones',
        valueKey: 'id',
        labelKey: 'nombre'
    });
    select.disabled = false;
}

async function loadResponsablesRrhhEdit(){
    const select = qse('id_rrhh_edit');
    if(!select) return;
    select.disabled = true;
    setOptions(select, [], {placeholder: 'Cargando responsables RRHH...'});

    const responsables = await fetchJsonEdit('/api/ciudades/usuarios-operaciones?departamento_id=1');
    setOptions(select, responsables, {
        placeholder: 'Selecciona responsable RRHH',
        valueKey: 'id',
        labelKey: 'nombre'
    });
    select.disabled = false;
}

function fillEditForm(data){
    if(!data) return;
    qse('id_ciudad_edit').value = data.id ?? '';
    qse('nombre_ciudad_edit').value = data.name ?? data.nombre ?? data.municipio ?? '';
    qse('time_zone_edit').value = data.time_zone ?? '';
    qse('abreviatura_edit').value = data.abreviatura ?? '';
    qse('codigo_postal_edit').value = data.codigo_postal ?? '';
    qse('pais_edit').value = data.pais ?? '';
    qse('prefijo_telefono_edit').value = data.prefijo_telefono ?? '';

    const comunidad = data.comunidad_autonoma ?? '';
    const provincia = data.provincia ?? '';
    const municipio = data.municipio ?? data.name ?? data.nombre ?? '';

    qse('comunidad_autonoma_edit').value = comunidad;

    const opValue = data.id_op != null ? String(data.id_op) : '';
    const rrhhValue = data.id_rrhh != null ? String(data.id_rrhh) : '';
    ensureSelectValueVisible(qse('id_op_edit'), opValue, 'Responsable operaciones actual');
    ensureSelectValueVisible(qse('id_rrhh_edit'), rrhhValue, 'Responsable RRHH actual');

    return { provincia, municipio };
}

async function loadCityDetail(cityId){
    if(!cityId) return;
    showStatusEdit('Cargando datos de ciudad...');
    const data = await fetchJsonEdit('/api/ciudades/' + encodeURIComponent(cityId));

    const location = fillEditForm(data) || { provincia: '', municipio: '' };

    await loadProvinciasEdit(valueEdit('comunidad_autonoma_edit'));
    qse('provincia_edit').value = location.provincia || '';

    const provinceOption = qse('provincia_edit').options[qse('provincia_edit').selectedIndex];
    const provinceCode = provinceOption?.dataset?.code || '';

    await loadMunicipiosEdit(provinceCode);
    qse('municipio_edit').value = location.municipio || '';

    showStatusEdit('Ciudad cargada', 2000);
}

document.addEventListener('DOMContentLoaded', function(){
    const form = qse('ciudadEditForm');
    const selector = qse('ciudad_selector');
    const comunidadSelect = qse('comunidad_autonoma_edit');
    const provinciaSelect = qse('provincia_edit');
    const municipioSelect = qse('municipio_edit');

    Promise.all([
        loadCiudades(),
        loadComunidadesEdit(),
        loadResponsablesOpEdit(),
        loadResponsablesRrhhEdit()
    ]).catch(function(error){
        console.error('init ciudad modificacion', error);
        showStatusEdit('Error al cargar datos iniciales', 5000);
    });

    selector?.addEventListener('change', async function(){
        const cityId = this.value;
        if(!cityId){
            showStatusEdit('Selecciona una ciudad para editar', 3000);
            return;
        }
        try{
            await loadCityDetail(cityId);
        }catch(error){
            console.error('load city detail', error);
            showStatusEdit('No se pudo cargar la ciudad seleccionada', 5000);
        }
    });

    comunidadSelect?.addEventListener('change', async function(){
        try{
            await loadProvinciasEdit(this.value);
        }catch(error){
            console.error('load provincias edit', error);
            showStatusEdit('No se pudieron cargar provincias', 5000);
        }
    });

    provinciaSelect?.addEventListener('change', async function(){
        const selected = this.options[this.selectedIndex];
        const provinceCode = selected?.dataset?.code || '';
        try{
            await loadMunicipiosEdit(provinceCode);
        }catch(error){
            console.error('load municipios edit', error);
            showStatusEdit('No se pudieron cargar municipios', 5000);
        }
    });

    municipioSelect?.addEventListener('change', function(){
        const municipality = this.value;
        const nombre = qse('nombre_ciudad_edit');
        if(nombre && municipality && !nombre.value.trim()){
            nombre.value = municipality;
        }
    });

    qse('btnRecargarCiudad')?.addEventListener('click', async function(){
        const cityId = valueEdit('ciudad_selector');
        if(!cityId){
            showStatusEdit('Selecciona una ciudad para recargar', 3000);
            return;
        }
        try{
            await loadCityDetail(cityId);
        }catch(error){
            console.error('reload city detail', error);
            showStatusEdit('No se pudo recargar la ciudad', 5000);
        }
    });

    form?.addEventListener('submit', async function(e){
        e.preventDefault();

        const cityId = valueEdit('ciudad_selector');
        const nombre = valueEdit('nombre_ciudad_edit');
        if(!cityId){
            showStatusEdit('Selecciona una ciudad para guardar cambios', 4000);
            return;
        }
        if(!nombre){
            qse('err_nombre_ciudad_edit').textContent = 'Nombre requerido';
            return;
        }
        qse('err_nombre_ciudad_edit').textContent = '';

        const payload = {
            name: nombre,
            time_zone: valueEdit('time_zone_edit') || null,
            abreviatura: valueEdit('abreviatura_edit') || null,
            codigo_postal: valueEdit('codigo_postal_edit') || null,
            municipio: valueEdit('municipio_edit') || null,
            provincia: valueEdit('provincia_edit') || null,
            comunidad_autonoma: valueEdit('comunidad_autonoma_edit') || null,
            pais: valueEdit('pais_edit') || null,
            prefijo_telefono: valueEdit('prefijo_telefono_edit') || null,
            id_op: toIntOrNullEdit('id_op_edit'),
            id_rrhh: toIntOrNullEdit('id_rrhh_edit')
        };

        showStatusEdit('Guardando cambios...');
        try{
            await fetchJsonEdit('/api/ciudades/' + encodeURIComponent(cityId), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            showStatusEdit('Ciudad actualizada correctamente', 3000);
            await loadCiudades();
            qse('ciudad_selector').value = cityId;
        }catch(error){
            console.error('save city changes', error);
            showStatusEdit('Error al guardar cambios', 5000);
        }
    });
});
