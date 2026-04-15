import { useEffect, useState } from "react";
import { MeResponse } from "../api/auth";
import { getMyProgress, UserProgress } from "../api/analytics";
import { getProfile, Profile } from "../api/profile";
import { myAttempts, AttemptResult } from "../api/assessments";
import DashboardHero from "../components/dashboard/DashboardHero";
import FloatingStatsRow from "../components/dashboard/FloatingStatsRow";
import QuickActionsSection from "../components/dashboard/QuickActionsSection";
import LatestTasksBoard from "../components/dashboard/LatestTasksBoard";

interface Props {
  user: MeResponse;
}

export default function DashboardPage({ user }: Props) {
  const [progress, setProgress] = useState<UserProgress | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [attempts, setAttempts] = useState<AttemptResult[]>([]);
  const [progressLoading, setProgressLoading] = useState(true);

  useEffect(() => {
    getMyProgress()
      .then(setProgress)
      .catch(() => {})
      .finally(() => setProgressLoading(false));
    getProfile()
      .then(setProfile)
      .catch(() => {});
    myAttempts()
      .then(setAttempts)
      .catch(() => {});
  }, []);

  const firstName =
    profile?.first_name?.trim() ??
    user.full_name?.trim().split(/\s+/)[0] ??
    user.email?.split("@")[0] ??
    "Макар";

  return (
    <div className="dashboard-page">
      <DashboardHero firstName={firstName} heroImageSrc="/pictures/professionals-in-modern-office.webp" />
      <FloatingStatsRow progress={progress} loading={progressLoading} />
      <div className="dashboard-bottom-grid">
        <QuickActionsSection />
        <LatestTasksBoard attempts={attempts} loading={progressLoading} />
      </div>
    </div>
  );
}
