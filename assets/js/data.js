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
    codeFiles: [
      {
        name: 'AI based Malicious Comment Legal Risk Insurance Service Project Code.ipynb',
        language: 'python',
        path: '/reports/AI based Malicious Comment Legal Risk Insurance Service Project Code.ipynb'
      }
    ]
  },

  {
    id: 'market-report-03',
    category: 'analysis-reports',
    title: 'Walmart (NASDAQ: WMT) Equity Valuation — FCF-DCF with Assumption Board',
    experience: 'FIN 5203 Financial Management · WashU Olin',
    writtenDate: '2026-11-20',
    postedDate: '2026-11-20',
    summary: 'Fiscal-year FCF-DCF valuation of Walmart with CAPM/WACC (regression, Blume, peer-relevered betas), WACC×g sensitivity, Monte Carlo, and P/E · EV/EBITDA cross-checks; quarterly appendix (1Q23–3Q27, S&P Capital IQ). Includes a live assumption board.',
    content: `
      <p>Research note on Walmart built on the FIN 5203 FCF-DCF framework (Market Value Balance Sheet → CAPM/WACC → historical ratios → projected FCF), extended with quarterly data from S&amp;P Capital IQ (19 quarters), an event-tagged historical analysis, and quant risk support (sensitivity grid, bear/base/bull scenarios, 10,000-draw Monte Carlo). P/E and EV/EBITDA on Walmart's own 5-year history serve as cross-checks; a reverse DCF shows what the market price implies.</p>
      <p><a href="wmt-board/" target="_blank" rel="noopener">Open the live assumption board &rarr;</a> — set each FCF driver (history · consensus · peers · agent recommendation) and watch WACC, DCF, sensitivity and Monte Carlo recompute. &nbsp; <a href="reports/wmt-valuation-report-kor.pdf" target="_blank" rel="noopener">Korean version (PDF)</a></p>
    `,
    link: 'reports/wmt-valuation-report-eng.pdf',
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
    codeFiles: [
      {
        name: 'KCI_FI003240857 Code.ipynb',
        language: 'json',
        path: 'reports/KCI_FI003240857 Code.ipynb'
      }
    ]
  },
];

const CATEGORY_LABELS = {
  'portfolio-management': 'Portfolio Management Projects',
  'risk-management': 'Risk Management Projects',
  'other-finance-projects': 'Other Finance Projects',
  'analysis-reports': 'Analysis Reports',
  'publication': 'Publication',
};
