import { useState } from 'react';

const INDICATORS_DATA = {
  RSI: {
    title: 'RSI',
    fullName: 'Relative Strength Index',
    quote: '지금 이 주식, 과열되었을까? 아니면 과도하게 떨어졌을까?',
    desc: 'RSI는 일정 기간 동안 주가가 전일 가격에 비해 상승한 변화량과 하락한 변화량의 평균값을 구하여, 현재 주가 추세의 강도를 0에서 100 사이의 백분율로 나타낸 모멘텀 진동형(Oscillator) 지표입니다. 주로 시장의 과매수(Overbought) 및 과매도(Oversold) 상태를 판단하는 데 사용됩니다.',
    cards: [
      {
        type: 'negative',
        title: 'RSI 70+',
        status: '과매수 상태',
        signal: '매도 신호',
        detail:
          '최근 상승 압력이 너무 강해 시장이 과열되었습니다. 주가가 고점에 다다랐을 확률이 높으므로 추격 매수를 자제하고 매도 타이밍을 고려하세요.',
      },
      {
        type: 'watch',
        title: 'RSI 50',
        status: '중심선',
        signal: '보유',
        detail:
          '상승 세력과 하락 세력의 균형을 뜻합니다. 50선을 상향 돌파하면 단기 상승 추세 전환, 하향 돌파하면 단기 하락 추세 전환의 신호로 해석할 수 있습니다.',
      },
      {
        type: 'positive',
        title: 'RSI 30-',
        status: '과매도 상태',
        signal: '매수 신호',
        detail:
          '최근 하락 압력이 지나쳐 과도하게 매도되었다는 뜻입니다. 기술적 반등이나 추세 전환이 일어날 가능성이 크므로 분할 매수 타이밍으로 해석합니다.',
      },
    ],
  },
  ATR14: {
    title: 'ATR14',
    fullName: 'Average True Range (14)',
    quote: '최근 이 종목이 하루에 얼마나 거칠게 움직이고 있을까?',
    desc: 'ATR은 일정 기간(주로 14일) 동안의 주가 변동폭을 평균 내어 시장의 변동성을 측정하는 지표입니다. 주로 손절선 설정에 활용됩니다.',
    cards: [
      {
        type: 'negative',
        title: '고변동성',
        status: 'ATR 급상승',
        signal: '위험 관리',
        detail:
          '시장의 변동성이 비정상적으로 커졌습니다. 예상치 못한 급등락으로 손절선이 터질 수 있으므로 투자 비중을 줄이거나 포지션을 보수적으로 잡아야 합니다.',
      },
      {
        type: 'watch',
        title: '평균 변동성',
        status: 'ATR 유지',
        signal: '관망/유지',
        detail:
          '평소와 다름없는 정상적인 주가 움직임 범위 내에 있습니다. 기존에 세워둔 추세 추종 전략을 그대로 유지하며 시장의 돌발 수급을 모니터링합니다.',
      },
      {
        type: 'positive',
        title: '저변동성',
        status: 'ATR 바닥권',
        signal: '에너지 응축',
        detail:
          '주가가 장기간 횡보하며 힘을 모으고 있는 구간입니다. 조만간 위든 아래든 강력한 방향성 돌파가 나올 가능성이 높으므로 돌파 방향으로 진입을 준비합니다.',
      },
    ],
  },
  OBV: {
    title: 'OBV',
    fullName: 'On-Balance Volume',
    quote: '세력과 주포들이 몰래 매집 중일까, 아니면 이탈 중일까?',
    desc: 'OBV는 거래량 상승/하락 누적 지표입니다. 주가가 정체되어 있어도 OBV가 오르면 스마트 머니의 매집으로 해석합니다.',
    cards: [
      {
        type: 'negative',
        title: 'OBV 하락',
        status: '분산 (매도 우위)',
        signal: '이탈 경고',
        detail:
          '주가가 버티고 있더라도 거래량이 동반된 하락세가 지속되며 자금이 빠져나가고 있습니다. 조만간 주가가 하방으로 무너질 위험이 매우 큽니다.',
      },
      {
        type: 'watch',
        title: 'OBV 횡보',
        status: '거래량 균형',
        signal: '에너지 수렴',
        detail:
          '주가 흐름과 거래량 유출입이 일정한 박스권 안에서 균형을 이루고 있습니다. 새로운 거대 수급이나 재료가 들어오기 전까지는 박스권 매매가 유리합니다.',
      },
      {
        type: 'positive',
        title: 'OBV 상승',
        status: '매집 (매수 우위)',
        signal: '돌파 기대',
        detail:
          '주가가 강하게 오르지 못했음에도 거래량이 지속적으로 유입되며 누적 누계가 우상향합니다. 세력 매집 시그널로 조만간 강한 슈팅이 나올 수 있습니다.',
      },
    ],
  },
  'Bollinger Band(20,2)': {
    title: 'Bollinger Band',
    fullName: 'Bollinger Bands (20, 2)',
    quote: '주가가 통계적으로 정상 범위 안에 있을까, 밴드를 찢고 나갈까?',
    desc: '이동평균선을 중심으로 주가가 움직일 수 있는 표준편차 범위를 상한선과 하한선으로 그려놓은 변동성 지표입니다.',
    cards: [
      {
        type: 'negative',
        title: '상한선 터치',
        status: '밴드 상단 도달',
        signal: '단기 저항',
        detail:
          '통계적 범위의 최고점에 다다랐습니다. 밴드를 타고 상승하는 강한 추세가 아니라면 단기 차익 매물이 출회되어 하락 반전할 확률이 높은 자리입니다.',
      },
      {
        type: 'watch',
        title: '중중선 안착',
        status: '20일 이평선',
        signal: '방향성 탐색',
        detail:
          '밴드의 중심선에 위치해 있습니다. 중심선 지지에 성공하면 상한선을 향해 재상승하고, 중심선이 붕괴되면 하한선까지 밀리는 분수령 공간입니다.',
      },
      {
        type: 'positive',
        title: '하한선 터치',
        status: '밴드 하단 도달',
        signal: '단기 지지',
        detail:
          '통계적 범위의 최하단에 도달하여 낙폭과대 인식이 강해지는 자리입니다. 지지 양봉이 출현할 경우 밴드 중심선을 목표로 한 기술적 반등 타점입니다.',
      },
    ],
  },
  SMA20: {
    title: 'SMA20',
    fullName: 'Simple Moving Average (20)',
    quote: '한 달 동안 이 주식을 산 사람들의 평균 단가는 얼마일까?',
    desc: "최근 20일 동안의 종가를 단순 산술 평균하여 연결한 선으로, '생명선'이라고 불리는 지표입니다.",
    cards: [
      {
        type: 'negative',
        title: '이평선 이탈',
        status: '20선 하향 돌파',
        signal: '추세 이탈',
        detail:
          '주가가 한 달 평균 매수 단가 아래로 추락했습니다. 실망 매물과 손절 물량이 쏟아지며 단기 하락 추세가 깊어질 수 있으므로 리스크 관리가 필요합니다.',
      },
      {
        type: 'watch',
        title: '이평선 수렴',
        status: '20선 밀착',
        signal: '방향 대기',
        detail:
          '주가와 20일 이평선이 강하게 밀착되며 에너지를 모으고 있습니다. 이평선 횡보가 끝나면 위나 아래로 강한 단기 방향성이 결정됩니다.',
      },
      {
        type: 'positive',
        title: '이평선 지지',
        status: '20선 상향 돌파',
        signal: '추세 회복',
        detail:
          '주가가 20일선 위로 다시 올라타거나, 눌림목에서 20일선의 지지를 받고 반등했습니다. 단기 매수세가 살아나며 우상향 기조를 이어갈 신호입니다.',
      },
    ],
  },
  EMA20: {
    title: 'EMA20',
    fullName: 'Exponential Moving Average (20)',
    quote: '단순 평균보다 최근의 주가 변화에 더 빠르게 대응하려면?',
    desc: '최근 가격에 더 높은 가중치를 두어 계산하여 주가 변동에 훨씬 민감하고 빠르게 반응합니다.',
    cards: [
      {
        type: 'negative',
        title: 'EMA 데드',
        status: '최근 수급 악화',
        signal: '빠른 매도',
        detail:
          '최근 며칠간의 급격한 매도세가 반영되면서 지수이평선이 꺾였습니다. 단순이평선보다 한발 빠르게 하락 추세 시작을 경고하는 시그널입니다.',
      },
      {
        type: 'watch',
        title: '이격 조정',
        status: 'EMA 추종',
        signal: '추세 추동',
        detail:
          '주가가 지수이평선을 크게 벗어나지 않고 적정 거리를 유지하며 순항 중입니다. 급격한 이격 과열이 없으므로 기존 추세를 그대로 따라가면 됩니다.',
      },
      {
        type: 'positive',
        title: 'EMA 골든',
        status: '최근 수급 개선',
        signal: '빠른 매수',
        detail:
          '최근 유입된 강력한 매수세가 가중치로 반영되어 선이 가파르게 돌아섰습니다. 바닥권 탈출이나 신고가 랠리의 초기 타점을 빠르게 잡아낼 수 있습니다.',
      },
    ],
  },
  'MACD(12/26/9)': {
    title: 'MACD',
    fullName: 'Moving Average Convergence Divergence',
    quote: '장단기 이평선들이 서로 만날까, 아니면 멀어질까?',
    desc: '단기 지수이평선(12)과 장기 지수이평선(26)의 차이를 이용해 추세의 강도와 방향을 측정합니다.',
    cards: [
      {
        type: 'negative',
        title: '데드 크로스',
        status: 'MACD 0선 아래',
        signal: '매도 확정',
        detail:
          'MACD 선이 시그널 선을 하향 돌파했거나 오실레이터가 음수 영역으로 확장 중입니다. 상승 동력이 완전히 꺾이고 본격적인 하락 사이클 진입을 뜻합니다.',
      },
      {
        type: 'watch',
        title: '0선 부근',
        status: '추세 전환점',
        signal: '분수령 관망',
        detail:
          '장단기 수급의 균형점으로, 여기서 지지받고 골든크로스가 나면 대시세가 나고, 저항 맞고 밀리면 대폭락이 나오는 변곡점입니다.',
      },
      {
        type: 'positive',
        title: '골든 크로스',
        status: 'MACD 0선 돌파',
        signal: '매수 전환',
        detail:
          'MACD 선이 시그널 선을 상향 돌파하며 오실레이터 양운이 켜졌습니다. 하락 기조를 끝내고 강력한 메이저 상승 랠리가 시작됨을 시사합니다.',
      },
    ],
  },
  ADX14: {
    title: 'ADX14',
    fullName: 'Average Directional Index (14)',
    quote: '지금 추세가 상승이든 하락이든, 그 힘이 강력한가?',
    desc: '현재 시장이 추세 시장인지 박스권 시장인지를 판별해 주는 지표입니다.',
    cards: [
      {
        type: 'negative',
        title: 'ADX 20 이하',
        status: '추세 소멸',
        signal: '추세 매매 금지',
        detail:
          '시장 방향성이 완전히 죽고 지루한 횡보 박스권에 갇혔습니다. 추세 추종 전략은 손실을 보기 쉬우므로 박스권 상하단 매매로 전환해야 합니다.',
      },
      {
        type: 'watch',
        title: 'ADX 20~25',
        status: '추세 도입기',
        signal: '방향 주시',
        detail:
          '지표가 바닥을 탈출하며 서서히 머리를 들고 있습니다. 주가가 박스권을 뚫고 새로운 대추세를 형성하려는 준비 단계이므로 진입 대기를 선언합니다.',
      },
      {
        type: 'positive',
        title: 'ADX 25 이상',
        status: '강력한 추세',
        signal: '추세 적극 추종',
        detail:
          '상승이든 하락이든 한쪽 방향으로 엄청난 가속도가 붙었습니다. 이 상태에서는 지표를 거스르는 역추세 매매는 절대 금물이며 달리는 말에 올라타야 합니다.',
      },
    ],
  },
  SMA50: {
    title: 'SMA50',
    fullName: 'Simple Moving Average (50)',
    quote: '기관과 외국인 같은 메이저 수급의 중기 방어선은 어디일까?',
    desc: "50일 동안의 종가 평균선으로, 중기 추세의 방향성을 결정짓는 '수급선'입니다.",
    cards: [
      {
        type: 'negative',
        title: '50선 붕괴',
        status: '중기 추세 꺾임',
        signal: '비중 축소',
        detail:
          '기관/외인의 중기 지지선이 무너졌습니다. 단순 기술적 조정을 넘어 중기적인 하락 패러다임으로 진입했을 확률이 높으므로 포트폴리오 비중을 덜어내야 합니다.',
      },
      {
        type: 'watch',
        title: '50선 이격',
        status: '이격 좁히기',
        signal: '눌림목 확인',
        detail:
          '급등했던 주가가 중기 평균선인 50일선 부근까지 내려와 숨고르기를 하고 있습니다. 여기서 지지 양봉이 뜨는지 이탈하는지 중기 수급 주포의 의도를 체크해야 합니다.',
      },
      {
        type: 'positive',
        title: '50선 지지반등',
        status: '메이저 수급 유입',
        signal: '중기 매수 타점',
        detail:
          '50일선 근처에서 기관 및 외국인의 대량 저가 매수세가 유입되며 아래꼬리를 달고 반등했습니다. 리스크 대비 기대수익률이 매우 높은 중기 정석 타점입니다.',
      },
    ],
  },
  Stochastic: {
    title: 'Stochastic',
    fullName: 'Stochastic Oscillator',
    quote: '최근 변동폭 중에서 오늘 종가는 어느 위치에 마감했을까?',
    desc: '주어진 기간의 최고가/최저가 범위 내에서 현재 주가의 위치를 백분율로 나타낸 지표입니다.',
    cards: [
      {
        type: 'negative',
        title: '스토 80 이상',
        status: '단기 과열 (%K 꺾임)',
        signal: '단기 매도',
        detail:
          '단기 변동성 범위의 꼭대기에 도달했습니다. 단기 매수 에너지가 극점에 달해 멈칫하는 구간이므로 단기 트레이더들은 이익 실현을 최우선으로 고려합니다.',
      },
      {
        type: 'watch',
        title: '스토 50',
        status: '모멘텀 중간 지대',
        signal: '단기 보유',
        detail:
          '%K선과 %D선이 중심부에서 꼬이며 힘겨루기를 하고 있습니다. 분봉이나 시간봉의 수급이 한쪽으로 치우치기 전까지는 성급한 진입을 자제합니다.',
      },
      {
        type: 'positive',
        title: '스토 20 이하',
        status: '단기 침체 (골든)',
        signal: '단기 매수',
        detail:
          '최근 변동폭 중에서 가격이 바닥권까지 과도하게 밀렸습니다. %K선이 %D선을 밑에서 위로 뚫어 올릴 때 강력 단기 낙폭과대 반등 타점이 형성됩니다.',
      },
    ],
  },
  'OBV Trend': {
    title: 'OBV Trend',
    fullName: 'OBV Trend Analysis',
    quote: '단기 일회성 거래량인가, 아니면 장기 누적 추세의 우상향인가?',
    desc: 'OBV 지표 자체에 이동평균선을 결합하여 장기적인 자금 유출입 추세를 분석하는 기법입니다.',
    cards: [
      {
        type: 'negative',
        title: '데드 다이버전스',
        status: '주가 상승 / OBV 하락',
        signal: '가짜 상승 (속임수)',
        detail:
          '주가는 신고가를 경신하며 가는데 거래량 추세는 오히려 저점을 낮추며 우하향합니다. 개미들만 불타기 중이며 주포는 털고 나가는 전형적인 폭락 전조 증상입니다.',
      },
      {
        type: 'watch',
        title: '동행 순항',
        status: '추세 일치',
        signal: '안정적 보유',
        detail:
          '주가가 오르는 만큼 거래량 누적 추세도 건전하게 우상향하고 있습니다. 속임수 없는 정석적인 추세이므로 추세가 무너지기 전까지는 포지션을 길게 유지합니다.',
      },
      {
        type: 'positive',
        title: '불리시 다이버전스',
        status: '주가 하락 / OBV 상승',
        signal: '진짜 바닥 (매집)',
        detail:
          '시장의 공포로 주가는 바닥을 기거나 저점을 깨고 내려가는데, 거래량 추세선은 저점을 높이며 우상향합니다. 은밀한 매집이 완료되어 폭발적 반등이 임박했음을 뜻합니다.',
      },
    ],
  },
};

const redKeywords = [
  '하락 추세',
  '매도 타이밍',
  '리스크 관리',
  '하방으로 무너질',
  '단기 저항',
  '하락 반전',
  '추세 이탈',
  '수급 악화',
  '데드 크로스',
  '대폭락',
  '50선 붕괴',
  '단기 과열',
  '이익 실현',
  '우하향',
  '폭락 전조',
];

const greenKeywords = [
  '우상향 기조',
  '상승 추세',
  '분할 매수',
  '기술적 반등',
  '추세 전환',
  '에너지 응축',
  '진입을 준비',
  '매집 시그널',
  '단기 지지',
  '양봉이 출현',
  '추세 회복',
  '매수세가 살아나며',
  '골든 크로스',
  '대시세',
  '상승 랠리',
  '적극 추종',
  '지지선',
  '지지반등',
  '낙폭과대',
  '바닥권',
  '진짜 바닥',
  '우상향',
];

const blueKeywords = ['손절선', '중심선', '이평선', '박스권', '돌파', '변곡점'];

const keywordPattern = new RegExp(
  `(${[...redKeywords, ...greenKeywords, ...blueKeywords]
    .map((keyword) => keyword.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&'))
    .join('|')})`,
  'g'
);

function TechnicalPlaybook() {
  const [selectedId, setSelectedId] = useState('RSI');
  const currentData = INDICATORS_DATA[selectedId];

  return (
    <section className="technical-playbook">
      <div className="technical-playbook__inner">
        <h1 className="technical-playbook__title">TECHNICAL INDICATORS</h1>

        <div className="technical-playbook__layout">
          <aside className="technical-playbook__sidebar" aria-label="지표 목록">
            {Object.entries(INDICATORS_DATA).map(([key, value]) => (
              <button
                key={key}
                type="button"
                onClick={() => setSelectedId(key)}
                className={`technical-playbook__sidebar-item ${
                  selectedId === key ? 'active' : ''
                }`}
              >
                {value.title}
              </button>
            ))}
          </aside>

          <article className="technical-playbook__board">
            <div className="technical-playbook__header">
              <span className="technical-playbook__badge">
                {currentData.title}
              </span>
              <span className="technical-playbook__full-name">
                {currentData.fullName}
              </span>
            </div>

            <p className="technical-playbook__quote">"{currentData.quote}"</p>
            <p className="technical-playbook__desc">{currentData.desc}</p>

            <div className="technical-playbook__grid">
              {currentData.cards.map((card) => (
                <IndicatorCard key={`${selectedId}-${card.title}`} card={card} />
              ))}
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}

function IndicatorCard({ card }) {
  return (
    <div className={`technical-playbook__card ${card.type}`}>
      <div className="technical-playbook__card-title">{card.title}</div>
      <div className="technical-playbook__card-status">{card.status}</div>
      <div className="technical-playbook__card-signal">{card.signal}</div>

      <div className="technical-playbook__detail">
        <p className="technical-playbook__detail-text">
          {renderHighlightedText(card.detail)}
        </p>
      </div>
    </div>
  );
}

function renderHighlightedText(text) {
  return text.split(keywordPattern).map((part, index) => {
    if (redKeywords.includes(part)) {
      return (
        <span key={`${part}-${index}`} className="technical-playbook__red">
          {part}
        </span>
      );
    }

    if (greenKeywords.includes(part)) {
      return (
        <span key={`${part}-${index}`} className="technical-playbook__green">
          {part}
        </span>
      );
    }

    if (blueKeywords.includes(part)) {
      return (
        <span key={`${part}-${index}`} className="technical-playbook__blue">
          {part}
        </span>
      );
    }

    return part;
  });
}

export default TechnicalPlaybook;
