(function () {
  const params = new URLSearchParams(window.location.search);
  const id = params.get('id');
  const item = WORKS.find((w) => w.id === id);

  const root = document.getElementById('detail-root');

  if (!item) {
    root.innerHTML = '<p class="empty-state">Work not found.</p>';
    return;
  }

  document.title = `${item.title} · SangWoo Chon`;

  root.innerHTML = `
    <a class="back-link" href="list.html?cat=${encodeURIComponent(item.category)}">&larr; Back to ${CATEGORY_LABELS[item.category]}</a>
    <h1>${item.title}</h1>
    <div class="detail-meta">
      <span>${item.experience}</span>
      <span>Written ${item.writtenDate}</span>
      <span>Posted ${item.postedDate}</span>
      <span>${CATEGORY_LABELS[item.category]}</span>
    </div>
    <div class="detail-content">${item.content}</div>
    ${
      item.link
        ? `<section class="pdf-section" aria-labelledby="pdf-heading">
            <div class="pdf-section-header">
              <h2 id="pdf-heading">Report</h2>
              <a href="${item.link}">Open PDF directly &rarr;</a>
            </div>
            <object class="pdf-viewer" data="${item.link}#view=FitH" type="application/pdf" aria-label="${item.title} PDF">
              <p>PDF preview is unavailable. <a href="${item.link}">Open the PDF directly.</a></p>
            </object>
          </section>`
        : ''
    }
  `;
})();
