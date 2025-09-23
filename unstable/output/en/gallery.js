(function(){
  function init(root){
    if (!root) return;
    const modal = root.querySelector('.gallery-modal');
    const img = root.querySelector('.gallery-full');
    const cap = root.querySelector('.gallery-caption');
    const backdrop = root.querySelector('.gallery-backdrop');
    const closeBtn = root.querySelector('.gallery-close');
    const prevBtn = root.querySelector('.gallery-prev');
    const nextBtn = root.querySelector('.gallery-next');

    // Collect all items in order
    const items = Array.from(root.querySelectorAll('.gallery-item')).map(item => ({
      full: item.dataset.full,
      alt: item.dataset.alt || ''
    }));

    let currentIndex = -1;

    function open(full, alt, index){
      if (!modal || !img) return;
      currentIndex = typeof index === 'number' ? index : items.findIndex(item => item.full === full);
      if (currentIndex === -1) return;
      img.src = full; img.alt = alt || '';
      if (cap) cap.textContent = alt || '';
      updateButtons();
      modal.hidden = false;
      document.addEventListener('keydown', onKey);
    }
    function close(){
      if (!modal) return;
      modal.hidden = true;
      document.removeEventListener('keydown', onKey);
    }
    function onKey(e){
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowLeft') goPrev();
      else if (e.key === 'ArrowRight') goNext();
    }
    function goPrev(){
      if (currentIndex > 0){
        currentIndex--;
        updateImage();
      }
    }
    function goNext(){
      if (currentIndex < items.length - 1){
        currentIndex++;
        updateImage();
      }
    }
    function updateImage(){
      const item = items[currentIndex];
      img.src = item.full;
      img.alt = item.alt || '';
      if (cap) cap.textContent = item.alt || '';
      updateButtons();
    }
    function updateButtons(){
      if (prevBtn) prevBtn.style.display = currentIndex > 0 ? '' : 'none';
      if (nextBtn) nextBtn.style.display = currentIndex < items.length - 1 ? '' : 'none';
    }

    root.addEventListener('click', (e) => {
      const a = e.target.closest ? e.target.closest('.gallery-item') : null;
      if (a && a.dataset.full){
        e.preventDefault();
        const clickedIndex = Array.from(root.querySelectorAll('.gallery-item')).indexOf(a);
        open(a.dataset.full, a.dataset.alt || '', clickedIndex);
      }
    });
    if (backdrop) backdrop.addEventListener('click', close);
    if (closeBtn) closeBtn.addEventListener('click', close);
    if (prevBtn) prevBtn.addEventListener('click', goPrev);
    if (nextBtn) nextBtn.addEventListener('click', goNext);
  }

  document.querySelectorAll('.gallery').forEach(init);
})();
