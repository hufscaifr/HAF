import { useEffect, useState } from 'react';

function HafJoinHero({
  eyebrow = 'HAF · JOIN US',
  title = 'Read the Market.',
  highlight = 'Build the Insight.',
  description = '금융시장과 데이터를 탐구하고, AI와 계량적 분석을 통해 자신만의 투자 인사이트를 만들어갈 HAF의 새로운 연구원을 기다립니다.',
  primaryButton = 'Join HAF',
  primaryLink = '#application',
  secondaryButton = 'About HAF',
  secondaryLink = '/about-us',
}) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setVisible(true);
    }, 120);

    return () => window.clearTimeout(timer);
  }, []);

  return (
    <section className={`haf-join-hero ${visible ? 'visible' : ''}`}>
      <div className="haf-join-inner">
        <div className="haf-join-copy">
          <div className="haf-join-eyebrow">
            <span className="haf-join-eyebrow-dot" />
            {eyebrow}
          </div>

          <h1 className="haf-join-title">
            {title}
            <br />
            <span className="haf-join-highlight">{highlight}</span>
          </h1>

          <p className="haf-join-description">{description}</p>

          <div className="haf-join-actions">
            <a className="haf-join-primary" href={primaryLink}>
              {primaryButton}
            </a>
            <a className="haf-join-secondary" href={secondaryLink}>
              {secondaryButton}
            </a>
          </div>
        </div>

        <div className="haf-join-market-visual">
          <div className="haf-join-glow" />

          <div className="haf-join-data-card">
            <div className="haf-join-card-head">
              <div className="haf-join-market-label">
                <span className="haf-join-market-name">
                  HAF Research Signal
                </span>
                <span className="haf-join-market-sub">
                  AI · Finance · Quantitative Research
                </span>
              </div>

              <div className="haf-join-ai-pill">
                <span className="haf-join-ai-live" />
                AI ANALYSIS
              </div>
            </div>

            <div className="haf-join-chart">
              <div className="haf-join-grid-line" />
              <div className="haf-join-grid-line" />
              <div className="haf-join-grid-line" />
              <div className="haf-join-grid-line" />

              <svg
                className="haf-join-chart-svg"
                viewBox="0 0 500 220"
                preserveAspectRatio="none"
              >
                <defs>
                  <linearGradient
                    id="hafJoinGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor="#0a4d2e" stopOpacity="0.13" />
                    <stop offset="100%" stopColor="#0a4d2e" stopOpacity="0" />
                  </linearGradient>
                </defs>

                <path
                  className="haf-join-area-path"
                  d="M 0 188 C 35 178, 52 184, 76 161 S 121 173, 151 142 S 202 151, 230 115 S 279 128, 310 91 S 358 105, 388 66 S 433 81, 500 28 L 500 220 L 0 220 Z"
                />
                <path
                  className="haf-join-line-path"
                  d="M 0 188 C 35 178, 52 184, 76 161 S 121 173, 151 142 S 202 151, 230 115 S 279 128, 310 91 S 358 105, 388 66 S 433 81, 500 28"
                />
              </svg>

              <span className="haf-join-point one" />
              <span className="haf-join-point two" />
              <span className="haf-join-point three" />
            </div>

            <div className="haf-join-metrics">
              <div className="haf-join-metric">
                <div className="haf-join-metric-label">DATA</div>
                <div className="haf-join-metric-value">60D</div>
              </div>
              <div className="haf-join-metric">
                <div className="haf-join-metric-label">SIGNAL</div>
                <div className="haf-join-metric-value green">+18.4%</div>
              </div>
              <div className="haf-join-metric">
                <div className="haf-join-metric-label">CONFIDENCE</div>
                <div className="haf-join-metric-value">87%</div>
              </div>
            </div>
          </div>

          <div className="haf-join-signal-card">
            <div className="haf-join-signal-label">Research Insight</div>
            <div className="haf-join-signal-value">Opportunity</div>
            <div className="haf-join-signal-caption">
              Turn financial data into actionable research.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HafJoinHero;
