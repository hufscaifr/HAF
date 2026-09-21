const mockReports = [
  {
    id: 'mock-001', date: '2026.09.21', category: 'Market Outlook', company: '국내 증시',
    title: '[AI 시황] 반도체 중심의 수급 회복과 이번 주 시장 전망',
    desc: '외국인 수급, 반도체 업황, 주요 매크로 일정을 바탕으로 국내 증시의 단기 방향성을 점검합니다.',
    summary: '반도체 대형주로 외국인 수급이 재유입되고 있으나 환율과 금리 변동성이 남아 있어 지수 추격 매수보다 실적 가시성이 높은 종목 중심의 대응이 유효합니다.',
    highlights: ['외국인 반도체 순매수 회복', '원·달러 환율 변동성 주의', '실적 가시성 중심 선별 접근'],
    thumbnail: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80',
  },
  {
    id: 'mock-002', date: '2026.09.20', category: 'Company', company: '삼성전자',
    title: '삼성전자: 메모리 가격 반등과 AI 서버 수요의 교차점',
    desc: '메모리 가격과 HBM 공급 확대가 실적 추정치에 미치는 영향을 분석합니다.',
    summary: '메모리 가격 반등과 데이터센터 수요가 실적 개선을 지지할 전망입니다. 다만 HBM 고객 인증 속도와 파운드리 가동률은 지속적인 확인이 필요합니다.',
    highlights: ['메모리 ASP 상승', 'HBM 공급 확대 기대', '파운드리 가동률 점검 필요'],
    thumbnail: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80',
  },
  {
    id: 'mock-003', date: '2026.09.19', category: 'Company', company: 'SK하이닉스',
    title: 'SK하이닉스: HBM 리더십과 수익성 개선 지속 여부',
    desc: 'HBM 출하량과 DRAM 믹스 개선을 중심으로 중기 실적 모멘텀을 점검합니다.',
    summary: '고부가 HBM 비중 확대가 수익성을 견인하고 있습니다. 경쟁사 증설과 고객사의 재고 조정 가능성은 밸류에이션의 핵심 변수입니다.',
    highlights: ['HBM 매출 비중 확대', '제품 믹스 개선', '고객사 재고 조정 리스크'],
    thumbnail: 'https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?auto=format&fit=crop&w=1200&q=80',
  },
  {
    id: 'mock-004', date: '2026.09.18', category: 'Macro', company: '글로벌 시장',
    title: 'FOMC 이후 금리 경로와 성장주 밸류에이션',
    desc: '정책금리 기대 변화가 채권, 환율, 성장주에 미치는 영향을 시나리오별로 정리합니다.',
    summary: '완만한 금리 인하 기대는 성장주에 우호적이지만 물가 재상승 신호가 확인되면 장기금리 변동성이 확대될 수 있습니다.',
    highlights: ['정책금리 경로', '장기금리 민감도', '성장주 밸류에이션'],
    thumbnail: 'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1200&q=80',
  },
  {
    id: 'mock-005', date: '2026.09.17', category: 'Sector', company: '2차전지',
    title: '2차전지: 수요 둔화 국면에서 확인할 세 가지 지표',
    desc: '전기차 판매, 재고, 원재료 가격을 통해 업황 바닥 통과 가능성을 살펴봅니다.',
    summary: '단기 수요 회복은 제한적이지만 재고 정상화와 원재료 가격 안정은 마진 방어에 긍정적입니다. 출하량 회복이 확인되기 전까지 선별 접근이 필요합니다.',
    highlights: ['재고 정상화', '원재료 가격 안정', '출하량 회복 확인 필요'],
    thumbnail: 'https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=1200&q=80',
  },
  {
    id: 'mock-006', date: '2026.09.16', category: 'Strategy', company: '포트폴리오',
    title: '변동성 확대 구간의 방어적 포트폴리오 전략',
    desc: '배당, 현금흐름, 이익 안정성을 기준으로 방어 업종의 상대 매력을 비교합니다.',
    summary: '시장 변동성이 확대될 때는 현금흐름이 안정적이고 배당 가시성이 높은 업종의 하방 방어력이 상대적으로 높습니다.',
    highlights: ['현금흐름 안정성', '배당 가시성', '업종 분산'],
    thumbnail: 'https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80',
  },
];

export default mockReports;
