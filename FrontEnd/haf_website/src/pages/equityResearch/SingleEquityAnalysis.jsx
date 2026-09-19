import { useEffect, useMemo, useState } from 'react';
import { API_HEADERS, apiUrl } from '../../config/api';

const departments = [
  {
    key: 'issue',
    name: 'Issue Department',
    label: '이슈 발굴',
    icon: 'radar',
    junior: 'Junior Issue Analyst',
    senior: 'Senior Issue Analyst',
    request: '기업명과 시장 정보를 받아 핵심 이슈를 분류합니다.',
    response: '주가, 공시, 수익성 이슈를 승인 대기열로 보냅니다.',
  },
  {
    key: 'cause',
    name: 'Cause Analysis Dept',
    label: '원인 분석',
    icon: 'network',
    junior: 'Junior Cause Analyst',
    senior: 'Senior Cause Analyst',
    request: '승인된 이슈별 가설과 필요 데이터를 요청합니다.',
    response: '영향 metric과 가설 검증 요청을 Data 부서로 전달합니다.',
  },
  {
    key: 'data',
    name: 'Data Research Dept',
    label: 'Data',
    icon: 'database',
    junior: 'Junior Data Analyst',
    senior: 'Senior Data Analyst',
    request: 'KRX, 가격, DART 재무 데이터를 수집합니다.',
    response: '검증된 evidence, chart, table artifact를 공유합니다.',
  },
  {
    key: 'fundamental',
    name: 'Fundamental Research Dept',
    label: 'Fundamental',
    icon: 'building',
    junior: 'Junior Fundamental Analyst',
    senior: 'Senior Fundamental Analyst',
    request: '수집 evidence를 assumption과 forecast로 번역합니다.',
    response: '매출, 이익, 수익성, 안정성 가정을 Estimate 부서로 넘깁니다.',
  },
  {
    key: 'estimate',
    name: 'Estimate Department',
    label: 'Estimate',
    icon: 'calculator',
    junior: 'Junior Estimate Analyst',
    senior: 'Senior Estimate Analyst',
    request: '승인 assumption을 실적 추정치로 계산합니다.',
    response: '매출, 영업이익, EPS snapshot을 리스크 부서로 보냅니다.',
  },
  {
    key: 'risk',
    name: 'Risk Department',
    label: 'Risk',
    icon: 'shield',
    junior: 'Junior Risk Analyst',
    senior: 'Senior Risk Analyst',
    request: '이슈별 리스크와 가격/펀더멘탈 영향을 검증합니다.',
    response: '리스크 등급, 주가 검증, monitoring point를 작성합니다.',
  },
  {
    key: 'report',
    name: 'Report Department',
    label: 'Writing',
    icon: 'pen',
    junior: 'Section Drafting Desk',
    senior: 'Senior Section Editor',
    request: '부서별 승인 데이터를 섹션 draft로 작성합니다.',
    response: '이슈, 실적, 밸류에이션, 리스크 섹션을 승인합니다.',
  },
  {
    key: 'merge',
    name: 'Merging Department',
    label: 'Merge',
    icon: 'merge',
    junior: 'Merging Junior Editor',
    senior: 'Senior Merging Editor',
    request: '승인된 섹션 draft를 하나의 JSON 보고서로 취합합니다.',
    response: '프론트 렌더링 가능한 최종 리포트를 Verification으로 보냅니다.',
  },
  {
    key: 'verify',
    name: 'Verification Department',
    label: 'Verify',
    icon: 'check',
    junior: 'Fact · Numerical · Consistency',
    senior: 'Verification Senior Reviewer',
    request: 'claim lineage, 계산, 숫자 정합성을 검사합니다.',
    response: '검증 통과 후 최종 보고서를 발행합니다.',
  },
];

const statusMessages = [
  'Research Director가 프로젝트를 열고 있습니다.',
  'Junior analyst가 요청서를 확인했습니다.',
  'Senior analyst가 evidence lineage를 검토합니다.',
  '다음 부서로 업무 메모를 전송합니다.',
];

function SingleEquityAnalysis() {
  const [company, setCompany] = useState('삼성전자');
  const [refreshListings, setRefreshListings] = useState(false);
  const [running, setRunning] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [messageIndex, setMessageIndex] = useState(0);
  const [selectedDepartmentKey, setSelectedDepartmentKey] = useState('issue');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!running) return undefined;
    const timer = window.setInterval(() => {
      setActiveIndex((current) => Math.min(current + 1, departments.length - 1));
      setMessageIndex((current) => (current + 1) % statusMessages.length);
    }, 1800);
    return () => window.clearInterval(timer);
  }, [running]);

  const completedNames = result?.project?.completed_departments || [];
  const report = result?.report?.json_payload || null;
  const logs = result?.logs || [];
  const riskCount = result?.risk_assessments?.length || 0;
  const chartCount = result?.charts?.length || 0;
  const tableCount = result?.tables?.length || 0;
  const selectedDepartment = departments.find(
    (department) => department.key === selectedDepartmentKey
  ) || departments[0];

  const progress = useMemo(() => {
    if (result) return 100;
    return Math.round(((activeIndex + (running ? 0.35 : 0)) / departments.length) * 100);
  }, [activeIndex, result, running]);

  const runResearch = async () => {
    if (!company.trim()) {
      setError('기업명을 입력해주세요.');
      return;
    }

    setRunning(true);
    setResult(null);
    setError('');
    setActiveIndex(0);
    setMessageIndex(0);
    setSelectedDepartmentKey('issue');

    try {
      const response = await fetch(apiUrl('/api/ai-research/run'), {
        method: 'POST',
        headers: {
          ...API_HEADERS,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company: company.trim(),
          data_mode: 'real',
          refresh_krx_listings: refreshListings,
        }),
      });

      if (!response.ok) {
        let message = `서버 응답 에러 (${response.status})`;
        try {
          const errorBody = await response.json();
          message = errorBody.detail || message;
        } catch {
          // Keep fallback message.
        }
        throw new Error(message);
      }

      const payload = await response.json();
      setResult(payload);
      setActiveIndex(departments.length - 1);
    } catch (requestError) {
      console.error('AI 리서치 실행 실패:', requestError);
      setError(requestError.message);
    } finally {
      setRunning(false);
    }
  };

  const getDepartmentState = (department, index) => {
    if (result && completedNames.includes(department.name)) return 'completed';
    if (result && department.key === 'verify') return 'completed';
    if (running && index === activeIndex) return 'active';
    if (running && index < activeIndex) return 'completed';
    return 'idle';
  };

  const selectDepartment = (departmentKey) => {
    setSelectedDepartmentKey(departmentKey);
  };

  return (
    <section className="ai-research-center">
      <div className="ai-center-hero">
        <div className="ai-center-hero__copy">
          <span className="ai-center-eyebrow">HAF · AI Research Center</span>
          <h1>AI 리서치 센터</h1>
          <p>
            기업명을 입력하면 리서치 조직이 이슈 발굴부터 최종 보고서 검증까지
            순차적으로 움직입니다.
          </p>
        </div>

        <div className="ai-center-command">
          <div className="ai-command-input">
            <label htmlFor="ai-company">Company</label>
            <input
              id="ai-company"
              value={company}
              onChange={(event) => setCompany(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !running) runResearch();
              }}
              disabled={running}
              placeholder="삼성전자"
            />
          </div>

          <label className="ai-refresh-toggle">
            <input
              type="checkbox"
              checked={refreshListings}
              onChange={(event) => setRefreshListings(event.target.checked)}
              disabled={running}
            />
            <span>KRX DB refresh</span>
          </label>

          <button
            className="ai-run-button"
            type="button"
            onClick={runResearch}
            disabled={running}
          >
            {running ? 'Researching' : 'Run Research'}
          </button>
        </div>
      </div>

      {error && <div className="ai-center-error">{error}</div>}

      <div className="ai-center-status">
        <div>
          <span>Research Floor</span>
          <strong>{running ? statusMessages[messageIndex] : result ? 'Final report issued.' : 'Ready.'}</strong>
        </div>
        <div className="ai-progress-track" aria-label="AI 리서치 진행률">
          <span style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="ai-center-grid">
        <section className="ai-office-floor" aria-label="AI 리서치 부서 현황">
          <div className="ai-office-backdrop">
            <div className="ai-office-board">
              <span>Director Desk</span>
              <strong>{company || 'Company'}</strong>
            </div>

            <div className="ai-department-map">
              {departments.map((department, index) => {
                const state = getDepartmentState(department, index);
                const isActive = state === 'active';
                return (
                  <article
                    className={`ai-dept-node ${state} ${
                      selectedDepartmentKey === department.key ? 'selected' : ''
                    }`}
                    key={department.key}
                    role="button"
                    tabIndex={0}
                    aria-pressed={selectedDepartmentKey === department.key}
                    onClick={() => selectDepartment(department.key)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        selectDepartment(department.key);
                      }
                    }}
                    style={{ '--node-index': index }}
                  >
                    <div className="ai-dept-node__top">
                      <span className="ai-dept-icon">
                        <DepartmentIcon type={department.icon} />
                      </span>
                      <span className="ai-dept-state">{state}</span>
                    </div>

                    <h2>{department.label}</h2>
                    <p>{department.name}</p>

                    <div className="ai-agent-row">
                      <span>J</span>
                      <small>{department.junior}</small>
                    </div>
                    <div className="ai-agent-row senior">
                      <span>S</span>
                      <small>{department.senior}</small>
                    </div>

                    {isActive && (
                      <div className="ai-speech-bubble">
                        {index % 2 === 0 ? department.request : department.response}
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <aside className="ai-communication-panel" aria-label="부서 커뮤니케이션">
          <div className="ai-panel-head">
            <span>Live Communication</span>
            <strong>{result ? 'Completed' : running ? 'In progress' : 'Standby'}</strong>
          </div>

          <div className="ai-flow-list">
            {departments.slice(0, -1).map((department, index) => {
              const nextDepartment = departments[index + 1];
              const state = getDepartmentState(department, index);
              return (
                <div className={`ai-flow-item ${state}`} key={`${department.key}-${nextDepartment.key}`}>
                  <span className="ai-flow-dot" />
                  <div>
                    <strong>{department.label} → {nextDepartment.label}</strong>
                    <p>{department.response}</p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="ai-result-metrics">
            <div>
              <span>Risks</span>
              <strong>{riskCount}</strong>
            </div>
            <div>
              <span>Charts</span>
              <strong>{chartCount}</strong>
            </div>
            <div>
              <span>Tables</span>
              <strong>{tableCount}</strong>
            </div>
          </div>

          <DepartmentOutputPanel
            department={selectedDepartment}
            result={result}
            running={running}
            state={getDepartmentState(
              selectedDepartment,
              departments.findIndex((item) => item.key === selectedDepartment.key)
            )}
          />
        </aside>
      </div>

      <ReportPreview report={report} logs={logs} />
    </section>
  );
}

function DepartmentOutputPanel({ department, result, running, state }) {
  const output = buildDepartmentOutput(department, result);

  return (
    <div className="ai-dept-output">
      <div className="ai-dept-output__head">
        <span>Selected Department Output</span>
        <strong>{department.label}</strong>
      </div>

      <div className={`ai-dept-output__status ${state}`}>
        {running && state === 'active'
          ? 'Processing live request'
          : result
            ? 'Output available'
            : 'Waiting for run'}
      </div>

      <p className="ai-dept-output__summary">{output.summary}</p>

      <div className="ai-dept-output__grid">
        {output.metrics.map((metric) => (
          <div key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </div>
        ))}
      </div>

      <div className="ai-dept-output__list">
        {output.items.map((item) => (
          <div key={item.title} className="ai-dept-output__item">
            <strong>{item.title}</strong>
            <p>{item.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function buildDepartmentOutput(department, result) {
  const report = result?.report?.json_payload;
  const risks = result?.risk_assessments || [];
  const charts = result?.charts || [];
  const tables = result?.tables || [];
  const logs = result?.logs || [];
  const snapshot = report?.financial_snapshot || {};

  if (!result) {
    return {
      summary: department.request,
      metrics: [
        { label: 'Junior', value: department.junior },
        { label: 'Senior', value: department.senior },
      ],
      items: [
        { title: 'Expected request', body: department.request },
        { title: 'Expected response', body: department.response },
      ],
    };
  }

  const baseMetrics = [
    { label: 'Stage', value: result.project?.stage || 'completed' },
    { label: 'Report', value: result.report?.verification_passed ? 'verified' : 'draft' },
  ];

  if (department.key === 'issue') {
    return {
      summary: 'Issue Department가 승인한 핵심 이슈가 최종 보고서의 Key Issues로 전달됐습니다.',
      metrics: [
        { label: 'Issues', value: report?.key_issues?.length || 0 },
        ...baseMetrics,
      ],
      items: (report?.key_issues || []).slice(0, 5).map((issue, index) => ({
        title: `Issue ${index + 1}`,
        body: issue,
      })),
    };
  }

  if (department.key === 'cause') {
    return {
      summary: 'Cause Analysis Dept는 이슈별 영향 metric과 downstream data request를 구성했습니다.',
      metrics: [
        { label: 'Flows', value: 'issue → data' },
        ...baseMetrics,
      ],
      items: [
        { title: 'Request sent', body: '이슈별 affected metric을 Data Research Dept에 전달했습니다.' },
        { title: 'Linked output', body: report?.key_issues?.[0] || department.response },
      ],
    };
  }

  if (department.key === 'data') {
    return {
      summary: 'Data Research Dept가 가격, 재무 evidence와 visualization artifact를 생성했습니다.',
      metrics: [
        { label: 'Charts', value: charts.length },
        { label: 'Tables', value: tables.length },
        { label: 'Raw data', value: 'evidence' },
      ],
      items: [
        ...charts.slice(0, 3).map((chart) => ({
          title: chart.title || chart.chart_id,
          body: `${chart.chart_type || 'chart'} · ${chart.metric || 'metric'} · ${chart.chart_id}`,
        })),
        ...tables.slice(0, 2).map((table) => ({
          title: table.title || table.table_id,
          body: `${table.rows?.length || 0} rows · ${table.columns?.length || 0} columns`,
        })),
      ],
    };
  }

  if (department.key === 'fundamental') {
    return {
      summary: 'Fundamental Research Dept가 수집된 evidence를 매출, 이익, 수익성 snapshot으로 번역했습니다.',
      metrics: [
        { label: 'Revenue', value: formatOutputValue(snapshot.revenue) },
        { label: 'OP', value: formatOutputValue(snapshot.operating_profit) },
        { label: 'ROE', value: formatOutputValue(snapshot.roe) },
      ],
      items: [
        { title: 'Operating margin', body: formatOutputValue(snapshot.operating_margin) },
        { title: 'Debt ratio', body: formatOutputValue(snapshot.debt_ratio) },
      ],
    };
  }

  if (department.key === 'estimate') {
    return {
      summary: 'Estimate Department가 승인 assumption을 기반으로 실적 preview snapshot을 계산했습니다.',
      metrics: [
        { label: 'Period', value: snapshot.period || 'N/A' },
        { label: 'Revenue', value: formatOutputValue(snapshot.revenue) },
        { label: 'EPS', value: formatOutputValue(snapshot.eps) },
      ],
      items: [
        { title: 'Operating profit', body: formatOutputValue(snapshot.operating_profit) },
        { title: 'EPS revision', body: snapshot.eps_revision_pct ?? 'consensus unavailable' },
      ],
    };
  }

  if (department.key === 'risk') {
    return {
      summary: 'Risk Department가 발생 이슈의 리스크, 영향 분석, 펀더멘탈/주가 검증을 수행했습니다.',
      metrics: [
        { label: 'Risks', value: risks.length },
        { label: 'Report risks', value: report?.risks?.length || 0 },
        { label: 'Severity', value: risks[0]?.severity || 'N/A' },
      ],
      items: risks.slice(0, 4).map((risk) => ({
        title: risk.title,
        body: `${risk.risk_type} · ${risk.severity} · ${risk.verification_view}`,
      })),
    };
  }

  if (department.key === 'report') {
    return {
      summary: 'Report Department가 부서별 output을 섹션 draft와 본문 구조로 작성했습니다.',
      metrics: [
        { label: 'Summary', value: report?.investment_summary?.length || 0 },
        { label: 'Points', value: report?.investment_points?.length || 0 },
        { label: 'Risks', value: report?.risks?.length || 0 },
      ],
      items: (report?.investment_summary || []).slice(0, 4).map((item, index) => ({
        title: `Summary ${index + 1}`,
        body: item,
      })),
    };
  }

  if (department.key === 'merge') {
    return {
      summary: 'Merging Department가 승인된 섹션 draft를 프론트 렌더링용 JSON payload로 취합했습니다.',
      metrics: [
        { label: 'Writer', value: result.report?.writer || 'N/A' },
        { label: 'Claims', value: result.report?.claims?.length || 0 },
        { label: 'Sections', value: result.report?.sections?.length || 0 },
      ],
      items: [
        { title: 'Final title', body: report?.title || result.report?.title || 'N/A' },
        { title: 'Payload', body: 'title, financial_snapshot, investment_points, risks, chart_ids, table_ids' },
      ],
    };
  }

  return {
    summary: 'Verification Department가 claim lineage, 숫자 계산, report consistency를 최종 검증했습니다.',
    metrics: [
      { label: 'Verified', value: result.report?.verification_passed ? 'true' : 'false' },
      { label: 'Logs', value: logs.length },
      { label: 'Ready', value: result.project?.report_ready ? 'true' : 'false' },
    ],
    items: logs.slice(-5).map((log, index) => ({
      title: `Check ${index + 1}`,
      body: log,
    })),
  };
}

function formatOutputValue(value) {
  if (value === null || value === undefined || value === '') return 'N/A';
  if (typeof value === 'number') {
    if (Math.abs(value) >= 1_0000_0000_0000) return `${(value / 1_0000_0000_0000).toFixed(1)}조`;
    if (Math.abs(value) >= 1_0000_0000) return `${(value / 1_0000_0000).toFixed(1)}억`;
    if (Math.abs(value) >= 1_0000) return `${value.toLocaleString('ko-KR', { maximumFractionDigits: 1 })}`;
  }
  return String(value);
}

function ReportPreview({ report, logs }) {
  if (!report) {
    return (
      <section className="ai-report-preview empty">
        <span>Final Report</span>
        <h2>리서치 보고서 대기 중</h2>
        <p>최종 검증을 통과하면 이 영역에 보고서가 표시됩니다.</p>
      </section>
    );
  }

  return (
    <section className="ai-report-preview">
      <div className="ai-report-paper">
        <header className="ai-report-header">
          <span>{report.report_type}</span>
          <h2>{report.title}</h2>
          <p>
            {report.company} · {report.ticker || 'N/A'} · {report.market || 'Market'}
          </p>
        </header>

        <article className="ai-report-section">
          <h3>Investment Summary</h3>
          {report.investment_summary?.map((item) => (
            <p key={item}>{item}</p>
          ))}
        </article>

        <article className="ai-report-section">
          <h3>Key Issues</h3>
          <ul>
            {report.key_issues?.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <div className="ai-report-columns">
          <article className="ai-report-section">
            <h3>{report.earnings_outlook?.title || 'Earnings Outlook'}</h3>
            <p>{report.earnings_outlook?.summary}</p>
            <ul>
              {report.earnings_outlook?.bullets?.slice(0, 4).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>

          <article className="ai-report-section">
            <h3>Risks</h3>
            <ul>
              {report.risks?.slice(0, 4).map((risk) => (
                <li key={`${risk.title}-${risk.description}`}>
                  <strong>{risk.title}</strong>
                  <span>{risk.description}</span>
                </li>
              ))}
            </ul>
          </article>
        </div>

        <article className="ai-report-section">
          <h3>{report.conclusion?.title || 'Conclusion'}</h3>
          <p>{report.conclusion?.summary}</p>
        </article>
      </div>

      <aside className="ai-report-log">
        <span>Audit Trail</span>
        {logs.slice(-8).map((log) => (
          <p key={log}>{log}</p>
        ))}
      </aside>
    </section>
  );
}

function DepartmentIcon({ type }) {
  const common = {
    width: 22,
    height: 22,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    'aria-hidden': 'true',
  };

  if (type === 'radar') {
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="8" />
        <path d="M12 4v8l5 3" />
        <path d="M8 12h1" />
        <path d="M15 8h1" />
      </svg>
    );
  }
  if (type === 'network') {
    return (
      <svg {...common}>
        <circle cx="6" cy="7" r="2.5" />
        <circle cx="18" cy="7" r="2.5" />
        <circle cx="12" cy="18" r="2.5" />
        <path d="M8 8l3 7" />
        <path d="M16 8l-3 7" />
        <path d="M8.5 7h7" />
      </svg>
    );
  }
  if (type === 'database') {
    return (
      <svg {...common}>
        <ellipse cx="12" cy="6" rx="7" ry="3" />
        <path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6" />
        <path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" />
      </svg>
    );
  }
  if (type === 'building') {
    return (
      <svg {...common}>
        <path d="M4 20V8l8-4 8 4v12" />
        <path d="M9 20v-6h6v6" />
        <path d="M8 10h.01M12 10h.01M16 10h.01" />
      </svg>
    );
  }
  if (type === 'calculator') {
    return (
      <svg {...common}>
        <rect x="5" y="3" width="14" height="18" rx="3" />
        <path d="M8 7h8" />
        <path d="M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01" />
      </svg>
    );
  }
  if (type === 'shield') {
    return (
      <svg {...common}>
        <path d="M12 3l7 3v5c0 4.5-2.8 8.1-7 10-4.2-1.9-7-5.5-7-10V6z" />
        <path d="M9 12l2 2 4-5" />
      </svg>
    );
  }
  if (type === 'pen') {
    return (
      <svg {...common}>
        <path d="M4 20l4.5-1 10-10a2.1 2.1 0 0 0-3-3l-10 10z" />
        <path d="M13.5 6.5l4 4" />
      </svg>
    );
  }
  if (type === 'merge') {
    return (
      <svg {...common}>
        <path d="M6 4v5a5 5 0 0 0 5 5h7" />
        <path d="M6 20v-5a5 5 0 0 1 5-5h2" />
        <path d="M15 11l3 3-3 3" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}

export default SingleEquityAnalysis;
