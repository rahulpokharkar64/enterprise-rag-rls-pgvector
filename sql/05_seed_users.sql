-- 05_seed_users.sql
-- Run as the INGESTION role. Groups, 4 demo identities, memberships. Idempotent.
SET search_path = rag, public;

INSERT INTO rag.groups (group_key, display_name) VALUES
    ('application', 'Application Engineering'),
    ('platform',    'Platform Engineering'),
    ('security',    'Security Engineering'),
    ('shared',      'Shared knowledge')
ON CONFLICT (group_key) DO NOTHING;

INSERT INTO rag.app_users (username, display_name) VALUES
    ('priya', 'Priya'),
    ('arjun', 'Arjun'),
    ('meena', 'Meena'),
    ('divya', 'Divya')
ON CONFLICT (username) DO NOTHING;

-- Membership matrix (every user is also in 'shared')
INSERT INTO rag.user_groups (user_id, group_id)
SELECT u.user_id, g.group_id
FROM (VALUES
    ('priya','application'), ('priya','shared'),
    ('arjun','platform'),    ('arjun','shared'),
    ('meena','security'),    ('meena','shared'),
    ('divya','application'), ('divya','security'), ('divya','shared')
) AS m(username, group_key)
JOIN rag.app_users u ON u.username  = m.username
JOIN rag.groups    g ON g.group_key = m.group_key
ON CONFLICT DO NOTHING;

-- Show result
SELECT u.username, string_agg(g.group_key, ', ' ORDER BY g.group_key) AS groups
FROM rag.app_users u
JOIN rag.user_groups ug USING (user_id)
JOIN rag.groups g USING (group_id)
GROUP BY u.username ORDER BY u.username;
