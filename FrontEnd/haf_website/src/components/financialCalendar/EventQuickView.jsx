import { COUNTRY_META, getImportanceLabel, getTypeMeta } from './calendarData';

function EventQuickView({ event, onClose, onOpenDetail, onOpenAnalysis }) {
  if (!event) return null;

  const typeMeta = getTypeMeta(event.type);
  const country = COUNTRY_META[event.country] || COUNTRY_META.GLOBAL;

  return (
    <div className="financial-calendar__quick-backdrop" onClick={onClose}>
      <article
        className="financial-calendar__quick-view"
        onClick={(quickViewEvent) => quickViewEvent.stopPropagation()}
      >
        <div className="financial-calendar__panel-head">
          <div className="financial-calendar__modal-badges">
            <span className={`financial-calendar__event-badge ${typeMeta.tone}`}>
              {typeMeta.label}
            </span>
            <span className={`financial-calendar__importance-badge ${event.importance}`}>
              {getImportanceLabel(event.importance)}
            </span>
          </div>
          <button
            className="financial-calendar__panel-close"
            onClick={onClose}
            type="button"
            aria-label="간이 창 닫기"
          >
            ×
          </button>
        </div>

        <h2>{event.title}</h2>
        <p className="financial-calendar__quick-meta">
          {country.name} · {event.date} · {event.time}
        </p>

        {(event.forecast || event.consensus) && (
          <div className="financial-calendar__quick-consensus">
            {event.forecast && (
              <span>
                <small>Forecast</small>
                {event.forecast}
              </span>
            )}
            {event.consensus && (
              <span>
                <small>Consensus</small>
                {event.consensus}
              </span>
            )}
          </div>
        )}

        <p className="financial-calendar__quick-desc">{event.detail}</p>

        <div className="financial-calendar__quick-actions">
          <button type="button" onClick={() => onOpenAnalysis(event)}>
            analysis
          </button>
          <button type="button" onClick={() => onOpenDetail(event)}>
            자세히 보기
          </button>
        </div>
      </article>
    </div>
  );
}

export default EventQuickView;
