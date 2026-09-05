import { useEffect, useState } from 'react';

function RecommendedList() {
  const [researchData, setResearchData] = useState(null);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const savedData = sessionStorage.getItem('researchData');

    if (savedData) {
      try {
        setResearchData(JSON.parse(savedData));
      } catch (error) {
        console.error('결과 데이터 파싱 실패:', error);
      }
    }

    const timer = window.setTimeout(() => {
      setMounted(true);
    }, 100);

    return () => window.clearTimeout(timer);
  }, []);

  if (
    !researchData ||
    !Array.isArray(researchData.companies) ||
    researchData.companies.length === 0
  ) {
    return (
      <section className="recommended-result-page">
        <div className="recommended-empty">
          <div className="recommended-empty__icon">⌕</div>
          <div className="recommended-empty__title">분석 데이터가 없습니다</div>
          <div className="recommended-empty__description">
            먼저 뉴스 기사 URL을 입력해 AI 분석을 진행해 주세요.
          </div>
        </div>
      </section>
    );
  }

  const handleCompanyClick = (index) => {
    const detailCompanyData = researchData.companies[index];

    if (detailCompanyData) {
      sessionStorage.setItem(
        'selectedCompany',
        JSON.stringify(detailCompanyData)
      );

      window.location.href =
        '/equity_research/news_research/new_research_result_detail';
    } else {
      alert('해당 기업의 상세 분석 데이터를 찾을 수 없습니다.');
    }
  };

  return (
    <section className="recommended-result-page">
      <div
        className={`recommended-list ${mounted ? 'is-visible' : ''}`}
        aria-live="polite"
      >
        <div className="recommended-list__header">
          <div>
            <div className="recommended-list__eyebrow">
              <span className="recommended-list__eyebrow-dot" />
              AI COMPANY SCREENING
            </div>

            <h1 className="recommended-list__title">
              Recommended Companies
            </h1>

            <p className="recommended-list__description">
              뉴스 이벤트와 시장 영향을 기반으로 AI가 관련성이 높은 기업을
              선별했습니다.
            </p>
          </div>

          <div className="recommended-list__badge">
            {researchData.companies.length} Companies
          </div>
        </div>

        <div className="recommended-summary">
          <div className="recommended-summary__icon">AI</div>

          <div className="recommended-summary__content">
            <div className="recommended-summary__label">
              AI RESEARCH SUMMARY
            </div>

            <p className="recommended-summary__text">
              {researchData.summary || '선정된 기업의 종합 분석 리스트입니다.'}
            </p>
          </div>
        </div>

        <div className="recommended-list__items">
          {researchData.companies.map((company, index) => {
            const isHovered = hoveredIndex === index;
            const score =
              company.score_percent != null
                ? Math.round(company.score_percent)
                : company.score != null
                  ? Math.round(company.score * 100)
                  : 0;
            const ticker = company.korean_ticker || company.ticker?.split('.')[0];

            return (
              <div
                key={`${company.ticker || company.name || 'company'}-${index}`}
                className={`recommended-card ${isHovered ? 'is-hovered' : ''}`}
                onClick={() => handleCompanyClick(index)}
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    handleCompanyClick(index);
                  }
                }}
              >
                <div className="recommended-card__rank">
                  <span className="recommended-card__rank-label">AI PICK</span>
                  <span className="recommended-card__rank-number">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                </div>

                <div className="recommended-card__company">
                  <div className="recommended-card__label">COMPANY</div>
                  <div className="recommended-card__name">
                    {company.name || 'Unknown Company'}
                  </div>
                  {ticker && (
                    <div className="recommended-card__ticker">{ticker}</div>
                  )}
                </div>

                <div className="recommended-card__score">
                  <div className="recommended-card__label">
                    AI RECOMMENDATION
                  </div>

                  <div className="recommended-card__score-row">
                    <span className="recommended-card__score-value">
                      {score}%
                    </span>

                    <span className="recommended-card__score-badge">
                      {score >= 80
                        ? 'High'
                        : score >= 60
                          ? 'Positive'
                          : 'Review'}
                    </span>
                  </div>

                  <div className="recommended-card__score-track">
                    <div
                      className="recommended-card__score-fill"
                      style={{
                        width: `${Math.min(100, Math.max(0, score))}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="recommended-card__arrow">→</div>
              </div>
            );
          })}
        </div>

        <div className="recommended-list__footnote">
          <span>AI-generated insight</span>
          추천 점수는 뉴스 이벤트와 관련 데이터 분석을 기반으로 한 상대적
          신호이며, 투자 수익을 보장하지 않습니다.
        </div>
      </div>
    </section>
  );
}

export default RecommendedList;
