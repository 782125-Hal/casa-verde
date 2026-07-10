"""Constantes y choices compartidos del sistema Casa Verde."""

TIPO_INMUEBLE_CHOICES = [
    ('terreno', 'Terreno'),
    ('casa', 'Casa'),
    ('departamento', 'Departamento'),
    ('local', 'Local comercial'),
    ('nave', 'Nave industrial'),
    ('otro', 'Otro'),
]

ESTADO_FISICO_CHOICES = [
    ('excelente', 'Excelente'),
    ('bueno', 'Bueno'),
    ('regular', 'Regular'),
    ('malo', 'Malo'),
    ('demoler', 'Requiere demolición parcial'),
]

ESTATUS_PROPIEDAD_CHOICES = [
    ('nueva', 'Nueva'),
    ('en_analisis', 'En análisis'),
    ('descartada', 'Descartada'),
    ('oportunidad', 'Oportunidad'),
    ('comprada', 'Comprada'),
    ('vendida', 'Vendida'),
    ('archivada', 'Archivada'),
]

SEMAFORO_CHOICES = [
    ('verde', 'Verde — Alta oportunidad'),
    ('amarillo', 'Amarillo — Requiere análisis'),
    ('rojo', 'Rojo — No recomendable'),
    ('gris', 'Gris — Datos insuficientes'),
]

ROL_USUARIO_CHOICES = [
    ('administrador', 'Administrador'),
    ('analista', 'Analista inmobiliario'),
    ('inversionista', 'Inversionista'),
    ('capturista', 'Capturista'),
    ('consulta', 'Usuario de consulta'),
]

TIPO_FUENTE_CHOICES = [
    ('portal', 'Portal inmobiliario'),
    ('red_social', 'Red social'),
    ('agencia', 'Agencia inmobiliaria'),
    ('avaluo', 'Fuente de avalúo'),
    ('manual', 'Captura manual'),
    ('otro', 'Otro'),
]

TIPO_ALERTA_CHOICES = [
    ('nueva_oportunidad', 'Nueva oportunidad'),
    ('descuento_relevante', 'Descuento relevante'),
    ('roi_atractivo', 'ROI atractivo'),
    ('baja_precio', 'Baja de precio'),
    ('nueva_zona', 'Nueva propiedad en zona'),
]

CANAL_ALERTA_CHOICES = [
    ('interna', 'Notificación interna'),
    ('email', 'Correo electrónico'),
    ('telegram', 'Telegram'),
    ('whatsapp', 'WhatsApp'),
]

CANAL_PREFERIDO_CHOICES = [
    ('interna', 'Solo en la app (gratis)'),
    ('email', 'Correo electrónico (gratis)'),
    ('telegram', 'Telegram (gratis)'),
    ('email_telegram', 'Email + Telegram'),
]

NIVEL_RIESGO_CHOICES = [
    (1, 'Muy bajo'),
    (2, 'Bajo'),
    (3, 'Medio'),
    (4, 'Alto'),
    (5, 'Muy alto'),
]

# Factores de estado físico para valoración de construcción
FACTOR_ESTADO_FISICO = {
    'excelente': 1.00,
    'bueno': 0.90,
    'regular': 0.75,
    'malo': 0.55,
    'demoler': 0.30,
}

# Defaults de configuración de inversión
DEFAULT_DESCUENTO_MINIMO = 15.0       # %
DEFAULT_PLAZO_RECUPERACION = 3        # años
DEFAULT_TASA_BANCARIA = 4.5           # % anual
DEFAULT_RIESGO_MAXIMO = 3

# ---------------------------------------------------------------------------
# Remodelación / presupuesto de obra
# ---------------------------------------------------------------------------
NIVEL_REMODELACION_CHOICES = [
    ('ninguna', 'Ninguna — lista para habitar'),
    ('ligera', 'Ligera — cosmética (pintura, detalles)'),
    ('media', 'Media — baños, cocina, pisos, instalaciones parciales'),
    ('completa', 'Completa — remodelación integral / estructural'),
]

# Mapa: estado físico de la propiedad → nivel de obra sugerido por defecto.
# Se usa cuando el usuario no captura un nivel_remodelacion explícito.
ESTADO_FISICO_A_NIVEL_REMODELACION = {
    'excelente': 'ninguna',
    'bueno': 'ligera',
    'regular': 'media',
    'malo': 'completa',
    'demoler': 'completa',
}

# Costo de remodelación por m² de construcción (MXN) — fallback global.
# Sirve cuando una zona todavía no tiene costos capturados en la BD.
# Valores de referencia para Tijuana, B.C. (ajustables por zona en el admin).
DEFAULT_COSTO_REMODELACION_M2 = {
    'ninguna': 0,
    'ligera': 2500,
    'media': 6000,
    'completa': 12000,
}