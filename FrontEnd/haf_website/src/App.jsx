import Footer from './components/Footer';
import Navbar from './components/Navbar';
import EquityResearchLayout from './layouts/EquityResearchLayout';
import AboutUs from './pages/AboutUs';
import Home from './pages/Home';
import JoinUs from './pages/JoinUs';
import Reports from './pages/Reports';
import ReportsView from './pages/ReportsView';
import AiRecommend from './pages/equityResearch/AiRecommend';
import EquityResearchHome from './pages/equityResearch/EquityResearchHome';
import EquityResearchHelp from './pages/equityResearch/Help';
import Indicators from './pages/equityResearch/Indicators';
import NewResearch from './pages/equityResearch/newsResearch/NewResearch';
import NewResearchResult from './pages/equityResearch/newsResearch/NewResearchResult';
import NewResearchResultDetail from './pages/equityResearch/newsResearch/NewResearchResultDetail';
import SectorAnalysis from './pages/equityResearch/SectorAnalysis';
import SingleEquityAnalysis from './pages/equityResearch/SingleEquityAnalysis';

const routes = {
  '/': Home,
  '/about-us': AboutUs,
  '/reports': Reports,
  '/reports-view': ReportsView,
  '/join-us': JoinUs,
  '/equity_research': EquityResearchHome,
  '/equity_research/help': EquityResearchHelp,
  '/equity_research/indicators': Indicators,
  '/equity_research/ai_recommend': AiRecommend,
  '/equity_research/single_equity_analysis': SingleEquityAnalysis,
  '/equity_research/sector_analysis': SectorAnalysis,
  '/equity_research/news_research/new_research': NewResearch,
  '/equity_research/news_research/new_research_result': NewResearchResult,
  '/equity_research/news_research/new_research_result_detail':
    NewResearchResultDetail,
};

function getPageComponent() {
  const normalizedPath = window.location.pathname.replace(/\/$/, '') || '/';
  return routes[normalizedPath] || Home;
}

function App() {
  const pathname = window.location.pathname.replace(/\/$/, '') || '/';
  const isEquityResearchPage = pathname.startsWith('/equity_research');
  const Page = getPageComponent();

  return (
    <div className="app">
      <Navbar />
      <main>
        {isEquityResearchPage ? (
          <EquityResearchLayout>
            <Page />
          </EquityResearchLayout>
        ) : (
          <Page />
        )}
      </main>
      <Footer />
    </div>
  );
}

export default App;
