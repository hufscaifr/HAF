const menuItems = [
  {
    id: 1,
    label: 'Home',
    href: '/equity_research',
    icon: HomeIcon,
  },
  {
    id: 2,
    label: '기업 분석',
    href: '/equity_research/single_equity_analysis',
    icon: CompanyIcon,
  },
  {
    id: 3,
    label: '섹터 분석',
    href: '/equity_research/sector_analysis',
    icon: SectorIcon,
  },
  {
    id: 4,
    label: '뉴스 기업 분석',
    href: '/equity_research/news_research/new_research',
    icon: NewsIcon,
  },
  {
    id: 5,
    label: '기술적 분석 도움말',
    href: '/equity_research/help',
    icon: BookIcon,
  },
  {
    id: 6,
    label: '지표 설명',
    href: '/equity_research/indicators',
    icon: HelpIcon,
  },
  {
    id: 7,
    label: 'AI 추천 기업',
    href: '/equity_research/ai_recommend',
    icon: AiIcon,
  },
];

function BaseIcon({ children, size = 20, strokeWidth = 1.8 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  );
}

function HomeIcon(props) {
  return (
    <BaseIcon {...props}>
      <path d="M3 11.5L12 4l9 7.5" />
      <path d="M5.5 10.5V20h13v-9.5" />
      <path d="M9.5 20v-6h5v6" />
    </BaseIcon>
  );
}

function CompanyIcon(props) {
  return (
    <BaseIcon {...props}>
      <path d="M4 20V9h7v11" />
      <path d="M11 20V4h9v16" />
      <path d="M2 20h20" />
      <path d="M7 12h1" />
      <path d="M7 15h1" />
      <path d="M14 8h2" />
      <path d="M14 12h2" />
      <path d="M14 16h2" />
    </BaseIcon>
  );
}

function SectorIcon(props) {
  return (
    <BaseIcon {...props}>
      <path d="M3 20h18" />
      <path d="M5 20v-8l5-3v11" />
      <path d="M10 20V5l5-2v17" />
      <path d="M15 20v-6h4v6" />
    </BaseIcon>
  );
}

function NewsIcon(props) {
  return (
    <BaseIcon {...props}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M7 9h5" />
      <path d="M7 13h3" />
      <path d="M14 10h3" />
      <path d="M14 14h3" />
      <path d="M7 16h4" />
    </BaseIcon>
  );
}

function BookIcon(props) {
  return (
    <BaseIcon {...props}>
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5z" />
      <path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5z" />
    </BaseIcon>
  );
}

function HelpIcon(props) {
  return (
    <BaseIcon {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.8 9a2.4 2.4 0 1 1 3.8 2c-.9.6-1.6 1.1-1.6 2.3" />
      <path d="M12 17h.01" />
    </BaseIcon>
  );
}

function AiIcon(props) {
  return (
    <BaseIcon {...props}>
      <path d="M12 3l1.3 3.7L17 8l-3.7 1.3L12 13l-1.3-3.7L7 8l3.7-1.3z" />
      <path d="M18.5 13l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z" />
      <path d="M6 15l.7 1.8 1.8.7-1.8.7L6 20l-.7-1.8-1.8-.7 1.8-.7z" />
    </BaseIcon>
  );
}

function getActiveMenu(pathname) {
  if (pathname === '/equity_research') return 1;
  if (pathname.startsWith('/equity_research/single_equity_analysis')) return 2;
  if (pathname.startsWith('/equity_research/sector_analysis')) return 3;
  if (pathname.startsWith('/equity_research/news_research')) return 4;
  if (pathname.startsWith('/equity_research/help')) return 5;
  if (pathname.startsWith('/equity_research/indicators')) return 6;
  if (pathname.startsWith('/equity_research/ai_recommend')) return 7;
  return 1;
}

function EquityResearchQuickMenu({ compact = false }) {
  const pathname = window.location.pathname.replace(/\/$/, '') || '/';
  const activeMenu = getActiveMenu(pathname);

  return (
    <div className="equity-quick-menu">
      <div className="equity-quick-menu__scroll">
        <nav className="equity-quick-menu__nav" aria-label="투자 분석 메뉴">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeMenu === item.id;

            return (
              <a
                key={item.id}
                href={item.href}
                className={`equity-quick-menu__item ${
                  isActive ? 'active' : ''
                } ${compact ? 'compact' : ''}`}
                aria-current={isActive ? 'page' : undefined}
              >
                <span className="equity-quick-menu__icon">
                  <Icon size={18} strokeWidth={1.8} />
                </span>

                {!compact && (
                  <span className="equity-quick-menu__label-wrap">
                    <span className="equity-quick-menu__number">
                      {String(item.id).padStart(2, '0')}
                    </span>
                    <span className="equity-quick-menu__label">
                      {item.label}
                    </span>
                  </span>
                )}

                {isActive && <span className="equity-quick-menu__indicator" />}
              </a>
            );
          })}
        </nav>
      </div>
    </div>
  );
}

export default EquityResearchQuickMenu;
