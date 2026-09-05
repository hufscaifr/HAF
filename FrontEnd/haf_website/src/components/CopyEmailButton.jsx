import { useState } from 'react';

function CopyEmailButton() {
  const email = 'hufscaifr@gmail.com';
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(email);
      setCopied(true);

      window.setTimeout(() => {
        setCopied(false);
      }, 1800);
    } catch (error) {
      console.error('이메일 복사 실패:', error);
    }
  };

  return (
    <button
      className={`copy-email-button ${copied ? 'copied' : ''}`}
      onClick={handleCopy}
      aria-label="이메일 주소 복사"
      type="button"
    >
      <span className="copy-email-button__icon">{copied ? '✓' : '⧉'}</span>
      <span>{copied ? '이메일 복사 완료' : email}</span>
    </button>
  );
}

export default CopyEmailButton;
