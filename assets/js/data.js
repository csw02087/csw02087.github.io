// category: 'finance' | 'pricing' | 'nlp' | 'market-reports' | 'research'
// To add a work, push an object onto the array below.
// The `content` field is the detail page body and accepts raw HTML.
const WORKS = [
  {
    id: 'market-report-01',
    category: 'market-reports',
    title: 'BH(090460.KS) Company Research',
    experience: 'HYU Investment Club Research',
    writtenDate: '2024-11-05',
    postedDate: '2026-08-24',
    summary: 'Company analysis of BH(090460.KS) valuation and market position.',
    content: `
      <p>This report examines BH(090460.KS) valuation and market position.</p>
    `,
    link: 'reports/bh-company-analysis-eng.pdf'
  },
  {
    id: 'market-report-02',
    category: 'market-reports',
    title: 'VT(018290.KQ) Company Research',
    experience: 'HYU Investment Club Research',
    writtenDate: '2024-07-26',
    postedDate: '2026-08-24',
    summary: 'Company analysis of VT(018290.KQ) valuation and market position.',
    content: `
      <p>This report examines VT(018290.KQ) valuation and market position.</p>
    `,
    link: 'reports/vt-company-analysis-eng.pdf'
  },
];

const CATEGORY_LABELS = {
  finance: 'Finance Project',
  pricing: 'Pricing Project',
  nlp: 'NLP Project',
  'market-reports': 'Industry & Company Research Reports',
  research: 'Research',
};