# Modelo de Base de Datos — Casa Verde

## Diagrama Entidad-Relación

```mermaid
erDiagram
    Usuario ||--o{ ConfiguracionBusqueda : configura
    Usuario ||--o{ AnalisisInversion : analiza
    Usuario ||--o{ Alerta : recibe

    Estado ||--|{ Municipio : contiene
    Municipio ||--|{ ZonaMercado : contiene
    ZonaMercado ||--|{ ValorMetroCuadrado : tiene
    ZonaMercado ||--|{ Propiedad : ubica
    ZonaMercado ||--|{ ComparativoMercado : compara

    FuenteDatos ||--|{ Propiedad : origina
    Propiedad ||--|{ HistorialPrecio : registra
    Propiedad ||--o| AnalisisInversion : evalua
    Propiedad ||--o{ Alerta : dispara

    TasaReferenciaBancaria ||--o{ AnalisisInversion : referencia

    Usuario {
        int id PK
        string username
        string email
        string rol
        decimal tasa_ahorro_personal
        decimal descuento_minimo
        int plazo_recuperacion_max
        int riesgo_maximo
    }

    Estado {
        int id PK
        string nombre
        string clave
    }

    Municipio {
        int id PK
        int estado_id FK
        string nombre
    }

    ZonaMercado {
        int id PK
        int municipio_id FK
        string nombre
        string colonia
        string ciudad
        decimal latitud
        decimal longitud
        int radio_metros
    }

    ValorMetroCuadrado {
        int id PK
        int zona_id FK
        string tipo_inmueble
        decimal valor_terreno_m2
        decimal valor_construccion_m2
        decimal valor_min
        decimal valor_promedio
        decimal valor_max
        int antiguedad_anos
        string estado_fisico
        string servicios
        string uso_suelo
        date fecha_actualizacion
        string fuente
        int confiabilidad
    }

    FuenteDatos {
        int id PK
        string nombre
        string tipo
        string url_base
        boolean activa
        boolean requiere_api
        string terminos_uso
    }

    Propiedad {
        int id PK
        int zona_id FK
        int fuente_id FK
        string titulo
        text descripcion
        decimal precio_publicado
        decimal latitud
        decimal longitud
        decimal m2_terreno
        decimal m2_construccion
        int habitaciones
        int banos
        int niveles
        int estacionamientos
        string estado_fisico
        string tipo_inmueble
        string url_anuncio
        string contacto_publico
        date fecha_publicacion
        datetime fecha_deteccion
        string estatus
        string semaforo
    }

    HistorialPrecio {
        int id PK
        int propiedad_id FK
        decimal precio_anterior
        decimal precio_nuevo
        datetime fecha_cambio
        string motivo
    }

    AnalisisInversion {
        int id PK
        int propiedad_id FK
        int analista_id FK
        decimal valor_terreno_estimado
        decimal valor_construccion_estimado
        decimal valor_total_estimado
        decimal inversion_total
        decimal utilidad_potencial
        decimal descuento_mercado
        decimal roi
        decimal roi_anualizado
        decimal anos_recuperacion
        string semaforo
        boolean es_oportunidad
        boolean es_prioritaria
        text riesgos
        text recomendacion
        text comentarios_analista
    }

    ConfiguracionBusqueda {
        int id PK
        int usuario_id FK
        int zona_id FK
        string tipo_inmueble
        int radio_metros
        decimal descuento_minimo
        boolean activa
        string frecuencia
    }

    Alerta {
        int id PK
        int usuario_id FK
        int propiedad_id FK
        string tipo
        string canal
        string mensaje
        boolean enviada
        datetime fecha_envio
    }

    TasaReferenciaBancaria {
        int id PK
        string institucion
        decimal tasa_anual
        date fecha_vigencia
        string fuente
    }

    ComparativoMercado {
        int id PK
        int zona_id FK
        string tipo_inmueble
        decimal precio_promedio_m2
        int total_propiedades
        date periodo
    }
```

## Índices recomendados

- `Propiedad(zona_id, estatus, semaforo)`
- `Propiedad(precio_publicado, fecha_deteccion)`
- `ValorMetroCuadrado(zona_id, tipo_inmueble, fecha_actualizacion)`
- `HistorialPrecio(propiedad_id, fecha_cambio)`
- `AnalisisInversion(es_oportunidad, es_prioritaria, semaforo)`