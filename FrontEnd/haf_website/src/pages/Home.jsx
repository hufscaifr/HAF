import HafActivitiesGrid from '../components/HafActivitiesGrid';
import HafMainBanner from '../components/HafMainBanner';
import HafIntroTitle from '../components/HafIntroTitle';
import chargingBullImage from '../assets/images/main-banner-charging-bull.png';
import nyseFloorImage from '../assets/images/main-banner-nyse-floor.jpeg';
import wallStreetFlagsImage from '../assets/images/main-banner-wall-street-flags.png';
import wallStreetSignImage from '../assets/images/main-banner-wall-street-sign.webp';

function Home() {
  return (
    <>
      <HafIntroTitle />
      <HafMainBanner
        image1={wallStreetSignImage}
        image2={chargingBullImage}
        image3={wallStreetFlagsImage}
        image4={nyseFloorImage}
      />
      <HafActivitiesGrid />
    </>
  );
}

export default Home;
