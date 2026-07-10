# Backlog Inicial — Casa Verde

## Fase 1 — Registro manual y base de mercado (Sprint 1-2)

| ID | Tarea | Prioridad | Story Points |
|----|-------|-----------|--------------|
| F1-01 | Scaffold Django + apps modulares | Alta | 3 |
| F1-02 | Modelos: Estado, Municipio, ZonaMercado | Alta | 5 |
| F1-03 | Modelos: ValorMetroCuadrado, FuenteDatos | Alta | 5 |
| F1-04 | Modelo Propiedad + HistorialPrecio | Alta | 8 |
| F1-05 | Usuario personalizado con roles | Alta | 5 |
| F1-06 | Django Admin completo | Alta | 5 |
| F1-07 | Formulario captura manual propiedades | Alta | 8 |
| F1-08 | CRUD valores m² por zona | Alta | 5 |
| F1-09 | Seed data estados/municipios México | Media | 3 |
| F1-10 | Templates base Bootstrap | Alta | 5 |

## Fase 2 — Cálculo automático (Sprint 3-4)

| ID | Tarea | Prioridad | Story Points |
|----|-------|-----------|--------------|
| F2-01 | ValoracionService + fórmulas | Alta | 8 |
| F2-02 | OportunidadService + semáforo | Alta | 8 |
| F2-03 | Modelo AnalisisInversion | Alta | 5 |
| F2-04 | TasaReferenciaBancaria | Alta | 3 |
| F2-05 | Signal post-save Propiedad → análisis | Alta | 5 |
| F2-06 | Ficha técnica de propiedad | Alta | 8 |
| F2-07 | Configuración parámetros usuario | Media | 5 |
| F2-08 | Tests unitarios fórmulas | Alta | 5 |

## Fase 3 — Dashboard (Sprint 5-6)

| ID | Tarea | Prioridad | Story Points |
|----|-------|-----------|--------------|
| F3-01 | Dashboard KPIs | Alta | 8 |
| F3-02 | Gráficas Plotly/Chart.js | Alta | 8 |
| F3-03 | Ranking oportunidades | Alta | 5 |
| F3-04 | Filtros por zona/periodo/semáforo | Media | 5 |
| F3-05 | ComparativoMercado | Media | 5 |

## Fase 4 — Búsqueda automatizada (Sprint 7-9)

| ID | Tarea | Prioridad | Story Points |
|----|-------|-----------|--------------|
| F4-01 | Celery + Redis setup | Alta | 5 |
| F4-02 | ConfiguracionBusqueda + scheduler | Alta | 5 |
| F4-03 | ScrapingService base | Alta | 8 |
| F4-04 | Scraper portales inmobiliarios | Alta | 13 |
| F4-05 | Deduplicación y normalización | Alta | 8 |
| F4-06 | Migración PostgreSQL | Media | 5 |

## Fase 5 — Alertas (Sprint 10)

| ID | Tarea | Prioridad | Story Points |
|----|-------|-----------|--------------|
| F5-01 | Modelo Alerta + AlertaService | Alta | 5 |
| F5-02 | Email SMTP | Alta | 5 |
| F5-03 | Twilio WhatsApp | Media | 8 |
| F5-04 | Notificaciones internas | Media | 5 |

## Fase 6 — Mapas y reportes (Sprint 11-12)

| ID | Tarea | Prioridad | Story Points |
|----|-------|-----------|--------------|
| F6-01 | Google Maps integración | Media | 8 |
| F6-02 | Exportación Excel/CSV | Alta | 5 |
| F6-03 | Exportación PDF | Media | 8 |
| F6-04 | Módulo histórico completo | Alta | 8 |

## Fase 7 — IA predictiva (Sprint 13+)

| ID | Tarea | Prioridad | Story Points |
|----|-------|-----------|--------------|
| F7-01 | Modelo predictivo precios | Baja | 13 |
| F7-02 | Recomendación automática ML | Baja | 13 |
| F7-03 | Detección anomalías de precio | Baja | 8 |

**Total estimado Fases 1-3:** ~120 story points (~6 sprints de 2 semanas)