import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import CatalogPage from "./pages/CatalogPage";
import EstimatePage from "./pages/EstimatePage";
import PriceListPage from "./pages/PriceListPage";
import PriceListsPage from "./pages/PriceListsPage";
import ProjectsPage from "./pages/ProjectsPage";
import SuppliersPage from "./pages/SuppliersPage";

export default function App() {
  return (
    <>
      <nav>
        <NavLink to="/suppliers">Поставщики</NavLink>
        <NavLink to="/price-lists">Прайс-листы</NavLink>
        <NavLink to="/catalog">Каталог</NavLink>
        <NavLink to="/projects">Проекты</NavLink>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Navigate to="/suppliers" replace />} />
          <Route path="/suppliers" element={<SuppliersPage />} />
          <Route path="/price-lists" element={<PriceListsPage />} />
          <Route path="/price-lists/:id" element={<PriceListPage />} />
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/estimates/:id" element={<EstimatePage />} />
        </Routes>
      </main>
    </>
  );
}
