import { useEffect, useState } from 'react';
import { API_HEADERS, apiUrl } from '../config/api';

function ReportArchive({ sectionTitle = 'Research Reports' }) {
  const [currentPage, setCurrentPage] = useState(1);
  const [reports, setReports] = useState([]);
  const [error, setError] = useState('');
  const itemsPerPage = 9;
  const totalPages = Math.ceil(reports.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentReports = reports.slice(startIndex, startIndex + itemsPerPage);

  useEffect(() => {
    fetch(apiUrl('/api/reports?limit=100'), { headers: API_HEADERS })
      .then((response) => {
        if (!response.ok) throw new Error('보고서 데이터를 불러오지 못했습니다.');
        return response.json();
      })
      .then((payload) => setReports((payload.reports || []).filter((report) => report.s3_key || report.content)))
      .catch((requestError) => setError(requestError.message));
  }, []);

  return (
    <section className="caifr-video-archive">
      <div className="caifr-inner">
        <div className="caifr-title-wrap">
          <p className="caifr-eyebrow">HAF Research Archive · Database</p>
          <h1 className="caifr-title">{sectionTitle}</h1>
        </div>
        {error && <p role="alert">{error}</p>}
        <div className="caifr-grid">
          {currentReports.map((report) => (
            <a key={report.id} className="caifr-card" href={`/reports-view?id=${report.id}`}>
              <div className="caifr-thumbnail-wrap">
                {report.thumbnail ? (
                  <img className="caifr-thumbnail" src={report.thumbnail} alt="" loading="lazy" />
                ) : (
                  <div className="caifr-report-cover" aria-hidden="true">
                    <span>HAF</span>
                    <strong>RESEARCH REPORT</strong>
                  </div>
                )}
                <div className="caifr-play caifr-play--document" />
              </div>
              <div className="caifr-content">
                <div className="caifr-date">{report.date} · {report.category || 'Research'}</div>
                <h2 className="caifr-video-title">{report.title}</h2>
                <p className="caifr-desc">{report.desc || report.company || 'HAF AI Research 보고서'}</p>
              </div>
            </a>
          ))}
        </div>
        {totalPages > 1 && (
          <div className="caifr-pagination">
            {Array.from({ length: totalPages }, (_, index) => {
              const page = index + 1;
              return <button key={page} type="button" className={`caifr-page-button ${currentPage === page ? 'active' : ''}`} onClick={() => setCurrentPage(page)} aria-current={currentPage === page ? 'page' : undefined}>{page}</button>;
            })}
          </div>
        )}
      </div>
    </section>
  );
}

export default ReportArchive;
