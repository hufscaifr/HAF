export const EVENT_TYPES = [
  { id: 'all', label: 'All' },
  { id: 'macro', label: 'Macro' },
  { id: 'earnings', label: 'Earnings' },
  { id: 'disclosure', label: 'Disclosure' },
  { id: 'policy', label: 'Policy' },
  { id: 'market_holiday', label: 'Holiday' },
];

export const WEEKDAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];

export const COUNTRY_META = {
  US: { name: 'United States', lat: 38.9, lon: -77.0, flag: 'US' },
  KR: { name: 'South Korea', lat: 37.6, lon: 127.0, flag: 'KR' },
  JP: { name: 'Japan', lat: 35.7, lon: 139.7, flag: 'JP' },
  EU: { name: 'Euro Area', lat: 50.1, lon: 8.7, flag: 'EU' },
  CN: { name: 'China', lat: 39.9, lon: 116.4, flag: 'CN' },
  GLOBAL: { name: 'Global', lat: 10, lon: 20, flag: 'GLOBAL' },
};

export const MOCK_EVENTS = [
  {
    id: 'evt-us-cpi',
    date: '2026-09-10',
    title: 'US August CPI',
    type: 'macro',
    country: 'US',
    time: '21:30 KST',
    importance: 'high',
    actual: null,
    forecast: '2.8% YoY',
    consensus: '2.8% YoY',
    previous: '2.7% YoY',
    source_name: 'BLS',
    source_url: 'https://www.bls.gov/cpi/',
    detail:
      'Shelter disinflation and services momentum will shape expectations for the next FOMC path.',
    aiComment:
      '컨센서스 상회 시 장기금리와 달러가 함께 민감하게 반응할 가능성이 큽니다.',
    expectedImpact:
      '미국채 10년물 금리 상승, 달러 강세, 성장주 밸류에이션 압박이 예상됩니다.',
  },
  {
    id: 'evt-kr-memory',
    date: '2026-09-12',
    title: 'SK Hynix Q3 Guidance Update',
    type: 'earnings',
    country: 'KR',
    time: 'Before Market',
    importance: 'high',
    actual: null,
    forecast: 'OP 8.1T KRW',
    consensus: 'OP 8.0T KRW',
    previous: 'OP 6.9T KRW',
    source_name: 'Company IR',
    source_url: 'https://www.skhynix.com',
    detail:
      'Investors will focus on HBM pricing, shipment mix, and 2027 capacity commentary.',
    aiComment:
      'HBM 단가와 증설 코멘트가 국내 반도체 밸류체인 재평가의 핵심입니다.',
    expectedImpact:
      '긍정적 가이던스는 메모리, 장비, 소재주로 매수세를 확산시킬 수 있습니다.',
  },
  {
    id: 'evt-fed',
    date: '2026-09-16',
    title: 'FOMC Rate Decision',
    type: 'policy',
    country: 'US',
    time: '03:00 KST',
    importance: 'high',
    actual: null,
    forecast: '4.25% - 4.50%',
    consensus: 'Hold',
    previous: '4.25% - 4.50%',
    source_name: 'Federal Reserve',
    source_url: 'https://www.federalreserve.gov',
    detail:
      'The dot plot and press conference language will matter more than the headline decision.',
    aiComment:
      '동결 자체보다 점도표의 중립금리 경로 변화가 위험자산 방향성을 가릅니다.',
    expectedImpact:
      '점도표가 매파적으로 이동하면 주식 멀티플 축소와 단기 달러 강세가 예상됩니다.',
  },
  {
    id: 'evt-kr-dart',
    date: '2026-09-18',
    title: 'Samsung Electronics Share Buyback Filing',
    type: 'disclosure',
    country: 'KR',
    time: 'After Close',
    importance: 'medium',
    actual: null,
    forecast: null,
    consensus: null,
    previous: null,
    source_name: 'DART',
    source_url: 'https://dart.fss.or.kr',
    detail:
      'The market will compare the buyback size and cancellation schedule with prior capital return plans.',
    aiComment:
      '소각 여부가 명확하면 단기 수급보다 주주환원 프리미엄에 더 큰 의미가 있습니다.',
    expectedImpact:
      '자사주 소각 일정이 구체적이면 대형 IT 지주·배당주 선호가 강화될 수 있습니다.',
  },
  {
    id: 'evt-ecb',
    date: '2026-09-21',
    title: 'ECB President Speech',
    type: 'macro',
    country: 'EU',
    time: '18:00 KST',
    importance: 'medium',
    actual: null,
    forecast: 'Neutral',
    consensus: 'Dovish hold',
    previous: 'Data dependent',
    source_name: 'ECB',
    source_url: 'https://www.ecb.europa.eu',
    detail:
      'Markets will listen for clues on wage pressure and the timing of the next policy adjustment.',
    aiComment:
      '유로존 경기 둔화 표현이 강해지면 유로 약세와 유럽 방어주 선호가 나타날 수 있습니다.',
    expectedImpact:
      '비둘기파적 발언은 유로 약세, 유럽 채권 강세, 경기방어 섹터 선호로 이어질 수 있습니다.',
  },
  {
    id: 'evt-jp-cpi',
    date: '2026-09-24',
    title: 'Tokyo CPI',
    type: 'macro',
    country: 'JP',
    time: '08:30 KST',
    importance: 'medium',
    actual: null,
    forecast: '2.6% YoY',
    consensus: '2.5% YoY',
    previous: '2.4% YoY',
    source_name: 'Statistics Bureau',
    source_url: 'https://www.stat.go.jp/english/',
    detail:
      'Tokyo CPI is a timely read-through for national inflation and Bank of Japan normalization risk.',
    aiComment:
      '엔화와 일본 은행주가 가장 빠르게 반응할 수 있는 선행 물가 이벤트입니다.',
    expectedImpact:
      '예상 상회 시 엔화 강세와 일본 은행주 강세, 수출주 부담이 나타날 수 있습니다.',
  },
  {
    id: 'evt-cn-pmi',
    date: '2026-09-30',
    title: 'China Manufacturing PMI',
    type: 'macro',
    country: 'CN',
    time: '10:30 KST',
    importance: 'medium',
    actual: null,
    forecast: '50.2',
    consensus: '50.1',
    previous: '49.9',
    source_name: 'NBS China',
    source_url: 'https://www.stats.gov.cn/english/',
    detail:
      'A return above 50 would support cyclicals and Korea export-sensitive names.',
    aiComment:
      '50선 회복 여부가 소재, 산업재, 중국 소비주 심리의 단기 분기점입니다.',
    expectedImpact:
      '확장 국면 확인 시 철강, 화학, 운송, 한국 수출 민감주에 우호적입니다.',
  },
];

const API_TYPE_MAP = {
  economic_indicator: 'macro',
  earning: 'earnings',
  earnings: 'earnings',
  rate: 'policy',
  auction: 'macro',
  policy: 'policy',
  market_holiday: 'market_holiday',
  disclosure: 'disclosure',
};

export function normalizeEvent(event) {
  const type = API_TYPE_MAP[event.type || event.category] || event.type || 'macro';

  return {
    id: event.id,
    date: event.date,
    title: event.title,
    type,
    country: event.country || 'GLOBAL',
    time: event.time || event.event_time || 'TBD',
    importance: event.importance || 'medium',
    actual: event.actual ?? null,
    forecast: event.forecast ?? event.consensus_forecast ?? null,
    consensus: event.consensus ?? event.market_consensus ?? null,
    previous: event.previous ?? null,
    detail: event.detail || event.description || '추가 설명이 준비 중입니다.',
    source_name: event.source_name,
    source_url: event.source_url,
    aiComment:
      event.aiComment ||
      event.ai_comment ||
      '가격 민감도가 높은 자산과 업종을 중심으로 이벤트 직전 변동성 확대 가능성을 점검하세요.',
    expectedImpact:
      event.expectedImpact ||
      event.expected_impact ||
      event.impact ||
      '컨센서스와 실제치의 차이에 따라 금리, 환율, 섹터 로테이션이 빠르게 반응할 수 있습니다.',
  };
}

export function getTypeMeta(type) {
  switch (type) {
    case 'macro':
      return { label: 'Macro', tone: 'blue' };
    case 'earnings':
      return { label: 'Earnings', tone: 'green' };
    case 'disclosure':
      return { label: 'Disclosure', tone: 'amber' };
    case 'policy':
      return { label: 'Policy', tone: 'black' };
    case 'market_holiday':
      return { label: 'Holiday', tone: 'red' };
    default:
      return { label: 'Event', tone: 'gray' };
  }
}

export function getImportanceLabel(importance) {
  if (importance === 'high') return 'High';
  if (importance === 'low') return 'Low';
  return 'Medium';
}
