// category: 'portfolio-management' | 'risk-management' | 'other-finance-projects' | 'analysis-reports' | 'publication'
// To add a work, push an object onto the array below.
// The `content` field is the detail page body and accepts raw HTML.
// Add code with `codeFiles: [{ name: 'analysis.py', language: 'python', path: 'code/analysis.py' }]`.
// Use `content` instead of `path` when the source should be embedded directly in this file.
const WORKS = [
    {
    id: 'risk-management-finance-01',
    category: 'risk-management',
    title: 'Carhart 4 Factor Project',
    experience: 'Team Project',
    writtenDate: '2026-02-23',
    postedDate: '2026-08-31',
    summary: 'Carhart 4 Factor Project Checking the risks.',
    content: `
      <p>Project description.</p>
  `,
    link: 'reports/Carhart 4 Factor Project.pdf',
    codeFiles: []
  },

  {
    id: 'other-finance-01',
    category: 'other-finance-projects',
    title: 'AI Based Malicious Comment Insurance Service Project',
    experience: 'Team Project',
    writtenDate: '2026-05-15',
    postedDate: '2026-08-31',
    summary: 'AI based malicious comment insurance service project.',
    content: `
      <p>Project description.</p>
  `,
    link: 'reports/AI based Malicious Comment Legal Risk Insurance Service Project.pdf',
    codeFiles: []
  },

  {
    id: 'market-report-01',
    category: 'analysis-reports',
    title: 'BH(090460.KS) Company Research',
    experience: 'HYU Investment Club Research',
    writtenDate: '2024-11-05',
    postedDate: '2026-08-24',
    summary: 'Company analysis of BH(090460.KS) valuation and market position.',
    content: `
      <p>This report examines BH(090460.KS) valuation and market position.</p>
    `,
    link: 'reports/bh-company-analysis-eng.pdf',
    codeFiles: []
  },
  {
    id: 'market-report-02',
    category: 'analysis-reports',
    title: 'VT(018290.KQ) Company Research',
    experience: 'HYU Investment Club Research',
    writtenDate: '2024-07-26',
    postedDate: '2026-08-24',
    summary: 'Company analysis of VT(018290.KQ) valuation and market position.',
    content: `
      <p>This report examines VT(018290.KQ) valuation and market position.</p>
    `,
    link: 'reports/vt-company-analysis-eng.pdf',
    codeFiles: []
  },

    {
    id: 'Publication-01',
    category: 'publication',
    title: 'Analyzing UI/UX Elements of Financial Apps Using BERTopic and Changes in User Reactions before and after the Super App Launch',
    experience: 'Publication',
    writtenDate: '2025-08-20',
    postedDate: '2026-08-31',
    summary: 'Analyzing UI/UX Elements of Financial Apps Using BERTopic and Changes in User Reactions before and after the Super App Launch',
    content: `
      <p>Project description.</p>
  `,
    link: 'reports/KCI_FI003240857.pdf',
    codeFiles: []
  },
];

const CATEGORY_LABELS = {
  'portfolio-management': 'Portfolio Management Projects',
  'risk-management': 'Risk Management Projects',
  'other-finance-projects': 'Other Finance Projects',
  'analysis-reports': 'Analysis Reports',
  'publication': 'Publication',
};
