"""Carga datos iniciales de demostración para Casa Verde — Tijuana, B.C."""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from analisis.models import ConfiguracionBusqueda
from geografia.models import Estado, Municipio, ZonaMercado
from mercado.models import FuenteDatos, TasaReferenciaBancaria, ValorMetroCuadrado
from propiedades.models import Propiedad


ZONAS_TIJUANA = [
    {
        'nombre': 'Zona Río',
        'colonia': 'Zona Urbana Río Tijuana',
        'ciudad': 'Tijuana',
        'radio_metros': 2500,
        'latitud': '32.5289000',
        'longitud': '-117.0210000',
        'prioritaria': True,
        'valores': {
            'casa': {'terreno': 12500, 'construccion': 23000, 'min': 3800000, 'prom': 5800000, 'max': 9500000},
            'departamento': {'terreno': 0, 'construccion': 26000, 'min': 1900000, 'prom': 3400000, 'max': 5800000},
            'terreno': {'terreno': 10000, 'construccion': 0, 'min': 2500000, 'prom': 4200000, 'max': 7000000},
            'local': {'terreno': 14000, 'construccion': 20000, 'min': 2200000, 'prom': 4000000, 'max': 8000000},
        },
    },
    {
        'nombre': 'La Mesa',
        'colonia': 'La Mesa',
        'ciudad': 'Tijuana',
        'radio_metros': 3500,
        'latitud': '32.5025000',
        'longitud': '-116.9647000',
        'prioritaria': True,
        'valores': {
            'casa': {'terreno': 5800, 'construccion': 14500, 'min': 1900000, 'prom': 2950000, 'max': 4600000},
            'departamento': {'terreno': 0, 'construccion': 15500, 'min': 1100000, 'prom': 1800000, 'max': 2800000},
            'terreno': {'terreno': 4800, 'construccion': 0, 'min': 800000, 'prom': 1400000, 'max': 2200000},
            'local': {'terreno': 6500, 'construccion': 14000, 'min': 1500000, 'prom': 2600000, 'max': 4200000},
        },
    },
    {
        'nombre': 'Las Palmas',
        'colonia': 'Las Palmas',
        'ciudad': 'Tijuana',
        'radio_metros': 3000,
        'latitud': '32.5118000',
        'longitud': '-116.9820000',
        'prioritaria': True,
        'valores': {
            'casa': {'terreno': 7200, 'construccion': 16500, 'min': 2200000, 'prom': 3400000, 'max': 5200000},
            'departamento': {'terreno': 0, 'construccion': 17500, 'min': 1400000, 'prom': 2200000, 'max': 3500000},
            'terreno': {'terreno': 6000, 'construccion': 0, 'min': 1000000, 'prom': 1700000, 'max': 2800000},
            'local': {'terreno': 7500, 'construccion': 15500, 'min': 1800000, 'prom': 2900000, 'max': 4500000},
        },
    },
    {
        'nombre': 'Playas de Tijuana',
        'colonia': 'Playas de Tijuana Sección Jardines',
        'ciudad': 'Tijuana',
        'radio_metros': 3000,
        'prioritaria': False,
        'valores': {
            'casa': {'terreno': 8500, 'construccion': 18000, 'min': 2800000, 'prom': 4200000, 'max': 7000000},
            'terreno': {'terreno': 7000, 'construccion': 0},
        },
    },
    {
        'nombre': 'Otay',
        'colonia': 'Otay Constituyentes',
        'ciudad': 'Tijuana',
        'radio_metros': 4000,
        'prioritaria': False,
        'valores': {
            'casa': {'terreno': 4200, 'construccion': 12000, 'min': 1200000, 'prom': 2100000, 'max': 3500000},
            'terreno': {'terreno': 3500, 'construccion': 0},
            'nave': {'terreno': 2800, 'construccion': 8000},
        },
    },
    {
        'nombre': 'Centro',
        'colonia': 'Zona Centro',
        'ciudad': 'Tijuana',
        'radio_metros': 2000,
        'prioritaria': False,
        'valores': {
            'casa': {'terreno': 4800, 'construccion': 13000, 'min': 1500000, 'prom': 2400000, 'max': 3800000},
            'local': {'terreno': 6000, 'construccion': 15000},
        },
    },
]

PROPIEDADES_EJEMPLO = [
    {
        'zona': 'La Mesa',
        'titulo': 'Casa 3 recámaras La Mesa — oportunidad',
        'precio_publicado': Decimal('1650000'),
        'm2_terreno': Decimal('140'),
        'm2_construccion': Decimal('130'),
        'habitaciones': 3,
        'banos': 2,
        'estado_fisico': 'bueno',
        'tipo_inmueble': 'casa',
        'direccion': 'Calle Primera, Col. La Mesa',
    },
    {
        'zona': 'La Mesa',
        'titulo': 'Terreno residencial La Mesa — precio bajo mercado',
        'precio_publicado': Decimal('680000'),
        'm2_terreno': Decimal('200'),
        'm2_construccion': None,
        'estado_fisico': 'excelente',
        'tipo_inmueble': 'terreno',
        'direccion': 'Blvd. Salinas, Col. La Mesa',
    },
    {
        'zona': 'Las Palmas',
        'titulo': 'Casa 4 recámaras Las Palmas — oportunidad',
        'precio_publicado': Decimal('2100000'),
        'm2_terreno': Decimal('160'),
        'm2_construccion': Decimal('155'),
        'habitaciones': 4,
        'banos': 3,
        'estado_fisico': 'bueno',
        'tipo_inmueble': 'casa',
        'direccion': 'Calle Las Palmas, Col. Las Palmas',
    },
    {
        'zona': 'Las Palmas',
        'titulo': 'Terreno en venta Las Palmas',
        'precio_publicado': Decimal('850000'),
        'm2_terreno': Decimal('180'),
        'm2_construccion': None,
        'estado_fisico': 'excelente',
        'tipo_inmueble': 'terreno',
        'direccion': 'Av. Las Palmas, Tijuana',
    },
    {
        'zona': 'Zona Río',
        'titulo': 'Departamento Zona Río — 2 recámaras',
        'precio_publicado': Decimal('2650000'),
        'm2_terreno': None,
        'm2_construccion': Decimal('85'),
        'habitaciones': 2,
        'banos': 2,
        'estado_fisico': 'excelente',
        'tipo_inmueble': 'departamento',
        'direccion': 'Blvd. Sánchez Taboada, Zona Río',
    },
    {
        'zona': 'Zona Río',
        'titulo': 'Casa Zona Río — precio reducido',
        'precio_publicado': Decimal('3200000'),
        'm2_terreno': Decimal('110'),
        'm2_construccion': Decimal('120'),
        'habitaciones': 3,
        'banos': 2,
        'estado_fisico': 'bueno',
        'tipo_inmueble': 'casa',
        'direccion': 'Paseo de los Héroes, Zona Río',
    },
    {
        'zona': 'Playas de Tijuana',
        'titulo': 'Casa 3 recámaras Playas de Tijuana — oportunidad',
        'precio_publicado': Decimal('1850000'),
        'm2_terreno': Decimal('120'),
        'm2_construccion': Decimal('110'),
        'habitaciones': 3,
        'banos': 2,
        'estado_fisico': 'bueno',
        'tipo_inmueble': 'casa',
        'direccion': 'Calle Paseo de la Victoria, Playas de Tijuana',
    },
    {
        'zona': 'Otay',
        'titulo': 'Casa Otay — sobrevalorada (referencia negativa)',
        'precio_publicado': Decimal('3200000'),
        'm2_terreno': Decimal('150'),
        'm2_construccion': Decimal('140'),
        'habitaciones': 3,
        'banos': 2,
        'estado_fisico': 'regular',
        'tipo_inmueble': 'casa',
        'direccion': 'Col. Otay Constituyentes',
    },
    {
        'zona': 'Centro',
        'titulo': 'Local comercial Centro Tijuana',
        'precio_publicado': Decimal('1900000'),
        'm2_terreno': Decimal('60'),
        'm2_construccion': Decimal('55'),
        'estado_fisico': 'bueno',
        'tipo_inmueble': 'local',
        'direccion': 'Av. Revolución, Zona Centro',
    },
]


class Command(BaseCommand):
    help = 'Carga Tijuana, B.C. con zonas, valores de mercado y propiedades de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina propiedades de demostración anteriores antes de cargar',
        )

    def handle(self, *args, **options):
        User = get_user_model()

        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@casaverde.local',
                'rol': 'administrador',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Usuario admin creado (admin / admin123)'))

        if options['reset']:
            borradas = Propiedad.objects.filter(
                descripcion__startswith='Propiedad de demostración Casa Verde',
            ).delete()[0]
            self.stdout.write(f'Propiedades demo eliminadas: {borradas}')

        bc = Estado.objects.get_or_create(clave='BC', defaults={'nombre': 'Baja California'})[0]
        tijuana = Municipio.objects.get_or_create(estado=bc, nombre='Tijuana')[0]

        fuente_manual = FuenteDatos.objects.get_or_create(
            nombre='Captura manual',
            defaults={'tipo': 'manual', 'activa': True},
        )[0]

        fuentes_portales = [
            ('Mercado Libre Tijuana', 'portal', 'https://listado.mercadolibre.com.mx', True, False,
             'Playwright — fuente principal recomendada'),
            ('Lamudi Tijuana', 'portal', 'https://www.lamudi.com.mx', False, False,
             'Playwright — captcha frecuente, activar manualmente si se requiere'),
            ('Propiedades.com Tijuana', 'portal', 'https://propiedades.com', False, False,
             'Playwright — inestable, activar manualmente'),
            ('Vivanuncios Tijuana', 'portal', 'https://www.vivanuncios.com.mx', False, False,
             'Playwright — bloqueo frecuente'),
            ('Inmuebles24 Tijuana', 'portal', 'https://www.inmuebles24.com', False, False,
             'Playwright — Cloudflare, activar manualmente'),
            ('Facebook Marketplace', 'red_social', '', False, True,
             'Requiere API oficial — solo captura manual'),
        ]
        for nombre, tipo, url_base, activa, requiere_api, terminos in fuentes_portales:
            FuenteDatos.objects.update_or_create(
                nombre=nombre,
                defaults={
                    'tipo': tipo,
                    'url_base': url_base,
                    'activa': activa,
                    'requiere_api': requiere_api,
                    'terminos_uso': terminos,
                },
            )

        TasaReferenciaBancaria.objects.get_or_create(
            institucion='Promedio bancario México',
            fecha_vigencia=date.today(),
            defaults={'tasa_anual': Decimal('4.50'), 'es_default': True, 'fuente': 'Manual'},
        )

        zonas_creadas = {}
        zonas_prioritarias = []
        for zdata in ZONAS_TIJUANA:
            defaults = {
                'colonia': zdata['colonia'],
                'ciudad': zdata['ciudad'],
                'radio_metros': zdata['radio_metros'],
                'activa': True,
            }
            if zdata.get('latitud'):
                defaults['latitud'] = Decimal(zdata['latitud'])
            if zdata.get('longitud'):
                defaults['longitud'] = Decimal(zdata['longitud'])

            zona, created = ZonaMercado.objects.update_or_create(
                municipio=tijuana,
                nombre=zdata['nombre'],
                defaults=defaults,
            )
            zonas_creadas[zdata['nombre']] = zona
            if zdata.get('prioritaria'):
                zonas_prioritarias.append(zdata['nombre'])

            for tipo, vals in zdata['valores'].items():
                ValorMetroCuadrado.objects.update_or_create(
                    zona=zona,
                    tipo_inmueble=tipo,
                    fecha_actualizacion=date.today(),
                    defaults={
                        'valor_terreno_m2': Decimal(str(vals['terreno'])),
                        'valor_construccion_m2': Decimal(str(vals['construccion'])),
                        'valor_min': Decimal(str(vals['min'])) if vals.get('min') else None,
                        'valor_promedio': Decimal(str(vals['prom'])) if vals.get('prom') else None,
                        'valor_max': Decimal(str(vals['max'])) if vals.get('max') else None,
                        'confiabilidad': 4,
                        'fuente': fuente_manual,
                        'servicios': 'Agua, luz, drenaje',
                    },
                )

        propiedades_ok = 0
        for data in PROPIEDADES_EJEMPLO:
            zona = zonas_creadas[data['zona']]
            campos = {k: v for k, v in data.items() if k != 'zona'}
            _, creada = Propiedad.objects.get_or_create(
                titulo=campos['titulo'],
                zona=zona,
                defaults={
                    **campos,
                    'fuente': fuente_manual,
                    'capturado_por': admin,
                    'descripcion': 'Propiedad de demostración Casa Verde — Tijuana',
                },
            )
            if creada:
                propiedades_ok += 1

        busquedas_ok = 0
        for zona in zonas_creadas.values():
            _, creada = ConfiguracionBusqueda.objects.get_or_create(
                usuario=admin,
                zona=zona,
                defaults={
                    'frecuencia': 'semanal',
                    'descuento_minimo': Decimal('15'),
                    'activa': True,
                },
            )
            if creada:
                busquedas_ok += 1

        self.stdout.write(self.style.SUCCESS(
            f'Tijuana configurado: {len(zonas_creadas)} zonas, '
            f'{propiedades_ok} propiedades nuevas, {busquedas_ok} búsquedas nuevas'
        ))
        self.stdout.write('Zonas prioritarias: ' + ', '.join(zonas_prioritarias))
        self.stdout.write('Todas las zonas: ' + ', '.join(zonas_creadas.keys()))