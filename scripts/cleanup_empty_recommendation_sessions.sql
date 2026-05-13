-- ============================================================================
-- One-shot cleanup of empty recommendation sessions.
--
-- These sessions are produced when the scheduled refresh job runs while
-- ml-service or vacancy-service is unavailable / returns no candidates.
-- They look like rows with total_scored = 0 and have no joined items in
-- vacancy_recommendations. Their mere existence shadows older, useful
-- sessions for the same user, so GET /recommendations/me returns 200 with
-- items=[] and the frontend shows "Рекомендации пока не готовы".
--
-- After this script runs:
--   • the next GET /recommendations/me with no remaining sessions for the
--     user will return 404
--   • the frontend's refresh-on-404 logic posts /recommendations/refresh,
--     which now (post-fix) refuses to persist an empty session and instead
--     surfaces the upstream error to the caller.
--
-- Run from host shell:
--   podman exec -i -e PGPASSWORD=secret123 career_nagigator_postgres_1 \
--       psql -U career_navigator -d career_navigator \
--       < career_nagigator/scripts/cleanup_empty_recommendation_sessions.sql
-- ============================================================================

BEGIN;

-- Preview: how many empty sessions and their owners
SELECT
    'before' AS phase,
    COUNT(*) AS empty_sessions,
    COUNT(DISTINCT user_id) AS affected_users
FROM recommendation_sessions
WHERE total_scored = 0
   OR id NOT IN (SELECT DISTINCT session_id FROM vacancy_recommendations);

-- Delete dependent skill-gap rows (FK on session_id)
DELETE FROM skill_gap_reports
WHERE session_id IN (
    SELECT id FROM recommendation_sessions
    WHERE total_scored = 0
       OR id NOT IN (SELECT DISTINCT session_id FROM vacancy_recommendations)
);

-- Delete dependent vacancy_recommendations rows (defensive; should be 0 for
-- empty sessions but covers half-written sessions too)
DELETE FROM vacancy_recommendations
WHERE session_id IN (
    SELECT id FROM recommendation_sessions
    WHERE total_scored = 0
       OR id NOT IN (SELECT DISTINCT session_id FROM vacancy_recommendations)
);

-- Finally remove the sessions themselves
DELETE FROM recommendation_sessions
WHERE total_scored = 0
   OR id NOT IN (SELECT DISTINCT session_id FROM vacancy_recommendations);

SELECT
    'after' AS phase,
    COUNT(*) AS remaining_sessions,
    COUNT(DISTINCT user_id) AS users_with_recommendations
FROM recommendation_sessions;

COMMIT;
