// src/components/Layout.jsx
function Layout({ children }) {
  return (
    <div className="layout">
      <nav className="navbar">
        <img src="/swole_ai_logo_embedded.svg" alt="Swole.ai Logo" className="app-logo" />
        <h1>Swole.ai</h1>
      </nav>

      <main className="main-content">
        {children}
      </main>

      <footer>
        <p>© 2026 Swole.ai</p>
      </footer>
    </div>
  );
}

export default Layout;
