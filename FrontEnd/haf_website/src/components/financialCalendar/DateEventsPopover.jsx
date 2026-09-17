import { getImportanceLabel, getTypeMeta } from './calendarData';

function DateEventsPopover({ date, events, onClose, onSelectEvent }) {
  if (!date) return null;

  const formattedDate = new Date(`${date}T00:00:00`).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  });

  return (
    <div className="financial-calendar__date-backdrop" onClick={onClose}>
      <section
        className="financial-calendar__date-popover"
        onClick={(event) => event.stopPropagation()}
        aria-modal="true"
        aria-labelledby="financial-calendar-date-title"
        role="dialog"
      >
        <header className="financial-calendar__date-popover-head">
          <div>
            <span>{events.length} events</span>
            <h2 id="financial-calendar-date-title">{formattedDate}</h2>
          </div>
          <button
            className="financial-calendar__panel-close"
            onClick={onClose}
            type="button"
            aria-label="날짜 일정 닫기"
          >
            ×
          </button>
        </header>

        {events.length === 0 ? (
          <div className="financial-calendar__date-empty">
            예정된 금융 이벤트가 없습니다.
          </div>
        ) : (
          <div className="financial-calendar__date-event-list">
            {events.map((event) => {
              const typeMeta = getTypeMeta(event.type);
              return (
                <button
                  className={`financial-calendar__date-event ${event.importance}`}
                  key={event.id}
                  onClick={() => onSelectEvent(event)}
                  type="button"
                >
                  <span className="financial-calendar__date-event-meta">
                    <span className={`financial-calendar__event-badge ${typeMeta.tone}`}>
                      {typeMeta.label}
                    </span>
                    <span>{event.country}</span>
                    {event.time && <span>{event.time}</span>}
                    <span>{getImportanceLabel(event.importance)}</span>
                  </span>
                  <strong>{event.title}</strong>
                  {(event.forecast || event.consensus) && (
                    <span className="financial-calendar__date-event-consensus">
                      {event.forecast && <span>Forecast {event.forecast}</span>}
                      {event.consensus && <span>Consensus {event.consensus}</span>}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

export default DateEventsPopover;
