import { useState } from 'react';

const videos = [
  {
    id: 1,
    date: '2026.07.10',
    title: '[AI 시황] LLM이 분석한 7월 2주차 국내 증시 변동성 및 주요 섹터 전망',
    desc: '자체 개발한 AI 뉴스 센티먼트 모델을 활용하여 코스피/코스닥 시장의 주요 이벤트와 수급 변화를 분석합니다.',
    thumbnail:
      'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 2,
    date: '2026.07.03',
    title: '[AI 시황] 미 연준(Fed) 의사록 공개에 따른 글로벌 자산시장 AI 예측 시나리오',
    desc: 'FOMC 의사록 텍스트 마이닝을 통해 주요 환율 및 채권 금리의 단기 방향성을 예측합니다.',
    thumbnail:
      'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 3,
    date: '2026.06.26',
    title: '[AI 시황] 빅테크 실적 발표 시즌 돌입, AI가 평가한 적정 주가와 리스크 요인',
    desc: '주요 빅테크 기업의 실적 발표 데이터를 기반으로 감성 분석을 수행해 주가 변동 범위를 산출합니다.',
    thumbnail:
      'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 4,
    date: '2026.06.19',
    title: '[AI 시황] 반도체 업종 수급 변화와 AI 기반 단기 모멘텀 분석',
    desc: '기관 및 외국인 매매 데이터를 기반으로 반도체 섹터 내 상대 강도와 리스크 구간을 분석합니다.',
    thumbnail:
      'https://images.unsplash.com/photo-1518186285589-2f7649de83e0?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 5,
    date: '2026.06.12',
    title: '[AI 시황] 환율 변동성이 국내 증시에 미치는 영향',
    desc: '원달러 환율과 주요 업종 지수의 상관관계를 모델링하여 단기 시장 방향성을 점검합니다.',
    thumbnail:
      'https://images.unsplash.com/photo-1569025690938-a00729c9e1f9?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 6,
    date: '2026.06.05',
    title: '[AI 시황] 채권 금리 상승 구간에서 주목할 방어 섹터',
    desc: '금리 민감 업종과 방어 섹터의 과거 패턴을 비교하여 포트폴리오 리밸런싱 관점을 제시합니다.',
    thumbnail:
      'https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 7,
    date: '2026.05.29',
    title: '[AI 시황] 글로벌 ETF 자금 흐름으로 본 위험자산 선호도',
    desc: 'ETF 유입 및 유출 데이터를 활용해 글로벌 투자 심리와 주요 자산군의 상대 매력을 분석합니다.',
    thumbnail:
      'https://images.unsplash.com/photo-1642790106117-e829e14a795f?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 8,
    date: '2026.05.22',
    title: '[AI 시황] 코스닥 성장주 변동성 확대와 대응 전략',
    desc: '성장주 밸류에이션, 거래대금, 변동성 지표를 종합해 단기 과열 여부를 점검합니다.',
    thumbnail:
      'https://images.unsplash.com/photo-1642543348745-03b1219733d9?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 9,
    date: '2026.05.15',
    title: '[AI 시황] 실적 시즌 이후 업종별 이익 전망 변화',
    desc: '컨센서스 변화율과 주가 반응을 비교해 이익 모멘텀이 유지되는 업종을 선별합니다.',
    thumbnail:
      'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 10,
    date: '2026.05.08',
    title: '[AI 시황] 원자재 가격 변화와 인플레이션 재점검',
    desc: '원유, 구리, 금 가격 데이터를 기반으로 인플레이션 압력과 관련 섹터의 흐름을 분석합니다.',
    thumbnail:
      'https://images.unsplash.com/photo-1620228885847-9eab2a1adddc?auto=format&fit=crop&w=800&q=80',
  },
];

function CaifrVideoArchive({ sectionTitle = 'Research Reports' }) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 9;
  const totalPages = Math.ceil(videos.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentVideos = videos.slice(startIndex, startIndex + itemsPerPage);

  return (
    <section className="caifr-video-archive">
      <div className="caifr-inner">
        <div className="caifr-title-wrap">
          <p className="caifr-eyebrow">HAF Research Archive</p>
          <h1 className="caifr-title">{sectionTitle}</h1>
        </div>

        <div className="caifr-grid">
          {currentVideos.map((video) => (
            <a
              key={video.id}
              className="caifr-card"
              href={`/reports-view?id=${video.id}`}
            >
              <div className="caifr-thumbnail-wrap">
                <img
                  className="caifr-thumbnail"
                  src={video.thumbnail}
                  alt={video.title}
                  loading="lazy"
                />
                <div className="caifr-play" />
              </div>

              <div className="caifr-content">
                <div className="caifr-date">{video.date}</div>
                <h2 className="caifr-video-title">{video.title}</h2>
                <p className="caifr-desc">{video.desc}</p>
              </div>
            </a>
          ))}
        </div>

        {totalPages > 1 && (
          <div className="caifr-pagination">
            {Array.from({ length: totalPages }, (_, index) => {
              const page = index + 1;

              return (
                <button
                  key={page}
                  type="button"
                  className={`caifr-page-button ${
                    currentPage === page ? 'active' : ''
                  }`}
                  onClick={() => setCurrentPage(page)}
                  aria-label={`${page} 페이지로 이동`}
                  aria-current={currentPage === page ? 'page' : undefined}
                >
                  {page}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

export default CaifrVideoArchive;
