# Casa Verde

Plataforma de detección de oportunidades de inversión inmobiliaria.

**Mercado inicial:** Tijuana, Baja California.

Identifica propiedades con precio por debajo del valor de mercado, calcula ROI y clasifica oportunidades con semáforo verde/amarillo/rojo.

## Inicio rápido

```bash
cd "Desktop/Casa Verde"
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_datos
python manage.py runserver
```

- **Dashboard:** http://127.0.0.1:8000/
- **Admin:** http://127.0.0.1:8000/admin/ (admin / admin123)

## Estructura

| App | Responsabilidad |
|-----|-----------------|
| `geografia` | Estados, municipios, zonas de mercado |
| `mercado` | Valores m², fuentes, tasas bancarias |
| `propiedades` | Propiedades, historial de precios |
| `analisis` | Análisis de inversión, búsquedas |
| `alertas` | Notificaciones |
| `usuarios` | Roles y parámetros de inversión |
| `services/` | Valoración y detección de oportunidades |

## Documentación

Ver carpeta `docs/` para requerimientos, arquitectura, ER, backlog y cronograma.

## Funciones disponibles

| Módulo | URL | Descripción |
|--------|-----|-------------|
| Dashboard | `/` | KPIs, gráficas, ranking, filtro por zona |
| Propiedades | `/propiedades/` | Listado con filtros + exportar CSV |
| Búsqueda | `/busqueda/` | Configurar búsqueda semanal por zona |
| Alertas | `/alertas/` | Notificaciones de oportunidades |

```bash
# Ejecutar búsqueda semanal (cron o manual)
python manage.py busqueda_semanal
```

## Fases

1. ✅ Registro manual + BD mercado + Admin
2. ✅ Cálculo automático valor/ROI/semáforo
3. ✅ Dashboard + gráficas Chart.js + filtros
4. ✅ Búsqueda semanal + scrapers (Lamudi, Propiedades.com, Vivanuncios, Inmuebles24)
5. 🔄 Alertas internas + email (WhatsApp pendiente)
6. ⏳ Mapas + reportes PDF/Excel
7. ⏳ IA predictiva