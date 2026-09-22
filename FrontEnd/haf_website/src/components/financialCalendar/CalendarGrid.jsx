import { getImportanceLabel, getTypeMeta, WEEKDAYS } from './calendarData';

function CalendarGrid({
  currentDate,
  events,
  loading,
  onPrevMonth,
  onNextMonth,
  onSelectDate,
  onSelectEvent,
}) {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayIndex = new Date(year, month, 1).getDay();

  const getEventsForDay = (day) => {
    const dayString = `${year}-${String(month + 1).padStart(2, '0')}-${String(
      day
    ).padStart(2, '0')}`;
    return events.filter((event) => event.date === dayString);
  };

  return (
    <section className="financial-calendar__calendar-panel">
      <div className="financial-calendar__month">
        <button
          className="financial-calendar__icon-button"
          onClick={onPrevMonth}
          aria-label="이전 달"
          type="button"
        >
          <span aria-hidden="true">‹</span>
        </button>
        <div>
          <span className="financial-calendar__month-kicker">Event Calendar</span>
          <strong className="financial-calendar__month-label">
            {currentDate.toLocaleDateString('en-US', {
              month: 'long',
              year: 'numeric',
            })}
          </strong>
        </div>
        <button
          className="financial-calendar__icon-button"
          onClick={onNextMonth}
          aria-label="다음 달"
          type="button"
        >
          <span aria-hidden="true">›</span>
        </button>
      </div>

      <div className="financial-calendar__weekdays">
        {WEEKDAYS.map((day) => (
          <div key={day} className="financial-calendar__weekday">
            {day}
          </div>
        ))}
      </div>

      {loading ? (
        <div className="financial-calendar__loading">
          <div className="financial-calendar__spinner" />
          데이터를 동기화하고 있습니다...
        </div>
      ) : (
        <div className="financial-calendar__days">
          {Array.from({ length: 42 }).map((_, index) => {
            const dayNumber = index - firstDayIndex + 1;
            const isCurrentMonth = dayNumber > 0 && dayNumber <= daysInMonth;

            if (!isCurrentMonth) {
              return (
                <div
                  key={`empty-${index}`}
                  className="financial-calendar__empty-day"
                />
              );
            }

            const dayEvents = getEventsForDay(dayNumber);
            const dayString = `${year}-${String(month + 1).padStart(
              2,
              '0'
            )}-${String(dayNumber).padStart(2, '0')}`;
            const now = new Date();
            const isToday =
              now.getFullYear() === year &&
              now.getMonth() === month &&
              now.getDate() === dayNumber;

            return (
              <div
                key={`day-${dayNumber}`}
                className={`financial-calendar__day ${isToday ? 'today' : ''}`}
                onClick={() => onSelectDate(dayString, dayEvents)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    onSelectDate(dayString, dayEvents);
                  }
                }}
                role="gridcell"
                tabIndex={0}
                aria-label={`${dayString}, 이벤트 ${dayEvents.length}개`}
              >
                <div className="financial-calendar__day-head">
                  <span className="financial-calendar__day-number">
                    {dayNumber}
                  </span>
                  {dayEvents.length > 0 && (
                    <span className="financial-calendar__day-count">
                      {dayEvents.length}
                    </span>
                  )}
                </div>

                <div className="financial-calendar__event-list">
                  {dayEvents.map((event) => (
                    <EventCard
                      event={event}
                      key={event.id}
                      onSelectEvent={onSelectEvent}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

function EventCard({ event, onSelectEvent }) {
  const typeMeta = getTypeMeta(event.type);
  const hasConsensus = Boolean(event.forecast || event.consensus);

  return (
    <button
      className={`financial-calendar__event ${event.importance}`}
      onClick={(clickEvent) => {
        clickEvent.stopPropagation();
        onSelectEvent(event);
      }}
      type="button"
    >
      <div className="financial-calendar__event-top">
        <span className={`financial-calendar__event-badge ${typeMeta.tone}`}>
          {typeMeta.label}
        </span>
        <span className="financial-calendar__event-country">{event.country}</span>
      </div>

      <span className="financial-calendar__event-title">{event.title}</span>

      {hasConsensus && (
        <div className="financial-calendar__consensus-strip">
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

      <div className="financial-calendar__event-footer">
        <span className={`financial-calendar__volatility ${event.importance}`}>
          {getImportanceLabel(event.importance)}
        </span>
        <span className="financial-calendar__event-open">Open</span>
      </div>
    </button>
  );
}

export default CalendarGrid;
