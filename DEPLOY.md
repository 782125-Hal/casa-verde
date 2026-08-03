# Despliegue de Casa Verde en cPanel — max.marhal.com.mx

Guía específica para tu hosting (usuario `marhalco`, dominio `marhal.com.mx`).
Tu cPanel tiene **Setup Python App**, **Terminal**, **Git Version Control** y
**SSL activo**, que es todo lo que se necesita.

Resultado final: la app corriendo en `https://max.marhal.com.mx`, sin tocar
tu página actual en `marhal.com.mx`.

> Nota importante: el código sube a GitHub, pero **la base de datos y el `.env`
> NO** (están en `.gitignore` por seguridad). Por eso el servidor arranca con una
> base vacía y creamos los datos allá — o subimos tu base local (ver Paso 7).

---

## Paso 1 — Crear el subdominio

1. cPanel → sección **Domains** → **Domains** → **Create A New Domain**.
2. Domain: `max.marhal.com.mx`
3. Deja que el "Document Root" se genere solo (algo como
   `/home/marhalco/max.marhal.com.mx`). No importa cuál sea; la app Python
   lo gestionará.
4. **Create**.

## Paso 2 — Bajar el código al servidor

1. cPanel → sección **Advanced** → **Terminal** (acepta el aviso).
2. Clona tu repositorio en tu carpeta home (usa un **token** de GitHub como en el
   push; reemplaza `TU_TOKEN`):

   ```bash
   cd ~
   git clone https://782125-Hal:TU_TOKEN@github.com/782125-Hal/casa-verde.git casa-verde
   ```

   (Si tu repo fuera público, basta `git clone https://github.com/782125-Hal/casa-verde.git casa-verde`.)

## Paso 3 — Crear la aplicación Python

1. cPanel → sección **Software** → **Setup Python App** → **Create Application**.
2. Configura:
   - **Python version:** 3.11 (o la 3.10+ más alta disponible)
   - **Application root:** `casa-verde`
   - **Application URL:** `max.marhal.com.mx`
   - **Application startup file:** `passenger_wsgi.py`
   - **Application Entry point:** `application`
3. **Create**. cPanel crea un entorno virtual y muestra arriba un comando
   `source /home/marhalco/virtualenv/casa-verde/3.11/bin/activate && cd ...`.
   **Cópialo**, lo usarás en el siguiente paso.

## Paso 4 — Instalar dependencias

1. En el **Terminal**, pega el comando `source ... && cd ...` que copiaste (activa
   el entorno virtual de la app).
2. Instala las dependencias **ligeras de producción** (rápidas, sin librerías
   pesadas que no operan en hosting compartido):

   ```bash
   pip install -r requirements-prod.txt
   ```

   > El sitio web (dashboard, propiedades, análisis, presupuesto de remodelación)
   > funciona con esto. El *scraping* con Playwright y el análisis con pandas se
   > siguen corriendo desde tu Mac (usan `requirements.txt` completo).

## Paso 5 — Configurar el archivo `.env` de producción

1. Genera una clave secreta nueva (en el mismo Terminal con el entorno activo):

   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

   Copia el resultado.

2. Crea el archivo `.env` dentro de `~/casa-verde`:

   ```bash
   cat > ~/casa-verde/.env <<'EOF'
   SECRET_KEY=PEGA_AQUI_LA_CLAVE_GENERADA
   DEBUG=False
   ALLOWED_HOSTS=max.marhal.com.mx
   CSRF_TRUSTED_ORIGINS=https://max.marhal.com.mx
   SECURE_SSL_REDIRECT=True
   EOF
   ```

   Luego ábrelo con el editor del File Manager (o `nano ~/casa-verde/.env`) y
   sustituye `PEGA_AQUI_LA_CLAVE_GENERADA` por la clave real.

   > **`SECRET_KEY` es obligatoria en producción.** Sin ella la app se niega a
   > arrancar (error `ImproperlyConfigured`) en vez de usar una clave conocida
   > que permitiría falsificar sesiones de administrador. Si el sitio devuelve
   > error 500 tras un despliegue, revisa primero que esta línea siga en el `.env`.

## Paso 6 — Preparar base de datos y archivos estáticos

Con el entorno virtual activo y dentro de `~/casa-verde`:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser        # usa una contraseña FUERTE y única
python manage.py seed_datos             # zonas de Tijuana + datos demo
python manage.py seed_remodelacion      # costos de remodelación por zona
```

`seed_datos` reutiliza el superusuario que acabas de crear. Solo si no existe
ninguno crea `admin` con una contraseña aleatoria que imprime **una sola vez**.

## Paso 6b — Comprobar que no quedó ningún usuario con contraseña débil

Versiones anteriores de `seed_datos` creaban `admin` con la contraseña `admin123`.
Si desplegaste antes de este cambio, ese usuario existe en el servidor y tiene
acceso total. Compruébalo y cámbialo:

```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
for u in get_user_model().objects.filter(is_superuser=True):
    print(u.username, '— contraseña débil:', u.check_password('admin123'))
"
```

Si alguno sale `True`, rota la contraseña de inmediato:

```bash
python manage.py changepassword admin
```

## Paso 7 (opcional) — Usar tu base de datos local en vez de la demo

Si prefieres llevar las 79 propiedades con las que ya trabajaste:

1. Omite `seed_datos` en el paso anterior.
2. Sube tu archivo local `db.sqlite3` (de `~/Desktop/Casa Verde/`) al servidor,
   a `~/casa-verde/db.sqlite3`, usando el **File Manager** de cPanel.
3. Ejecuta solo `python manage.py migrate` para asegurar que esté al día.

## Paso 8 — Reiniciar y probar

1. cPanel → **Setup Python App** → tu app → botón **Restart**.
2. Abre `https://max.marhal.com.mx`. Deberías ver el dashboard.
3. El admin queda en `https://max.marhal.com.mx/admin/`.

## Paso 9 — HTTPS

Tu cPanel ya muestra SSL activo; AutoSSL suele cubrir el subdominio en minutos. Si
el candado no aparece, ve a **Security → SSL/TLS Status**, marca
`max.marhal.com.mx` y ejecuta **Run AutoSSL**.

---

## Actualizar la app en el futuro

Cuando hagas cambios y los subas a GitHub (`git push`), para reflejarlos en el
servidor, en el **Terminal** con el entorno activo:

```bash
cd ~/casa-verde
git pull
pip install -r requirements.txt      # solo si cambiaron dependencias
python manage.py migrate             # solo si hubo cambios de modelos
python manage.py collectstatic --noinput
```

Luego **Restart** en Setup Python App.

## Seguridad — imprescindible antes de compartir la URL

- Usa una contraseña fuerte y única en `createsuperuser`.
- Ejecuta el **Paso 6b** para descartar usuarios con la vieja contraseña `admin123`.
- Verifica que `DEBUG=False` y `SECRET_KEY` estén en el `.env` (ya los pusimos).
- El `.env` y `db.sqlite3` nunca deben subir a GitHub (ya están ignorados).
- Todo el sitio exige sesión iniciada: un visitante anónimo es redirigido a
  `/login/`. Solo los usuarios que tú crees en el admin pueden ver las
  propiedades, el dashboard y la exportación CSV.

## Despliegue rápido con `deploy.sh`

A partir de ahora, los despliegues de actualizaciones se hacen con el script
`deploy.sh` incluido en el repositorio, en lugar de correr los comandos a mano.

### Uso

1. Entra a **cPanel → Terminal**.
2. Corre:

```bash
   cd ~/casa-verde && bash deploy.sh
```

3. Al terminar, si el sitio no refleja los cambios, entra a
   **cPanel → Setup Python App** y presiona **Restart**.

### Qué hace el script

El `deploy.sh` ejecuta el despliegue de forma segura y en orden:

1. Activa el entorno virtual (`/home/marhalco/virtualenv/casa-verde/3.9`).
2. **Verifica que exista `SECRET_KEY` en `.env` antes de tocar nada.** Si falta,
   aborta para no dejar la app caída (error 500).
3. `git pull` para traer los últimos cambios.
4. `python manage.py migrate` y `collectstatic --noinput`.
5. **Revisa si algún superusuario todavía usa la contraseña débil `admin123`**
   y avisa cuál rotar con `python manage.py changepassword <usuario>`.
6. Solicita el reinicio de la aplicación (`tmp/restart.txt`).
7. Imprime el último commit desplegado para confirmar la versión.

### Nota de mantenimiento

El script trae escrita la ruta del entorno virtual en la variable
`VENV_ACTIVATE`. Si el hosting actualiza la versión de Python (por ejemplo de
3.9 a 3.11), edita esa línea al inicio de `deploy.sh`.

---

## Cómo analizar una obra nueva (comprar terreno + construir)

Para saber si conviene **comprar un terreno y construir para vender**, la app
reutiliza el mismo análisis de inversión (ROI + semáforo) que las demás
propiedades. Son 3 pasos:

1. **Registra el terreno como propiedad.** En el admin (o en la captura del
   sitio), crea la propiedad con:
   - **Tipo de inmueble:** `Terreno`.
   - **Precio publicado:** el precio de compra del terreno.
   - **m² de terreno** y **zona**. Deja `m² de construcción` vacío.

2. **Crea un presupuesto de obra nueva y actívalo.** En `/presupuestos/nuevo/`:
   - Liga el presupuesto a esa propiedad y elige **Tipo de obra: `Obra nueva`**.
   - Captura las **partidas** (materiales, mano de obra, etc.) y el **área a
     construir** (`area_m2`). El costo de la obra sale de aquí.
   - Marca el presupuesto como **activo** (`es_activo`). Solo puede haber **uno
     activo por propiedad**: es el que manda sobre el ROI.

3. **Abre el análisis de la propiedad.** El ROI y el semáforo ya comparan:
   - **Valor de venta proyectado** = la casa terminada (suelo + área del
     presupuesto, al valor de **casa** de la zona), contra
   - **Inversión** = terreno + costos de compra + el costo del presupuesto de obra.

   Un aviso en *Riesgos* recuerda que el valor incluye construcción **proyectada,
   aún no edificada** (el ROI asume que se construye y se vende a valor de mercado).

> **Requisito de datos:** la zona debe tener capturado un **valor por m² de casa**
> (`Mercado → Valores por metro cuadrado`, tipo *Casa*). Sin él no hay contra qué
> comparar la casa terminada y el análisis se queda en gris/rojo. `seed_datos` ya
> carga estos valores para las zonas de Tijuana.
