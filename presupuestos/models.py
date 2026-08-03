"""Modelos del módulo de presupuestos de obra (Fase 1 del diseño).

Cinco modelos, según §3.2:

- ``CatalogoConcepto``   biblioteca reutilizable de precios unitarios
- ``Presupuesto``        cabecera ligada a una propiedad
- ``PartidaPresupuesto`` cada renglón
- ``RegistroGasto``      gasto real durante la obra (§4.3)
- ``OrdenCambio``        cambios de alcance documentados (§4.2)

Decisiones de modelado
----------------------
**El dinero es ``Decimal``, nunca float.** Se sigue la convención del proyecto:
``max_digits=14, decimal_places=2`` para importes (igual que
``Propiedad.precio_publicado``) y ``12,2`` para precios unitarios (igual que
``CostoRemodelacionM2.costo_m2``).

**Los totales se CALCULAN, no se guardan.** ``subtotal_directo``, ``total`` y
compañía son propiedades, no columnas: un total almacenado se desincroniza en
cuanto alguien edita una partida desde el admin. El costo es una consulta por
presupuesto, que a esta escala no importa. Si en Fase 3 el listado de
oportunidades lo pide en masa, se añade un campo desnormalizado con su
invalidación explícita —pero no antes de tener el problema—.

**Las capas se aplican en cascada** (§2.4): cada una se calcula sobre el
acumulado de las anteriores, no todas sobre el costo directo. Presupuestar solo
el directo deja corto un 30–40%, que es la causa #1 de obras que se disparan.
"""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from presupuestos.choices import (
    CATEGORIA_CHOICES,
    DEFAULT_PCT_CONTINGENCIA,
    DEFAULT_PCT_INDIRECTOS,
    DEFAULT_PCT_IVA,
    DEFAULT_PCT_UTILIDAD,
    ESTADO_ORDEN_CAMBIO_CHOICES,
    ESTADO_PRESUPUESTO_CHOICES,
    SEMAFORO_PRESUPUESTO_CHOICES,
    TIPO_OBRA_CHOICES,
    TIPO_OBRA_REMODELACION,
    UMBRAL_ALERTA_CONTINGENCIA,
    UNIDAD_CHOICES,
)

CERO = Decimal('0.00')
CIEN = Decimal('100')


def _pct(base: Decimal, porcentaje) -> Decimal:
    """``base`` × ``porcentaje``%, redondeado a centavos."""
    return (base * Decimal(porcentaje) / CIEN).quantize(Decimal('0.01'))


class CatalogoConcepto(models.Model):
    """Biblioteca de precios unitarios reutilizables (§2.3).

    La idea es no recotizar en cada obra: el PU se calcula una vez y se reutiliza
    ajustándolo por inflación. ``pu_total`` NO se guarda: es la suma de los tres
    componentes y guardarla permitiría que quedaran incoherentes.
    """
    codigo = models.CharField(max_length=30, unique=True, db_index=True)
    descripcion = models.CharField(max_length=300)
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES)
    unidad = models.CharField(max_length=10, choices=UNIDAD_CHOICES)
    pu_material = models.DecimalField(
        max_digits=12, decimal_places=2, default=CERO,
        validators=[MinValueValidator(CERO)], help_text='MXN por unidad',
    )
    pu_mano_obra = models.DecimalField(
        max_digits=12, decimal_places=2, default=CERO,
        validators=[MinValueValidator(CERO)], help_text='MXN por unidad',
    )
    pu_equipo = models.DecimalField(
        max_digits=12, decimal_places=2, default=CERO,
        validators=[MinValueValidator(CERO)],
        help_text='Herramienta y equipo, MXN por unidad',
    )
    vigencia = models.DateField(
        help_text='Fecha a la que corresponde el precio; sirve para saber si ya envejeció',
    )
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Concepto del catálogo'
        verbose_name_plural = 'Catálogo de conceptos'
        ordering = ['categoria', 'codigo']
        indexes = [models.Index(fields=['categoria', 'activo'])]

    def __str__(self):
        return f'{self.codigo} — {self.descripcion[:60]}'

    @property
    def pu_total(self) -> Decimal:
        """PU = material + mano de obra + equipo (§2.3)."""
        return self.pu_material + self.pu_mano_obra + self.pu_equipo


class Presupuesto(models.Model):
    """Cabecera del presupuesto, ligada (opcionalmente) a una propiedad.

    Una propiedad puede tener varios presupuestos —escenario "económico" vs
    "premium"—; el marcado como ``es_activo`` es el que alimentará el ROI en
    Fase 3. La FK es opcional para permitir presupuestos sueltos (§3.2).
    """
    propiedad = models.ForeignKey(
        'propiedades.Propiedad', on_delete=models.CASCADE,
        null=True, blank=True, related_name='presupuestos',
        help_text='Opcional: un presupuesto puede existir sin propiedad ligada',
    )
    nombre = models.CharField(max_length=200)
    tipo_obra = models.CharField(
        max_length=20, choices=TIPO_OBRA_CHOICES, default=TIPO_OBRA_REMODELACION,
    )
    estado = models.CharField(
        max_length=20, choices=ESTADO_PRESUPUESTO_CHOICES, default='borrador',
    )
    area_m2 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(CERO)],
        help_text='Área de intervención; permite comparar el costo real por m² (§4.6)',
    )
    pct_indirectos = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal(DEFAULT_PCT_INDIRECTOS),
        validators=[MinValueValidator(CERO)],
        help_text='Supervisión, traslados, permisos, herramienta (%)',
    )
    pct_contingencia = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal(DEFAULT_PCT_CONTINGENCIA[TIPO_OBRA_REMODELACION]),
        validators=[MinValueValidator(CERO)],
        help_text='Reserva para imprevistos REALES, no para mejoras (%)',
    )
    pct_utilidad = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal(DEFAULT_PCT_UTILIDAD),
        validators=[MinValueValidator(CERO)], help_text='Margen del inversionista (%)',
    )
    aplica_iva = models.BooleanField(
        default=False, help_text='Solo si se factura o se compra con factura',
    )
    pct_iva = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal(DEFAULT_PCT_IVA),
        validators=[MinValueValidator(CERO)],
    )
    es_activo = models.BooleanField(
        default=False,
        help_text='El que alimenta el ROI de la propiedad (Fase 3)',
    )
    notas = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='presupuestos_creados',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['propiedad', 'es_activo']),
            models.Index(fields=['estado', '-creado_en']),
        ]
        constraints = [
            # Un solo presupuesto activo por propiedad: si hubiera dos, no se
            # sabría cuál alimenta el ROI. Los sueltos (propiedad NULL) quedan
            # fuera de la restricción.
            models.UniqueConstraint(
                fields=['propiedad'],
                condition=models.Q(es_activo=True, propiedad__isnull=False),
                name='unico_presupuesto_activo_por_propiedad',
            ),
        ]

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_obra_display()})'

    # --- Capas del presupuesto (§2.4) ------------------------------------------
    # Cada capa se aplica sobre el acumulado de las anteriores, no sobre el
    # directo: así la utilidad también cubre indirectos y contingencia.

    @property
    def subtotal_directo(self) -> Decimal:
        """Materiales + mano de obra + equipo de todas las partidas."""
        total = self.partidas.aggregate(
            total=models.Sum(models.F('cantidad') * models.F('pu'),
                             output_field=models.DecimalField(max_digits=16, decimal_places=2))
        )['total']
        return (total or CERO).quantize(Decimal('0.01'))

    @property
    def monto_indirectos(self) -> Decimal:
        return _pct(self.subtotal_directo, self.pct_indirectos)

    @property
    def monto_contingencia(self) -> Decimal:
        return _pct(self.subtotal_directo + self.monto_indirectos, self.pct_contingencia)

    @property
    def base_con_contingencia(self) -> Decimal:
        """Directo + indirectos + contingencia: el techo antes de rebasar (§4.4)."""
        return self.subtotal_directo + self.monto_indirectos + self.monto_contingencia

    @property
    def monto_utilidad(self) -> Decimal:
        return _pct(self.base_con_contingencia, self.pct_utilidad)

    @property
    def subtotal(self) -> Decimal:
        """Todo antes de IVA."""
        return self.base_con_contingencia + self.monto_utilidad

    @property
    def monto_iva(self) -> Decimal:
        return _pct(self.subtotal, self.pct_iva) if self.aplica_iva else CERO

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.monto_iva

    @property
    def costo_para_roi(self) -> Decimal:
        """Lo que REALMENTE desembolsa el inversionista: directo + indirectos +
        contingencia. Sin utilidad ni IVA.

        Las obras se administran directamente, así que la **utilidad es margen,
        no desembolso**: meterla en el ROI inflaría la inversión con dinero que
        nadie paga y castigaría la rentabilidad de forma artificial. El IVA queda
        fuera por la misma razón —solo aplica si se factura, y es acreditable—.

        Es deliberadamente INDEPENDIENTE de ``pct_utilidad``: si algún día se
        sube el margen comercial, el ROI no se mueve.
        """
        return self.base_con_contingencia

    @property
    def costo_m2(self) -> Decimal | None:
        """Costo total por m² (número comercial, con utilidad e IVA)."""
        if not self.area_m2:
            return None
        return (self.total / self.area_m2).quantize(Decimal('0.01'))

    @property
    def costo_roi_m2(self) -> Decimal | None:
        """Costo por m² de lo que alimenta el ROI. Es el comparable contra el
        estimado paramétrico, que también es desembolso sin margen."""
        if not self.area_m2:
            return None
        return (self.costo_para_roi / self.area_m2).quantize(Decimal('0.01'))

    # --- Control de obra (§4.3 y §4.4) -----------------------------------------

    @property
    def gasto_real(self) -> Decimal:
        total = self.gastos.aggregate(total=models.Sum('importe_real'))['total']
        return (total or CERO).quantize(Decimal('0.01'))

    @property
    def presupuesto_base(self) -> Decimal:
        """Directo + indirectos: lo que NO debería rebasarse sin tocar contingencia."""
        return self.subtotal_directo + self.monto_indirectos

    @property
    def contingencia_consumida_pct(self) -> Decimal:
        """Qué tanto de la reserva ya se usó. Al 70% es alerta temprana (§4.1)."""
        if self.monto_contingencia <= CERO:
            return CERO
        exceso = self.gasto_real - self.presupuesto_base
        if exceso <= CERO:
            return CERO
        return min(
            (exceso / self.monto_contingencia * CIEN).quantize(Decimal('0.01')), CIEN
        )

    @property
    def semaforo(self) -> str:
        """Salud del presupuesto (§4.4). Gris mientras no haya gasto registrado."""
        if self.gasto_real <= CERO:
            return 'gris'
        if self.gasto_real <= self.presupuesto_base:
            return 'verde'
        if self.gasto_real <= self.base_con_contingencia:
            return 'amarillo'
        return 'rojo'

    @property
    def semaforo_display(self) -> str:
        """Etiqueta legible del semáforo. Hace falta porque ``semaforo`` es una
        propiedad calculada, no un campo con ``choices``: Django no genera su
        ``get_semaforo_display``."""
        return dict(SEMAFORO_PRESUPUESTO_CHOICES).get(self.semaforo, self.semaforo)

    @property
    def requiere_alerta(self) -> bool:
        """Amarillo/rojo, o contingencia consumida por encima del umbral (§4.1)."""
        return (
            self.semaforo in ('amarillo', 'rojo')
            or self.contingencia_consumida_pct >= UMBRAL_ALERTA_CONTINGENCIA
        )


class PartidaPresupuesto(models.Model):
    """Un renglón del presupuesto (§3.2).

    ``descripcion``, ``unidad`` y ``pu`` se COPIAN del catálogo al crear la
    partida en vez de leerse por la FK: el presupuesto debe conservar el precio
    con el que se aprobó, aunque el catálogo suba después. La FK se guarda solo
    como trazabilidad de origen y es opcional (partidas manuales).
    """
    presupuesto = models.ForeignKey(
        Presupuesto, on_delete=models.CASCADE, related_name='partidas',
    )
    concepto = models.ForeignKey(
        CatalogoConcepto, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='partidas', help_text='Origen en el catálogo; vacío si es manual',
    )
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES)
    descripcion = models.CharField(max_length=300)
    unidad = models.CharField(max_length=10, choices=UNIDAD_CHOICES)
    cantidad = models.DecimalField(
        max_digits=12, decimal_places=2, default=CERO,
        validators=[MinValueValidator(CERO)],
    )
    pu = models.DecimalField(
        max_digits=12, decimal_places=2, default=CERO,
        validators=[MinValueValidator(CERO)],
        help_text='Precio unitario congelado al momento de armar el presupuesto',
    )
    orden = models.PositiveIntegerField(default=0)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Partida'
        verbose_name_plural = 'Partidas'
        ordering = ['presupuesto', 'categoria', 'orden', 'id']
        indexes = [models.Index(fields=['presupuesto', 'categoria'])]

    def __str__(self):
        return f'{self.descripcion[:50]} ({self.cantidad} {self.unidad})'

    @property
    def importe(self) -> Decimal:
        return (self.cantidad * self.pu).quantize(Decimal('0.01'))

    @property
    def gasto_real(self) -> Decimal:
        """Gasto imputado a esta partida; permite la desviación por partida (§4.3)."""
        total = self.gastos.aggregate(total=models.Sum('importe_real'))['total']
        return (total or CERO).quantize(Decimal('0.01'))

    @property
    def desviacion(self) -> Decimal:
        """Gasto real − presupuestado. Positivo = se pasó."""
        return self.gasto_real - self.importe


class RegistroGasto(models.Model):
    """Gasto real durante la obra (§4.3).

    La partida es opcional: hay gastos que no caen en ninguna (un permiso, un
    flete). Sin partida cuentan igual para el total del presupuesto, pero no
    entran en la desviación por partida.
    """
    presupuesto = models.ForeignKey(
        Presupuesto, on_delete=models.CASCADE, related_name='gastos',
    )
    partida = models.ForeignKey(
        PartidaPresupuesto, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='gastos', help_text='Opcional: a qué renglón se imputa',
    )
    fecha = models.DateField()
    descripcion = models.CharField(max_length=300)
    proveedor = models.CharField(max_length=200, blank=True)
    importe_real = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(CERO)],
        help_text='MXN efectivamente pagados',
    )
    factura = models.CharField(
        max_length=100, blank=True, help_text='Folio o UUID de la factura, si la hay',
    )
    notas = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='gastos_registrados',
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de gasto'
        verbose_name_plural = 'Registros de gasto'
        ordering = ['-fecha', '-id']
        indexes = [models.Index(fields=['presupuesto', '-fecha'])]

    def __str__(self):
        return f'{self.fecha} — {self.descripcion[:40]} (${self.importe_real})'


class OrdenCambio(models.Model):
    """Cambio de alcance documentado (§4.2).

    Existe para frenar el "ya que estamos, cambiemos también...": ningún cambio
    se ejecuta sin quedar por escrito qué se agrega, cuánto cuesta y quién lo
    aprobó. El ``importe`` puede ser negativo (un cambio que reduce alcance).
    """
    presupuesto = models.ForeignKey(
        Presupuesto, on_delete=models.CASCADE, related_name='ordenes_cambio',
    )
    descripcion = models.CharField(max_length=300)
    motivo = models.TextField(help_text='Por qué se requiere; distingue imprevisto de mejora')
    importe = models.DecimalField(
        max_digits=14, decimal_places=2,
        help_text='MXN. Negativo si el cambio REDUCE el alcance',
    )
    estado = models.CharField(
        max_length=20, choices=ESTADO_ORDEN_CAMBIO_CHOICES, default='solicitada',
    )
    fecha = models.DateField()
    aprobado_por = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ordenes_cambio_aprobadas',
    )
    fecha_resolucion = models.DateField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Orden de cambio'
        verbose_name_plural = 'Órdenes de cambio'
        ordering = ['-fecha', '-id']
        indexes = [models.Index(fields=['presupuesto', 'estado'])]

    def __str__(self):
        return f'{self.descripcion[:50]} — {self.get_estado_display()} (${self.importe})'
