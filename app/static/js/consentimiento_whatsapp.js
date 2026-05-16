document.addEventListener("DOMContentLoaded", async () => {
  const tabs = document.getElementById("cwaTabs");
  const tbody = document.getElementById("cwaRows");
  const tableTitle = document.getElementById("cwaTableTitle");
  const tableCount = document.getElementById("cwaTableCount");
  const btnExportar = document.getElementById("btnExportarNoSheet");

  let currentCiudad = null;
  let sortBy = 'rider_id';
  let sortDir = 'asc';
  let busqueda = '';

  function updateSortArrows() {
    document.querySelectorAll('.cwa-table .sort-arrows').forEach(span => {
      const key = span.getAttribute('data-arrow');
      if (!key) return;
      if (sortBy === key) {
        span.innerHTML = sortDir === 'asc' ? '<b>↑</b>' : '<b>↓</b>';
      } else {
        span.innerHTML = '<span style="color:#bbb;">↑↓</span>';
      }
    });
  }

  function applySort(arr) {
    const dir = sortDir === 'asc' ? 1 : -1;
    return arr.slice().sort((a, b) => {
      let va = a[sortBy] ?? a['rider'] ?? '';
      let vb = b[sortBy] ?? b['rider'] ?? '';
      if (sortBy === 'rider_id') { va = a['rider_id'] || a['rider'] || ''; vb = b['rider_id'] || b['rider'] || ''; }
      if (sortBy === 'consentimiento') { va = a.consentimiento ? 1 : 0; vb = b.consentimiento ? 1 : 0; return (va - vb) * dir; }
      return String(va).localeCompare(String(vb), 'es') * dir;
    });
  }

  window.exportarNoSheet = async function () {
    if (!currentCiudad) return;
    const btn = document.getElementById("btnExportarNoSheet");
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = "⏳ Generando...";
    try {
      const res = await fetch(`/api/consentimiento_whatsapp/exportar-no-sheet?ciudad=${encodeURIComponent(currentCiudad)}`);
      if (!res.ok) {
        const json = await res.json().catch(() => ({}));
        alert("Error: " + (json.error || res.statusText));
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const cd = res.headers.get("Content-Disposition") || "";
      const match = cd.match(/filename="?([^"]+)"?/);
      a.download = match ? match[1] : `sin_consentimiento_${currentCiudad}.csv`;
      a.href = url;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert("Error de conexión al generar el CSV");
      console.error(err);
    } finally {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  };

  try {
    const res = await fetch("/api/consentimiento_whatsapp/listado");
    const json = await res.json();
    if (!json.ok) {
      tbody.innerHTML = "<tr><td colspan='3'>Error cargando datos</td></tr>";
      return;
    }
    const data = json.data;
    const ciudades = Object.keys(data);
    // tabs con badge de cantidad
    tabs.innerHTML = ciudades.map((c, i) => {
      const total = data[c]?.length || 0;
      return `<button class="cwa-tab ${i === 0 ? "active" : ""}" data-ciudad="${c}">
        ${c} <span class="cwa-badge">${total}</span>
      </button>`;
    }).join("");

    function render(ciudad) {
      currentCiudad = ciudad;
      const empleados = data[ciudad] || [];
      const q = busqueda.toLowerCase();
      const filtrados = q ? empleados.filter(e =>
        String(e.rider_id || e.rider || '').toLowerCase().includes(q) ||
        String(e.cod_activo || '').toLowerCase().includes(q) ||
        String(e.nombre_completo || '').toLowerCase().includes(q) ||
        String(e.telefono || '').toLowerCase().includes(q)
      ) : empleados;

      if (!filtrados.length) {
        tbody.innerHTML = "<tr><td colspan='3'>Sin datos</td></tr>";
        tableTitle.textContent = ciudad;
        tableCount.textContent = "";
        if (btnExportar) btnExportar.style.display = "none";
        return;
      }
      // Contar sí/no
      let si = 0, no = 0;
      filtrados.forEach(e => e.consentimiento ? si++ : no++);
      tableTitle.textContent = ciudad;
      tableCount.innerHTML = `<span class="cwa-badge-si">Sí: ${si}</span> <span class="cwa-badge-no">No: ${no}</span> <span style='color:#64748b;font-size:12px;margin-left:8px;'>Total: ${filtrados.length}${q ? ' (filtrado)' : ''}</span>`;
      if (btnExportar) btnExportar.style.display = no > 0 ? "inline-flex" : "none";
      const sorted = applySort(filtrados);
      updateSortArrows();
      tbody.innerHTML = sorted.map(e => {
        const rider = e.rider_id || e.rider || "";
        const codActivo = e.cod_activo || "";
        if (e.consentimiento) {
          return `<tr>
            <td>${rider}</td>
            <td>${codActivo}</td>
            <td>${e.nombre_completo || ""}</td>
            <td>${e.telefono || ""}</td>
            <td><span class='cwa-badge-si'>Sí</span></td>
          </tr>`;
        } else {
          // WhatsApp link
          // Generar enlace WhatsApp con el número real del empleado
          let telefonoWa = (e.telefono || '').replace(/[^0-9]/g, '');
          if (telefonoWa.startsWith('0')) telefonoWa = telefonoWa.substring(1);
          if (!telefonoWa.startsWith('34') && telefonoWa.length === 9) telefonoWa = '34' + telefonoWa;
          const mensaje = encodeURIComponent(`Hola,\n\nDesde Activos 100x100 estamos activando el sistema de notificaciones por WhatsApp para comunicaciones importantes.\n\nSi deseas recibirlas, puedes darte de alta aquí:\n👉 https://wa.me/34643707382?text=ALTA\n\nGracias.`);
          const waUrl = `https://wa.me/${telefonoWa}?text=${mensaje}`;
          return `<tr class='cwa-row-no'>
            <td>${rider}</td>
            <td>${codActivo}</td>
            <td>${e.nombre_completo || ""}</td>
            <td>${e.telefono || ""}</td>
            <td><a href='${waUrl}' target='_blank' class='cwa-btn-wa'>No</a></td>
          </tr>`;
        }
      }).join("");
    }
    // eventos tabs
    tabs.querySelectorAll(".cwa-tab").forEach(btn => {
      btn.addEventListener("click", () => {
        tabs.querySelectorAll(".cwa-tab").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        render(btn.dataset.ciudad);
      });
    });
    if (ciudades.length) render(ciudades[0]);

    // Flechas de ordenación
    document.querySelectorAll('.cwa-table th[data-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.getAttribute('data-sort');
        if (sortBy === key) {
          sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          sortBy = key;
          sortDir = 'asc';
        }
        if (currentCiudad) render(currentCiudad);
      });
    });
    updateSortArrows();

    // Buscador
    const searchInput = document.getElementById('cwaSearch');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        busqueda = searchInput.value.trim();
        if (currentCiudad) render(currentCiudad);
      });
    }
  } catch (err) {
    tbody.innerHTML = "<tr><td colspan='3'>Error de conexión</td></tr>";
    if(tableTitle) tableTitle.textContent = "";
    if(tableCount) tableCount.textContent = "";
    console.error(err);
  }
});
