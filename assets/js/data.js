// category: 'finance' | 'pricing' | 'nlp' | 'market-reports' | 'research'
// To add a work, push an object onto the array below.
// The `content` field is the detail page body and accepts raw HTML.
const WORKS = [
  {
    id: 'market-report-01',
    category: 'market-reports',
    title: 'BH(090460 KOSPI) Company Research',
    experience: 'HYU Investment Club Research',
    date: '2024-11',
    summary: 'Company analysis of BH(090460 KOSPI).',
    content: `
      <p>This report examines BH(090460 KOSPI) valuation and market position.</p>
    `,
    link: 'reports/bh-company-analysis-eng.pdf'
  },
];

const CATEGORY_LABELS = {
  finance: 'Finance Project',
  pricing: 'Pricing Project',
  nlp: 'NLP Project',
  'market-reports': 'Industry & Company Research Reports',
  research: 'Research',
};
