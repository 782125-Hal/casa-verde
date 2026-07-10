# Requerimientos Funcionales — Casa Verde

**Proyecto:** Plataforma de detección de oportunidades inmobiliarias  
**Versión:** 1.0  
**Fecha:** Junio 2026

---

## 1. Propósito del sistema

Casa Verde es una plataforma web que identifica propiedades inmobiliarias (casas, terrenos, departamentos, locales, naves industriales) cuyo precio publicado está por debajo del valor estimado de mercado, calculando rentabilidad financiera (ROI) y priorizando oportunidades de inversión mediante un semáforo visual.

---

## 2. Actores del sistema

| Actor | Descripción |
|-------|-------------|
| Administrador | Configura el sistema, usuarios, fuentes de datos y parámetros globales |
| Analista inmobiliario | Revisa, valida y clasifica oportunidades; captura datos de mercado |
| Inversionista | Consulta oportunidades, configura alertas y criterios de inversión |
| Capturista | Registra manualmente propiedades encontradas en fuentes externas |
| Usuario de consulta | Solo lectura de dashboard y fichas técnicas |

---

## 3. Requerimientos funcionales

### RF-01 Configuración geográfica
- **RF-01.1** El sistema permitirá seleccionar Estado, Municipio, Ciudad, Colonia/zona y radio de búsqueda.
- **RF-01.2** El usuario podrá filtrar por tipo de propiedad: terreno, casa, departamento, local, nave industrial u otro.
- **RF-01.3** Las configuraciones se guardarán como perfiles de búsqueda reutilizables.

### RF-02 Búsqueda semanal automatizada
- **RF-02.1** El sistema ejecutará búsquedas programadas (semanales) en fuentes autorizadas.
- **RF-02.2** Fuentes objetivo: portales inmobiliarios, agencias, redes sociales públicas (Facebook Marketplace, grupos públicos), fuentes de avalúos.
- **RF-02.3** Se respetarán términos de uso, privacidad y restricciones legales de cada plataforma.
- **RF-02.4** Cuando no exista acceso autorizado, se habilitará registro manual de oportunidades.

### RF-03 Base de datos de mercado
- **RF-03.1** Mantener valores promedio por m² de terreno y construcción por zona.
- **RF-03.2** Registrar valor mínimo, promedio y máximo por zona y tipo de inmueble.
- **RF-03.3** Almacenar antigüedad, estado físico, servicios, uso de suelo, fecha y fuente del dato.
- **RF-03.4** Asignar nivel de confiabilidad a cada dato de mercado.

### RF-04 Registro de propiedades
- **RF-04.1** Registrar título, descripción, precio, ubicación, coordenadas, superficies, habitaciones, baños, niveles, estacionamientos.
- **RF-04.2** Guardar fotografías o enlaces públicos, fuente, fechas de publicación y detección.
- **RF-04.3** Contacto solo si es público y permitido legalmente.
- **RF-04.4** Estatus: nueva, en análisis, descartada, oportunidad, comprada, vendida, archivada.

### RF-05 Cálculo de valor estimado
- **RF-05.1** Valor terreno = m² terreno × valor promedio m² terreno zona.
- **RF-05.2** Valor construcción = m² construidos × valor promedio m² construido × factor estado físico.
- **RF-05.3** Valor total = valor terreno + valor construcción.
- **RF-05.4** Factores ajustables: conservación, antigüedad, ubicación, accesibilidad, servicios, urgencia, riesgo documental, reparaciones, costos notariales.

### RF-06 Identificación de oportunidad
- **RF-06.1** Oportunidad si precio publicado < valor estimado de mercado.
- **RF-06.2** Descuento mínimo configurable (15%, 20%, 30%).
- **RF-06.3** Retorno estimado ≤ 3 años (configurable).
- **RF-06.4** Rendimiento ≥ tasa bancaria de ahorro del usuario.
- **RF-06.5** Riesgo documental/legal/físico ≤ nivel máximo del usuario.

### RF-07 Cálculo financiero
- **RF-07.1** Inversión total = precio + notariales + impuestos + comisiones + reparaciones + otros.
- **RF-07.2** Utilidad potencial = valor estimado − inversión total.
- **RF-07.3** Descuento = (valor estimado − precio publicado) / valor estimado × 100.
- **RF-07.4** ROI = utilidad potencial / inversión total × 100.
- **RF-07.5** ROI anualizado = ROI / años de recuperación.
- **RF-07.6** Comparación contra tasa bancaria configurable.

### RF-08 Semáforo de oportunidad
- **Verde:** alta oportunidad, descuento significativo, ROI atractivo, recuperación ≤ 3 años.
- **Amarillo:** oportunidad media, requiere análisis o negociación.
- **Rojo:** no recomendable, precio alto, ROI bajo, riesgo elevado o recuperación > 3 años.

### RF-09 Panel de control
- **RF-09.1** Total propiedades analizadas, oportunidades por semana, promedio descuento.
- **RF-09.2** Zonas con mayor oportunidad, mejor ROI, propiedades descartadas.
- **RF-09.3** Evolución precio/m² por zona, gráficas de tendencia, ranking de oportunidades.

### RF-10 Módulo de alertas
- **RF-10.1** Alertas por email, WhatsApp (Twilio) y notificaciones internas.
- **RF-10.2** Disparadores: descuento relevante, ROI atractivo, precio bajo mercado, nueva propiedad en zona, baja de precio.

### RF-11 Análisis detallado
- **RF-11.1** Ficha técnica con datos generales, ubicación, fotos, precios, comparativos, ROI, costos, riesgos, recomendación automática, comentarios del analista.

### RF-12 Base histórica
- **RF-12.1** Historial de cambios de precio, propiedades similares, valores por zona, oportunidades, compras/ventas, ROI real, tiempo de recuperación.

### RF-13 Roles y permisos
- **RF-13.1** Cinco roles con permisos diferenciados (ver matriz en RF-13).

### RF-14 Exportación
- **RF-14.1** Exportar a Excel, PDF y CSV.

---

## 4. Reglas de negocio

| ID | Regla |
|----|-------|
| RN-01 | No marcar como oportunidad sin datos mínimos (precio, ubicación, m²) |
| RN-02 | Solicitar captura manual cuando falten datos críticos |
| RN-03 | Permitir estimaciones conservadoras con datos incompletos |
| RN-04 | Penalizar propiedades con alto riesgo legal/documental |
| RN-05 | Descuento mínimo, tasa bancaria y plazo recuperación configurables |
| RN-06 | Comparar propiedades similares en la misma zona |
| RN-07 | Oportunidad prioritaria: recuperación ≤ 3 años Y supera tasa bancaria |

---

## 5. Datos mínimos para análisis

| Campo | Obligatorio | Impacto si falta |
|-------|-------------|------------------|
| Precio publicado | Sí | No se puede analizar |
| Ubicación (zona) | Sí | No se puede comparar mercado |
| m² terreno o construidos | Sí* | Estimación conservadora |
| Tipo de propiedad | Sí | Factor de valor incorrecto |
| Estado físico | No | Factor por defecto 0.85 |

*Al menos uno de los dos superficies.