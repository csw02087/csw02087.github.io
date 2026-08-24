(function () {
  const params = new URLSearchParams(window.location.search);
  const category = params.get('cat');

  const titleEl = document.getElementById('page-title');
  const listEl = document.getElementById('work-list');

  titleEl.textContent = CATEGORY_LABELS[category] || 'Projects';
  document.title = `${titleEl.textContent} · SangWoo Chon`;

  const items = WORKS.filter((w) => !category || w.category === category).sort((a, b) =>
    b.writtenDate.localeCompare(a.writtenDate)
  );

  if (items.length === 0) {
    listEl.innerHTML = '<p class="empty-state">No works listed yet.</p>';
    return;
  }

  listEl.innerHTML = `
    <div class="work-list-header" role="row">
      <span role="columnheader">Title</span>
      <span role="columnheader">Written Date</span>
      <span role="columnheader">Posted Date</span>
    </div>
    ${items
    .map(
      (item) => `
      <a class="work-row" role="row" href="detail.html?id=${encodeURIComponent(item.id)}">
        <span class="work-title" role="cell">${item.title}</span>
        <time role="cell" datetime="${item.writtenDate}">${item.writtenDate}</time>
        <time role="cell" datetime="${item.postedDate}">${item.postedDate}</time>
      </a>`
    )
    .join('')}`;
})();
