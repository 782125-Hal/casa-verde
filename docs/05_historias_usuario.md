# Historias de Usuario — Casa Verde

## Épica 1: Configuración geográfica

| ID | Historia | Criterios de aceptación |
|----|----------|------------------------|
| HU-01 | Como inversionista quiero seleccionar estado, municipio y colonia para enfocar mi búsqueda | Puedo elegir de catálogo y guardar perfil |
| HU-02 | Como inversionista quiero definir radio de búsqueda | Radio en km/metros, mapa opcional Fase 6 |
| HU-03 | Como inversionista quiero filtrar por tipo de inmueble | Terreno, casa, depto, local, nave, otro |

## Épica 2: Base de mercado

| ID | Historia | Criterios de aceptación |
|----|----------|------------------------|
| HU-04 | Como analista quiero registrar valor m² por zona | CRUD con fuente y confiabilidad |
| HU-05 | Como analista quiero ver evolución histórica de precios/m² | Gráfica por zona y periodo |
| HU-06 | Como administrador quiero importar valores desde CSV | Importación masiva validada |

## Épica 3: Registro de propiedades

| ID | Historia | Criterios de aceptación |
|----|----------|------------------------|
| HU-07 | Como capturista quiero registrar propiedad manualmente | Formulario completo con validación |
| HU-08 | Como sistema quiero detectar propiedades automáticamente | Scraping semanal Fase 4 |
| HU-09 | Como analista quiero ver historial de cambios de precio | Timeline de HistorialPrecio |

## Épica 4: Análisis financiero

| ID | Historia | Criterios de aceptación |
|----|----------|------------------------|
| HU-10 | Como inversionista quiero ver valor estimado vs precio publicado | Cálculo automático con factores |
| HU-11 | Como inversionista quiero configurar descuento mínimo y tasa bancaria | Parámetros en perfil de usuario |
| HU-12 | Como inversionista quiero ver ROI y plazo de recuperación | Fórmulas visibles en ficha |
| HU-13 | Como sistema quiero clasificar con semáforo verde/amarillo/rojo | Reglas RN-01 a RN-07 |

## Épica 5: Dashboard y alertas

| ID | Historia | Criterios de aceptación |
|----|----------|------------------------|
| HU-14 | Como inversionista quiero dashboard con KPIs | Totales, oportunidades, ranking |
| HU-15 | Como inversionista quiero alertas por email | Al detectar oportunidad prioritaria |
| HU-16 | Como inversionista quiero alertas por WhatsApp | Integración Twilio Fase 5 |

## Épica 6: Gestión y reportes

| ID | Historia | Criterios de aceptación |
|----|----------|------------------------|
| HU-17 | Como analista quiero agregar comentarios a una ficha | Campo comentarios_analista |
| HU-18 | Como administrador quiero exportar a Excel/PDF | Botones de exportación |
| HU-19 | Como administrador quiero gestionar roles y permisos | 5 roles con matriz de permisos |
| HU-20 | Como inversionista quiero comparar propiedades similares | Vista comparativa por zona |