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
            <object class="pdf-desktop-viewer" data="${item.link}#view=FitH" type="application/pdf" aria-label="${item.title} PDF">
              <p>PDF preview is unavailable. <a href="${item.link}">Open the PDF directly.</a></p>
            </object>
            <div class="pdf-mobile-viewer" data-pdf-url="${item.link}" aria-label="${item.title} PDF" aria-busy="true">
              <p class="pdf-status" role="status">Loading PDF preview&hellip;</p>
            </div>
          </section>`
        : ''
    }
  `;

  if (item.link && window.matchMedia('(max-width: 768px)').matches) {
    renderPdf(item.link);
  }

  async function renderPdf(pdfUrl) {
    const viewer = document.querySelector('.pdf-mobile-viewer');

    try {
      if (!window.pdfjsLib) {
        throw new Error('PDF.js failed to load.');
      }

      window.pdfjsLib.GlobalWorkerOptions.workerSrc =
        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

      const pdf = await window.pdfjsLib.getDocument(pdfUrl).promise;
      viewer.innerHTML = '';

      for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
        const page = await pdf.getPage(pageNumber);
        const unscaledViewport = page.getViewport({ scale: 1 });
        const availableWidth = Math.min(viewer.clientWidth - 24, 900);
        const scale = availableWidth / unscaledViewport.width;
        const viewport = page.getViewport({ scale });
        const outputScale = Math.min(window.devicePixelRatio || 1, 2);
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        canvas.className = 'pdf-page';
        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);
        canvas.style.width = `${Math.floor(viewport.width)}px`;
        canvas.style.height = `${Math.floor(viewport.height)}px`;
        canvas.setAttribute('aria-label', `Page ${pageNumber} of ${pdf.numPages}`);
        viewer.appendChild(canvas);

        await page.render({
          canvasContext: context,
          transform: outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null,
          viewport,
        }).promise;
      }

      viewer.setAttribute('aria-busy', 'false');
    } catch (error) {
      console.error('Unable to render PDF preview.', error);
      viewer.setAttribute('aria-busy', 'false');
      viewer.innerHTML = `
        <p class="pdf-status">
          PDF preview is unavailable.
          <a href="${pdfUrl}" target="_blank" rel="noopener">Open the PDF directly.</a>
        </p>`;
    }
  }
})();
