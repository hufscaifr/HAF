import { useEffect, useState } from 'react';
import logo from '../assets/images/logo.png';

function Navbar() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setMounted(true);
    }, 120);

    return () => clearTimeout(timer);
  }, []);

  const menus = [
    {
      label: 'HOME',
      href: '/',
      external: false,
    },
    {
      label: 'ABOUT US',
      href: '/about-us',
      external: false,
    },
    {
      label: 'REPORTS',
      href: '/reports',
      external: false,
    },
    {
      label: 'Equity Research',
      href: 'https://caifr.framer.website/',
      external: true,
    },
    {
      label: 'JOIN US',
      href: '/join-us',
      external: false,
    },
  ];

  return (
    <header className="haf-navigation">
      <div className="haf-nav-inner">
        <a className={`haf-logo-link ${mounted ? 'visible' : ''}`} href="/">
          <img className="haf-logo" src={logo} alt="HAF" />
        </a>

        <div className={`haf-menu-reveal ${mounted ? 'visible' : ''}`}>
          <nav className="haf-menu" aria-label="Primary navigation">
            {menus.map((menu) => (
              <a
                key={menu.label}
                href={menu.href}
                className="haf-menu-link"
                target={menu.external ? '_blank' : '_self'}
                rel={menu.external ? 'noopener noreferrer' : undefined}
              >
                {menu.label}
              </a>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
