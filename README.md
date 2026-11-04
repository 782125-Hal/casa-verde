# Casa Verde

Plataforma de detección de oportunidades de inversión inmobiliaria.

**Mercados:** Tijuana y Tecate, Baja California (selector de ciudad en dashboard y listado).

Identifica propiedades con precio por debajo del valor de mercado, calcula ROI y clasifica oportunidades con semáforo verde/amarillo/rojo. Incluye un módulo de **presupuestos de obra** que alimenta el ROI con el costo real de remodelación o construcción.

**Producción:** https://max.marhal.com.mx (cPanel + Passenger, Python 3.9). Ver [DEPLOY.md](DEPLOY.md).

## Inicio rápido

```bash
cd ~/Desktop/ProyectosHAL/casa-verde
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # DEBUG=True para desarrollo local
python manage.py migrate
python manage.py seed_datos       # zonas de Tijuana + datos demo; imprime una contraseña aleatoria para `admin`
python manage.py seed_tecate      # zonas de Tecate (opcional)
python manage.py seed_remodelacion  # costos de remodelación por m² y zona
python manage.py seed_catalogo    # catálogo de conceptos para presupuestos
python manage.py runserver
```

- **Acceso:** http://127.0.0.1:8000/login/ — todo el sitio requiere sesión
- **Dashboard:** http://127.0.0.1:8000/
- **Admin:** http://127.0.0.1:8000/admin/

`seed_datos` reutiliza el superusuario existente si ya hay uno. Si tiene que
crear `admin`, genera una contraseña aleatoria y la muestra **una sola vez**;
guárdala. Para fijarla tú: `python manage.py seed_datos --admin-password 'TuClave'`.

### Dependencias

| Archivo | Uso |
|---------|-----|
| `requirements.txt` | Desarrollo local completo (incluye pandas, numpy, plotly, Playwright para scraping) |
| `requirements-prod.txt` | Servidor cPanel: solo lo que el sitio necesita (incluye reportlab y openpyxl para exportar) |

### Antes de desplegar

El hosting cPanel corre **Python 3.9**, y es habitual desarrollar en una versión
más nueva. Sintaxis como `Decimal | None` (3.10+) pasa el `manage.py check` local
y revienta al importar en el servidor, así que hay un comando que la detecta:

```bash
python manage.py check_39     # sale con código 1 si encuentra algo
```

También corre dentro de `manage.py test`, de modo que la suite falla si alguien
introduce sintaxis que el servidor no acepta.

En el servidor, el despliegue se hace con `bash deploy.sh` (instala
dependencias, corre `check_39`, migra y junta estáticos). Detalles en
[DEPLOY.md](DEPLOY.md).

## Estructura

| App | Responsabilidad |
|-----|-----------------|
| `geografia` | Estados, municipios, zonas de mercado |
| `mercado` | Valores m², fuentes, tasas bancarias, costos de remodelación por m² |
| `propiedades` | Propiedades, historial de precios |
| `analisis` | Análisis de inversión, búsqueda semanal |
| `presupuestos` | Presupuestos de obra, control de gastos, órdenes de cambio, exportación PDF/Excel |
| `alertas` | Notificaciones internas, email y Telegram |
| `usuarios` | Roles y parámetros de inversión |
| `core` | Vistas del sitio, login, comando `check_39` |
| `services/` | Valoración, detección de oportunidades, alertas, scraping |

## Documentación

Ver carpeta `docs/` para requerimientos, arquitectura, ER, backlog y cronograma.

## Funciones disponibles

Todas las vistas exigen sesión iniciada; los visitantes anónimos van a `/login/`.

| Módulo | URL | Descripción |
|--------|-----|-------------|
| Acceso | `/login/` | Inicio de sesión (roles no-staff incluidos) |
| Dashboard | `/` | KPIs, gráficas, ranking, filtro por ciudad y zona |
| Propiedades | `/propiedades/` | Listado con filtros + exportar CSV; ficha con estimado rápido de remodelación |
| Presupuestos | `/presupuestos/` | Partidas, gastos reales, órdenes de cambio, exportar PDF/Excel, reporte de cierre |
| Búsqueda | `/busqueda/` | Configurar búsqueda semanal por zona |
| Alertas | `/alertas/` | Notificaciones de oportunidades (email / Telegram) |

El presupuesto activo de una propiedad reemplaza el costo estimado de
remodelación en el ROI y el semáforo. Para terrenos, se puede valuar una
**obra nueva** proyectando la casa terminada (ver DEPLOY.md, "Cómo analizar una
obra nueva").

```bash
# Ejecutar búsqueda semanal (cron o manual)
python manage.py busqueda_semanal
```

El scraping (Lamudi, Propiedades.com, Vivanuncios, Inmuebles24, MercadoLibre)
usa Playwright y corre en local; no opera en el hosting compartido.

## Fases

1. ✅ Registro manual + BD mercado + Admin
2. ✅ Cálculo automático valor/ROI/semáforo
3. ✅ Dashboard + gráficas Chart.js + filtros
4. ✅ Búsqueda semanal + scrapers (Celery/Redis y PostgreSQL pendientes)
5. 🔄 Alertas internas + email + Telegram (WhatsApp pendiente)
6. 🔄 Reportes: CSV de propiedades y PDF/Excel de presupuestos listos (mapas e histórico pendientes)
7. ⏳ IA predictiva

**Módulo de presupuestos:** ✅ completo (captura, impacto en ROI, control de obra, órdenes de cambio, exportación y cierre) + valuación de obra nueva.
