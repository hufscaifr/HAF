import { getImportanceLabel, getTypeMeta } from './calendarData';

function AiAnalysisPanel({ event, onClose }) {
  if (!event) {
    return (
      <aside className="financial-calendar__analysis-panel empty">
        <span className="financial-calendar__panel-eyebrow">AI Analysis</span>
        <h2>이벤트를 선택하면 분석이 표시됩니다.</h2>
        <p>
          달력 셀의 analysis를 클릭하면 중요도, 컨센서스 대비 관전 포인트,
          한줄 코멘트와 예상 영향을 즉시 확인할 수 있습니다.
        </p>
      </aside>
    );
  }

  const typeMeta = getTypeMeta(event.type);

  return (
    <aside className="financial-calendar__analysis-panel active">
      <div className="financial-calendar__panel-head">
        <span className="financial-calendar__panel-eyebrow">AI Analysis</span>
        <button
          type="button"
          className="financial-calendar__panel-close"
          onClick={onClose}
          aria-label="분석 패널 닫기"
        >
          ×
        </button>
      </div>

      <div className="financial-calendar__analysis-score">
        <span>{getImportanceLabel(event.importance)}</span>
        <small>importance</small>
      </div>

      <h2>{event.title}</h2>
      <div className="financial-calendar__analysis-briefs">
        <section>
          <span>One-line comment</span>
          <p>{event.aiComment}</p>
        </section>
        <section>
          <span>Expected impact</span>
          <p>{event.expectedImpact}</p>
        </section>
      </div>

      <dl className="financial-calendar__analysis-grid">
        <div>
          <dt>Type</dt>
          <dd>{typeMeta.label}</dd>
        </div>
        <div>
          <dt>Country</dt>
          <dd>{event.country}</dd>
        </div>
        <div>
          <dt>Forecast</dt>
          <dd>{event.forecast || 'N/A'}</dd>
        </div>
        <div>
          <dt>Consensus</dt>
          <dd>{event.consensus || 'N/A'}</dd>
        </div>
      </dl>
    </aside>
  );
}

export default AiAnalysisPanel;
