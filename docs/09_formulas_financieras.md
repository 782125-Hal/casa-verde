# Fórmulas Financieras — Casa Verde

## Valoración de mercado

```
Valor terreno estimado = m²_terreno × valor_m²_terreno_zona

Valor construcción estimado = m²_construidos × valor_m²_construcción_zona × factor_estado_físico

Valor total estimado = (valor_terreno + valor_construcción) × factor_antigüedad × factor_riesgo × factor_ubicación
```

### Factores de estado físico

| Estado | Factor |
|--------|--------|
| Excelente | 1.00 |
| Bueno | 0.90 |
| Regular | 0.75 |
| Malo | 0.55 |
| Demoler | 0.30 |

### Factor antigüedad

```
factor = max(0.70, 1.0 - (años / 10) × 0.02)
```

### Factor riesgo (RN-04)

| Riesgo máximo | Factor |
|---------------|--------|
| 1 | 1.00 |
| 2 | 0.95 |
| 3 | 0.85 |
| 4 | 0.70 |
| 5 | 0.50 |

---

## Cálculo financiero

```
Inversión total = precio_compra + notariales + impuestos + comisiones + reparaciones + otros

Utilidad potencial = valor_estimado_mercado - inversión_total

Descuento contra mercado (%) = (valor_estimado - precio_publicado) / valor_estimado × 100

ROI (%) = utilidad_potencial / inversión_total × 100

Años recuperación = inversión_total / utilidad_potencial

ROI anualizado (%) = ROI / años_recuperación
```

### Costos estimados (% sobre precio)

| Concepto | Porcentaje |
|----------|------------|
| Gastos notariales | 6% |
| Impuestos | 2% |
| Comisiones | 3% |
| Reparaciones (regular) | 5% |

---

## Criterios de oportunidad

```
ES_OPORTUNIDAD = descuento ≥ descuento_mínimo AND utilidad > 0

ES_PRIORITARIA = ES_OPORTUNIDAD
              AND años_recuperación ≤ plazo_máximo (default 3)
              AND ROI_anualizado ≥ tasa_bancaria
              AND riesgo_total ≤ riesgo_máximo_usuario
```

## Semáforo

| Color | Condición |
|-------|-----------|
| Verde | Es prioritaria |
| Amarillo | Es oportunidad parcial o descuento moderado |
| Rojo | Sin descuento suficiente o ROI bajo |
| Gris | Datos insuficientes |