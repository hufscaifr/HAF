import { useEffect, useState } from 'react';
import { API_HEADERS, apiUrl } from '../config/api';

function ReportsView() {
  const reportId = new URLSearchParams(window.location.search).get('id');
  const isMockReport = reportId?.startsWith('mock-');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [chatting, setChatting] = useState(false);
  const [chatError, setChatError] = useState('');

  useEffect(() => {
    if (!reportId) {
      setLoading(false);
      return;
    }
    const detailPath = isMockReport ? '/api/report-archive' : '/api/reports';
    fetch(apiUrl(`${detailPath}/${encodeURIComponent(reportId)}`), { headers: API_HEADERS })
      .then((response) => {
        if (!response.ok) throw new Error('Report not found.');
        return response.json();
      })
      .then((payload) => setReport(payload.report))
      .catch(() => setReport(null))
      .finally(() => setLoading(false));
  }, [reportId, isMockReport]);

  const askReport = async (event) => {
    event.preventDefault();
    const normalizedQuestion = question.trim();
    if (normalizedQuestion.length < 2 || chatting) return;
    setChatting(true);
    setChatError('');
    try {
      const chatPath = isMockReport ? '/api/report-archive' : '/api/reports';
      const response = await fetch(apiUrl(`${chatPath}/${encodeURIComponent(reportId)}/chat`), {
        method: 'POST',
        headers: { ...API_HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: normalizedQuestion }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || '답변을 생성하지 못했습니다.');
      setAnswer(payload.answer);
    } catch (requestError) {
      setChatError(requestError.message);
    } finally {
      setChatting(false);
    }
  };

  if (loading) {
    return <section className="report-detail report-detail--empty"><p>보고서를 불러오는 중입니다.</p></section>;
  }

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
          <p className="page__eyebrow">{report.category || 'HAF'} · {report.is_mock ? 'Mock 데이터' : 'Research Report'}</p>
          <h1>{report.title}</h1>
          <p className="report-detail__meta">{report.date} · {report.company || 'HAF'} · HAF AI Research</p>
        </div>
        <div className="report-detail__cover" aria-hidden="true"><span>HAF</span><strong>RESEARCH REPORT</strong></div>
      </header>
      <section className="report-detail__body">
        <article>
          <p className="page__eyebrow">Executive Summary</p>
          <h2>핵심 요약</h2>
          <p>{report.summary || report.desc || '이 보고서는 PDF 원문으로 제공됩니다.'}</p>
          {report.content && <div className="report-detail__content">{report.content}</div>}
          {report.s3_key && <a className="report-detail__download" href={apiUrl(`/api/reports/${encodeURIComponent(reportId)}/download`)} target="_blank" rel="noreferrer">PDF 보고서 열기</a>}
        </article>
        <aside>
          <p className="page__eyebrow">Key Highlights</p>
          <ul>
            {(report.highlights || []).map((highlight) => <li key={highlight}>{highlight}</li>)}
          </ul>
          {report.is_mock && <p className="report-detail__notice">PostgreSQL에 저장된 기능 검증용 mock 데이터입니다.</p>}
          {!report.is_mock && !report.content && <p className="report-detail__notice">이전 업로드 보고서는 본문 데이터가 없어 PDF만 열 수 있습니다. 새 보고서부터 본문 기반 대화가 지원됩니다.</p>}
          <div className="report-chat">
            <p className="page__eyebrow">Ask this report · Qwen</p>
            <form onSubmit={askReport}>
              <textarea value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={500} placeholder="이 보고서에서 중요한 투자 위험은 뭐야?" rows={3} />
              <button type="submit" disabled={chatting || question.trim().length < 2}>
                {chatting ? '답변 생성 중…' : '보고서에 질문하기'}
              </button>
            </form>
            {chatError && <p className="report-chat__error" role="alert">{chatError}</p>}
            {answer && <div className="report-chat__answer">{answer}</div>}
          </div>
        </aside>
      </section>
    </main>
  );
}

export default ReportsView;
