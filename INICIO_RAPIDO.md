# Guía de Inicio Rápido - Procesador de Facturas

## 🚀 Comenzar en 5 minutos

### 1. Instalar dependencias (primera vez)
```bash
pip install -r requirements.txt
```

### 2. Configurar base de datos

Asegúrate de que PostgreSQL esté corriendo:

```bash
# En macOS con Homebrew
brew services start postgresql

# O iniciar manualmente
postgres -D /usr/local/var/postgres
```

Crear la base de datos:
```bash
createdb facturas_db
```

### 3. Configurar variables de entorno

Editar `.env` y asegurarse de que tenga:

```env
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/facturas_db
OPENAI_API_KEY=sk-xxxxx
```

### 4. Ejecutar la aplicación

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

O usar VS Code: Ctrl+Shift+B → "Run FastAPI local"

### 5. Acceder a la aplicación

- **Interfaz principal**: http://localhost:8080/
- **Dashboard**: http://localhost:8080/dashboard
- **Documentación API**: http://localhost:8080/docs

## 📁 Archivos creados

### Configuración
- `app/config.py` - Configuración centralizada
- `.env` - Variables de entorno

### Base de datos
- `app/database.py` - Conexión SQLAlchemy
- `app/ftra/models.py` - Modelos con prefijo FTRA_

### Servicios
- `app/services/ocr_service.py` - OCR con PaddleOCR
- `app/services/ai_service.py` - IA con OpenAI
- `app/services/factura_service.py` - Orquestación

### API
- `app/routers/facturas.py` - Endpoints de facturas
- `app/schemas/factura_schemas.py` - Esquemas Pydantic

### Principal
- `app/main.py` - Aplicación FastAPI
- `app/database.py` - Configuración BD

## 🎯 Próximos pasos

1. **Configurar OpenAI**: 
   - Obtener clave en https://platform.openai.com/api-keys
   - Añadir a `.env`

2. **Configurar PostgreSQL**:
   - Instalar si no tienes
   - Crear base de datos `facturas_db`
   - Verificar conexión

3. **Probar OCR**:
   - Las tablas se crean automáticamente
   - Subir un PDF de prueba
   - Ver procesamiento en tiempo real

## 🐛 Comandos útiles

```bash
# Ver logs en tiempo real
tail -f logs/app.log

# Resetear base de datos (CUIDADO!)
python -c "from app.database import drop_db, init_db; drop_db(); init_db()"

# Verificar conexión a PostgreSQL
psql facturas_db

# Listar facturas en BD
psql facturas_db -c "SELECT * FROM FTRA_facturas;"

# Ver estructura de tablas
psql facturas_db -c "\dt FTRA_*"
```

## 📦 Tablas creadas automáticamente

- FTRA_proveedores
- FTRA_clientes
- FTRA_facturas
- FTRA_lineas_factura
- FTRA_historial_facturas
- FTRA_errores_procesamiento

## ✅ Checklist de instalación

- [ ] Python 3.11+ instalado
- [ ] PostgreSQL corriendo
- [ ] venv creado y activado
- [ ] requirements.txt instalado
- [ ] .env configurado
- [ ] DATABASE_URL válido
- [ ] OPENAI_API_KEY configurada
- [ ] Base de datos facturas_db creada
- [ ] `uvicorn` ejecutando
- [ ] http://localhost:8080 accesible

## 💡 Tips

- Usa `--reload` en desarrollo para recargar automáticamente
- Accede a `/docs` para ver documentación interactiva
- Los archivos se guardan en `uploads/`
- Todos los modelos tienen prefijo `FTRA_`
- Las respuestas de OpenAI se limpian automáticamente
- El historial de cambios se registra automáticamente

## 📞 Soporte

Si tienes problemas, revisa:
1. Los logs de la aplicación
2. La documentación en http://localhost:8080/docs
3. El archivo README_FACTURAS.md
