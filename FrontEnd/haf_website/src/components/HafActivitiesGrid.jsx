const activities = [
  {
    id: 1,
    eyebrow: 'ACADEMIC FOUNDATION',
    title: '계량경제학 학습',
    description:
      '리서치와 주가 분석에 필요한 통계·계량적 사고를 익히고, 실제 금융 데이터를 활용해 분석의 기초를 다집니다.',
    buttonText: '함께하기',
    href: '/join-us',
    tone: 'light',
  },
  {
    id: 2,
    eyebrow: 'RESEARCH',
    title: '리서치',
    description:
      '기업의 주가·재무 데이터와 주요 이벤트를 분석하고, 이벤트 스터디와 정량적 방법론을 활용해 투자 아이디어와 리서치 결과물을 만듭니다.',
    buttonText: 'Report',
    href: '/reports',
    tone: 'green',
  },
  {
    id: 3,
    eyebrow: 'WEEKLY SESSION',
    title: '정기 세션',
    description:
      '개인 및 팀 프로젝트의 진행 상황과 분석 방향을 정기적으로 공유하고, 학회원 간 피드백과 토론을 통해 연구의 완성도를 높입니다.',
    buttonText: '함께하기',
    href: '/join-us',
    tone: 'mint',
  },
  {
    id: 4,
    eyebrow: 'NETWORK',
    title: 'Networking',
    description:
      '금융업계에 진출한 선배 및 현업자를 초청해 직무와 커리어에 대한 인사이트를 나누고, 학기 활동을 돌아보는 세미나와 교류 프로그램을 진행합니다.',
    buttonText: '함께하기',
    href: '/join-us',
    tone: 'blue',
  },
  {
    id: 5,
    eyebrow: 'CHALLENGE',
    title: '공모전',
    description:
      '학회에서 축적한 금융 지식과 분석 경험을 실제 과제에 적용하며, 공모전과 프로젝트를 통해 문제 해결력과 실무 수행 역량을 키웁니다.',
    buttonText: '수상 내역',
    href: '/about-us',
    tone: 'gold',
  },
  {
    id: 6,
    eyebrow: 'AI × FINANCE',
    title: 'AI 기반 금융 개발',
    description:
      'AI와 금융 데이터를 결합해 기업 분석 프로그램과 리서치 자동화 에이전트를 직접 설계·개발하며, 분석 과정을 더 빠르고 구조적으로 만드는 방법을 연구합니다.',
    buttonText: 'AI 기업 분석하기',
    href: '/equity_research/single_equity_analysis',
    tone: 'dark',
  },
];

function HafActivitiesGrid() {
  return (
    <section className="haf-activities">
      <div className="haf-activities-inner">
        <div className="haf-section-head">
          <div className="haf-section-eyebrow">What We Do</div>

          <h2 className="haf-section-title">Learn. Research. Build.</h2>

          <p className="haf-section-desc">
            금융을 공부하는 데서 그치지 않고, 직접 분석하고 토론하고 개발하며
            실전 역량을 만들어갑니다.
          </p>
        </div>

        <div className="haf-activity-grid">
          {activities.map((item) => (
            <a
              key={item.id}
              className={`haf-activity-card ${item.tone}`}
              href={item.href}
              target={item.external ? '_blank' : '_self'}
              rel={item.external ? 'noopener noreferrer' : undefined}
            >
              <div className="haf-card-content">
                <div className="haf-card-eyebrow">{item.eyebrow}</div>
                <h3 className="haf-card-title">{item.title}</h3>
                <p className="haf-card-desc">{item.description}</p>
              </div>

              <div className="haf-card-bottom">
                <span className="haf-card-button">{item.buttonText} →</span>
                <span className="haf-card-number">0{item.id}</span>
              </div>
            </a>
          ))}
        </div>

        <section className="haf-manifesto">
          <div className="haf-manifesto-top">
            <div className="haf-manifesto-eyebrow">
              HAF · Finance Research Society
            </div>

            <h3 className="haf-manifesto-title">
              Research together.
              <br />
              Grow further.
            </h3>

            <p className="haf-manifesto-desc">
              금융을 배우는 데서 그치지 않고, 분석하고 토론하고 직접
              만들어보며 서로의 성장을 가속하는 학회입니다. 각자의 관심과
              강점을 리서치, 데이터, AI, 커리어로 연결해 실제 결과물로
              만들어갑니다.
            </p>
          </div>

          <div className="haf-manifesto-bottom">
            <div className="haf-manifesto-keywords">
              <span className="haf-keyword">Quantitative Finance</span>
              <span className="haf-keyword">Equity Research</span>
              <span className="haf-keyword">AI Development</span>
              <span className="haf-keyword">Networking</span>
            </div>

            <div className="haf-manifesto-mark">HAF · HUFS</div>
          </div>
        </section>
      </div>
    </section>
  );
}

export default HafActivitiesGrid;
