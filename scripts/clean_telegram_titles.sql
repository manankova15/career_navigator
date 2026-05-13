-- Clean up Markdown emphasis leftovers in canonical_vacancies.title.
--
-- TG posts often contain "__tldr <title>__" or "**<title>**" markers
-- (Telegram Markdown). The legacy extract_title() preserved underscores
-- because they are part of \w, so the markers survived into the DB.
--
-- This script repeats what _clean_title() does in Python:
--   1. Strip "__<text>__"  →  <text>
--   2. Strip "**<text>**"  →  <text>
--   3. Strip "~~<text>~~"  →  <text>
--   4. Trim leading/trailing underscores, asterisks, dashes, bullets, spaces.
--   5. Drop a leading "tldr" / "tl;dr" word and any punctuation that follows.
--   6. Compact double spaces, so "Senior   Python" → "Senior Python".
--
-- Run inside the vacancy-service DB:
--   psql $DATABASE_URL -f scripts/clean_telegram_titles.sql
-- or:
--   docker exec -i <postgres-container> psql -U <user> -d <vacancy_db> \
--       < scripts/clean_telegram_titles.sql

BEGIN;

-- Step 1-3: strip Markdown emphasis around a substring.
-- We run the same pattern twice to handle nested "__**title**__".
UPDATE canonical_vacancies
   SET title = regexp_replace(title, '\*\*(.+?)\*\*', '\1', 'g')
 WHERE title ~ '\*\*.+?\*\*';

UPDATE canonical_vacancies
   SET title = regexp_replace(title, '__(.+?)__', '\1', 'g')
 WHERE title ~ '__.+?__';

UPDATE canonical_vacancies
   SET title = regexp_replace(title, '\*\*(.+?)\*\*', '\1', 'g')
 WHERE title ~ '\*\*.+?\*\*';

UPDATE canonical_vacancies
   SET title = regexp_replace(title, '__(.+?)__', '\1', 'g')
 WHERE title ~ '__.+?__';

UPDATE canonical_vacancies
   SET title = regexp_replace(title, '~~(.+?)~~', '\1', 'g')
 WHERE title ~ '~~.+?~~';

-- Step 4: trim Markdown / bullet noise at the edges.
UPDATE canonical_vacancies
   SET title = btrim(title, E'_*-—–·•· \t\n\r')
 WHERE title ~ E'^[_*\\-—–·•· \\t]|[_*\\-—–·•· \\t]$';

-- Step 5: drop a leading "tldr" / "tl;dr" word + the punctuation/spaces that follow.
UPDATE canonical_vacancies
   SET title = regexp_replace(title, '^(tldr|tl;dr|tl dr)[\s:_*\-—–·•]*', '', 'gi')
 WHERE title ~* '^(tldr|tl;dr|tl dr)';

-- Step 6: collapse any double whitespace that may have appeared after stripping.
UPDATE canonical_vacancies
   SET title = regexp_replace(title, '\s{2,}', ' ', 'g')
 WHERE title ~ '\s{2,}';

UPDATE canonical_vacancies
   SET title = btrim(title)
 WHERE title <> btrim(title);

COMMIT;
