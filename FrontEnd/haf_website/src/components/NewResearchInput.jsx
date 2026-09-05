import { useEffect, useState } from 'react';
import { API_HEADERS, apiUrl } from '../config/api';

function NewResearchInput() {
  const [newsUrl, setNewsUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setMounted(true);
    }, 100);

    return () => window.clearTimeout(timer);
  }, []);

  const handleSearch = async () => {
    if (!newsUrl.trim()) {
      alert('뉴스 URL을 입력해주세요.');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        apiUrl('/api/company-dashboard'),
        {
          method: 'POST',
          headers: {
            ...API_HEADERS,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ url: newsUrl }),
        }
      );

      if (!response.ok) {
        throw new Error('서버 응답 에러');
      }

      const result = await response.json();

      sessionStorage.setItem('researchData', JSON.stringify(result));

      window.location.href =
        '/equity_research/news_research/new_research_result';
    } catch (error) {
      console.error('API 호출 실패:', error);

      alert(
        '데이터를 가져오는 중 오류가 발생했습니다. 백엔드 서버 상태를 확인해 주세요.'
      );

      setLoading(false);
    }
  };

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
