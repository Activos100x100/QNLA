// Modal button wiring and global exposures
(function(){
window.EMP = window.EMP || {};
try{
    const btnAddP = document.getElementById('btnAddPuesto'); if(btnAddP) btnAddP.addEventListener('click', ()=>{ if(window.openModalAddPuesto) window.openModalAddPuesto(); });
    const btnAddN = document.getElementById('btnAddNivel'); if(btnAddN) btnAddN.addEventListener('click', ()=>{ if(window.openModalAddNivel) window.openModalAddNivel(); });
    const btnAddC = document.getElementById('btnAddConvenio'); if(btnAddC) btnAddC.addEventListener('click', ()=>{ if(window.openModalAddConvenio) window.openModalAddConvenio(); });
    const btnAddCT = document.getElementById('btnAddConvenioTramo'); if(btnAddCT) btnAddCT.addEventListener('click', ()=>{ if(window.openModalAddConvenioTramo) window.openModalAddConvenioTramo(); });

    const modalCancelP = document.getElementById('modal_cancel_puesto'); if(modalCancelP) modalCancelP.addEventListener('click', ()=>{ if(window.closeModalAddPuesto) window.closeModalAddPuesto(); });
    const modalSaveP = document.getElementById('modal_save_puesto'); if(modalSaveP) modalSaveP.addEventListener('click', ()=>{ if(window.savePuestoFromModal) window.savePuestoFromModal(); });

    const modalCancelN = document.getElementById('modal_cancel_nivel'); if(modalCancelN) modalCancelN.addEventListener('click', ()=>{ if(window.closeModalAddNivel) window.closeModalAddNivel(); });
    const modalSaveN = document.getElementById('modal_save_nivel'); if(modalSaveN) modalSaveN.addEventListener('click', ()=>{ if(window.saveNivelFromModal) window.saveNivelFromModal(); });

    const modalCancelC = document.getElementById('modal_cancel_convenio'); if(modalCancelC) modalCancelC.addEventListener('click', ()=>{ if(window.closeModalAddConvenio) window.closeModalAddConvenio(); });
    const modalSaveC = document.getElementById('modal_save_convenio'); if(modalSaveC) modalSaveC.addEventListener('click', ()=>{ if(window.saveConvenioFromModal) window.saveConvenioFromModal(); });

    const modalCancelCT = document.getElementById('modal_cancel_convenio_tramo'); if(modalCancelCT) modalCancelCT.addEventListener('click', ()=>{ if(window.closeModalAddConvenioTramo) window.closeModalAddConvenioTramo(); });
    const modalSaveCT = document.getElementById('modal_save_convenio_tramo'); if(modalSaveCT) modalSaveCT.addEventListener('click', ()=>{ if(window.saveConvenioTramoFromModal) window.saveConvenioTramoFromModal(); });
}catch(e){ console.warn('attach modal listeners failed', e); }

// Expose any modal helpers if needed
window.EMP.openModalAddPuesto = window.openModalAddPuesto;
window.EMP.openModalAddNivel = window.openModalAddNivel;
window.EMP.openModalAddConvenio = window.openModalAddConvenio;
window.EMP.openModalAddConvenioTramo = window.openModalAddConvenioTramo;

})();
