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

# El servidor corre Python 3.9: sin esto, una anotación como `Decimal | None`
# se evalúa al importar y truena con "unsupported operand type(s) for |".
from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from presupuestos.choices import (
    CATEGORIA_CHOICES,
    FUENTE_CAPITAL_ADICIONAL,
    FUENTE_CONTINGENCIA,
    FUENTE_ORDEN_CAMBIO_CHOICES,
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
    UMBRAL_DESVIACION_PARTIDA,
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
        """El TECHO: pasarlo es rojo (§4.4). Base + la reserva ÍNTEGRA.

        La reserva entra completa porque es dinero que existe y está apartado;
        aprobar una orden contra ella no lo hace desaparecer, solo lo compromete.
        Ese compromiso se refleja en ``contingencia_disponible`` y en el semáforo,
        no bajando el techo —bajarlo contaría el mismo peso dos veces cuando
        además se gasta—.

        Las órdenes de capital adicional sí lo suben, vía ``presupuesto_base``.
        """
        return self.presupuesto_base + self.monto_contingencia

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
        sube el margen comercial, el ROI no se mueve. Sí depende de las órdenes
        de cambio aprobadas con capital adicional: eso es desembolso real nuevo y
        el ROI debe reflejarlo.
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

    def _ordenes_aprobadas(self, fuente=None):
        qs = self.ordenes_cambio.filter(estado='aprobada')
        if fuente:
            qs = qs.filter(fuente=fuente)
        total = qs.aggregate(total=models.Sum('importe'))['total']
        return (total or CERO).quantize(Decimal('0.01'))

    @property
    def monto_ordenes_capital(self) -> Decimal:
        """Órdenes aprobadas con CAPITAL ADICIONAL: suben el techo aprobado.

        Es dinero nuevo que alguien autorizó a inyectar, así que el presupuesto
        aprobado crece con ellas.
        """
        return self._ordenes_aprobadas(FUENTE_CAPITAL_ADICIONAL)

    @property
    def monto_ordenes_contingencia(self) -> Decimal:
        """Órdenes aprobadas CON CARGO A LA RESERVA.

        NO suben el techo: consumen contingencia, que es exactamente para lo que
        está. Su efecto es acercar el semáforo a amarillo/rojo antes.
        """
        return self._ordenes_aprobadas(FUENTE_CONTINGENCIA)

    @property
    def monto_ordenes_aprobadas(self) -> Decimal:
        """Todas las aprobadas, sin importar la fuente. KPI del §4.6."""
        return self._ordenes_aprobadas()

    @property
    def ordenes_aprobadas_count(self) -> int:
        return self.ordenes_cambio.filter(estado='aprobada').count()

    @property
    def contingencia_disponible(self) -> Decimal:
        """Reserva que queda tras las órdenes ya cargadas a ella. Nunca negativa:
        si se aprobó de más, la reserva está agotada, no en rojo dos veces."""
        return max(CERO, self.monto_contingencia - self.monto_ordenes_contingencia)

    @property
    def presupuesto_base(self) -> Decimal:
        """Gasto esperado SIN tocar la reserva: directo + indirectos + capital
        adicional aprobado.

        Las de capital adicional suman porque son dinero nuevo autorizado; sin
        ellas, un cambio legítimamente aprobado empujaría el semáforo a amarillo
        de inmediato y el aviso dejaría de significar "cuidado".

        Las cargadas a contingencia NO suman aquí: si lo hicieran, gastarlas
        dejaría el semáforo en verde, y el §4.4 define el amarillo justamente
        como "consumiendo contingencia".
        """
        return self.subtotal_directo + self.monto_indirectos + self.monto_ordenes_capital

    @property
    def contingencia_consumida(self) -> Decimal:
        """Reserva comprometida: el MAYOR entre lo autorizado y lo ya sobregirado.

        No se suman: una orden aprobada contra la reserva se acaba pagando, y ese
        pago aparece como sobregiro del gasto. Sumar ambas contaría dos veces el
        mismo dinero. Se toma el máximo porque cada vía puede ir por delante: la
        orden autoriza antes de gastar, y un sobrecosto sin orden gasta sin
        autorizar.
        """
        sobregiro = max(CERO, self.gasto_real - self.presupuesto_base)
        return max(self.monto_ordenes_contingencia, sobregiro)

    @property
    def contingencia_consumida_pct(self) -> Decimal:
        """Qué tanto de la reserva ya se usó. Al 70% es alerta temprana (§4.1)."""
        if self.monto_contingencia <= CERO:
            return CERO
        return min(
            (self.contingencia_consumida / self.monto_contingencia * CIEN).quantize(
                Decimal('0.01'),
            ),
            CIEN,
        )

    @property
    def semaforo(self) -> str:
        """Salud del presupuesto (§4.4). Gris mientras no haya gasto registrado."""
        if self.gasto_real <= CERO and self.monto_ordenes_contingencia <= CERO:
            return 'gris'
        if self.gasto_real > self.base_con_contingencia:
            return 'rojo'
        # Comprometer reserva YA es amarillo, aunque todavía no se haya pagado:
        # el §4.4 define el amarillo como "consumiendo contingencia".
        if self.contingencia_consumida > CERO:
            return 'amarillo'
        if self.gasto_real <= self.presupuesto_base:
            return 'verde'
        if self.gasto_real <= self.base_con_contingencia:
            return 'amarillo'
        return 'rojo'

    # --- KPIs semanales (§4.6) --------------------------------------------------

    @property
    def desviacion_acumulada(self) -> Decimal:
        """Gasto real − presupuesto aprobado. Positivo = se pasó."""
        return (self.gasto_real - self.presupuesto_base).quantize(Decimal('0.01'))

    @property
    def desviacion_acumulada_pct(self) -> Decimal:
        if self.presupuesto_base <= CERO:
            return CERO
        return (self.desviacion_acumulada / self.presupuesto_base * CIEN).quantize(
            Decimal('0.01'),
        )

    @property
    def avance_gasto_pct(self) -> Decimal:
        """Qué proporción del techo (base + contingencia) ya se gastó.

        El §4.3 lo contrasta con el avance FÍSICO de obra: si el dinero va al 80%
        y la obra al 50%, hay problema ahora, con tiempo de corregir. El avance
        físico no se captura todavía, así que aquí solo se expone el del gasto.
        """
        techo = self.base_con_contingencia
        if techo <= CERO:
            return CERO
        return min((self.gasto_real / techo * CIEN).quantize(Decimal('0.01')), Decimal('999'))

    @property
    def costo_real_m2(self) -> Decimal | None:
        """Costo real por m², para contrastarlo con el estimado paramétrico."""
        if not self.area_m2 or self.gasto_real <= CERO:
            return None
        return (self.gasto_real / self.area_m2).quantize(Decimal('0.01'))

    @property
    def partidas_desviadas(self) -> list:
        """Partidas que se pasaron más del umbral, de mayor a menor desviación."""
        return sorted(
            (p for p in self.partidas.all() if p.excede_umbral),
            key=lambda p: p.desviacion, reverse=True,
        )

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

    @property
    def desviacion_pct(self) -> Decimal:
        """% de desviación sobre lo presupuestado.

        Sin importe presupuestado no hay porcentaje que calcular: un gasto contra
        una partida en cero es infinito, y mostrarlo como 100% mentiría.
        """
        if self.importe <= CERO:
            return CERO
        return (self.desviacion / self.importe * CIEN).quantize(Decimal('0.01'))

    @property
    def excede_umbral(self) -> bool:
        """¿Se pasó más del umbral que dispara alerta por partida? (§4.4)"""
        return self.desviacion > CERO and self.desviacion_pct >= UMBRAL_DESVIACION_PARTIDA


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
    fuente = models.CharField(
        max_length=20, choices=FUENTE_ORDEN_CAMBIO_CHOICES, default='contingencia',
        help_text='De dónde sale el dinero (§4.2). Solo "adicional" amplía el '
                  'presupuesto aprobado; con cargo a contingencia consume la reserva.',
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
