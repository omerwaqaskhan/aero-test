-- Fix migration state for auth_module
-- This script resets the alembic_version table if it has incorrect entries
-- Run this if you see "Can't locate revision identified by '0002_add_hotel_details_fields'" error

-- For auth_module: Reset to the correct revision (0001)
-- Connect to the auth database and run:
-- DELETE FROM alembic_version WHERE version_num != '0001';
-- Or if the table is empty/corrupted:
-- INSERT INTO alembic_version (version_num) VALUES ('0001') ON CONFLICT DO NOTHING;

-- Note: This should be run manually if needed, as it requires database access
-- The entrypoint.sh already handles migration failures gracefully

