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
    <div class="project-viewers">
      <section class="viewer-panel pdf-section" aria-labelledby="pdf-heading">
        <div class="viewer-panel-header">
          <h2 id="pdf-heading">Related PDF</h2>
          ${item.link ? `<a href="${item.link}" target="_blank" rel="noopener">Open PDF &rarr;</a>` : ''}
        </div>
        ${item.link
          ? `<object class="pdf-desktop-viewer" data="${item.link}#view=FitH" type="application/pdf" aria-label="${item.title} PDF">
              <p>PDF preview is unavailable. <a href="${item.link}">Open the PDF directly.</a></p>
            </object>
            <div class="pdf-mobile-viewer" data-pdf-url="${item.link}" aria-label="${item.title} PDF" aria-busy="true">
              <p class="pdf-status" role="status">Loading PDF preview&hellip;</p>
            </div>`
          : '<div class="viewer-empty">No PDF has been added for this project yet.</div>'}
      </section>

      <section class="viewer-panel code-section" aria-labelledby="code-heading">
        <div class="viewer-panel-header">
          <h2 id="code-heading">Code</h2>
        </div>
        <div id="code-viewer" class="code-viewer" aria-live="polite"></div>
      </section>
    </div>
  `;

  renderCodeViewer(item.codeFiles || []);

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

  async function renderCodeViewer(files) {
    const viewer = document.getElementById('code-viewer');

    if (files.length === 0) {
      viewer.innerHTML = '<div class="viewer-empty">Code will be added for this project.</div>';
      return;
    }

    viewer.innerHTML = `
      <div class="code-tabs" role="tablist" aria-label="Project source files">
        ${files.map((file, index) => `
          <button class="code-tab${index === 0 ? ' is-active' : ''}" type="button" role="tab"
            aria-selected="${index === 0}" data-code-index="${index}">${escapeHtml(file.name)}</button>
        `).join('')}
      </div>
      <div class="code-content"><p class="code-status">Loading code&hellip;</p></div>`;

    const tabs = Array.from(viewer.querySelectorAll('.code-tab'));
    tabs.forEach((tab) => {
      tab.addEventListener('click', () => selectCodeFile(Number(tab.dataset.codeIndex)));
    });

    await selectCodeFile(0);

    async function selectCodeFile(index) {
      const file = files[index];
      const content = viewer.querySelector('.code-content');

      tabs.forEach((tab, tabIndex) => {
        const active = tabIndex === index;
        tab.classList.toggle('is-active', active);
        tab.setAttribute('aria-selected', String(active));
      });

      content.innerHTML = '<p class="code-status">Loading code&hellip;</p>';

      try {
        const source = Object.prototype.hasOwnProperty.call(file, 'content')
          ? file.content
          : await fetchCode(file.path);
        content.innerHTML = `<pre tabindex="0"><code class="language-${escapeHtml(file.language || 'text')}">${escapeHtml(source)}</code></pre>`;
      } catch (error) {
        console.error('Unable to load source code.', error);
        content.innerHTML = '<p class="code-status">Unable to load this source file.</p>';
      }
    }
  }

  async function fetchCode(path) {
    if (!path) throw new Error('Code file path is missing.');
    const response = await fetch(path);
    if (!response.ok) throw new Error(`Code request failed: ${response.status}`);
    return response.text();
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }
})();
