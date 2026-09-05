import React from 'react';

export function CompanyDashboard() {
  const [dashboardData, setDashboardData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [activeTab, setActiveTab] = React.useState('추천 이유');
  const [activeSubTab, setActiveSubTab] = React.useState('Trend');

  React.useEffect(() => {
    const savedData = sessionStorage.getItem('selectedCompany');

    if (savedData) {
      try {
        setDashboardData(JSON.parse(savedData));
        setLoading(false);
        return;
      } catch (error) {
        console.error('데이터 파싱 에러:', error);
      }
    }

    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="company-state">
        <div className="company-state-spinner" />
        <p>AI 분석 데이터를 불러오는 중입니다.</p>
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

  const riskList =
    dashboardData.risks ||
    dashboardData.key_catalysts ||
    dashboardData.catalysts ||
    [];

  const deepRiskAnalysis = dashboardData.risk_analysis || '';

  const financialAnalysis =
    dashboardData.financial_analysis ||
    dashboardData.financial_opinion ||
    fin.analysis ||
    fin.comment ||
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
            </div>

            {dashboardData.recommendation_reason && (
              <p className="company-hero-summary">
                {dashboardData.recommendation_reason}
              </p>
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
                  {dashboardData.recommendation_reason ||
                    dashboardData.reason ||
                    '추천 이유 정보가 없습니다.'}
                </p>
              </div>
            )}

            {activeTab === '의견' && (
              <div className="company-feature-card">
                <div className="company-feature-label">Investment Opinion</div>
                <p className="company-feature-text">
                  {dashboardData.ai_opinion ||
                    dashboardData.technical_opinion ||
                    '의견을 준비 중입니다.'}
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
                <div className="company-content-group">
                  <div className="company-content-label">Key Risks</div>

                  <div className="company-risk-list">
                    {riskList.length > 0 ? (
                      riskList.map((item, index) => (
                        <div key={`${item}-${index}`} className="company-risk-item">
                          <div className="company-risk-dot" />
                          <span>{item}</span>
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
