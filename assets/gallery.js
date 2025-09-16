(function(){
  function init(root){
    if (!root) return;
    const modal = root.querySelector('.gallery-modal');
    const img = root.querySelector('.gallery-full');
    const cap = root.querySelector('.gallery-caption');
    const backdrop = root.querySelector('.gallery-backdrop');
    const closeBtn = root.querySelector('.gallery-close');

    function open(full, alt){
      if (!modal || !img) return;
      img.src = full; img.alt = alt || '';
      if (cap) cap.textContent = alt || '';
      modal.hidden = false;
      document.addEventListener('keydown', onKey);
    }
    function close(){
      if (!modal) return;
      modal.hidden = true;
      document.removeEventListener('keydown', onKey);
    }
    function onKey(e){ if (e.key === 'Escape') close(); }

    root.addEventListener('click', (e) => {
      const a = e.target.closest ? e.target.closest('.gallery-item') : null;
      if (a && a.dataset.full){ e.preventDefault(); open(a.dataset.full, a.dataset.alt || ''); }
    });
    if (backdrop) backdrop.addEventListener('click', close);
    if (closeBtn) closeBtn.addEventListener('click', close);
  }

  document.querySelectorAll('.gallery').forEach(init);
})();