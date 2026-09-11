import { useEffect, useState } from 'react';
import { API_HEADERS, apiUrl } from '../config/api';

const ANALYSIS_STEPS = [
  { key: 'article', label: '뉴스 읽는 중', startsAt: 8 },
  { key: 'market', label: '주가 데이터 가져오는 중', startsAt: 28 },
  { key: 'analysis', label: '분석 중', startsAt: 48 },
  { key: 'writing', label: '글 쓰는 중', startsAt: 72 },
];

function NewResearchInput() {
  const [newsUrl, setNewsUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState({
    progress: 0,
    step: 'queued',
    message: '분석 작업을 준비하는 중',
  });

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
    setAnalysisProgress({
      progress: 0,
      step: 'queued',
      message: '분석 작업을 준비하는 중',
    });

    try {
      const response = await fetch(
        apiUrl('/api/company-dashboard-stream'),
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
        const errorPayload = await response.json().catch(() => ({}));
        if (response.status === 429 && errorPayload.retry_after_seconds) {
          const remainingMinutes = Math.ceil(
            errorPayload.retry_after_seconds / 60
          );
          throw new Error(
            `AI 분석은 1시간에 한 번만 가능합니다. 약 ${remainingMinutes}분 후 다시 시도해 주세요.`
          );
        }
        throw new Error(errorPayload.detail || '서버 응답 에러');
      }

      if (!response.body) {
        throw new Error('브라우저가 스트리밍 응답을 지원하지 않습니다.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let result = null;

      const handleEvent = (event) => {
        if (event.type === 'progress') {
          setAnalysisProgress({
            progress: event.progress,
            step: event.step,
            message: event.message,
          });
        } else if (event.type === 'result') {
          result = event.data;
          setAnalysisProgress({
            progress: 100,
            step: 'completed',
            message: '분석이 완료되었습니다.',
          });
        } else if (event.type === 'error') {
          throw new Error(event.detail || '분석 중 오류가 발생했습니다.');
        }
      };

      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        lines.filter(Boolean).forEach((line) => handleEvent(JSON.parse(line)));
        if (done) break;
      }

      if (buffer.trim()) {
        handleEvent(JSON.parse(buffer));
      }

      if (!result) {
        throw new Error('분석 결과를 받지 못했습니다.');
      }

      sessionStorage.setItem('researchData', JSON.stringify(result));

      await new Promise((resolve) => window.setTimeout(resolve, 350));

      window.location.href =
        '/equity_research/news_research/new_research_result';
    } catch (error) {
      console.error('API 호출 실패:', error);

      alert(error.message || '분석 중 오류가 발생했습니다.');

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
              {loading
                ? `뉴스 분석 중... ${analysisProgress.progress}%`
                : 'AI 분석 시작하기'}

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
            <div className="research-progress-value" aria-hidden="true">
              {analysisProgress.progress}%
            </div>

            <div className="research-loading-eyebrow">
              HAF AI Research Engine
            </div>

            <h3 className="research-loading-title">
              {analysisProgress.message}
            </h3>

            <div
              className="research-progress-track"
              role="progressbar"
              aria-valuemin="0"
              aria-valuemax="100"
              aria-valuenow={analysisProgress.progress}
            >
              <div
                className="research-progress-fill"
                style={{ width: `${analysisProgress.progress}%` }}
              />
            </div>

            <div className="research-progress-steps">
              {ANALYSIS_STEPS.map((step) => {
                const completed = analysisProgress.progress > step.startsAt;
                const active = analysisProgress.step === step.key;

                return (
                  <div
                    className={`research-progress-step ${
                      completed ? 'is-complete' : ''
                    } ${active ? 'is-active' : ''}`}
                    key={step.key}
                  >
                    <span className="research-progress-step-dot">
                      {completed ? '✓' : ''}
                    </span>
                    <span>{step.label}</span>
                  </div>
                );
              })}
            </div>
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
