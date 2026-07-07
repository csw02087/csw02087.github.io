(function () {
  const container = document.getElementById('recent-projects');

  const items = [...WORKS].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 3);

  if (items.length === 0) {
    container.innerHTML = '<p class="empty-state">No projects yet.</p>';
    return;
  }

  container.innerHTML = items
    .map(
      (item) => `
      <a class="work-card" href="detail.html?id=${encodeURIComponent(item.id)}">
        <span class="work-title">${item.title}</span>
        <div class="work-meta">
          <span>${CATEGORY_LABELS[item.category]}</span>
          <span>${item.date}</span>
        </div>
        <div class="work-summary">${item.summary}</div>
      </a>`
    )
    .join('');
})();
