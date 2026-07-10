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

## Estado actual (Junio 2026)

- ✅ Documentación completa (RF, RT, ER, arquitectura, backlog)
- ✅ Scaffold Django con apps modulares
- 🔄 Fase 1 en implementación: modelos, admin, servicios base