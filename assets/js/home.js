(function () {
  const container = document.getElementById('project-sections');

  container.innerHTML = Object.keys(CATEGORY_LABELS)
    .map((cat) => {
      const items = WORKS.filter((w) => w.category === cat)
        .sort((a, b) => b.writtenDate.localeCompare(a.writtenDate))
        .slice(0, 3);

      const body =
        items.length === 0
          ? '<p class="empty-state-sm">Coming soon.</p>'
          : `<div class="work-list" role="table" aria-label="${CATEGORY_LABELS[cat]}">
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
