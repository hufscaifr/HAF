import { useEffect, useMemo, useState } from 'react';

const defaultBanner = {
  eyebrow: 'HAF · Finance Research Society',
  titleLine1: 'Understand.',
  titleLine2: 'Analyze.',
  titleLine3: 'Invest.',
  description:
    '기업과 산업, 그리고 시장을 데이터로 해석합니다. 금융과 AI를 연결해 더 나은 투자 인사이트를 만들어가는 한국외국어대학교 금융학회입니다.',
  primaryText: 'Explore Research',
  primaryLink: '/equity_research/news_research/new_research',
  secondaryText: 'About HAF',
  secondaryLink: '/equity_research/help',
  autoPlay: true,
  interval: 5500,
};

function HafMainBanner({
  eyebrow = defaultBanner.eyebrow,
  titleLine1 = defaultBanner.titleLine1,
  titleLine2 = defaultBanner.titleLine2,
  titleLine3 = defaultBanner.titleLine3,
  description = defaultBanner.description,
  primaryText = defaultBanner.primaryText,
  primaryLink = defaultBanner.primaryLink,
  secondaryText = defaultBanner.secondaryText,
  secondaryLink = defaultBanner.secondaryLink,
  image1 = '',
  image2 = '',
  image3 = '',
  image4 = '',
  autoPlay = defaultBanner.autoPlay,
  interval = defaultBanner.interval,
}) {
  const [mounted, setMounted] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  const images = useMemo(
    () => [image1, image2, image3, image4].filter(Boolean),
    [image1, image2, image3, image4]
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setMounted(true);
    }, 120);

    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!autoPlay || images.length <= 1) return undefined;

    const timer = window.setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % images.length);
    }, interval);

    return () => window.clearInterval(timer);
  }, [autoPlay, interval, images.length]);

  return (
    <section className={`haf-main-banner ${mounted ? 'visible' : ''}`}>
      <div className="haf-backgrounds">
        {images.map((image, index) => (
          <img
            key={image}
            src={image}
            alt=""
            className={`haf-background-image ${
              activeIndex === index ? 'active' : ''
            }`}
          />
        ))}
      </div>

      <div className="haf-photo-shade" />
      <div className="haf-bottom-shade" />
      <div className="haf-photo-softener" />
      <div className="haf-vertical-line" />

      <div className="haf-banner-inner">
        <div className="haf-banner-top">
          <div className="haf-eyebrow">
            <span className="haf-eyebrow-line" />
            {eyebrow}
          </div>

          <div className="haf-university">
            Hankuk University of Foreign Studies
          </div>
        </div>

        <div className="haf-main-copy">
          <h1 className="haf-hero-title">
            <span className="haf-title-line">{titleLine1}</span>
            <span className="haf-title-line">{titleLine2}</span>
            <span className="haf-title-line">{titleLine3}</span>
          </h1>

          <div className="haf-description-row">
            <p className="haf-description">{description}</p>

            <div className="haf-actions">
              <a href={primaryLink} className="haf-primary">
                {primaryText}
              </a>
              <a href={secondaryLink} className="haf-secondary">
                {secondaryText}
              </a>
            </div>
          </div>
        </div>

        <div className="haf-bottom">
          <div className="haf-fields">
            <span className="haf-field">
              <strong>01</strong>
              Equity Research
            </span>
            <span className="haf-field">
              <strong>02</strong>
              Quantitative Analysis
            </span>
            <span className="haf-field">
              <strong>03</strong>
              AI Finance
            </span>
          </div>

          {images.length > 1 && (
            <div className="haf-image-navigation">
              {images.map((image, index) => (
                <button
                  key={image}
                  className={`haf-image-dot ${
                    activeIndex === index ? 'active' : ''
                  }`}
                  onClick={() => setActiveIndex(index)}
                  aria-label={`배경 이미지 ${index + 1}`}
                  type="button"
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default HafMainBanner;
