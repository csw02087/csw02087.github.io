// category: 'finance' | 'pricing' | 'nlp' | 'market-reports' | 'research'
// To add a work, push an object onto the array below.
// The `content` field is the detail page body and accepts raw HTML.
const WORKS = [
  {
    id: 'market-report-01',
    category: 'market-reports',
    title: 'BH(KS090460) Company Research',
    experience: 'HYU Investment Club Research',
    writtenDate: '2024-11-05',
    postedDate: '2026-08-24',
    summary: 'Company analysis of BH(KSS090460) valuation and market position.',
    content: `
      <p>This report examines BH(KS090460) valuation and market position.</p>
    `,
    link: 'reports/bh-company-analysis-eng.pdf'
  },
  {
    id: 'market-report-02',
    category: 'market-reports',
    title: 'VT(KQ018290) Company Research',
    experience: 'HYU Investment Club Research',
    writtenDate: '2024-07-26',
    postedDate: '2026-08-24',
    summary: 'Company analysis of VT(KQ018290) valuation and market position.',
    content: `
      <p>This report examines VT(KQ018290) valuation and market position.</p>
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