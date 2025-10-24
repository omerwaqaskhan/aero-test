-- Create default tenant for LuftWay
INSERT INTO tenants (id, slug, name, status, settings, branding, created_at, updated_at) 
VALUES (
    gen_random_uuid(), 
    'luftway', 
    'LuftWay', 
    'active', 
    '{}', 
    '{}', 
    NOW(), 
    NOW()
) ON CONFLICT (slug) DO NOTHING;
