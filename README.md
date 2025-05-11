# VIA Forms Hub

Aplicación web para gestionar formularios de contratos integrados con Monday.com.

## Características

- Formularios para clientes comerciales y residenciales
- Formularios específicos para AirNation Leads
- Integración completa con Monday.com
- Funcionalidad PWA para instalación en dispositivos móviles
- Autenticación OAuth con Google y Zoho

## Requisitos

- Python 3.11+
- Flask y dependencias (ver requirements.txt)
- Cuenta de Monday.com
- Credenciales OAuth para Google
- Servicio de hosting como Render.com

## Despliegue en Render.com

### 1. Crear un nuevo repositorio en GitHub

```bash
git init
git add .
git commit -m "Versión inicial"
git branch -M main
git remote add origin https://github.com/tu-usuario/via-forms-hub.git
git push -u origin main
```

### 2. Configurar servicio web en Render.com

1. Inicia sesión en [Render.com](https://render.com)
2. Haz clic en "New +" y selecciona "Web Service"
3. Conecta tu repositorio de GitHub
4. Configura el servicio:
   - **Nombre**: via-forms-hub
   - **Entorno**: Python
   - **Comando de construcción**: `pip install -r requirements.txt`
   - **Comando de inicio**: `gunicorn app:app`
   - **Plan**: Starter o superior

### 3. Configurar variables de entorno

En la sección "Environment" de tu servicio web en Render, agrega las siguientes variables:

- `FLASK_SECRET_KEY` - Clave secreta para Flask (generar con `secrets.token_hex(16)`)
- `GOOGLE_OAUTH_CLIENT_ID` - ID de cliente de Google OAuth
- `GOOGLE_OAUTH_CLIENT_SECRET` - Secreto de cliente de Google OAuth
- `ZOHO_OAUTH_CLIENT_ID` - ID de cliente de Zoho OAuth (opcional)
- `ZOHO_OAUTH_CLIENT_SECRET` - Secreto de cliente de Zoho OAuth (opcional)
- `MAIL_USERNAME` - Correo electrónico para enviar notificaciones
- `MAIL_PASSWORD` - Contraseña del correo electrónico
- `RENDER` - Establecer en `true` para indicar que es un entorno de producción

### 4. Actualizar URLs de redirección OAuth

Después de desplegar, actualiza las URLs de redirección en la consola de desarrolladores de Google:
- `https://tu-app.render.com/login/google/authorized`

## Desarrollo local

1. Clona el repositorio
2. Crea un entorno virtual: `python -m venv venv`
3. Activa el entorno virtual:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Instala dependencias: `pip install -r requirements.txt`
5. Crea un archivo `.env` con las variables necesarias
6. Ejecuta la aplicación: `flask run`

## Mantenimiento

Para actualizar la aplicación:
1. Realiza cambios en el código
2. Prueba localmente
3. Haz commit y push a GitHub
4. Render.com desplegará automáticamente la nueva versión 
