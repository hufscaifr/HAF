import { COUNTRY_META, getImportanceLabel, getTypeMeta } from './calendarData';
import AiAnalysisPanel from './AiAnalysisPanel';
import EventGlobe from './EventGlobe';

function EventDetailModal({ event, activeTab, onChangeTab, onClose }) {
  if (!event) return null;

  const typeMeta = getTypeMeta(event.type);
  const country = COUNTRY_META[event.country] || COUNTRY_META.GLOBAL;

  return (
    <div className="financial-calendar__modal-backdrop" onClick={onClose}>
      <article
        className="financial-calendar__modal"
        onClick={(modalEvent) => modalEvent.stopPropagation()}
      >
        <div className="financial-calendar__modal-copy">
          <div className="financial-calendar__modal-header">
            <div className="financial-calendar__modal-badges">
              <span className={`financial-calendar__event-badge ${typeMeta.tone}`}>
                {typeMeta.label}
              </span>
              <span className={`financial-calendar__importance-badge ${event.importance}`}>
                {getImportanceLabel(event.importance)} importance
              </span>
            </div>
            <button
              className="financial-calendar__modal-close"
              onClick={onClose}
              aria-label="닫기"
              type="button"
            >
              ×
            </button>
          </div>

          <h2 className="financial-calendar__modal-title">{event.title}</h2>
          <p className="financial-calendar__modal-date">
            {country.name} · {event.date} · {event.time}
          </p>

          <div className="financial-calendar__detail-tabs" role="tablist">
            <button
              className={activeTab === 'detail' ? 'active' : ''}
              onClick={() => onChangeTab('detail')}
              type="button"
            >
              detail
            </button>
            <button
              className={activeTab === 'analysis' ? 'active' : ''}
              onClick={() => onChangeTab('analysis')}
              type="button"
            >
              analysis
            </button>
          </div>

          {activeTab === 'detail' ? (
            <>
              <div className="financial-calendar__modal-metrics">
                <Metric label="Forecast" value={event.forecast || 'N/A'} />
                <Metric label="Consensus" value={event.consensus || 'N/A'} />
                <Metric label="Previous" value={event.previous || 'N/A'} />
              </div>

              <div className="financial-calendar__modal-divider" />

              <span className="financial-calendar__modal-label">
                Event Description
              </span>
              <p className="financial-calendar__modal-desc">{event.detail}</p>

              <div className="financial-calendar__modal-actions">
                {event.source_url && (
                  <a
                    href={event.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Source
                  </a>
                )}
              </div>
            </>
          ) : (
            <AiAnalysisPanel event={event} onClose={() => onChangeTab('detail')} />
          )}
        </div>

        <EventGlobe country={event.country} zoomed />
      </article>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default EventDetailModal;
