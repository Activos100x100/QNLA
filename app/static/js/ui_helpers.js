/* Simple UI helpers used across the employee form.
   Exposes `window.UI.showToast`, `UI.showModal`, `UI.hideModal`, `UI.copyToClipboard`.
*/
(function(window){
  function showToast(msg, timeout=3500){
    const t = document.createElement('div');
    t.className = 'ui-toast';
    t.textContent = msg;
    Object.assign(t.style, {
      position: 'fixed',
      right: '20px',
      bottom: '20px',
      background: '#111',
      color: '#fff',
      padding: '8px 12px',
      borderRadius: '8px',
      zIndex: 2000,
      boxShadow: '0 6px 18px rgba(2,6,23,0.2)'
    });
    document.body.appendChild(t);
    // fade out and remove
    requestAnimationFrame(()=>{ t.style.opacity = '1'; t.style.transition = 'opacity 0.25s'; });
    setTimeout(()=>{ t.style.opacity = '0'; t.addEventListener('transitionend', ()=>t.remove()); }, timeout);
  }

  function ensureModal(){
    let m = document.getElementById('ui_helpers_modal');
    if(!m){
      m = document.createElement('div');
      m.id = 'ui_helpers_modal';
      m.className = 'modal hidden';
      m.innerHTML = '<div class="modal-dialog"><div id="ui_helpers_modal_body"></div><div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px"><button id="ui_helpers_modal_close" class="btn secondary">Cerrar</button></div></div>';
      document.body.appendChild(m);
      m.querySelector('#ui_helpers_modal_close').addEventListener('click', hideModal);
    }
    return m;
  }

  function showModal(html){
    const m = ensureModal();
    const body = m.querySelector('#ui_helpers_modal_body');
    body.innerHTML = typeof html === 'string' ? html : '';
    m.classList.remove('hidden');
  }

  function hideModal(){
    const m = document.getElementById('ui_helpers_modal');
    if(m) m.classList.add('hidden');
  }

  function copyToClipboard(text){
    if(!navigator.clipboard) return showToast('Portapapeles no disponible');
    navigator.clipboard.writeText(text).then(()=> showToast('Copiado al portapapeles'), ()=> showToast('Error al copiar'));
  }

  window.UI = { showToast, showModal, hideModal, copyToClipboard };
})(window);
