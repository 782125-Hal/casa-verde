# Casos de Uso — Casa Verde

## CU-01: Configurar búsqueda geográfica

| Campo | Valor |
|-------|-------|
| Actor | Inversionista, Analista |
| Precondición | Usuario autenticado |
| Flujo principal | 1. Selecciona estado → municipio → colonia 2. Define radio y tipo inmueble 3. Guarda ConfiguracionBusqueda |
| Postcondición | Perfil de búsqueda activo |
| Excepción | Zona sin datos de mercado → advertencia |

## CU-02: Registrar propiedad manual

| Campo | Valor |
|-------|-------|
| Actor | Capturista, Analista |
| Precondición | Zona de mercado existente |
| Flujo principal | 1. Completa formulario 2. Sistema valida datos mínimos 3. Guarda Propiedad con estatus "nueva" 4. Dispara análisis automático |
| Postcondición | Propiedad registrada y analizada |
| Excepción | Faltan m² → solicita captura o estimación conservadora |

## CU-03: Calcular valor estimado y ROI

| Campo | Valor |
|-------|-------|
| Actor | Sistema (automático) |
| Precondición | Propiedad con precio, zona y superficies |
| Flujo principal | 1. Consulta ValorMetroCuadrado 2. Aplica factores 3. Calcula inversión total 4. Calcula ROI 5. Asigna semáforo 6. Guarda AnalisisInversion |
| Postcondición | Ficha con análisis completo |

## CU-04: Identificar oportunidad prioritaria

| Campo | Valor |
|-------|-------|
| Actor | Sistema |
| Precondición | Análisis calculado |
| Flujo principal | 1. Verifica descuento ≥ mínimo 2. Verifica recuperación ≤ 3 años 3. Verifica ROI > tasa bancaria 4. Verifica riesgo ≤ máximo 5. Marca es_oportunidad y es_prioritaria |
| Postcondición | Semáforo verde, alerta generada |

## CU-05: Enviar alerta de oportunidad

| Campo | Valor |
|-------|-------|
| Actor | Sistema |
| Precondición | Oportunidad prioritaria detectada |
| Flujo principal | 1. Crea Alerta 2. Envía por canal configurado 3. Marca como enviada |
| Postcondición | Usuario notificado |

## CU-06: Consultar dashboard

| Campo | Valor |
|-------|-------|
| Actor | Inversionista, Analista, Consulta |
| Precondición | Usuario autenticado con permiso lectura |
| Flujo principal | 1. Accede dashboard 2. Ve KPIs, gráficas, ranking 3. Filtra por zona/periodo |
| Postcondición | Vista actualizada |

## CU-07: Búsqueda semanal automatizada

| Campo | Valor |
|-------|-------|
| Actor | Sistema (Celery) |
| Precondición | ConfiguracionBusqueda activa, fuentes habilitadas |
| Flujo principal | 1. Ejecuta scrapers 2. Parsea resultados 3. Deduplica 4. Registra nuevas 5. Actualiza precios existentes 6. Re-analiza |
| Postcondición | Propiedades actualizadas, alertas si aplica |
| Excepción | Fuente bloqueada → log + captura manual |

## CU-08: Gestionar estatus de propiedad

| Campo | Valor |
|-------|-------|
| Actor | Analista, Inversionista |
| Flujo principal | 1. Abre ficha 2. Cambia estatus (análisis/descartada/oportunidad/comprada) 3. Agrega comentarios |
| Postcondición | Estatus actualizado, historial conservado |