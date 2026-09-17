import React from 'react';
import { API_HEADERS, apiUrl } from '../config/api';
import {
  buildResearchResultPath,
  normalizeCompanyTicker,
  parseResearchPath,
} from '../utils/researchRoutes';

export function CompanyDashboard() {
  const [dashboardData, setDashboardData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [researchContext, setResearchContext] = React.useState({});
  const [stageLoading, setStageLoading] = React.useState({});
  const [stageErrors, setStageErrors] = React.useState({});
  const [activePanel, setActivePanel] = React.useState(null);
  const [activeSubTab, setActiveSubTab] = React.useState('Trend');

  React.useEffect(() => {
    const controller = new AbortController();
    const route = parseResearchPath();

    const loadCompanyPage = async () => {
      let companySeed = null;
      let context = {};

      try {
        const savedCompany = sessionStorage.getItem('selectedCompany');
        const savedContext = sessionStorage.getItem('selectedResearchContext');
        if (savedCompany) companySeed = JSON.parse(savedCompany);
        if (savedContext) context = JSON.parse(savedContext);
      } catch (parseError) {
        console.error('저장된 기업 데이터 파싱 실패:', parseError);
      }

      const routeMatchesSession =
        companySeed &&
        (!route?.ticker || normalizeCompanyTicker(companySeed) === route.ticker) &&
        (!route?.researchId || context.research_id === route.researchId);

      if (!routeMatchesSession && route?.researchId && route?.ticker) {
        try {
          const response = await fetch(
            apiUrl(`/api/new-research/${encodeURIComponent(route.researchId)}`),
            { headers: { ...API_HEADERS, Accept: 'application/json' }, signal: controller.signal }
          );
          if (!response.ok) throw new Error(`분석 컨텍스트 조회 실패 (${response.status})`);
          const research = await response.json();
          companySeed = research.companies?.find(
            (company) => normalizeCompanyTicker(company) === route.ticker
          );
          if (!companySeed) throw new Error('해당 분석에서 기업을 찾을 수 없습니다.');
          context = {
            research_id: research.research_id,
            provider: research.provider,
            model: research.model,
            article: research.article,
            selection: research.selection,
          };
          sessionStorage.setItem('researchData', JSON.stringify(research));
          sessionStorage.setItem('selectedCompany', JSON.stringify(companySeed));
          sessionStorage.setItem('selectedResearchContext', JSON.stringify(context));
        } catch (resolveError) {
          if (resolveError.name !== 'AbortError') {
            setStageErrors({ profile: resolveError.message });
          }
          setLoading(false);
          return;
        }
      }

      if (!isPlainObject(companySeed) || !hasUsefulObjectData(companySeed)) {
        setLoading(false);
        return;
      }

      setResearchContext(context);
      setDashboardData(companySeed);

      try {
        const response = await fetch(apiUrl('/api/company/profile'), {
          method: 'POST',
          headers: { ...API_HEADERS, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            company: companySeed,
            research_id: context.research_id || undefined,
            provider: context.provider || 'openai',
            model: context.model || undefined,
          }),
          signal: controller.signal,
        });
        if (!response.ok) {
          const errorBody = await response.json().catch(() => ({}));
          throw new Error(formatApiErrorDetail(errorBody.detail) || `기업 소개 응답 에러 (${response.status})`);
        }
        const result = await response.json();
        const detailedCompany = result.company || {};
        if (!hasUsefulObjectData(detailedCompany)) throw new Error('기업 소개 응답이 비어 있습니다.');
        const mergedCompany = mergeUsefulCompanyData(companySeed, detailedCompany);
        sessionStorage.setItem('selectedCompany', JSON.stringify(mergedCompany));
        setDashboardData(mergedCompany);
      } catch (profileError) {
        if (profileError.name !== 'AbortError') {
          setStageErrors({ profile: profileError.message });
        }
      } finally {
        setLoading(false);
      }
    };

    loadCompanyPage();
    return () => controller.abort();
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
            onClick={() => {
              if (researchContext.research_id) {
                window.location.href = buildResearchResultPath(researchContext.research_id);
              } else {
                window.history.back();
              }
            }}
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

        <section className="company-overview">
          <div className="company-overview__copy">
            <span>News Relevance</span>
            <p>{recommendationReason || '뉴스와 기업의 연결 근거를 준비 중입니다.'}</p>
          </div>
          {dashboardData.business_model && (
            <div className="company-overview__copy">
              <span>Business Model</span>
              <p>{dashboardData.business_model}</p>
            </div>
          )}
        </section>

        <section className="company-launchpad" aria-label="기업 분석 메뉴">
          <div className="company-launchpad__head">
            <div>
              <span>Analysis Desk</span>
              <h2>필요한 분석만 선택하세요.</h2>
            </div>
            {dashboardData.article_relevance && (
              <p>{dashboardData.article_relevance}</p>
            )}
          </div>

          <div className="company-launchpad__grid">
            <AnalysisLaunchButton
              eyebrow="Market"
              title="기술적 분석"
              description="가격, 거래량과 기술 지표를 확인합니다."
              status={dashboardData.technical_context ? 'Data ready' : 'Not loaded'}
              onClick={() => setActivePanel('technical')}
            />
            <AnalysisLaunchButton
              eyebrow="Fundamentals"
              title="재무 분석"
              description="DART 재무지표와 AI 의견을 확인합니다."
              status={dashboardData.financial_context ? 'Data ready' : 'Not loaded'}
              onClick={() => setActivePanel('financial')}
            />
            <AnalysisLaunchButton
              eyebrow="Risk"
              title="리스크 분석"
              description="뉴스 투자 논리의 주요 위험을 검토합니다."
              status={deepRiskAnalysis ? 'Analysis ready' : 'Not analyzed'}
              onClick={() => setActivePanel('risk')}
            />
          </div>
        </section>
      </div>

      <CompanyAnalysisModal
        panel={activePanel}
        onClose={() => setActivePanel(null)}
        companyName={companyName}
        dashboardData={dashboardData}
        finalChartUrl={finalChartUrl}
        fin={fin}
        financialAnalysis={financialAnalysis}
        riskList={riskList}
        deepRiskAnalysis={deepRiskAnalysis}
        sortedHighlights={sortedHighlights}
        parsedSections={parsedSections}
        activeSubTab={activeSubTab}
        setActiveSubTab={setActiveSubTab}
        subTabs={subTabs}
        stageLoading={stageLoading}
        stageErrors={stageErrors}
        runStage={runStage}
      />
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

function AnalysisLaunchButton({ eyebrow, title, description, status, onClick }) {
  return (
    <button className="company-launch-button" type="button" onClick={onClick}>
      <span className="company-launch-button__eyebrow">{eyebrow}</span>
      <strong>{title}</strong>
      <p>{description}</p>
      <span className="company-launch-button__footer">
        <span>{status}</span>
        <span aria-hidden="true">→</span>
      </span>
    </button>
  );
}

function CompanyAnalysisModal({
  panel, onClose, companyName, dashboardData, finalChartUrl, fin,
  financialAnalysis, riskList, deepRiskAnalysis, sortedHighlights,
  parsedSections, activeSubTab, setActiveSubTab, subTabs,
  stageLoading, stageErrors, runStage,
}) {
  React.useEffect(() => {
    if (!panel) return undefined;
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [panel, onClose]);

  if (!panel) return null;
  const titles = {
    technical: ['Technical Analysis', '가격 흐름과 기술 지표'],
    financial: ['Financial Analysis', '재무지표와 기업가치'],
    risk: ['Risk Analysis', '뉴스 투자 논리의 위험 요인'],
  };
  const [eyebrow, title] = titles[panel];

  return (
    <div className="company-analysis-modal__backdrop" onClick={onClose}>
      <section
        className="company-analysis-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="company-analysis-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="company-analysis-modal__header">
          <div>
            <span>{eyebrow} · {companyName}</span>
            <h2 id="company-analysis-modal-title">{title}</h2>
          </div>
          <button type="button" onClick={onClose} aria-label="분석 창 닫기">×</button>
        </header>

        <div className="company-analysis-modal__body">
          {panel === 'technical' && (
            <>
              <StageActions
                primaryLabel={dashboardData.technical_context ? '기술 데이터 새로고침' : '기술 데이터 불러오기'}
                primaryLoading={stageLoading.technicalData}
                onPrimary={() => runStage('technicalData', '/api/company/technical-data', Boolean(dashboardData.technical_context))}
                secondaryLabel="AI Analyze"
                secondaryLoading={stageLoading.technicalAi}
                secondaryDisabled={!dashboardData.technical_context}
                onSecondary={() => runStage('technicalAi', '/api/company/technical-analysis')}
                error={stageErrors.technicalData || stageErrors.technicalAi}
              />
              {finalChartUrl ? (
                <div className="company-analysis-modal__chart">
                  <img src={finalChartUrl} alt={`${companyName} 주가 차트`} />
                </div>
              ) : (
                <AnalysisEmpty text="기술 데이터 불러오기를 누르면 차트와 지표가 표시됩니다." />
              )}
              {dashboardData.technical_context && (
                <TechnicalIndicatorGrid context={dashboardData.technical_context} />
              )}
              {sortedHighlights.length > 0 && (
                <div className="company-highlight-grid">
                  {sortedHighlights.map((item, index) => (
                    <HighlightCard key={`${item.title || 'highlight'}-${index}`} item={item} />
                  ))}
                </div>
              )}
              {dashboardData.technical_context && (
                <div className="company-technical-card">
                  <div className="company-sub-tabs">
                    {subTabs.map((sub) => {
                      const hasContent = parsedSections[sub.id]?.length > 0;
                      if (!hasContent && sub.id !== 'Overall') return null;
                      return (
                        <button
                          key={sub.id}
                          type="button"
                          className={`company-sub-tab ${activeSubTab === sub.id ? 'active' : ''}`}
                          onClick={() => setActiveSubTab(sub.id)}
                        >
                          {sub.label}
                        </button>
                      );
                    })}
                  </div>
                  <div className="company-technical-content">
                    {parsedSections[activeSubTab]?.length > 0 ? (
                      parsedSections[activeSubTab].map((line, index) => (
                        <p key={`${activeSubTab}-${index}`}>{line}</p>
                      ))
                    ) : (
                      <div className="company-empty-text">AI Analyze를 누르면 지표 기반 의견이 표시됩니다.</div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}

          {panel === 'financial' && (
            <>
              <StageActions
                primaryLabel={dashboardData.financial_context ? '재무 데이터 새로고침' : 'DART 재무 데이터 불러오기'}
                primaryLoading={stageLoading.financialData}
                onPrimary={() => runStage('financialData', '/api/company/financial-data', Boolean(dashboardData.financial_context))}
                secondaryLabel="AI Analyze"
                secondaryLoading={stageLoading.financialAi}
                secondaryDisabled={!dashboardData.financial_context}
                onSecondary={() => runStage('financialAi', '/api/company/financial-analysis')}
                error={stageErrors.financialData || stageErrors.financialAi}
              />
              {dashboardData.financial_context ? (
                <>
                  <div className="company-financial-grid">
                    <FinancialMetric label="PER" value={formatRatio(fin.per, 'x')} />
                    <FinancialMetric label="PBR" value={formatRatio(fin.pbr, 'x')} />
                    <FinancialMetric label="ROE" value={formatRatio(fin.roe, '%')} />
                    <FinancialMetric label="EPS" value={formatNumber(fin.eps)} />
                    <FinancialMetric label="BPS" value={formatNumber(fin.bps)} />
                    <FinancialMetric label="Dividend Yield" value={formatRatio(fin.cash_dividend_yield ?? fin.dividend_yield, '%')} />
                  </div>
                  {financialAnalysis ? (
                    <MarkdownText text={financialAnalysis} tone="financial" />
                  ) : (
                    <AnalysisEmpty text="AI Analyze를 누르면 재무지표 기반 의견이 표시됩니다." />
                  )}
                </>
              ) : (
                <AnalysisEmpty text="DART 재무 데이터 불러오기를 눌러 분석을 시작하세요." />
              )}
            </>
          )}

          {panel === 'risk' && (
            <>
              <StageActions
                primaryLabel={deepRiskAnalysis ? '리스크 다시 분석' : '리스크 분석 시작'}
                primaryLoading={stageLoading.risk}
                onPrimary={() => runStage('risk', '/api/company/risk-analysis', Boolean(deepRiskAnalysis))}
                error={stageErrors.risk}
              />
              {riskList.length > 0 ? (
                <div className="company-risk-list">
                  {riskList.map((item, index) => (
                    <div key={`${formatRiskItem(item)}-${index}`} className="company-risk-item">
                      <div className="company-risk-dot" />
                      <span>{formatRiskItem(item)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <AnalysisEmpty text="리스크 분석 시작을 누르면 주요 위험 요인이 표시됩니다." />
              )}
              {deepRiskAnalysis && <MarkdownText text={deepRiskAnalysis} tone="risk" />}
            </>
          )}
        </div>
      </section>
    </div>
  );
}

function AnalysisEmpty({ text }) {
  return <div className="company-analysis-empty">{text}</div>;
}

function TechnicalIndicatorGrid({ context }) {
  const indicators = context.latest_indicators || {};
  const signals = context.signal_context || {};
  const metrics = buildTechnicalMetrics(indicators, signals);

  return (
    <section className="company-indicators" aria-label="최신 기술적 지표">
      <div className="company-indicators__head">
        <div>
          <span>Latest Indicators</span>
          <h3>기술적 지표</h3>
        </div>
        {context.latest_date && <time>{context.latest_date}</time>}
      </div>
      <div className="company-indicators__grid">
        {metrics.map((metric) => (
          <div className="company-indicator" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <small className={metric.tone}>{metric.status}</small>
          </div>
        ))}
      </div>
    </section>
  );
}

function buildTechnicalMetrics(indicators, signals) {
  const rsi = indicators.rsi_14;
  const adx = indicators.adx_14;
  const stochK = indicators.stoch_k;
  const return5 = indicators.return_5;
  const macdPositive = indicators.macd >= indicators.macd_signal;

  return [
    metric('Close', formatIndicatorNumber(indicators.close), 'Latest', 'neutral'),
    metric(
      'SMA 20',
      formatIndicatorNumber(indicators.sma_20),
      signalLabel(signals.price_vs_sma20, 'Above', 'Below'),
      comparisonTone(signals.price_vs_sma20)
    ),
    metric(
      'SMA 50',
      formatIndicatorNumber(indicators.sma_50),
      signalLabel(signals.price_vs_sma50, 'Above', 'Below'),
      comparisonTone(signals.price_vs_sma50)
    ),
    metric(
      'RSI 14',
      formatIndicatorNumber(rsi, 2),
      rsi >= 70 ? 'Overbought' : rsi <= 30 ? 'Oversold' : 'Neutral',
      rsi >= 70 || rsi <= 30 ? 'watch' : 'neutral'
    ),
    metric(
      'MACD',
      formatIndicatorNumber(indicators.macd, 2),
      macdPositive ? 'Above signal' : 'Below signal',
      macdPositive ? 'positive' : 'negative'
    ),
    metric('Signal', formatIndicatorNumber(indicators.macd_signal, 2), 'MACD 12·26·9', 'neutral'),
    metric(
      'ADX 14',
      formatIndicatorNumber(adx, 2),
      adx >= 25 ? 'Strong trend' : 'Range',
      adx >= 25 ? 'positive' : 'neutral'
    ),
    metric('ATR 14', formatIndicatorNumber(indicators.atr_14, 2), 'Volatility', 'neutral'),
    metric(
      'Stochastic',
      `${formatIndicatorNumber(stochK, 2)} / ${formatIndicatorNumber(indicators.stoch_d, 2)}`,
      stochK >= 80 ? 'Overbought' : stochK <= 20 ? 'Oversold' : 'Neutral',
      stochK >= 80 || stochK <= 20 ? 'watch' : 'neutral'
    ),
    metric(
      '5D Return',
      formatPercent(return5),
      signals.bollinger_position || 'Bollinger neutral',
      return5 > 0 ? 'positive' : return5 < 0 ? 'negative' : 'neutral'
    ),
  ];
}

function metric(label, value, status, tone) {
  return { label, value, status, tone };
}

function formatIndicatorNumber(value, digits = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '-';
  return number.toLocaleString('ko-KR', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '-';
  return `${number > 0 ? '+' : ''}${number.toFixed(2)}%`;
}

function comparisonTone(value) {
  if (value === 'above') return 'positive';
  if (value === 'below') return 'negative';
  return 'neutral';
}

function signalLabel(value, positiveLabel, negativeLabel) {
  if (value === 'above') return positiveLabel;
  if (value === 'below') return negativeLabel;
  return 'Neutral';
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
