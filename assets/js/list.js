(function () {
  const params = new URLSearchParams(window.location.search);
  const category = params.get('cat');

  const titleEl = document.getElementById('page-title');
  const listEl = document.getElementById('work-list');

  titleEl.textContent = CATEGORY_LABELS[category] || 'Works';
  document.title = `${titleEl.textContent} · SangWoo Chon`;

  const items = WORKS.filter((w) => w.category === category).sort((a, b) =>
    b.date.localeCompare(a.date)
  );

  if (items.length === 0) {
    listEl.innerHTML = '<p class="empty-state">No works listed yet.</p>';
    return;
  }

  listEl.innerHTML = items
    .map(
      (item) => `
      <a class="work-card" href="detail.html?id=${encodeURIComponent(item.id)}">
        <span class="work-title">${item.title}</span>
        <div class="work-meta">
          <span>${item.experience}</span>
          <span>${item.date}</span>
        </div>
        <div class="work-summary">${item.summary}</div>
      </a>`
    )
    .join('');
})();
