const RESEARCH_BASE = '/equity_research/news_research';

export function buildResearchResultPath(researchId) {
  return `${RESEARCH_BASE}/${encodeURIComponent(researchId)}`;
}

export function buildCompanyResearchPath(researchId, ticker) {
  return `${buildResearchResultPath(researchId)}/company/${encodeURIComponent(ticker)}`;
}

export function parseResearchPath(pathname = window.location.pathname) {
  const normalized = pathname.replace(/\/$/, '');
  const companyMatch = normalized.match(
    /^\/equity_research\/news_research\/([^/]+)\/company\/([^/]+)$/
  );
  if (companyMatch) {
    return {
      kind: 'company',
      researchId: decodeURIComponent(companyMatch[1]),
      ticker: decodeURIComponent(companyMatch[2]),
    };
  }

  const resultMatch = normalized.match(
    /^\/equity_research\/news_research\/([^/]+)$/
  );
  if (resultMatch && resultMatch[1] !== 'new_research') {
    return {
      kind: 'result',
      researchId: decodeURIComponent(resultMatch[1]),
    };
  }

  return null;
}

export function normalizeCompanyTicker(company) {
  return String(company?.korean_ticker || company?.ticker || '')
    .split('.')[0]
    .replace(/\D/g, '')
    .padStart(6, '0');
}
