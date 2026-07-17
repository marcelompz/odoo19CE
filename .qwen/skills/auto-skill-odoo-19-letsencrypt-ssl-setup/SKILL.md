---
name: odoo-19-letsencrypt-ssl-setup
description: Configure Let's Encrypt SSL for Odoo 19 CE behind Traefik v3.3 (exclusive edge proxy)
source: auto-skill
extracted_at: '2026-07-02T21:19:40.779Z'
---

# Let's Encrypt SSL Setup for Odoo 19 CE Behind Traefik v3.3

> **Nota de Arquitectura:** Nginx ha sido completamente eliminado del ecosistema. **Traefik v3.3** es el proxy inverso nativo y gestor SSL exclusivo para Odoo 19 CE y OrderFlow.

## Arquitectura de SSL en Traefik

Traefik v3.3 gestiona automáticamente la generación y renovación de certificados SSL Let's Encrypt para Odoo 19 CE sin necesidad de instaladores certbot en el contenedor ni servidores Nginx.

### Configuración de Enrutamiento Dinámico (`/srv/traefik/dynamic/services.yml`)

```yaml
http:
  routers:
    odoo-prod:
      rule: "Host(`odoo.pesallaccia.com`)"
      priority: 100
      entryPoints: [websecure]
      tls:
        certResolver: letsencrypt
      service: odoo-19-ce
      middlewares: [secure-headers]

  services:
    odoo-19-ce:
      loadBalancer:
        servers:
          - url: "http://odoo_web_8084:8069"
```

### Red Docker

El servicio web de Odoo debe estar conectado a la red externa `traefik-public`:

```yaml
services:
  web8084:
    container_name: odoo_web_8084
    networks:
      - default
      - traefik-public

networks:
  default:
    driver: bridge
  traefik-public:
    external: true
```

### DNS en Cloudflare

El registro DNS en Cloudflare debe configurarse como **DNS Only (Nube Gris ☁️)** para que Traefik gestione directamente el handshake SSL y las conexiones WebSocket de Odoo 19 CE.
