const requirements = [
  {
    id: 1,
    title: '한국외국어대학교 재학생 및 휴학생',
    desc: '캠퍼스 및 전공에 무관하게 금융 연구 및 학회 활동에 열정을 가지고 주도적으로 참여할 수 있는 인재를 모집합니다.',
  },
  {
    id: 2,
    title: '금융 및 데이터 분석 관심자',
    desc: '금융 시장, 기업 분석, 계량 경제 또는 데이터 분석에 기본적인 관심과 학구열을 가진 분을 환영합니다.',
  },
  {
    id: 3,
    title: '연속 2학기 이상 활동 가능자',
    desc: '정규 리서치 및 학술 세션의 연속성을 위해 최소 2학기 이상 파트 수료가 가능한 분을 대상으로 합니다.',
  },
  {
    id: 4,
    title: '매주 정기 세션 참석 가능자',
    desc: '학회원 간의 원활한 피드백과 연구 진행을 위해 매주 지정된 정기 학술 세션 및 팀 활동에 필수 참석해야 합니다.',
  },
];

function CaifrRequirementsList({ title = 'REQUIREMENTS' }) {
  return (
    <section className="caifr-requirements">
      <div className="caifr-requirements__title-section">
        <h2 className="caifr-requirements__title">{title}</h2>
        <div className="caifr-requirements__underline" />
      </div>

      <div className="caifr-requirements__list">
        {requirements.map((item) => (
          <article key={item.id} className="caifr-requirements__card">
            <div className="caifr-requirements__badge">{item.id}</div>
            <div className="caifr-requirements__content">
              <h3 className="caifr-requirements__card-title">{item.title}</h3>
              <p className="caifr-requirements__card-desc">{item.desc}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default CaifrRequirementsList;
