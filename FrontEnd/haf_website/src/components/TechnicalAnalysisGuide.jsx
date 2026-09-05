import { useEffect, useState } from 'react';

const tabs = [
  {
    id: 1,
    number: '01',
    label: '기술적 분석의 정의',
  },
  {
    id: 2,
    number: '02',
    label: '기술적 분석 방법',
  },
  {
    id: 3,
    number: '03',
    label: '매력과 차이점',
  },
  {
    id: 4,
    number: '04',
    label: 'AI 기술적 분석',
  },
];

function TechnicalAnalysisGuide() {
  const [activeTab, setActiveTab] = useState(1);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setMounted(true);
    }, 100);

    return () => window.clearTimeout(timer);
  }, []);

  return (
    <section className={`ta-page ${mounted ? 'is-visible' : ''}`}>
      <div className="ta-inner">
        <section className="ta-hero">
          <div className="ta-eyebrow">
            <span className="ta-eyebrow-dot" />
            HAF · Technical Analysis
          </div>

          <h1 className="ta-title">
            Understanding
            <br />
            <span className="ta-title-accent">Technical Analysis.</span>
          </h1>

          <p className="ta-intro">
            가격과 거래량에 나타난 시장의 정보를 통해 추세와 모멘텀을 읽고,
            AI를 활용해 여러 기술지표를 종합적으로 해석하는 방법을
            살펴봅니다.
          </p>
        </section>

        <div className="ta-tabs-wrap">
          <div className="ta-tabs-scroll">
            <div className="ta-tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  className={`ta-tab ${activeTab === tab.id ? 'active' : ''}`}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                >
                  <span className="ta-tab-number">{tab.number}</span>
                  <span className="ta-tab-label">{tab.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {activeTab === 1 && <DefinitionPanel />}
        {activeTab === 2 && <MethodsPanel />}
        {activeTab === 3 && <ComparisonPanel />}
        {activeTab === 4 && <AiPanel />}

        <div className="ta-footnote">
          <strong>Technical analysis is a decision-support tool.</strong>{' '}
          기술적 분석은 미래 가격을 확정적으로 예측하는 방법이 아니라 시장
          상태를 구조적으로 해석하고 투자 판단의 확률과 리스크를 관리하기 위한
          분석 도구입니다.
        </div>
      </div>
    </section>
  );
}

function DefinitionPanel() {
  return (
    <section className="ta-panel">
      <div className="ta-panel-head">
        <div className="ta-panel-kicker">01 · DEFINITION</div>
        <h2 className="ta-panel-title">기술적 분석이란 무엇인가?</h2>
        <p className="ta-panel-desc">
          기술적 분석은 과거와 현재의 가격, 거래량, 변동성 등 시장 데이터를
          이용해 시장의 상태와 향후 움직임의 가능성을 판단하는 분석 방법입니다.
          기업의 내재가치를 직접 계산하기보다 투자자들의 심리와 수급이 가격에
          어떻게 반영되고 있는지를 관찰합니다.
        </p>
      </div>

      <div className="ta-grid-3">
        <InfoCard
          icon="↗"
          title="Trend"
          text="가격이 상승, 하락 또는 횡보 중인지 파악합니다. 이동평균선과 추세선이 대표적인 분석 수단입니다."
        />
        <InfoCard
          icon="◫"
          title="Momentum"
          text="가격 움직임의 속도와 강도를 분석합니다. RSI, Stochastic RSI, MACD 등이 대표적으로 사용됩니다."
        />
        <InfoCard
          icon="◎"
          title="Volatility"
          text="시장 가격의 변동 폭과 위험 수준을 평가합니다. Bollinger Band와 ATR 등을 활용할 수 있습니다."
        />
      </div>
    </section>
  );
}

function MethodsPanel() {
  return (
    <section className="ta-panel">
      <div className="ta-panel-head">
        <div className="ta-panel-kicker">02 · METHODS</div>
        <h2 className="ta-panel-title">기술적 분석은 어떻게 하는가?</h2>
        <p className="ta-panel-desc">
          일반적으로 하나의 지표만으로 시장을 판단하지 않습니다. 추세, 모멘텀,
          변동성, 거래량 등 서로 다른 정보를 제공하는 지표를 함께 살펴보며 현재
          시장의 상태를 종합적으로 평가합니다.
        </p>
      </div>

      <div className="ta-grid-2">
        <MethodCard
          title="추세 분석"
          text="이동평균선의 방향과 배열, 고점·저점의 변화를 통해 시장의 큰 흐름을 파악합니다."
          tags={['MA5', 'MA20', 'MA60', 'MA120']}
        />
        <MethodCard
          title="모멘텀 분석"
          text="가격 변화의 속도와 강도를 측정해 과매수·과매도와 추세 약화 가능성을 살펴봅니다."
          tags={['RSI', 'Stochastic RSI', 'MACD']}
        />
        <MethodCard
          title="변동성 분석"
          text="변동 범위가 확대 또는 축소되는지를 관찰해 돌파 및 위험 확대 가능성을 분석합니다."
          tags={['Bollinger Band', 'ATR']}
        />
        <MethodCard
          title="거래량 분석"
          text="가격 변화와 실제 거래의 강도를 함께 확인해 추세의 신뢰성을 평가합니다."
          tags={['Volume', 'OBV', 'Volume Change']}
        />
      </div>
    </section>
  );
}

function ComparisonPanel() {
  const fundamentalItems = [
    '기업의 매출, 이익, 현금흐름 등 펀더멘털을 분석합니다.',
    '적정 기업가치와 내재가치 추정에 초점을 둡니다.',
    '기업 및 산업에 대한 깊은 이해가 중요합니다.',
    '중장기적인 투자 판단에 특히 유용합니다.',
  ];

  const technicalItems = [
    '실제 가격, 거래량과 변동성의 움직임을 분석합니다.',
    '시장 심리와 수급 변화를 빠르게 관찰할 수 있습니다.',
    '매수·매도 시점과 리스크 관리에 활용하기 용이합니다.',
    '주식뿐 아니라 다양한 자산에 동일한 틀을 적용할 수 있습니다.',
  ];

  return (
    <section className="ta-panel">
      <div className="ta-panel-head">
        <div className="ta-panel-kicker">03 · WHY TECHNICAL ANALYSIS</div>
        <h2 className="ta-panel-title">무엇이 다른가?</h2>
        <p className="ta-panel-desc">
          기본적 분석과 기술적 분석은 경쟁 관계라기보다 서로 다른 질문에 답하는
          분석 방법에 가깝습니다. 기본적 분석이 “무엇을 살 것인가”에 강하다면
          기술적 분석은 “시장에서는 지금 어떤 움직임이 나타나고 있는가”를
          파악하는 데 강점이 있습니다.
        </p>
      </div>

      <div className="ta-compare">
        <CompareColumn
          label="FUNDAMENTAL ANALYSIS"
          title="전통적 분석"
          items={fundamentalItems}
        />
        <CompareColumn
          label="TECHNICAL ANALYSIS"
          title="기술적 분석"
          items={technicalItems}
        />
      </div>
    </section>
  );
}

function AiPanel() {
  return (
    <section className="ta-panel">
      <div className="ta-panel-head">
        <div className="ta-panel-kicker">04 · AI METHODOLOGY</div>
        <h2 className="ta-panel-title">AI는 기술적 분석을 어떻게 확장하는가?</h2>
        <p className="ta-panel-desc">
          AI 기술적 분석의 핵심은 특정 지표 하나의 매수·매도 신호를 따르는 것이
          아니라, 가격과 거래량 및 여러 기술지표를 동시에 해석하는 데 있습니다.
          이를 통해 사람이 놓치기 쉬운 다변량 패턴과 시장 상황을 보다 체계적으로
          평가할 수 있습니다.
        </p>
      </div>

      <div className="ta-ai-flow">
        <AiStep
          number="01"
          title="Market Data"
          text="OHLC, 거래량, 가격 시계열을 수집합니다."
        />
        <div className="ta-arrow">→</div>
        <AiStep
          number="02"
          title="Indicators"
          text="RSI, MACD, 이동평균, Bollinger Band 등의 특징을 생성합니다."
        />
        <div className="ta-arrow">→</div>
        <AiStep
          number="03"
          title="AI Interpretation"
          text="여러 기술지표와 시장 조건을 종합해 추세와 위험을 해석합니다."
        />
      </div>

      <div className="ta-ai-note-grid">
        <AiNote
          title="Feature Engineering"
          text="가격과 기술지표를 AI가 분석하기 쉬운 특징 변수로 변환합니다."
        />
        <AiNote
          title="Pattern Recognition"
          text="여러 시계열과 지표 조합에 나타나는 패턴을 동시에 탐색합니다."
        />
        <AiNote
          title="Decision Support"
          text="미래를 단정하기보다 추세, 과열, 위험 요소와 조건별 시나리오를 제시합니다."
        />
      </div>
    </section>
  );
}

function InfoCard({ icon, title, text }) {
  return (
    <div className="ta-card">
      <div className="ta-icon">{icon}</div>
      <h3 className="ta-card-title">{title}</h3>
      <p className="ta-card-text">{text}</p>
    </div>
  );
}

function MethodCard({ title, text, tags }) {
  return (
    <div className="ta-card ta-method">
      <h3 className="ta-card-title">{title}</h3>
      <p className="ta-card-text">{text}</p>
      <div className="ta-tags">
        {tags.map((tag) => (
          <span key={tag} className="ta-tag">
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}

function CompareColumn({ label, title, items }) {
  return (
    <div className="ta-compare-col">
      <div className="ta-compare-label">{label}</div>
      <h3 className="ta-compare-title">{title}</h3>
      {items.map((item) => (
        <div key={item} className="ta-list-item">
          <span className="ta-dot" />
          {item}
        </div>
      ))}
    </div>
  );
}

function AiStep({ number, title, text }) {
  return (
    <div className="ta-ai-step">
      <div className="ta-ai-num">{number}</div>
      <div className="ta-ai-title">{title}</div>
      <div className="ta-ai-text">{text}</div>
    </div>
  );
}

function AiNote({ title, text }) {
  return (
    <div className="ta-ai-note">
      <div className="ta-ai-note-title">{title}</div>
      <div className="ta-ai-note-text">{text}</div>
    </div>
  );
}

export default TechnicalAnalysisGuide;
