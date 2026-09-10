import { useCallback, useEffect, useMemo, useState } from 'react';
import { API_HEADERS, apiUrl } from '../config/api';

const MOCK_EVENTS = [
  {
    id: 1,
    date: '2026-07-22',
    title: '미국 6월 기존주택매매 건수 발표',
    category: 'economic_indicator',
    importance: 'medium',
    detail:
      '주택 시장의 선행 지표 역할을 합니다. 최근 금리 인하 기대감 속에 매수 대기 수요가 거래 실적으로 이어졌는지 확인하는 분수령입니다.',
    country: 'US',
    source_name: 'National Association of Realtors',
    source_url: 'https://www.nar.realtor',
  },
  {
    id: 2,
    date: '2026-07-23',
    title: 'SK하이닉스(000660) 2분기 실적 발표',
    category: 'earning',
    importance: 'high',
    detail:
      'HBM3E 공급 가속화와 고부가 DRAM 판매 비중 증가에 힘입어 전분기 대비 35% 이상의 영업이익 성장이 시장 컨센서스입니다.',
    country: 'KR',
    source_name: 'SK하이닉스 IR',
    source_url: 'https://www.skhynix.com',
  },
  {
    id: 3,
    date: '2026-07-30',
    title: '미국 Fed 기준금리 결정 (FOMC)',
    category: 'rate',
    importance: 'high',
    detail:
      '인플레이션 수치 안정세에 안착함에 따라 파월 의장의 전격 금리 인하 선언 및 점도표 변화 여부가 주목됩니다.',
    country: 'US',
    source_name: 'Federal Reserve',
    source_url: 'https://www.federalreserve.gov',
  },
];

const categories = [
  { id: 'all', label: '전체' },
  { id: 'rate', label: '금리' },
  { id: 'economic_indicator', label: '거시지표' },
  { id: 'earning', label: '실적' },
  { id: 'policy', label: '정책' },
  { id: 'market_holiday', label: '휴장' },
];

const weekdays = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];

function FinancialCalendar() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [toast, setToast] = useState(null);
  const [currentDate, setCurrentDate] = useState(() => new Date());
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [importanceFilter, setImportanceFilter] = useState('all');

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

  const loadEventsFromApi = useCallback(
    async (forceRefresh = false) => {
      if (forceRefresh) setRefreshing(true);
      else setLoading(true);

      const { start, end } = getMonthRange(year, month);

      try {
        let data;

        if (forceRefresh) {
          const response = await fetch(apiUrl('/api/financial-calendar/refresh'), {
            method: 'POST',
            headers: {
              ...API_HEADERS,
              'Content-Type': 'application/json',
              Accept: 'application/json',
            },
            body: JSON.stringify({
              start_date: start,
              end_date: end,
            }),
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: 서버 응답 오류`);
          }

          data = await response.json();
        } else {
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

          data = await response.json();
        }

        if (data.status === 'success' && Array.isArray(data.events)) {
          setEvents(data.events);
          setToast({
            message: forceRefresh
              ? `AI 웹 검색으로 최신 일정 ${data.events.length}건을 갱신했습니다.`
              : `DB에서 ${data.events.length}건의 일정을 불러왔습니다.`,
            isError: false,
          });
        } else {
          throw new Error('올바르지 않은 응답 데이터 구조');
        }
      } catch (error) {
        console.warn('백엔드 API 호출 실패, Mock 데이터 사용:', error);
        setEvents(MOCK_EVENTS);
        setToast({
          message: `백엔드 API 연결 실패 (${
            error?.message || '서버 미작동'
          }). Mock 데이터를 표시합니다.`,
          isError: true,
        });
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [year, month, getMonthRange]
  );

  useEffect(() => {
    loadEventsFromApi(false);
  }, [loadEventsFromApi]);

  useEffect(() => {
    if (!toast) return undefined;

    const timer = window.setTimeout(() => setToast(null), 4000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      const matchCategory =
        selectedCategory === 'all' || event.category === selectedCategory;
      let matchImportance = true;

      if (importanceFilter === 'high') {
        matchImportance = event.importance === 'high';
      }

      return matchCategory && matchImportance;
    });
  }, [events, selectedCategory, importanceFilter]);

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayIndex = new Date(year, month, 1).getDay();

  const getEventsForDay = (day) => {
    const dayString = `${year}-${String(month + 1).padStart(2, '0')}-${String(
      day
    ).padStart(2, '0')}`;
    return filteredEvents.filter((event) => event.date === dayString);
  };

  const handlePrevMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const handleNextMonth = () => setCurrentDate(new Date(year, month + 1, 1));

  return (
    <section className="financial-calendar">
      <div className="financial-calendar__header">
        <div>
          <h1 className="financial-calendar__title">Macroeconomic Calendar</h1>
          <p className="financial-calendar__subtitle">
            글로벌 거시 경제 지표 및 주요 기업 실적 일정
          </p>
        </div>

        <div className="financial-calendar__sync">
          {loading && (
            <span className="financial-calendar__sync-status">동기화 중...</span>
          )}
          <button
            className="financial-calendar__refresh"
            onClick={() => loadEventsFromApi(true)}
            disabled={refreshing || loading}
            type="button"
          >
            {refreshing ? '데이터 불러오는 중...' : '최신 일정 동기화'}
          </button>
        </div>
      </div>

      <div className="financial-calendar__filters">
        <div className="financial-calendar__filter-group">
          {categories.map((category) => (
            <button
              key={category.id}
              className={`financial-calendar__filter ${
                selectedCategory === category.id ? 'active' : ''
              }`}
              onClick={() => setSelectedCategory(category.id)}
              type="button"
            >
              {category.label}
            </button>
          ))}
        </div>

        <button
          className={`financial-calendar__importance ${
            importanceFilter === 'high' ? 'active' : ''
          }`}
          onClick={() =>
            setImportanceFilter((prev) => (prev === 'high' ? 'all' : 'high'))
          }
          type="button"
        >
          High Volatility (중요도 높음)
        </button>
      </div>

      <div className="financial-calendar__card">
        <div className="financial-calendar__month">
          <button
            className="financial-calendar__arrow"
            onClick={handlePrevMonth}
            aria-label="이전 달"
            type="button"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" />
            </svg>
          </button>
          <span className="financial-calendar__month-label">
            {year}. {String(month + 1).padStart(2, '0')}
          </span>
          <button
            className="financial-calendar__arrow"
            onClick={handleNextMonth}
            aria-label="다음 달"
            type="button"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" />
            </svg>
          </button>
        </div>

        <div className="financial-calendar__weekdays">
          {weekdays.map((day) => (
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
              const isCurrentMonth =
                dayNumber > 0 && dayNumber <= daysInMonth;

              if (!isCurrentMonth) {
                return (
                  <div
                    key={`empty-${index}`}
                    className="financial-calendar__empty-day"
                  />
                );
              }

              const dayEvents = getEventsForDay(dayNumber);
              const now = new Date();
              const isToday =
                now.getFullYear() === year &&
                now.getMonth() === month &&
                now.getDate() === dayNumber;

              return (
                <div
                  key={`day-${dayNumber}`}
                  className={`financial-calendar__day ${
                    isToday ? 'today' : ''
                  }`}
                >
                  <span className="financial-calendar__day-number">
                    {dayNumber}
                  </span>
                  <div className="financial-calendar__event-list">
                    {dayEvents.map((event) => {
                      const badge = getCategoryBadge(event.category);

                      return (
                        <button
                          key={event.id}
                          className={`financial-calendar__event ${event.importance}`}
                          onClick={() => setSelectedEvent(event)}
                          type="button"
                        >
                          <div className="financial-calendar__event-top">
                            <span>{getCountryFlag(event.country)}</span>
                            <span
                              className="financial-calendar__event-badge"
                              style={{
                                color: badge.text,
                                backgroundColor: badge.bg,
                                borderColor: badge.border,
                              }}
                            >
                              {badge.label}
                            </span>
                          </div>
                          <div className="financial-calendar__event-title">
                            {event.title}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {selectedEvent && (
        <EventModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
        />
      )}

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

function EventModal({ event, onClose }) {
  const badge = getCategoryBadge(event.category);

  return (
    <div className="financial-calendar__modal-backdrop" onClick={onClose}>
      <div
        className="financial-calendar__modal"
        onClick={(modalEvent) => modalEvent.stopPropagation()}
      >
        <div className="financial-calendar__modal-header">
          <div className="financial-calendar__modal-badges">
            <span
              className="financial-calendar__modal-badge"
              style={{
                backgroundColor: badge.bg,
                color: badge.text,
                borderColor: badge.border,
              }}
            >
              {badge.label}
            </span>
            <span className={`financial-calendar__importance-badge ${event.importance}`}>
              {event.importance === 'high'
                ? 'High Volatility'
                : event.importance === 'medium'
                  ? 'Medium Volatility'
                  : 'Low Volatility'}
            </span>
          </div>
          <button
            className="financial-calendar__modal-close"
            onClick={onClose}
            aria-label="닫기"
            type="button"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path
                d="M18 6L6 18M6 6l12 12"
                stroke="currentColor"
                strokeWidth="2"
              />
            </svg>
          </button>
        </div>

        <div>
          <h2 className="financial-calendar__modal-title">{event.title}</h2>
          <span className="financial-calendar__modal-date">
            {event.country && <strong>{getCountryFlag(event.country)}</strong>} ·{' '}
            {event.date}
          </span>
        </div>

        <div className="financial-calendar__modal-divider" />

        <div>
          <span className="financial-calendar__modal-label">
            Event Description
          </span>
          <p className="financial-calendar__modal-desc">{event.detail}</p>
        </div>

        {event.source_name && (
          <div className="financial-calendar__source">
            <span>
              Source: <strong>{event.source_name}</strong>
            </span>
            {event.source_url && (
              <a
                href={event.source_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                View Resource ↗
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function getCategoryBadge(category) {
  switch (category) {
    case 'rate':
      return {
        label: '금리',
        bg: '#f4f4f5',
        text: '#18181b',
        border: '#e4e4e7',
      };
    case 'economic_indicator':
      return {
        label: '거시지표',
        bg: '#f0f9ff',
        text: '#0369a1',
        border: '#e0f2fe',
      };
    case 'earning':
      return {
        label: '실적발표',
        bg: '#f0fdf4',
        text: '#15803d',
        border: '#dcfce7',
      };
    case 'policy':
      return {
        label: '정책',
        bg: '#fdf4ff',
        text: '#86198f',
        border: '#fae8ff',
      };
    case 'market_holiday':
      return {
        label: '휴장',
        bg: '#fef2f2',
        text: '#b91c1c',
        border: '#fee2e2',
      };
    case 'auction':
      return {
        label: '국채입찰',
        bg: '#fff7ed',
        text: '#c2410c',
        border: '#ffedd5',
      };
    default:
      return {
        label: '일정',
        bg: '#f8fafc',
        text: '#475569',
        border: '#f1f5f9',
      };
  }
}

function getCountryFlag(country) {
  if (!country) return '';
  if (country.toUpperCase() === 'GLOBAL') return 'GLOBAL';
  return country.toUpperCase();
}

export default FinancialCalendar;
