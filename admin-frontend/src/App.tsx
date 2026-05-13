import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import AssessmentEditorPage from "./pages/AssessmentEditorPage";
import AssessmentsListPage from "./pages/AssessmentsListPage";
import DashboardPage from "./pages/DashboardPage";
import IngestionRunsPage from "./pages/IngestionRunsPage";
import LoginPage from "./pages/LoginPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<DashboardPage />} />
        <Route path="/tests" element={<AssessmentsListPage />} />
        <Route path="/tests/new" element={<AssessmentEditorPage />} />
        <Route path="/tests/:id/edit" element={<AssessmentEditorPage />} />
        <Route path="/ingestion-runs" element={<IngestionRunsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
