"""Vocabularios del módulo de presupuestos.

Viven aquí y no en ``core.choices`` porque solo los usa esta app; ``core`` guarda
lo transversal (estado físico, nivel de obra, semáforo de oportunidad).

Los porcentajes por defecto salen de la §2.4 del diseño: el costo directo es solo
el 60–70% del costo total, así que un presupuesto sin capas queda corto un 30–40%.
"""

# --- Tipo de obra --------------------------------------------------------------
TIPO_OBRA_REMODELACION = 'remodelacion'
TIPO_OBRA_NUEVA = 'obra_nueva'

TIPO_OBRA_CHOICES = [
    (TIPO_OBRA_REMODELACION, 'Remodelación'),
    (TIPO_OBRA_NUEVA, 'Obra nueva'),
]

# --- Estado del presupuesto (§3.2: borrador → aprobado → en ejecución → cerrado)
ESTADO_PRESUPUESTO_CHOICES = [
    ('borrador', 'Borrador'),
    ('aprobado', 'Aprobado'),
    ('en_ejecucion', 'En ejecución'),
    ('cerrado', 'Cerrado'),
]

# --- Unidades de obra ----------------------------------------------------------
UNIDAD_CHOICES = [
    ('m2', 'm²'),
    ('m3', 'm³'),
    ('ml', 'Metro lineal'),
    ('pza', 'Pieza'),
    ('lote', 'Lote'),
    ('jgo', 'Juego'),
    ('salida', 'Salida'),
    ('serv', 'Servicio'),
]

# --- Categorías (partidas) -----------------------------------------------------
# §2.2 del diseño: 10 partidas para obra nueva y 10 para remodelación. Se juntan
# en un solo vocabulario porque un concepto del catálogo puede servir a ambas
# (p. ej. pintura); qué partidas se ofrecen en cada caso lo decide la plantilla.
CATEGORIA_OBRA_NUEVA = [
    ('preliminares', 'Preliminares'),
    ('cimentacion', 'Cimentación'),
    ('estructura', 'Estructura'),
    ('albanileria', 'Albañilería'),
    ('hidrosanitaria', 'Instalación hidrosanitaria'),
    ('electrica', 'Instalación eléctrica'),
    ('acabados', 'Acabados'),
    ('carpinteria', 'Carpintería y cancelería'),
    ('exteriores', 'Exteriores'),
    ('limpieza', 'Limpieza final y entrega'),
]

CATEGORIA_REMODELACION = [
    ('demolicion', 'Demolición y retiro de escombro'),
    ('reparaciones', 'Reparaciones estructurales / humedades'),
    ('cocina', 'Cocina'),
    ('banos', 'Baños'),
    ('pisos', 'Pisos y recubrimientos'),
    ('electrica_act', 'Instalación eléctrica (actualización)'),
    ('hidro_act', 'Instalación hidrosanitaria (actualización)'),
    ('pintura', 'Pintura y acabados'),
]

CATEGORIA_CHOICES = CATEGORIA_REMODELACION + CATEGORIA_OBRA_NUEVA

# Categorías que aplican a cada tipo de obra. 'carpinteria' y 'limpieza' se
# comparten: el diseño las lista en ambas columnas con el mismo nombre.
CATEGORIAS_POR_TIPO_OBRA = {
    TIPO_OBRA_REMODELACION: [c for c, _ in CATEGORIA_REMODELACION] + ['carpinteria', 'limpieza'],
    TIPO_OBRA_NUEVA: [c for c, _ in CATEGORIA_OBRA_NUEVA],
}

# --- Órdenes de cambio (§4.2) --------------------------------------------------
ESTADO_ORDEN_CAMBIO_CHOICES = [
    ('solicitada', 'Solicitada'),
    ('aprobada', 'Aprobada'),
    ('rechazada', 'Rechazada'),
]

# --- Porcentajes por defecto de las capas (§2.4, confirmados por el usuario) ---
DEFAULT_PCT_INDIRECTOS = 12
DEFAULT_PCT_UTILIDAD = 12
# La contingencia es MÁS alta en remodelación: hay más sorpresas ocultas
# (humedad, instalación vieja) que en obra nueva.
DEFAULT_PCT_CONTINGENCIA = {
    TIPO_OBRA_REMODELACION: 15,
    TIPO_OBRA_NUEVA: 8,
}
DEFAULT_PCT_IVA = 16

# --- Semáforo de salud del presupuesto (§4.4) ----------------------------------
SEMAFORO_PRESUPUESTO_CHOICES = [
    ('verde', 'Verde — dentro del presupuesto base'),
    ('amarillo', 'Amarillo — consumiendo contingencia'),
    ('rojo', 'Rojo — rebasó presupuesto + contingencia'),
    ('gris', 'Gris — sin gasto registrado'),
]

# §4.1: consumir el 70% de la contingencia es la señal de alerta temprana.
UMBRAL_ALERTA_CONTINGENCIA = 70

# Nivel de obra (core.choices.NIVEL_REMODELACION_CHOICES) → código del concepto
# paramétrico que lo representa en el catálogo. 'ninguna' no genera concepto:
# no hay obra que presupuestar.
NIVEL_PARAMETRICO_A_CODIGO = {
    'ligera': 'PAR-LIG',
    'media': 'PAR-MED',
    'completa': 'PAR-COM',
}
