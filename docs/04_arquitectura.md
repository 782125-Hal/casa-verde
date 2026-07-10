# Arquitectura del Sistema — Casa Verde

## Vista general

```mermaid
flowchart TB
    subgraph Usuarios
        INV[Inversionista]
        ANA[Analista]
        CAP[Capturista]
        ADM[Administrador]
    end

    subgraph Frontend
        WEB[Django Templates + Bootstrap]
        DASH[Dashboard]
        FICHA[Ficha Técnica]
    end

    subgraph Backend
        VIEWS[Django Views]
        SVC_VAL[ValoracionService]
        SVC_OPP[OportunidadService]
        SVC_ALT[AlertaService]
        SVC_SCR[ScrapingService]
    end

    subgraph Datos
        DB[(SQLite/PostgreSQL)]
        CELERY[Celery Worker]
        REDIS[(Redis)]
    end

    subgraph Externos
        PORTALES[Portales Inmobiliarios]
        REDES[Redes Sociales]
        MAPS[Google Maps]
        TWILIO[Twilio/WhatsApp]
        SMTP[Email SMTP]
    end

    Usuarios --> WEB
    WEB --> VIEWS
    VIEWS --> SVC_VAL
    VIEWS --> SVC_OPP
    VIEWS --> SVC_ALT
    SVC_VAL --> DB
    SVC_OPP --> DB
    SVC_ALT --> SMTP
    SVC_ALT --> TWILIO
    CELERY --> SVC_SCR
    SVC_SCR --> PORTALES
    SVC_SCR --> REDES
    SVC_SCR --> DB
    CELERY --> SVC_OPP
    CELERY --> SVC_ALT
    CELERY --> REDIS
```

## Flujo de operación

```mermaid
sequenceDiagram
    participant U as Usuario
    participant S as Sistema
    participant C as Celery
    participant M as Base Mercado
    participant A as Alertas

    U->>S: Configura zona y tipo propiedad
    S->>S: Guarda ConfiguracionBusqueda
    C->>S: Ejecuta búsqueda semanal
    S->>S: Registra Propiedades nuevas
    S->>M: Consulta ValorMetroCuadrado
    S->>S: Calcula valor estimado
    S->>S: Calcula ROI y semáforo
    alt Es oportunidad
        S->>A: Genera alerta
        A->>U: Email/WhatsApp/Notificación
    end
    U->>S: Revisa ficha técnica
    U->>S: Descarta / Negocia / Seguimiento
```

## Patrones de diseño aplicados

| Patrón | Uso |
|--------|-----|
| Service Layer | Lógica de valoración y oportunidades en `services/` |
| Repository (ORM) | Django Models como capa de datos |
| Strategy | Diferentes scrapers por fuente (Fase 4) |
| Observer | Alertas al detectar oportunidades |
| Factory | Creación de análisis desde propiedad |

## Despliegue por fases

| Fase | Componentes activos |
|------|---------------------|
| 1 | Django + SQLite + Admin + Captura manual |
| 2 | + ValoracionService + AnalisisInversion |
| 3 | + Dashboard + Plotly/Chart.js |
| 4 | + Celery + Scrapers |
| 5 | + Email + Twilio |
| 6 | + Maps + PDF/Excel + Histórico |
| 7 | + ML predictivo |