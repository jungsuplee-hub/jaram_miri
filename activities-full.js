(() => {
  const controls = Array.from(document.querySelectorAll('.archive-filter'));
  const yearSelect = document.querySelector('#archive-year');
  const sections = Array.from(document.querySelectorAll('[data-archive-group]'));
  const output = document.querySelector('#archive-result');
  const empty = document.querySelector('#archive-empty');
  if (!controls.length || !sections.length) return;

  let selectedCategory = 'all';
  const update = () => {
    let total = 0;
    const selectedYear = yearSelect?.value || 'all';
    controls.forEach(button => {
      const isSelected = button.dataset.category === selectedCategory;
      button.classList.toggle('is-active', isSelected);
      button.setAttribute('aria-pressed', String(isSelected));
    });
    sections.forEach(section => {
      const groupMatch = selectedCategory === 'all' || section.dataset.archiveGroup === selectedCategory;
      let groupTotal = 0;
      section.querySelectorAll('[data-gallery-card]').forEach(card => {
        const match = groupMatch && (selectedYear === 'all' || card.dataset.galleryYear === selectedYear);
        card.hidden = !match;
        if (match) {
          groupTotal += 1;
          card.classList.add('is-visible');
        }
      });
      section.hidden = groupTotal === 0;
      const count = section.querySelector('.archive-section-count');
      if (count) count.firstChild.textContent = String(groupTotal);
      total += groupTotal;
    });
    if (empty) empty.hidden = total > 0;
    if (output) output.textContent = '선택한 조건의 활동 사례 ' + total + '건';
  };
  controls.forEach(button => button.addEventListener('click', () => {
    selectedCategory = button.dataset.category;
    update();
  }));
  yearSelect?.addEventListener('change', update);
  update();
})();
