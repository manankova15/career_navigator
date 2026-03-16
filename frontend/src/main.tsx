import React, { useState } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./index.css";

import { useAuth } from "./hooks/useAuth";
import { MeResponse } from "./api/auth";
import Layout from "./components/Layout";
import Spinner from "./components/Spinner";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import VacanciesPage from "./pages/VacanciesPage";
import VacancyDetailPage from "./pages/VacancyDetailPage";
import RecommendationsPage from "./pages/RecommendationsPage";
import AssessmentsPage from "./pages/AssessmentsPage";
import AssessmentTakePage from "./pages/AssessmentTakePage";
import ProfilePage from "./pages/ProfilePage";

function App() {
  const { user, setUser, logout, loading } = useAuth();

  if (loading) return <Spinner />;

  if (!user) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage onLogin={setUser} />} />
          <Route path="/register" element={<RegisterPage onLogin={setUser} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    );
  }

  return (
    <BrowserRouter>
      <Layout user={user} onLogout={logout}>
        <Routes>
          <Route path="/" element={<DashboardPage user={user} />} />
          <Route path="/vacancies" element={<VacanciesPage />} />
          <Route path="/vacancies/:id" element={<VacancyDetailPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/assessments" element={<AssessmentsPage />} />
          <Route path="/assessments/:id" element={<AssessmentTakePage />} />
          <Route path="/profile" element={<ProfilePage user={user} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
