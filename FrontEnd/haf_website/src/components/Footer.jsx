function Footer({ bgTitle = 'HAFS', noticeText = '인공지능 기반 금융연구 센터' }) {
  return (
    <footer className="caifr-footer">
      <div className="caifr-footer__inner">
        <div className="caifr-footer__top">
          <div>
            <div className="caifr-footer__logo">{bgTitle}</div>
            <div className="caifr-footer__logo-accent" />
          </div>

          <div className="caifr-footer__notice">{noticeText}</div>
        </div>

        <div className="caifr-footer__divider" />

        <div className="caifr-footer__info-grid">
          <div className="caifr-footer__info-block">
            <span className="caifr-footer__label">ADDRESS</span>
            <p className="caifr-footer__value">
              17035 경기도 용인시 처인구 모현읍 외대로 81
            </p>
            <p className="caifr-footer__value">한국외국어대학교 국제금융학과</p>
          </div>

          <div className="caifr-footer__info-block">
            <span className="caifr-footer__label">CONTACT</span>
            <p className="caifr-footer__value">TEL : N/A</p>
            <p className="caifr-footer__value">EMAIL : hufscaifr@gmail.com</p>
          </div>

          <div className="caifr-footer__info-block">
            <span className="caifr-footer__label">RESEARCH FIELD</span>
            <p className="caifr-footer__value">
              Artificial Intelligence in Finance
            </p>
            <p className="caifr-footer__value">
              Quantitative Analysis & Economics
            </p>
          </div>
        </div>

        <div className="caifr-footer__divider" />

        <div className="caifr-footer__bottom">
          <p className="caifr-footer__copyright">
            © {new Date().getFullYear()} CAIFR. All Rights Reserved.
          </p>

          <p className="caifr-footer__brand">
            Center for AI-Based Finance Research
          </p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
