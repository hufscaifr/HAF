import { useEffect, useState } from 'react';

function HafIntroTitle() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setMounted(true);
    }, 100);

    return () => window.clearTimeout(timer);
  }, []);

  return (
    <section className={`haf-intro-title ${mounted ? 'visible' : ''}`}>
      <div className="haf-intro-inner">
        <div className="haf-intro-eyebrow">
          <span className="haf-intro-line" />
          HUFS · HAF
        </div>

        <h1 className="haf-intro-main">
          한국외국어대학교 국제금융학과
          <span className="haf-intro-sub">AI 기반 금융학회</span>
        </h1>

        <div className="haf-intro-meta">
          Finance · Quantitative Research · Artificial Intelligence
        </div>

        <div className="haf-intro-bottom-line" />
      </div>
    </section>
  );
}

export default HafIntroTitle;
