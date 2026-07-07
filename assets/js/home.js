(function () {
  const container = document.getElementById('project-sections');

  container.innerHTML = Object.keys(CATEGORY_LABELS)
    .map((cat) => {
      const items = WORKS.filter((w) => w.category === cat)
        .sort((a, b) => b.date.localeCompare(a.date))
        .slice(0, 3);

      const body =
        items.length === 0
          ? '<p class="empty-state-sm">Coming soon.</p>'
          : `<div class="work-list">${items
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
              .join('')}</div>`;

      return `
      <section class="project-section">
        <div class="project-section-header">
          <h3><a href="list.html?cat=${cat}">${CATEGORY_LABELS[cat]}</a></h3>
          <a class="btn-outline-sm" href="list.html?cat=${cat}">View all &rarr;</a>
        </div>
        ${body}
      </section>`;
    })
    .join('');
})();
