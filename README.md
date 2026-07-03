# Odoo 19 CE - Provecchio Deployment

[![Status](https://img.shields.io/badge/status-production-green)](https://github.com/marcelompz/odoo19CE)
[![Odoo Version](https://img.shields.io/badge/Odoo-19.0-blue)](https://www.odoo.com)
[![License](https://img.shields.io/badge/License-LGPL--3-blue)](LICENSE)

**Odoo 19 CE deployment for Provecchio (Paraguay) with full localization support.**

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- SSH key added to [GitHub](https://github.com/settings/keys)
- Access to `dimoraserverlocal` (Hetzner Cloud)

### Automatic Installation

```bash
# 1. Connect to server
ssh dimoraserverlocal

# 2. Clone and setup l10n_py modules (HOST)
cd /srv/odoo8083
bash setup_l10n_py.sh

# 3. Start Docker containers
docker compose up -d

# 4. Wait ~3 minutes for initialization
docker logs -f odoo_init_db
```

### Access

- **URL:** http://dimora.provecchio.com:8083
- **Database:** `prod`
- **Email:** `soporte@crossnexion.com`
- **Password:** `Cross1983_`

## 📁 Project Structure

```
/opt/odoo/odoo8083/
├── docker-compose.yml       # Docker configuration
├── .env                     # Environment variables
├── config/
│   └── odoo.conf           # Odoo configuration
├── addons/                  # Custom addons (git submodule)
├── init_prod_db.sh         # Database initialization script
└── setup_l10n_py.sh        # l10n_py modules setup (HOST)
```

### Multi-Repository Architecture

| Repository | Purpose | Path |
|------------|---------|------|
| **odoo19CE** | Main project | `/srv/odoo8083/` |
| **odoo-l10n-py** | Paraguay localization | `/srv/odoo-modules/l10n_py/` |
| **odoo-addons** | Custom addons | `./addons/` (submodule) |

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Database
DB_HOST=db
DB_PORT=5432
DB_USER=odoo
DB_PASSWORD=crossdimora.159753

# Odoo
ODOO_ADMIN_PASSWD=soportecrossdimora.159753
ODOO_DB_FILTER=^prod$

# System
TZ=America/Asuncion
```

### Odoo Configuration (config/odoo.conf)

```ini
[options]
addons_path = /mnt/extra-addons,/mnt/extra-addons-l10n,/usr/lib/python3/dist-packages/odoo/addons
admin_passwd = soportecrossdimora.159753
db_host = db
db_port = 5432
db_user = odoo
db_password = crossdimora.159753
dbfilter = ^prod$
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 100
limit_time_cpu = 600
limit_time_real = 1200
proxy_mode = True
```

### Docker Compose Services

| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| `web` | odoo:19.0 | 8083:8069, 8072:8072 | Odoo application |
| `db` | postgres:15 | 5434:5432 | PostgreSQL database |
| `init` | odoo:19.0 | - | One-time initialization |

## 🇵🇾 Paraguay Localization

### Installed Modules

1. **l10n_py** - Base Paraguay localization
   - Chart of accounts
   - Taxes configuration
   - Currency (PYG - Guaraní)
   - Departments and cities

2. **electronic_invoice_cross** - Electronic invoicing
   - RUC validation
   - Electronic documents (DNFE)
   - Requires: `tu-ruc-python-client`

3. **pos_einvoice_cross** - POS with electronic invoicing
   - POS integration
   - Real-time RUC lookup
   - Requires: `tu-ruc-python-client`

### Odoo 19 Specific Changes

- **Fiscal Package Visibility:** Added `name` and `visible: True` attributes to `_get_py_template_data` method
- **Tax Loading Fix:** Removed obsolete `chart_template_id` column from `account.tax-py.csv`
- **Template Naming Convention:** Strict CSV naming with `-py.csv` suffix for country-specific templates
- **Module Version:** Updated to `19.0.1.0.1` for Odoo 19 compatibility

### Dependencies

```bash
# Installed automatically in containers
pip install tu-ruc-python-client
pip install dnspython  # Required for de_send_email_cross
```

## 🔧 Maintenance

### Update Modules

```bash
# Update l10n_py modules
cd /srv/odoo-modules/l10n_py
git pull origin main

# Restart containers
cd /srv/odoo8083
docker compose restart
```

### View Logs

```bash
# All containers
docker compose logs -f

# Specific service
docker logs -f odoo_web_8083
docker logs -f odoo_init_db
```

### Database Backup

```bash
# Backup PostgreSQL
docker exec db_odoo_5434 pg_dump -U odoo prod > backup_prod_$(date +%Y%m%d).sql
```

### Reset Installation

```bash
# Complete reset
cd /srv/odoo8083
docker compose down -v
rm -rf /srv/odoo-modules/l10n_py

# Reinstall
bash setup_l10n_py.sh
docker compose up -d
```

## 🏗️ Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Hetzner Cloud                        │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              dimoraserverlocal                   │   │
│  │                                                  │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │         Docker Containers                 │   │   │
│  │  │  ┌─────────┐  ┌─────────┐  ┌──────────┐  │   │   │
│  │  │  │  odoo   │  │   db    │  │   init   │  │   │   │
│  │  │  │ :8069   │  │ :5432   │  │ (one-    │  │   │   │
│  │  │  └────┬────┘  └────┬────┘  │  time)   │  │   │   │
│  │  │       │            │        └──────────┘  │   │   │
│  │  │       └────────────┘                       │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  │                                                  │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │         Host Volumes                     │   │   │
│  │  │  /srv/odoo8083/       (project files)    │   │   │
│  │  │  /srv/odoo-modules/   (l10n_py modules)  │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Public Access: dimora.provecchio.com:8083             │
└─────────────────────────────────────────────────────────┘
```

## 📝 Development Workflow

### Local Development

```bash
# Clone repository
git clone git@github.com:marcelompz/odoo19CE.git
cd odoo19CE

# Initialize submodules
git submodule update --init --recursive

# Run locally
docker compose up -d
```

### Making Changes

1. **Custom addons:** Modify in `./addons/` (submodule)
2. **l10n_py modules:** Update in `github.com/marcelompz/odoo-l10n-py`
3. **Configuration:** Edit `docker-compose.yml`, `.env`, or `config/odoo.conf`

### Commit and Push

```bash
# Main project
git add .
git commit -m "feat: your change"
git push origin main

# Submodules
cd addons
git add .
git commit -m "feat: addon change"
git push origin main
```

## 🔐 Security Notes

- **SSH Key:** Required for cloning `odoo-l10n-py` on server
- **Database Password:** Change `crossdimora.159753` in production
- **Admin Password:** Change `soportecrossdimora.159753` after first login
- **Firewall:** Only ports 8083 and 5434 exposed

## 📄 License

LGPL-3 - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**Maintained by:** [marcelompz](https://github.com/marcelompz)  
**Last Updated:** 2026-07-03
