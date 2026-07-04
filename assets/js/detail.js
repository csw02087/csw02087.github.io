(function () {
  const params = new URLSearchParams(window.location.search);
  const id = params.get('id');
  const item = WORKS.find((w) => w.id === id);

  const root = document.getElementById('detail-root');

  if (!item) {
    root.innerHTML = '<p class="empty-state">해당 작품을 찾을 수 없습니다.</p>';
    return;
  }

  document.title = `${item.title} · SangWoo Chon`;

  root.innerHTML = `
    <a class="back-link" href="list.html?cat=${encodeURIComponent(item.category)}">&larr; ${CATEGORY_LABELS[item.category]} 목록으로</a>
    <h1>${item.title}</h1>
    <div class="detail-meta">
      <span>${item.experience}</span>
      <span>${item.date}</span>
      <span>${CATEGORY_LABELS[item.category]}</span>
    </div>
    <div class="detail-content">${item.content}</div>
    ${item.link ? `<a class="detail-link" href="${item.link}" target="_blank" rel="noopener">원문 보기 &rarr;</a>` : ''}
  `;
})();
