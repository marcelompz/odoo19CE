---
name: Create Odoo Admin User via Direct SQL
description: Create Odoo administrator user by inserting records directly into PostgreSQL database when ORM fails
source: auto-skill
extracted_at: '2026-06-09T14:27:16.285Z'
---

## When to Use

Use this approach when:
- Odoo ORM fails due to custom module errors (e.g., missing fields, broken dependencies)
- You need to create an admin user but cannot use Odoo shell or UI
- You have direct database access via PostgreSQL

## Prerequisites

- SSH access to the server running Odoo
- Docker access to the database container
- Knowledge of the database name (e.g., `prod`)

## Step-by-Step Procedure

### 1. Identify Database Container

```bash
ssh root@<server> "docker ps --filter 'name=odoo' --format '{{.Names}}'"
```

Look for `db_odoo_*` containers. Match to your Odoo instance (e.g., `odoo_web_8081` → `db_odoo_5433`).

### 2. Generate Password Hash

Odoo uses PBKDF2-SHA512. Generate a hash:

```python
import hashlib
import os
import base64

password = 'YourPassword123_'
salt = os.urandom(16)
iterations = 100000

dk = hashlib.pbkdf2_hmac('sha512', password.encode(), salt, iterations, dklen=64)
hash_str = '$pbkdf2-sha512$%d$%s$%s' % (iterations, base64.b64encode(salt).decode(), base64.b64encode(dk).decode())
print(hash_str)
```

### 3. Check Existing IDs

```bash
# Get next partner ID
ssh root@<server> "docker exec db_odoo_XXXX psql -U odoo -d <db> -c \"SELECT MAX(id)+1 FROM res_partner;\""

# Get next user ID  
ssh root@<server> "docker exec db_odoo_XXXX psql -U odoo -d <db> -c \"SELECT MAX(id)+1 FROM res_users;\""

# Get company ID (usually 1)
ssh root@<server> "docker exec db_odoo_XXXX psql -U odoo -d <db> -c \"SELECT id FROM res_company LIMIT 1;\""
```

### 4. Create Partner Record

```bash
ssh root@<server> "docker exec db_odoo_XXXX psql -U odoo -d <db> -c \"
INSERT INTO res_partner (id, name, email, active, lang, tz, type, autopost_bills, company_id, color, commercial_partner_id, create_uid, write_uid, is_company, partner_share, customer_rank, supplier_rank, invoice_warn, picking_warn, sale_warn, purchase_warn) 
VALUES (<partner_id>, 'User Name', 'email@domain.com', true, 'es_PY', 'America/Asuncion', 'contact', 'ask', 1, 0, <partner_id>, 1, 2, false, false, 0, 0, 'no-message', 'no-message', 'no-message', 'no-message') 
RETURNING id;\""
```

### 5. Create User Record

```bash
HASH='$pbkdf2-sha512$...'
ssh root@<server> "docker exec db_odoo_XXXX psql -U odoo -d <db> -c \"
INSERT INTO res_users (id, login, password, partner_id, active, notification_type, company_id) 
VALUES (<user_id>, 'email@domain.com', '$HASH', <partner_id>, true, 'email', 1) 
RETURNING id, login;\""
```

### 6. Grant Admin Privileges

First, find essential group IDs:
- Group 4: Ajustes (Settings)
- Group 7: Características técnicas (Technical Features)
- Group 60: Administrador (Administrator)

```bash
ssh root@<server> "docker exec db_odoo_XXXX psql -U odoo -d <db> -c \"
INSERT INTO res_groups_users_rel (gid, uid) VALUES (4, <user_id>), (7, <user_id>), (60, <user_id>);\""
```

### 7. Verify

```bash
ssh root@<server> "docker exec db_odoo_XXXX psql -U odoo -d <db> -c \"
SELECT u.id, u.login, p.name, g.name->>'es_PY' as group_name 
FROM res_users u 
JOIN res_partner p ON u.partner_id = p.id 
JOIN res_groups_users_rel rel ON u.id = rel.uid 
JOIN res_groups g ON rel.gid = g.id 
WHERE u.id = <user_id> 
ORDER BY g.id;\""
```

## Key Tables

| Table | Purpose |
|-------|---------|
| `res_partner` | Contact/partner information (name, email) |
| `res_users` | User authentication (login, password hash) |
| `res_groups` | Permission groups |
| `res_groups_users_rel` | User-to-group membership (gid, uid) |

## Important Notes

- **Password hash format**: `$pbkdf2-sha512$<iterations>$<base64_salt>$<base64_digest>`
- **Partner first**: Always create `res_partner` before `res_users` (foreign key dependency)
- **Required fields**: Many columns have NOT NULL constraints - copy values from existing users
- **Group 4 + 60**: Minimum for full admin access (Settings + Administrator)
