import { useCallback, useEffect, useMemo, useState } from 'react';
import { API_HEADERS, apiUrl } from '../config/api';
import CalendarGrid from './financialCalendar/CalendarGrid';
import {
  EVENT_TYPES,
  MOCK_EVENTS,
  normalizeEvent,
} from './financialCalendar/calendarData';
import EventDetailModal from './financialCalendar/EventDetailModal';
import EventQuickView from './financialCalendar/EventQuickView';
import DateEventsPopover from './financialCalendar/DateEventsPopover';

function FinancialCalendar() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [currentDate, setCurrentDate] = useState(() => new Date('2026-09-01'));
  const [selectedType, setSelectedType] = useState('all');
  const [quickViewEvent, setQuickViewEvent] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [detailTab, setDetailTab] = useState('detail');
  const [selectedDate, setSelectedDate] = useState(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const getMonthRange = useCallback((targetYear, targetMonth) => {
    const start = `${targetYear}-${String(targetMonth + 1).padStart(2, '0')}-01`;
    const lastDay = new Date(targetYear, targetMonth + 1, 0).getDate();
    const end = `${targetYear}-${String(targetMonth + 1).padStart(
      2,
      '0'
    )}-${String(lastDay).padStart(2, '0')}`;

    return { start, end };
  }, []);

  const loadEventsFromApi = useCallback(async () => {
    setLoading(true);

    const { start, end } = getMonthRange(year, month);

    try {
      const queryParams = new URLSearchParams({
        start_date: start,
        end_date: end,
        refresh_if_stale: 'false',
      });

      const response = await fetch(
        apiUrl(`/api/financial-calendar?${queryParams.toString()}`),
        {
          method: 'GET',
          headers: {
            ...API_HEADERS,
            Accept: 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: 서버 응답 오류`);
      }

      const data = await response.json();

      if (data.status === 'success' && Array.isArray(data.events)) {
        setEvents(data.events.map(normalizeEvent));
        setToast({
          message: `DB에서 ${data.events.length}건의 일정을 불러왔습니다.`,
          isError: false,
        });
      } else {
        throw new Error('올바르지 않은 응답 데이터 구조');
      }
    } catch (error) {
      console.warn('백엔드 API 호출 실패, Mock 데이터 사용:', error);
      setEvents(MOCK_EVENTS.map(normalizeEvent));
      setToast({
        message: `백엔드 API 연결 실패: Mock 데이터를 표시합니다.`,
        isError: true,
      });
    } finally {
      setLoading(false);
    }
  }, [year, month, getMonthRange]);

  useEffect(() => {
    loadEventsFromApi();
  }, [loadEventsFromApi]);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(null), 3600);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const filteredEvents = useMemo(() => {
    if (selectedType === 'all') return events;
    return events.filter((event) => event.type === selectedType);
  }, [events, selectedType]);

  const highImpactCount = filteredEvents.filter(
    (event) => event.importance === 'high'
  ).length;
  const consensusCount = filteredEvents.filter(
    (event) => event.forecast || event.consensus
  ).length;

  const handlePrevMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const handleNextMonth = () => setCurrentDate(new Date(year, month + 1, 1));

  const handleOpenDetail = (event, tab = 'detail') => {
    setDetailTab(tab);
    setSelectedEvent(event);
    setQuickViewEvent(null);
  };

  const handleSelectDate = (date, dateEvents) => {
    setSelectedDate({ date, events: dateEvents });
  };

  const handleSelectDateEvent = (event) => {
    setSelectedDate(null);
    setQuickViewEvent(event);
  };

  const handleCloseDetail = () => {
    setSelectedEvent(null);
    setDetailTab('detail');
  };

  return (
    <section className="financial-calendar">
      <div className="financial-calendar__aurora" aria-hidden="true" />

      <div className="financial-calendar__hero">
        <div className="financial-calendar__hero-copy">
          <span className="financial-calendar__eyebrow">Global Market Desk</span>
          <p className="financial-calendar__subtitle">
            매크로, 실적 발표, 공시 이벤트를 한 화면에서 보고 컨센서스와 AI
            코멘트까지 빠르게 확인합니다.
          </p>

          <div className="financial-calendar__stats">
            <Stat label="Filtered events" value={filteredEvents.length} />
            <Stat label="High importance" value={highImpactCount} />
            <Stat label="With consensus" value={consensusCount} />
          </div>
        </div>
      </div>

      <div className="financial-calendar__filters">
        <div className="financial-calendar__filter-group" role="tablist">
          {EVENT_TYPES.map((type) => (
            <button
              key={type.id}
              className={`financial-calendar__filter ${
                selectedType === type.id ? 'active' : ''
              }`}
              onClick={() => setSelectedType(type.id)}
              type="button"
            >
              {type.label}
            </button>
          ))}
        </div>

        {loading && (
          <div className="financial-calendar__sync">
            <span className="financial-calendar__sync-status">Syncing...</span>
          </div>
        )}
      </div>

      <div className="financial-calendar__workspace">
        <CalendarGrid
          currentDate={currentDate}
          events={filteredEvents}
          loading={loading}
          onPrevMonth={handlePrevMonth}
          onNextMonth={handleNextMonth}
          onSelectDate={handleSelectDate}
          onSelectEvent={setQuickViewEvent}
        />
      </div>

      <DateEventsPopover
        date={selectedDate?.date}
        events={selectedDate?.events || []}
        onClose={() => setSelectedDate(null)}
        onSelectEvent={handleSelectDateEvent}
      />

      <EventQuickView
        event={quickViewEvent}
        onClose={() => setQuickViewEvent(null)}
        onOpenDetail={(event) => handleOpenDetail(event, 'detail')}
        onOpenAnalysis={(event) => handleOpenDetail(event, 'analysis')}
      />

      <EventDetailModal
        event={selectedEvent}
        activeTab={detailTab}
        onChangeTab={setDetailTab}
        onClose={handleCloseDetail}
      />

      {toast && (
        <div
          className={`financial-calendar__toast ${toast.isError ? 'error' : ''}`}
        >
          {toast.message}
        </div>
      )}
    </section>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

export default FinancialCalendar;
