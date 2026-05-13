-- ============================================================================
-- Force re-refresh of every user's recommendations.
--
-- Deletes ALL recommendation sessions (and their items / skill-gaps), so the
-- next GET /recommendations/me returns 404 → frontend automatically issues
-- POST /recommendations/refresh → orchestrator runs the *fixed* scoring
-- pipeline with anti-saturation soft-cap.
--
-- Use after deploying:
--   • services/ml-service/app/scoring.py        (soft tanh squash >0.80)
--   • services/recommendation-service/app/personalization.py (mirror cap)
--   • services/ml-service/app/config.py         (top_n=200, max_candidates=1000)
--   • services/recommendation-service/app/config.py (top_n_store=150,
--                                                    vacancy_fetch_limit=1000)
--
-- Run:
--   podman exec -i -e PGPASSWORD=secret123 career_nagigator_postgres_1 \
--       psql -U career_navigator -d career_navigator \
--       < career_nagigator/scripts/force_rerefresh_all_sessions.sql
-- ============================================================================

BEGIN;

SELECT 'before' AS phase,
       COUNT(*)            AS sessions,
       COUNT(DISTINCT user_id) AS users
FROM recommendation_sessions;

DELETE FROM skill_gap_reports;
DELETE FROM vacancy_recommendations;
DELETE FROM recommendation_sessions;

SELECT 'after' AS phase,
       COUNT(*) AS sessions
FROM recommendation_sessions;

COMMIT;
