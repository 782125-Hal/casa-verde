# Cronograma de Desarrollo — Casa Verde

## Resumen por fases

| Fase | Duración | Entregable principal |
|------|----------|---------------------|
| **Fase 1** | Semanas 1-4 | Registro manual + BD mercado + Admin |
| **Fase 2** | Semanas 5-8 | Valoración automática + ROI + semáforo |
| **Fase 3** | Semanas 9-12 | Dashboard + gráficas + ranking |
| **Fase 4** | Semanas 13-18 | Scraping semanal + Celery |
| **Fase 5** | Semanas 19-20 | Alertas email + WhatsApp |
| **Fase 6** | Semanas 21-24 | Mapas + PDF/Excel + histórico |
| **Fase 7** | Semanas 25+ | IA predictiva |

## Gantt simplificado

```
Semana:  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
Fase 1: [████████████]
Fase 2:             [████████████]
Fase 3:                         [████████████]
Fase 4:                                     [████████████████████]
Fase 5:                                                         [████]
Fase 6:                                                             [████████████]
Fase 7:                                                                         [→]
```

## Hitos

| Hito | Fecha estimada | Criterio de éxito |
|------|----------------|-------------------|
| M1: MVP captura | Semana 4 | Registrar propiedades y valores m² |
| M2: Análisis automático | Semana 8 | ROI y semáforo funcionando |
| M3: Dashboard | Semana 12 | KPIs y gráficas operativos |
| M4: Automatización | Semana 18 | Búsqueda semanal sin intervención |
| M5: Alertas | Semana 20 | Notificaciones email/WhatsApp |
| M6: Producción | Semana 24 | Deploy con reportes y mapas |

## Estado actual (Noviembre 2026)

| Fase / hito | Estado | Notas |
|-------------|--------|-------|
| Fase 1 — M1 | ✅ | Registro manual, BD de mercado, admin |
| Fase 2 — M2 | ✅ | Valoración, ROI y semáforo automáticos |
| Fase 3 — M3 | ✅ | Dashboard, gráficas, ranking, filtros por ciudad/zona |
| Fase 4 — M4 | ✅ parcial | Búsqueda semanal y 5 scrapers (corren en local). Pendiente: Celery/Redis y PostgreSQL |
| Fase 5 — M5 | 🔄 | Alertas internas, email y Telegram listos. Pendiente: WhatsApp (Twilio) |
| Fase 6 — M6 | 🔄 | En producción desde julio 2026 (max.marhal.com.mx). Exportación CSV y PDF/Excel lista. Pendiente: mapas y módulo histórico |
| Fase 7 | ⏳ | IA predictiva sin iniciar |

### Trabajo fuera del plan original

- **Julio 2026:** despliegue en cPanel (Passenger, Python 3.9), soporte multi-ciudad (Tijuana + Tecate).
- **Agosto 2026:** seguridad (login obligatorio, sin contraseñas por defecto, `SECRET_KEY` obligatoria), `deploy.sh`, módulo de **presupuestos de obra** en 5 fases (captura, impacto en ROI, control de obra, órdenes de cambio, exportación PDF/Excel y cierre), valuación de obra nueva y comando `check_39` para compatibilidad con Python 3.9.

### Siguientes pasos

1. Pruebas para `presupuestos` y scrapers (hoy la suite cubre `core` y `analisis`).
2. WhatsApp (F5-03).
3. Mapas (F6-01) y módulo histórico (F6-04).
4. Migración a PostgreSQL (F4-06).