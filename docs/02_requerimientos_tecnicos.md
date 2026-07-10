# Requerimientos Técnicos — Casa Verde

**Versión:** 1.0 | **Fecha:** Junio 2026

---

## 1. Stack tecnológico

| Capa | Tecnología | Fase |
|------|------------|------|
| Backend | Python 3.11+, Django 5+ | 1 |
| Base de datos | SQLite (dev) → PostgreSQL (prod) | 1 → 4 |
| Tareas async | Celery + Redis | 4 |
| Scraping | BeautifulSoup, Scrapy, Playwright | 4 |
| Análisis | Pandas, NumPy | 2 |
| Gráficas | Plotly, Chart.js | 3 |
| Frontend | Django Templates + Bootstrap 5 | 1 |
| Mapas | Google Maps API (opcional) | 6 |
| Alertas | Django Email, Twilio/WhatsApp | 5 |
| Reportes | openpyxl, ReportLab | 6 |

---

## 2. Arquitectura de capas

```
┌─────────────────────────────────────────────┐
│  Presentación (Templates + Bootstrap)       │
├─────────────────────────────────────────────┤
│  Vistas / API REST (Django Views)           │
├─────────────────────────────────────────────┤
│  Servicios de negocio (services/)           │
│  - ValoracionService                        │
│  - OportunidadService                       │
│  - AlertaService                            │
│  - ScrapingService (Fase 4)                 │
├─────────────────────────────────────────────┤
│  Modelos ORM (Django Models)                │
├─────────────────────────────────────────────┤
│  SQLite / PostgreSQL                        │
└─────────────────────────────────────────────┘
```

---

## 3. Requisitos no funcionales

| ID | Requisito | Criterio |
|----|-----------|----------|
| RNF-01 | Disponibilidad | 99% en producción |
| RNF-02 | Tiempo respuesta | < 2s para dashboard |
| RNF-03 | Escalabilidad | Soporte 10K propiedades |
| RNF-04 | Seguridad | Autenticación Django, CSRF, roles |
| RNF-05 | Auditoría | Historial de cambios en precios y estatus |
| RNF-06 | Cumplimiento legal | Respeto ToS de fuentes, GDPR/LFPDPPP |
| RNF-07 | Portabilidad | Exportación CSV/Excel/PDF |
| RNF-08 | Mantenibilidad | Apps modulares, tests unitarios |

---

## 4. Estructura del proyecto

```
Casa Verde/
├── config/              # Settings, URLs, WSGI, Celery
├── core/                # Utilidades, mixins, context processors
├── geografia/           # Estado, Municipio, ZonaMercado
├── mercado/             # ValorMetroCuadrado, TasaReferencia, Comparativo
├── propiedades/         # Propiedad, FuenteDatos, HistorialPrecio
├── analisis/            # AnalisisInversion, ConfiguracionBusqueda
├── alertas/             # Alerta, notificaciones
├── usuarios/            # Usuario personalizado, roles
├── services/            # Lógica de negocio desacoplada
├── templates/           # Templates Django
├── static/              # CSS, JS, imágenes
├── docs/                # Documentación
└── manage.py
```

---

## 5. Integraciones externas (por fase)

| Integración | Fase | Método |
|-------------|------|--------|
| Portales inmobiliarios | 4 | Scraping autorizado / APIs |
| Facebook Marketplace | 4 | API oficial o captura manual |
| Google Maps | 6 | Geocoding API |
| Twilio WhatsApp | 5 | REST API |
| Banxico / tasa referencia | 2 | Captura manual + API futura |
| Email SMTP | 5 | Django send_mail |

---

## 6. Seguridad

- Autenticación con modelo `Usuario` extendido de `AbstractUser`
- Permisos basados en roles (grupos Django)
- Variables sensibles en `.env` (python-decouple)
- Rate limiting en scraping (Fase 4)
- Sanitización de datos de scraping
- No almacenar datos de contacto no públicos

---

## 7. Despliegue

| Entorno | BD | Servidor |
|---------|-----|----------|
| Desarrollo | SQLite | `runserver` |
| Staging | PostgreSQL | Gunicorn + Nginx |
| Producción | PostgreSQL | Gunicorn + Nginx + Celery |

---

## 8. Testing

- `pytest-django` para tests unitarios
- Cobertura mínima 70% en servicios de negocio
- Tests de fórmulas financieras con casos conocidos
- Fixtures para datos de mercado de prueba