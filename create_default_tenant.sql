-- Create default tenant for WindWays
INSERT INTO tenants (id, slug, name, status, settings, branding, created_at, updated_at) 
VALUES (
    gen_random_uuid(), 
    'windways', 
    'WindWays', 
    'active', 
    '{}', 
    '{}', 
    NOW(), 
    NOW()
) ON CONFLICT (slug) DO NOTHING;
