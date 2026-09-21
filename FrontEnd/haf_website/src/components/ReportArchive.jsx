import { useState } from 'react';
import mockReports from '../data/mockReports';

function ReportArchive({ sectionTitle = 'Research Reports' }) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 9;
  const totalPages = Math.ceil(mockReports.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentReports = mockReports.slice(startIndex, startIndex + itemsPerPage);

  return (
    <section className="caifr-video-archive">
      <div className="caifr-inner">
        <div className="caifr-title-wrap">
          <p className="caifr-eyebrow">HAF Research Archive · Mock Data</p>
          <h1 className="caifr-title">{sectionTitle}</h1>
        </div>
        <div className="caifr-grid">
          {currentReports.map((report) => (
            <a key={report.id} className="caifr-card" href={`/reports-view?id=${report.id}`}>
              <div className="caifr-thumbnail-wrap">
                <img className="caifr-thumbnail" src={report.thumbnail} alt="" loading="lazy" />
                <div className="caifr-play" />
              </div>
              <div className="caifr-content">
                <div className="caifr-date">{report.date} · {report.category}</div>
                <h2 className="caifr-video-title">{report.title}</h2>
                <p className="caifr-desc">{report.desc}</p>
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
