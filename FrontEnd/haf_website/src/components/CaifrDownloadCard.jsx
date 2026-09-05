import CopyEmailButton from './CopyEmailButton';

function CaifrDownloadCard({
  sectionTitle = 'APPLICATION',
  title = 'CAIFR 신입 학회원 지원서 양식',
  fileName = '[CAIFR] 지원서_양식_기수_이름.docx',
  fileUrl = 'https://docs.google.com/document/d/1oyoXF-rxGmYuEj3jCUp5G4-TgzT9H6qAySXaf3Vdjjg/export?format=docx',
  buttonText = '양식 다운로드',
}) {
  return (
    <section className="caifr-download">
      <div className="caifr-download__inner">
        <div className="caifr-download__title-section">
          <h2 className="caifr-download__title">{sectionTitle}</h2>
          <div className="caifr-download__underline" />
        </div>

        <div className="caifr-download__card" id="application">
          <div className="caifr-download__left">
            <div className="caifr-download__icon" aria-hidden="true">
              📋
            </div>

            <div className="caifr-download__text">
              <h3 className="caifr-download__card-title">{title}</h3>
              <p className="caifr-download__file-name">{fileName}</p>
            </div>
          </div>

          <a href={fileUrl} download className="caifr-download__button">
            {buttonText}
          </a>
        </div>

        <div className="caifr-download__email">
          <p className="caifr-download__email-text">
            지원서를 작성하여 아래 이메일로 보내주세요
          </p>
          <CopyEmailButton />
        </div>
      </div>
    </section>
  );
}

export default CaifrDownloadCard;
