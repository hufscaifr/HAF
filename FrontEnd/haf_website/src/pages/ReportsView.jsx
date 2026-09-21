import mockReports from '../data/mockReports';

function ReportsView() {
  const reportId = new URLSearchParams(window.location.search).get('id');
  const report = mockReports.find((item) => item.id === reportId);

  if (!report) {
    return (
      <section className="report-detail report-detail--empty">
        <p className="page__eyebrow">HAF Research Archive</p>
        <h1>보고서를 찾을 수 없습니다.</h1>
        <a href="/reports">보고서 목록으로 돌아가기</a>
      </section>
    );
  }

  return (
    <main className="report-detail">
      <a className="report-detail__back" href="/reports">← Research Reports</a>
      <header className="report-detail__hero">
        <div>
          <p className="page__eyebrow">{report.category} · Mock Report</p>
          <h1>{report.title}</h1>
          <p className="report-detail__meta">{report.date} · {report.company} · HAF AI Research</p>
        </div>
        <img src={report.thumbnail} alt="" />
      </header>
      <section className="report-detail__body">
        <article>
          <p className="page__eyebrow">Executive Summary</p>
          <h2>핵심 요약</h2>
          <p>{report.summary}</p>
        </article>
        <aside>
          <p className="page__eyebrow">Key Highlights</p>
          <ul>
            {report.highlights.map((highlight) => <li key={highlight}>{highlight}</li>)}
          </ul>
          <p className="report-detail__notice">현재 화면은 API 연동 전 검증을 위한 mock 데이터입니다.</p>
        </aside>
      </section>
    </main>
  );
}

export default ReportsView;
