import EquityResearchQuickMenu from '../components/EquityResearchQuickMenu';

function EquityResearchLayout({ children }) {
  return (
    <div className="equity-research-layout">
      <div className="equity-research-layout__menu">
        <EquityResearchQuickMenu />
      </div>
      {children}
    </div>
  );
}

export default EquityResearchLayout;
