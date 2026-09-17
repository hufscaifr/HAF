import React from 'react';
import { API_HEADERS, apiUrl } from '../config/api';

export function CompanyDashboard() {
  const [dashboardData, setDashboardData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [researchContext, setResearchContext] = React.useState({});
  const [stageLoading, setStageLoading] = React.useState({});
  const [stageErrors, setStageErrors] = React.useState({});
  const [activeTab, setActiveTab] = React.useState('추천 이유');
  const [activeSubTab, setActiveSubTab] = React.useState('Trend');

  React.useEffect(() => {
    const savedData = sessionStorage.getItem('selectedCompany');
    const savedContext = sessionStorage.getItem('selectedResearchContext');

    if (savedData) {
      let companySeed = null;
      let savedResearchContext = {};

      try {
        companySeed = JSON.parse(savedData);
      } catch (error) {
        console.error('데이터 파싱 에러:', error);
        setLoading(false);
        return;
      }

      if (!isPlainObject(companySeed) || !hasUsefulObjectData(companySeed)) {
        console.error('선택된 기업 데이터가 비어 있습니다:', companySeed);
        sessionStorage.removeItem('selectedCompany');
        setLoading(false);
        return;
      }

      try {
        savedResearchContext = savedContext ? JSON.parse(savedContext) : {};
      } catch (error) {
        console.error('분석 컨텍스트 파싱 에러:', error);
      }

      setResearchContext(savedResearchContext);
      setDashboardData(companySeed);
      const controller = new AbortController();
      const loadProfile = async () => {
        try {
          const response = await fetch(apiUrl('/api/company/profile'), {
            method: 'POST',
            headers: {
              ...API_HEADERS,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              company: companySeed,
              research_id: savedResearchContext.research_id || undefined,
              provider: savedResearchContext.provider || 'openai',
              model: savedResearchContext.model || undefined,
            }),
            signal: controller.signal,
          });

          if (!response.ok) {
            let message = '기업 소개 응답 에러';

            try {
              const errorBody = await response.json();
              message = formatApiErrorDetail(errorBody.detail) || message;
            } catch {
              message = `${message} (${response.status})`;
            }

            throw new Error(message);
          }

          const result = await response.json();
          const detailedCompany = result.company || {};
          if (!hasUsefulObjectData(detailedCompany)) {
            throw new Error('기업 소개 응답이 비어 있습니다.');
          }

          const mergedCompany = mergeUsefulCompanyData(
            companySeed,
            detailedCompany
          );

          sessionStorage.setItem('selectedCompany', JSON.stringify(mergedCompany));
          setDashboardData(mergedCompany);
        } catch (error) {
          if (error.name !== 'AbortError') {
            console.error('기업 소개 호출 실패:', error);
            setStageErrors({ profile: error.message });
          }
        } finally {
          setLoading(false);
        }
      };

      loadProfile();

      return () => controller.abort();
    }

    setLoading(false);
  }, []);

  const runStage = async (stage, endpoint, forceRefresh = false) => {
    if (!dashboardData || stageLoading[stage]) return;
    setStageLoading((current) => ({ ...current, [stage]: true }));
    setStageErrors((current) => ({ ...current, [stage]: null }));

    try {
      const response = await fetch(apiUrl(endpoint), {
        method: 'POST',
        headers: { ...API_HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company: dashboardData,
          research_id: researchContext.research_id || undefined,
          provider: researchContext.provider || 'openai',
          model: researchContext.model || undefined,
          force_refresh: forceRefresh,
        }),
      });
      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(formatApiErrorDetail(errorBody.detail) || `HTTP ${response.status}`);
      }
      const result = await response.json();
      const nextCompany = result.company || {};
      if (!hasUsefulObjectData(nextCompany)) throw new Error('분석 응답이 비어 있습니다.');
      setDashboardData((current) => {
        const merged = mergeUsefulCompanyData(current, nextCompany);
        sessionStorage.setItem('selectedCompany', JSON.stringify(merged));
        return merged;
      });
    } catch (error) {
      setStageErrors((current) => ({ ...current, [stage]: error.message }));
    } finally {
      setStageLoading((current) => ({ ...current, [stage]: false }));
    }
  };

  if (loading) {
    return (
      <div className="company-state">
        <div className="company-state-spinner" />
        <p>기업 소개를 불러오는 중입니다.</p>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="company-state">
        <p>선택된 기업 정보가 없습니다.</p>

        <button
          className="company-state-button"
          onClick={() => window.history.back()}
          type="button"
        >
          이전 페이지로 돌아가기
        </button>
      </div>
    );
  }

  const finalChartUrl =
    dashboardData.daily_chart_data_url ||
    dashboardData.chart_data_url ||
    dashboardData.intraday_chart_data_url ||
    dashboardData.daily_chart_url ||
    dashboardData.chart_url ||
    dashboardData.intraday_chart_url ||
    dashboardData.chart ||
    dashboardData.image_url;

  const tabs = [
    '추천 이유',
    '의견',
    '기술적 분석',
    '리스크 요인',
    '재무 분석',
  ];

  const subTabs = [
    { id: 'Trend', label: 'Trend' },
    { id: 'Momentum', label: 'Momentum' },
    { id: 'Volatility', label: 'Volatility' },
    { id: 'Volume', label: 'Volume & Money' },
    { id: 'Short-Term', label: 'Short-Term' },
    { id: 'Overall', label: 'Overall' },
  ];

  const fin = dashboardData.financial_metrics || dashboardData.financial || {};

  const technicalReportText =
    dashboardData.technical_analysis_text ||
    dashboardData.ai_technical_analysis ||
    '';

  const highlights = dashboardData.technical_highlights || [];

  const recommendationReason =
    dashboardData.recommendation_reason ||
    dashboardData.reason ||
    dashboardData.ai_opinion ||
    dashboardData.article_relevance ||
    '';

  const riskList = firstNonEmptyArray(
    dashboardData.risks,
    dashboardData.key_risks,
    dashboardData.keyRisks,
    dashboardData.key_catalysts,
    dashboardData.catalysts
  );

  const deepRiskAnalysis = dashboardData.risk_analysis || '';

  const financialAnalysis =
    dashboardData.financial_analysis ||
    dashboardData.financial_opinion ||
    fin.analysis ||
    fin.comment ||
    '';

  const investmentOpinionText =
    dashboardData.ai_opinion ||
    dashboardData.technical_opinion ||
    dashboardData.technical_analysis_text ||
    dashboardData.ai_technical_analysis ||
    '';

  const parsedSections = parseMarkdownSections(technicalReportText);

  const sortedHighlights = [...highlights].sort(
    (a, b) =>
      (b.importance === 'high' ? 1 : 0) - (a.importance === 'high' ? 1 : 0)
  );

  const latestPrice =
    dashboardData.latest_close || dashboardData.close_price || dashboardData.price;

  const ticker =
    dashboardData.korean_ticker || dashboardData.ticker || '000000';

  const companyName =
    dashboardData.name ||
    dashboardData.company_name_ko ||
    dashboardData.company_name ||
    '기업명';

  return (
    <main className="company-dashboard-page">
      <div className="company-dashboard-container">
        <div className="company-back-wrap">
          <button
            type="button"
            className="company-back-button"
            onClick={() => window.history.back()}
          >
            <span>←</span>
            추천 기업 리스트로 돌아가기
          </button>
        </div>

        <header className="company-hero">
          <div className="company-hero-left">
            <div className="company-eyebrow">HAF · AI Equity Analysis</div>

            <h1 className="company-name">{companyName}</h1>

            <div className="company-meta">
              <span>{ticker}</span>
              <span className="company-meta-divider">·</span>
              <span>{dashboardData.market || 'KOSPI'}</span>
              {dashboardData.industry && (
                <>
                  <span className="company-meta-divider">·</span>
                  <span>{dashboardData.industry}</span>
                </>
              )}
            </div>

            {(dashboardData.overview || recommendationReason) && (
              <p className="company-hero-summary">
                {dashboardData.overview || recommendationReason}
              </p>
            )}

            {stageErrors.profile && (
              <p className="company-stage-error">{stageErrors.profile}</p>
            )}
          </div>

          <div className="company-price-card">
            <div className="company-price-label">Latest Close</div>

            <div className="company-price-value">
              {latestPrice
                ? Number(latestPrice).toLocaleString('ko-KR')
                : '정보 없음'}
            </div>

            {latestPrice && (
              <div className="company-price-currency">
                {dashboardData.currency || 'KRW'}
              </div>
            )}
          </div>
        </header>

        <section className="company-chart-section">
          <div className="company-section-head compact">
            <div>
              <div className="company-section-eyebrow">Price Trend</div>
              <h2 className="company-section-title">Market Movement</h2>
            </div>
          </div>

          <div className="company-chart-card">
            {finalChartUrl ? (
              <img
                src={finalChartUrl}
                alt={`${companyName} 주가 차트`}
                className="company-chart-image"
              />
            ) : (
              <div className="company-chart-empty">
                <div className="company-chart-empty-icon">↗</div>
                <p>차트 데이터를 불러오는 중이거나 존재하지 않습니다.</p>
              </div>
            )}
          </div>
        </section>

        <section className="company-analysis-section">
          <div className="company-section-head">
            <div>
              <div className="company-section-eyebrow">AI Research</div>
              <h2 className="company-section-title">Company Analysis</h2>
            </div>

            {dashboardData.article_relevance && (
              <div className="company-relevance-pill">
                기사 관련성 · {dashboardData.article_relevance}
              </div>
            )}
          </div>

          <div className="company-main-tabs">
            {tabs.map((tab) => (
              <button
                key={tab}
                type="button"
                className={`company-main-tab ${activeTab === tab ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="company-tab-content">
            {activeTab === '추천 이유' && (
              <div className="company-feature-card">
                <div className="company-feature-label">AI Recommendation</div>
                <p className="company-feature-text">
                  {recommendationReason || '추천 이유 정보가 없습니다.'}
                </p>
              </div>
            )}

            {activeTab === '의견' && (
              <div className="company-feature-card">
                <div className="company-feature-label">Investment Opinion</div>
                <p className="company-feature-text">
                  {investmentOpinionText || '의견을 준비 중입니다.'}
                </p>

                {dashboardData.opinion_rationale && (
                  <div className="company-secondary-note">
                    {dashboardData.opinion_rationale}
                  </div>
                )}
              </div>
            )}

            {activeTab === '기술적 분석' && (
              <div className="company-technical-layout">
                <StageActions
                  primaryLabel={dashboardData.technical_context ? '기술 데이터 새로고침' : '기술 데이터 불러오기'}
                  primaryLoading={stageLoading.technicalData}
                  onPrimary={() => runStage(
                    'technicalData',
                    '/api/company/technical-data',
                    Boolean(dashboardData.technical_context)
                  )}
                  secondaryLabel="AI Analyze"
                  secondaryLoading={stageLoading.technicalAi}
                  secondaryDisabled={!dashboardData.technical_context}
                  onSecondary={() => runStage('technicalAi', '/api/company/technical-analysis')}
                  error={stageErrors.technicalData || stageErrors.technicalAi}
                />
                {sortedHighlights.length > 0 && (
                  <div className="company-highlight-grid">
                    {sortedHighlights.map((item, index) => (
                      <HighlightCard key={`${item.title || 'highlight'}-${index}`} item={item} />
                    ))}
                  </div>
                )}

                <div className="company-technical-card">
                  <div className="company-sub-tabs">
                    {subTabs.map((sub) => {
                      const hasContent =
                        parsedSections[sub.id] && parsedSections[sub.id].length > 0;

                      if (!hasContent && sub.id !== 'Overall') {
                        return null;
                      }

                      return (
                        <button
                          key={sub.id}
                          type="button"
                          className={`company-sub-tab ${
                            activeSubTab === sub.id ? 'active' : ''
                          }`}
                          onClick={() => setActiveSubTab(sub.id)}
                        >
                          {sub.label}
                        </button>
                      );
                    })}
                  </div>

                  <div className="company-technical-content">
                    {parsedSections[activeSubTab] &&
                    parsedSections[activeSubTab].length > 0 ? (
                      parsedSections[activeSubTab].map((line, index) => (
                        <p key={`${activeSubTab}-${index}`}>{line}</p>
                      ))
                    ) : (
                      <div className="company-empty-text">
                        선택한 {activeSubTab} 분석 데이터가 없습니다.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === '리스크 요인' && (
              <div className="company-risk-layout">
                <StageActions
                  primaryLabel={deepRiskAnalysis ? '리스크 다시 분석' : '리스크 분석 시작'}
                  primaryLoading={stageLoading.risk}
                  onPrimary={() => runStage('risk', '/api/company/risk-analysis')}
                  error={stageErrors.risk}
                />
                <div className="company-content-group">
                  <div className="company-content-label">Key Risks</div>

                  <div className="company-risk-list">
                    {riskList.length > 0 ? (
                      riskList.map((item, index) => (
                        <div key={`${formatRiskItem(item)}-${index}`} className="company-risk-item">
                          <div className="company-risk-dot" />
                          <span>{formatRiskItem(item)}</span>
                        </div>
                      ))
                    ) : (
                      <div className="company-empty-text">
                        감지된 리스크가 없습니다.
                      </div>
                    )}
                  </div>
                </div>

                {deepRiskAnalysis && (
                  <div className="company-content-group">
                    <div className="company-content-label">Deep Risk Analysis</div>
                    <MarkdownText text={deepRiskAnalysis} tone="risk" />
                  </div>
                )}
              </div>
            )}

            {activeTab === '재무 분석' && (
              <div className="company-financial-layout">
                <StageActions
                  primaryLabel={dashboardData.financial_context ? '재무 데이터 새로고침' : 'DART 재무 데이터 불러오기'}
                  primaryLoading={stageLoading.financialData}
                  onPrimary={() => runStage(
                    'financialData',
                    '/api/company/financial-data',
                    Boolean(dashboardData.financial_context)
                  )}
                  secondaryLabel="AI Analyze"
                  secondaryLoading={stageLoading.financialAi}
                  secondaryDisabled={!dashboardData.financial_context}
                  onSecondary={() => runStage('financialAi', '/api/company/financial-analysis')}
                  error={stageErrors.financialData || stageErrors.financialAi}
                />
                <div className="company-financial-grid">
                  <FinancialMetric label="PER" value={formatRatio(fin.per, 'x')} />
                  <FinancialMetric label="PBR" value={formatRatio(fin.pbr, 'x')} />
                  <FinancialMetric label="ROE" value={formatRatio(fin.roe, '%')} />
                  <FinancialMetric label="EPS" value={formatNumber(fin.eps)} />
                  <FinancialMetric label="BPS" value={formatNumber(fin.bps)} />
                  <FinancialMetric
                    label="Dividend Yield"
                    value={formatRatio(
                      fin.cash_dividend_yield ?? fin.dividend_yield,
                      '%'
                    )}
                  />
                </div>

                <div className="company-content-group">
                  <div className="company-content-label">Financial Analysis</div>

                  {financialAnalysis ? (
                    <MarkdownText text={financialAnalysis} tone="financial" />
                  ) : (
                    <div className="company-empty-text">
                      재무 분석 세부 코멘트가 없습니다.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function hasUsefulObjectData(value) {
  if (!isPlainObject(value)) {
    return false;
  }

  return Object.values(value).some((item) => {
    if (Array.isArray(item)) return item.length > 0;
    if (item && typeof item === 'object') return Object.keys(item).length > 0;
    return item !== null && item !== undefined && item !== '';
  });
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function mergeUsefulCompanyData(base, next) {
  const merged = { ...(base || {}) };

  Object.entries(next || {}).forEach(([key, value]) => {
    if (!isUsefulValue(value)) {
      return;
    }

    merged[key] = value;
  });

  return merged;
}

function isUsefulValue(value) {
  if (Array.isArray(value)) {
    return value.length > 0;
  }

  if (value && typeof value === 'object') {
    return Object.values(value).some(isUsefulValue);
  }

  return value !== null && value !== undefined && value !== '';
}

function firstNonEmptyArray(...values) {
  return values.find((value) => Array.isArray(value) && value.length > 0) || [];
}

function formatRiskItem(item) {
  if (typeof item === 'string') {
    return item;
  }

  if (item && typeof item === 'object') {
    return (
      item.title ||
      item.detail ||
      item.description ||
      item.name ||
      JSON.stringify(item)
    );
  }

  return String(item || '');
}

function formatApiErrorDetail(detail) {
  if (!detail) {
    return '';
  }

  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (!item || typeof item !== 'object') {
          return String(item);
        }

        const location = Array.isArray(item.loc) ? item.loc.join('.') : item.loc;
        return [location, item.msg].filter(Boolean).join(': ');
      })
      .filter(Boolean)
      .join('\n');
  }

  try {
    return JSON.stringify(detail);
  } catch {
    return String(detail);
  }
}

function parseMarkdownSections(text) {
  const lines = String(text || '').split('\n');
  let currentSection = 'Overall';

  const sections = {
    Trend: [],
    Momentum: [],
    Volatility: [],
    Volume: [],
    'Short-Term': [],
    Overall: [],
  };

  lines.forEach((line) => {
    const trimmed = line.trim();

    if (trimmed.startsWith('##')) {
      const headerText = trimmed.replace('##', '').trim().toLowerCase();

      if (headerText.includes('trend')) {
        currentSection = 'Trend';
      } else if (headerText.includes('momentum')) {
        currentSection = 'Momentum';
      } else if (headerText.includes('volatility')) {
        currentSection = 'Volatility';
      } else if (headerText.includes('volume') || headerText.includes('money')) {
        currentSection = 'Volume';
      } else if (headerText.includes('short')) {
        currentSection = 'Short-Term';
      } else {
        currentSection = 'Overall';
      }
    } else if (trimmed) {
      sections[currentSection].push(line);
    }
  });

  return sections;
}

function StageActions({
  primaryLabel,
  primaryLoading,
  onPrimary,
  secondaryLabel,
  secondaryLoading,
  secondaryDisabled,
  onSecondary,
  error,
}) {
  return (
    <div className="company-stage-actions-wrap">
      <div className="company-stage-actions">
        <button type="button" onClick={onPrimary} disabled={primaryLoading}>
          {primaryLoading ? '불러오는 중...' : primaryLabel}
        </button>
        {secondaryLabel && (
          <button
            type="button"
            onClick={onSecondary}
            disabled={secondaryDisabled || secondaryLoading}
          >
            {secondaryLoading ? '분석 중...' : secondaryLabel}
          </button>
        )}
      </div>
      {error && <p className="company-stage-error">{error}</p>}
    </div>
  );
}

function HighlightCard({ item }) {
  const type =
    item.type === 'positive'
      ? 'positive'
      : item.type === 'negative'
        ? 'negative'
        : 'watch';

  const label =
    type === 'positive'
      ? 'Positive Signal'
      : type === 'negative'
        ? 'Risk Signal'
        : 'Watch';

  return (
    <article className={`company-highlight-card ${type}`}>
      <div className="company-highlight-top">
        <span className="company-highlight-label">{label}</span>

        {item.importance && (
          <span className="company-highlight-importance">{item.importance}</span>
        )}
      </div>

      <h4>{item.title}</h4>
      <p>{item.detail}</p>
    </article>
  );
}

function FinancialMetric({ label, value }) {
  return (
    <div className="company-financial-metric">
      <div className="company-financial-label">{label}</div>
      <div className="company-financial-value">{value}</div>
    </div>
  );
}

function MarkdownText({ text, tone }) {
  return (
    <div className={`company-markdown-card ${tone || ''}`}>
      {String(text || '')
        .split('\n')
        .map((line, index) => {
          const trimmed = line.trim();

          if (!trimmed) {
            return null;
          }

          if (trimmed.startsWith('##')) {
            return <h4 key={index}>{trimmed.replace(/^##+/, '').trim()}</h4>;
          }

          return <p key={index}>{line}</p>;
        })}
    </div>
  );
}

function formatRatio(value, suffix) {
  if (value === null || value === undefined) {
    return '-';
  }

  return `${value}${suffix}`;
}

function formatNumber(value) {
  if (value === null || value === undefined) {
    return '-';
  }

  return Number(value).toLocaleString('ko-KR');
}

export default CompanyDashboard;
