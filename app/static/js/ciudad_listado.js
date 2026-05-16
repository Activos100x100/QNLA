function qcl(id){ return document.getElementById(id); }

function statusCiudadListado(msg, timeout){
    const box = qcl('ciudadListadoStatus');
    if(!box) return;
    box.textContent = msg || '';
    if(timeout){
        setTimeout(function(){ try{ box.textContent = ''; }catch(e){} }, timeout);
    }
}

async function fetchJsonCiudadListado(url){
    const res = await fetch(url);
    if(!res.ok) throw new Error('HTTP ' + res.status);
    return res.json();
}

function td(val){
    return val == null ? '' : String(val);
}

function renderCiudadListadoRows(items){
    const tbody = qcl('ciudadListadoRows');
    if(!tbody) return;
    tbody.innerHTML = '';

    if(!Array.isArray(items) || items.length === 0){
        tbody.innerHTML = '<tr><td colspan="9">Sin resultados</td></tr>';
        return;
    }

    items.forEach(function(item){
        const tr = document.createElement('tr');
        const nombre = item.name ?? item.nombre ?? '';
        tr.innerHTML = [
            '<td>' + td(item.id) + '</td>',
            '<td>' + td(nombre) + '</td>',
            '<td>' + td(item.municipio) + '</td>',
            '<td>' + td(item.provincia) + '</td>',
            '<td>' + td(item.comunidad_autonoma) + '</td>',
            '<td>' + td(item.pais) + '</td>',
            '<td>' + td(item.prefijo_telefono) + '</td>',
            '<td>' + td(item.id_op) + '</td>',
            '<td>' + td(item.id_rrhh) + '</td>'
        ].join('');
        tbody.appendChild(tr);
    });
}

async function loadCiudadListado(){
    const q = (qcl('ciudad_listado_q')?.value || '').trim();
    const params = new URLSearchParams();
    if(q) params.set('q', q);
    params.set('limit', '1000');

    const url = '/api/ciudades/listado?' + params.toString();
    statusCiudadListado('Cargando listado de ciudades...');

    try{
        const items = await fetchJsonCiudadListado(url);
        renderCiudadListadoRows(items);
        statusCiudadListado('Resultados: ' + (items?.length || 0), 2500);
    }catch(error){
        console.error('ciudad listado', error);
        statusCiudadListado('Error al cargar el listado de ciudades', 5000);
    }
}

document.addEventListener('DOMContentLoaded', function(){
    qcl('btnBuscarCiudadListado')?.addEventListener('click', loadCiudadListado);

    qcl('btnLimpiarCiudadListado')?.addEventListener('click', function(){
        if(qcl('ciudad_listado_q')) qcl('ciudad_listado_q').value = '';
        loadCiudadListado();
    });

    qcl('ciudad_listado_q')?.addEventListener('keydown', function(e){
        if(e.key === 'Enter'){
            e.preventDefault();
            loadCiudadListado();
        }
    });

    loadCiudadListado();
});
