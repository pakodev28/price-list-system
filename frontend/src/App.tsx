import type { ReactNode } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import CatalogPage from "./pages/CatalogPage";
import EstimatePage from "./pages/EstimatePage";
import PriceListPage from "./pages/PriceListPage";
import PriceListsPage from "./pages/PriceListsPage";
import ProjectsPage from "./pages/ProjectsPage";
import SuppliersPage from "./pages/SuppliersPage";

const ICONS: Record<string, ReactNode> = {
  suppliers: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  prices: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  ),
  catalog: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
    </svg>
  ),
  projects: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  ),
  logo: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 2 7 12 12 22 7 12 2" />
      <polyline points="2 17 12 22 22 17" />
      <polyline points="2 12 12 17 22 12" />
    </svg>
  ),
};

const NAV = [
  { to: "/suppliers", label: "Поставщики", icon: ICONS.suppliers },
  { to: "/price-lists", label: "Прайс-листы", icon: ICONS.prices },
  { to: "/catalog", label: "Каталог", icon: ICONS.catalog },
  { to: "/projects", label: "Проекты", icon: ICONS.projects },
];

export default function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="logo">{ICONS.logo}</span>
          <span>Прайс-система</span>
        </div>
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </aside>
      <main className="main">
        <div className="content">
          <Routes>
            <Route path="/" element={<Navigate to="/suppliers" replace />} />
            <Route path="/suppliers" element={<SuppliersPage />} />
            <Route path="/price-lists" element={<PriceListsPage />} />
            <Route path="/price-lists/:id" element={<PriceListPage />} />
            <Route path="/catalog" element={<CatalogPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/estimates/:id" element={<EstimatePage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
