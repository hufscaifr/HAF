import { useEffect, useState } from 'react';
import { API_HEADERS, apiUrl } from '../config/api';
import { buildResearchResultPath } from '../utils/researchRoutes';

const RESEARCH_STATE_KEY = 'haf:newsResearchState';

function NewResearchInput() {
  const [newsUrl, setNewsUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [errorInfo, setErrorInfo] = useState(null);
  const [cachedResearch, setCachedResearch] = useState(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setMounted(true);
    }, 100);

    const savedState = readResearchState();
    if (savedState?.url) setNewsUrl(savedState.url);
    if (savedState?.status === 'completed' && savedState.researchId) {
      setCachedResearch(savedState);
    }
    if (savedState?.status === 'pending' && savedState.url) {
      performResearch(savedState.url, true);
    }

    return () => window.clearTimeout(timer);
  }, []);

  async function performResearch(targetUrl, isResume = false) {
    const normalizedUrl = targetUrl.trim();
    if (!normalizedUrl) {
      setErrorInfo({
        title: '뉴스 주소가 필요합니다',
        description: '분석할 뉴스 기사 URL을 입력해 주세요.',
      });
      return;
    }

    setErrorInfo(null);
    setLoading(true);
    if (!isResume) {
      clearCompanyDashboardCache();
      sessionStorage.removeItem('researchData');
      setCachedResearch(null);
    }
    writeResearchState({
      status: 'pending',
      url: normalizedUrl,
      startedAt: Date.now(),
    });

    try {
      const response = await fetch(
        apiUrl('/api/new-research'),
        {
          method: 'POST',
          headers: {
            ...API_HEADERS,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ url: normalizedUrl }),
        }
      );

      if (!response.ok) {
        throw await buildResearchError(response);
      }

      const result = await response.json();
      const resultPath = buildResearchResultPath(result.research_id);

      sessionStorage.setItem('researchData', JSON.stringify(result));
      writeResearchState({
        status: 'completed',
        url: normalizedUrl,
        researchId: result.research_id,
        resultPath,
        completedAt: Date.now(),
      });

      window.location.href = resultPath;
    } catch (error) {
      console.error('API 호출 실패:', error);
      const localizedError = normalizeResearchError(error);
      setErrorInfo(localizedError);
      writeResearchState({
        status: 'failed',
        url: normalizedUrl,
        failedAt: Date.now(),
        error: localizedError,
      });
      setLoading(false);
    }
  }

  const handleSearch = () => performResearch(newsUrl);

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !loading) {
      handleSearch();
    }
  };

  return (
    <section className={`research-page ${mounted ? 'is-visible' : ''}`}>
      <div className="research-inner">
        <div className="research-hero">
          <div className="research-eyebrow">
            <span className="research-eyebrow-dot" />
            HAF · AI Research Engine
          </div>

          <h1 className="research-title">
            From News to
            <br />
            <span className="research-title-accent">Investment Insight.</span>
          </h1>

          <p className="research-description">
            뉴스를 입력하면 관련된 기업을 AI가 탐색합니다. 또한, 해당 기업에
            대한 기술적 분석과 재무분석을 수행하여 투자 의견을 도출합니다.
          </p>

          <div className="research-chips">
            <span className="research-chip">
              <span className="research-chip-dot" />
              News Analysis
            </span>
            <span className="research-chip">
              <span className="research-chip-dot" />
              Company Screening
            </span>
            <span className="research-chip">
              <span className="research-chip-dot" />
              Market Impact
            </span>
            <span className="research-chip">
              <span className="research-chip-dot" />
              AI Research
            </span>
          </div>
        </div>

        <div className="research-input-card">
          <div className="research-card-label">
            <div className="research-card-icon">↗</div>
            분석할 뉴스 기사 URL
          </div>

          <div className="research-input-form">
            <input
              className="research-url-input"
              type="url"
              inputMode="url"
              autoComplete="url"
              placeholder="https://example.com/news/article"
              aria-label="분석할 뉴스 기사 URL"
              value={newsUrl}
              onChange={(event) => setNewsUrl(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />

            <button
              className="research-submit-button"
              type="button"
              onClick={handleSearch}
              disabled={loading}
            >
              {loading ? '뉴스 분석 중...' : 'AI 분석 시작하기'}

              {!loading && (
                <span className="research-submit-arrow" aria-hidden="true">
                  →
                </span>
              )}
            </button>
          </div>

          <div className="research-input-footnote">
            <span className="research-lock">◈</span>
            입력한 URL은 분석 목적으로만 사용됩니다.
          </div>

          {errorInfo && (
            <div className="research-status-card is-error" role="alert">
              <div className="research-status-icon" aria-hidden="true">!</div>
              <div>
                <strong>{errorInfo.title}</strong>
                <p>{errorInfo.description}</p>
              </div>
            </div>
          )}

          {!loading && cachedResearch?.resultPath && (
            <div className="research-status-card is-complete">
              <div className="research-status-icon" aria-hidden="true">✓</div>
              <div>
                <strong>이전에 완료한 뉴스 분석이 있습니다</strong>
                <p>새 분석을 시작하기 전까지 기존 결과를 다시 확인할 수 있습니다.</p>
                <a href={cachedResearch.resultPath}>분석 결과 다시 보기 →</a>
              </div>
            </div>
          )}
        </div>

        <div className="research-process">
          <div className="research-process-title">AI Research Pipeline</div>

          <div className="research-process-row">
            <ResearchStep
              number="01"
              title="Article Parsing"
              desc="뉴스의 핵심 이벤트와 주요 정보를 추출합니다."
              icon="article"
            />
            <ResearchStep
              number="02"
              title="AI Interpretation"
              desc="AI가 이벤트의 금융시장 영향을 분석합니다."
              icon="spark"
            />
            <ResearchStep
              number="03"
              title="Company Insight"
              desc="영향받는 기업과 투자 인사이트를 제시합니다."
              icon="chart"
            />
          </div>
        </div>
      </div>

      {loading && (
        <div
          className="research-loading-overlay"
          role="status"
          aria-live="polite"
          aria-label="AI 뉴스 분석 중"
        >
          <div className="research-loading-card">
            <div className="research-spinner" aria-hidden="true" />

            <div className="research-loading-eyebrow">
              HAF AI Research Engine
            </div>

            <h3 className="research-loading-title">
              AI가 뉴스를 정밀 분석하고 있습니다
            </h3>

            <p className="research-loading-description">
              뉴스의 핵심 이벤트를 추출하고 있습니다.
              <br />
              관련 기업과 시장 영향을 분석해 대시보드를 생성합니다.
            </p>
          </div>
        </div>
      )}
    </section>
  );
}

async function buildResearchError(response) {
  const errorBody = await response.json().catch(() => ({}));
  const serverDetail = typeof errorBody.detail === 'string' ? errorBody.detail : '';
  const messages = {
    400: ['뉴스 주소를 확인해 주세요', '입력한 주소를 뉴스 기사로 처리할 수 없습니다.'],
    401: ['로그인이 필요한 뉴스입니다', '해당 뉴스는 로그인 후에만 볼 수 있어 자동 분석할 수 없습니다.'],
    403: ['언론사가 자동 접근을 차단했습니다', '개인정보 문제가 아니라 언론사의 접근 정책 또는 구독 제한 때문에 본문을 가져올 수 없습니다. 다른 공개 기사를 이용해 주세요.'],
    404: ['뉴스 페이지를 찾을 수 없습니다', '주소가 잘못되었거나 기사가 삭제·이동되었는지 확인해 주세요.'],
    408: ['뉴스 사이트 응답이 늦습니다', '뉴스 사이트가 제한 시간 안에 응답하지 않았습니다. 잠시 후 다시 시도해 주세요.'],
    410: ['더 이상 제공되지 않는 뉴스입니다', '삭제되었거나 만료된 기사일 수 있습니다.'],
    413: ['입력 데이터가 너무 큽니다', '처리 가능한 크기를 초과했습니다. 더 짧은 공개 기사를 이용해 주세요.'],
    422: ['뉴스 주소 형식이 올바르지 않습니다', 'http 또는 https로 시작하는 기사 주소를 입력해 주세요.'],
    429: ['요청이 너무 많습니다', '서버 또는 뉴스 사이트의 요청 제한에 도달했습니다. 잠시 후 다시 시도해 주세요.'],
    500: ['분석 서버에서 오류가 발생했습니다', '잠시 후 다시 시도해 주세요. 문제가 계속되면 관리자에게 알려주세요.'],
    502: ['뉴스 사이트의 내용을 가져오지 못했습니다', '사이트 연결이 불안정하거나 자동 수집을 허용하지 않는 기사일 수 있습니다.'],
    503: ['현재 분석 서버가 혼잡합니다', '잠시 후 다시 시도해 주세요.'],
    504: ['분석 시간이 초과되었습니다', '뉴스 사이트 또는 분석 서버 응답이 늦어 중단되었습니다.'],
  };
  const [title, fallbackDescription] = messages[response.status] || [
    '뉴스 분석을 완료하지 못했습니다',
    `예상하지 못한 응답을 받았습니다. (${response.status})`,
  ];
  const error = new Error(serverDetail || fallbackDescription);
  error.researchError = {
    title,
    description: serverDetail || fallbackDescription,
  };
  return error;
}

function normalizeResearchError(error) {
  if (error?.researchError) return error.researchError;
  if (error instanceof TypeError) {
    return {
      title: '서버에 연결할 수 없습니다',
      description: '인터넷 연결을 확인한 뒤 다시 시도해 주세요.',
    };
  }
  return {
    title: '뉴스 분석을 완료하지 못했습니다',
    description: error?.message || '잠시 후 다시 시도해 주세요.',
  };
}

function readResearchState() {
  try {
    const saved = localStorage.getItem(RESEARCH_STATE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

function writeResearchState(state) {
  try {
    localStorage.setItem(RESEARCH_STATE_KEY, JSON.stringify(state));
  } catch {
    // 브라우저 저장소가 차단되어도 현재 분석은 계속 진행합니다.
  }
}

function clearCompanyDashboardCache() {
  Object.keys(sessionStorage).forEach((key) => {
    if (key.startsWith('companyDashboard:')) {
      sessionStorage.removeItem(key);
    }
  });
}

function ResearchStep({ number, title, desc, icon }) {
  return (
    <div className="research-step">
      <div className="research-step-icon">
        <ResearchIcon icon={icon} />
      </div>

      <div className="research-step-copy">
        <span className="research-step-number">{number}</span>
        <span className="research-step-title">{title}</span>
        <span className="research-step-desc">{desc}</span>
      </div>
    </div>
  );
}

function ResearchIcon({ icon }) {
  if (icon === 'spark') {
    return (
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
      >
        <path d="M12 3l1.3 3.7L17 8l-3.7 1.3L12 13l-1.3-3.7L7 8l3.7-1.3z" />
        <path d="M18 14l.8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8z" />
      </svg>
    );
  }

  if (icon === 'chart') {
    return (
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
      >
        <path d="M4 17l5-5 4 4 7-8" />
        <path d="M16 8h4v4" />
        <path d="M4 21h16" />
      </svg>
    );
  }

  return (
    <svg
      width="23"
      height="23"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
    >
      <rect x="4" y="3" width="16" height="18" rx="2" />
      <path d="M8 8h8M8 12h8M8 16h5" />
    </svg>
  );
}

export default NewResearchInput;
