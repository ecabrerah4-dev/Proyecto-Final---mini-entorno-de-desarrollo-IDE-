# Mini IDE de Bases de Datos SQL y NoSQL

## Descripcion
Aplicacion de escritorio en Python para interactuar con SQLite (SQL) y MongoDB (NoSQL). Incluye editor de comandos, conexion a ambas bases, mensajes de estado y tabla para visualizar resultados.

## Tecnologias
- Python 3.11 o superior
- Tkinter para la interfaz grafica
- SQLite para datos relacionales
- MongoDB 7 para documentos
- PyMongo para la conexion con MongoDB
- Docker Compose para iniciar MongoDB
- Git y GitHub para control de versiones

## Requisitos
- Python instalado
- Docker Desktop instalado y en ejecucion
- Git (para publicar el repositorio)

## Instalacion en Windows
1. Abre PowerShell en la carpeta del proyecto.
2. Crea y activa el entorno virtual:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instala las dependencias:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Crea la configuracion privada:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Abre `.env` y cambia `MONGO_PASSWORD` por una clave propia.
6. Inicia MongoDB:

   ```powershell
   docker compose up -d
   docker compose ps
   ```

7. Ejecuta la aplicacion:

   ```powershell
   python main.py
   ```

SQLite se crea automaticamente en `data/ide_sqlite.db`. No requiere servidor aparte.

## Conexion a las bases
- **SQLite:** archivo local `data/ide_sqlite.db`; el programa se conecta automaticamente.
- **MongoDB:** version configurada 7, puerto local 27017, base de datos `mini_ide`. El usuario y la clave se leen de `.env`.
- Docker publica MongoDB solamente en la interfaz local `127.0.0.1`.

## Ejemplos SQL
Ejecuta una sentencia a la vez en el editor SQL.

Crear tabla:

```sql
CREATE TABLE productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0
);
```

Insertar:

```sql
INSERT INTO productos (nombre, precio, stock)
VALUES ('Teclado', 150.00, 10);
```

Consultar:

```sql
SELECT * FROM productos;
```

Actualizar:

```sql
UPDATE productos SET precio = 175.00 WHERE id = 1;
```

Eliminar:

```sql
DELETE FROM productos WHERE id = 1;
```

Modificar estructura:

```sql
ALTER TABLE productos ADD COLUMN categoria TEXT;
```

Eliminar tabla de prueba:

```sql
DROP TABLE productos;
```

## Ejemplos MongoDB
Selecciona el modo MongoDB e introduce cada objeto JSON por separado.

Crear coleccion:

```json
{
  "action": "createCollection",
  "collection": "productos"
}
```

Insertar documento:

```json
{
  "action": "insertOne",
  "collection": "productos",
  "document": {
    "nombre": "Teclado",
    "precio": 150,
    "stock": 10
  }
}
```

Consultar documentos:

```json
{
  "action": "find",
  "collection": "productos",
  "filter": {}
}
```

Actualizar:

```json
{
  "action": "updateOne",
  "collection": "productos",
  "filter": {"nombre": "Teclado"},
  "update": {"$set": {"precio": 175}}
}
```

Eliminar un documento (el filtro debe identificar el documento):

```json
{
  "action": "deleteOne",
  "collection": "productos",
  "filter": {"nombre": "Teclado"}
}
```

Contar documentos:

```json
{
  "action": "countDocuments",
  "collection": "productos",
  "filter": {}
}
```

## Estructura
```text
mini_ide_bases_datos/
|-- main.py
|-- requirements.txt
|-- docker-compose.yml
|-- .env.example
|-- .gitignore
|-- README.md
|-- data/
|-- capturas/
`-- documentacion/
```

## Capturas
Guarda capturas reales en `capturas/` que muestren:
1. La aplicacion abierta.
2. Una consulta SQL con resultados.
3. Una operacion MongoDB con resultados.
4. Conexion exitosa a MongoDB.

Las capturas deben agregarse al README una vez tomadas. No se incluyen capturas ficticias en esta plantilla.

## Reflexion personal
**Completar despues de probar la aplicacion.** Describe los retos reales que encontraste, como configuraste las conexiones y que aprendiste sobre las diferencias entre SQL y NoSQL.

## Autor
- Nombre completo: [ESCRIBE TU NOMBRE]
- Carnet: [ESCRIBE TU CARNET]
- Curso: [ESCRIBE EL NOMBRE DEL CURSO]

## Repositorio
[PEGA AQUI LA URL PUBLICA DE GITHUB]

## Limitaciones conocidas
- El editor SQL ejecuta una sentencia por vez.
- MongoDB usa un conjunto de operaciones JSON definido por la aplicacion; no es una consola completa de Mongo Shell.
- Prueba las operaciones de actualizacion y eliminacion solo con datos de prueba.
