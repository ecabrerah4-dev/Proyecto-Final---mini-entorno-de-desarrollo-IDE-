import json
import os
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.errors import PyMongoError


# CONFIGURACION GENERAL


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
SQL_PATH = BASE_DIR / "chinook-database-master" / "ChinookDatabase" / "DataSources" / "Chinook_Sqlite.sqlite"

SQL_EJEMPLO = """CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0
);"""

MONGO_EJEMPLO = """{
    "action": "find",
    "collection": "productos",
    "filter": {}
}"""


def cargar_env():
    """Carga variables sencillas desde .env sin dependencias adicionales."""
    archivo = BASE_DIR / ".env"
    if not archivo.exists():
        return
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def a_texto(valor):
    """Convierte valores a texto legible para mostrarlos en la tabla."""
    return json.dumps(valor, ensure_ascii=False, default=str)


class MiniIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini IDE de Bases de Datos SQL y NoSQL")
        self.root.geometry("1100x720")
        self.root.minsize(850, 600)

        self.sql_conn = None
        self.mongo_client = None
        self.mongo_db = None

        self.modo = tk.StringVar(value="SQL")
        self.estado_sql = tk.StringVar(value="SQL: desconectado")
        self.estado_mongo = tk.StringVar(value="MongoDB: desconectado")
        self.estado_general = tk.StringVar(value="Listo para trabajar")

        self.crear_interfaz()
        self.conectar_sql()
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)


    # CONEXIONES


    def conectar_sql(self):
        try:
            self.sql_conn = sqlite3.connect(SQL_PATH)
            self.sql_conn.execute("PRAGMA foreign_keys = ON")
            self.estado_sql.set("SQL: conectado (SQLite)")
        except sqlite3.Error as error:
            self.estado_sql.set("SQL: error de conexion")
            messagebox.showerror("Error SQL", str(error))

    def conectar_mongo(self):
        cargar_env()
        try:
            host = os.getenv("MONGO_HOST", "localhost")
            puerto = int(os.getenv("MONGO_PORT", "27017"))
            usuario = os.getenv("MONGO_USER", "ide_admin")
            clave = os.getenv("MONGO_PASSWORD", "")
            auth_db = os.getenv("MONGO_AUTH_DB", "admin")
            nombre_db = os.getenv("MONGO_DATABASE", "mini_ide")

            if self.mongo_client:
                self.mongo_client.close()
                self.mongo_client = None
                self.mongo_db = None

            if clave:
                uri = (
                    f"mongodb://{quote_plus(usuario)}:{quote_plus(clave)}"
                    f"@{host}:{puerto}/?authSource={quote_plus(auth_db)}"
                )
            else:
                uri = f"mongodb://{host}:{puerto}/"

            cliente = MongoClient(uri, serverSelectionTimeoutMS=3000)
            cliente.admin.command("ping")
            self.mongo_client = cliente
            self.mongo_db = cliente[nombre_db]
            self.estado_mongo.set("MongoDB: conectado")
            self.estado_general.set("Conexion con MongoDB exitosa")
            messagebox.showinfo(
                "Conexion",
                f"Conexion exitosa a MongoDB.\nBase de datos: {nombre_db}"
            )
        except (PyMongoError, ValueError, OSError) as error:
            if self.mongo_client:
                self.mongo_client.close()
            self.mongo_client = None
            self.mongo_db = None
            self.estado_mongo.set("MongoDB: desconectado")
            messagebox.showerror(
                "Error de conexion",
                "No fue posible conectar con MongoDB.\n\n"
                f"{error}\n\nVerifica Docker, el archivo .env y las credenciales."
            )


    # INTERFAZ


    def crear_interfaz(self):
        contenedor = ttk.Frame(self.root, padding=10)
        contenedor.pack(fill="both", expand=True)

        ttk.Label(
            contenedor, text="MINI IDE DE BASES DE DATOS",
            font=("Arial", 17, "bold")
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            contenedor,
            text="Editor de consultas SQL y operaciones MongoDB"
        ).pack(anchor="w", pady=(0, 10))

        barra = ttk.Frame(contenedor)
        barra.pack(fill="x", pady=5)
        ttk.Label(barra, text="Motor de base de datos:").pack(side="left")

        selector = ttk.Combobox(
            barra, textvariable=self.modo, values=("SQL", "MongoDB"),
            state="readonly", width=12
        )
        selector.pack(side="left", padx=8)
        selector.bind("<<ComboboxSelected>>", self.cambiar_modo)

        ttk.Button(
            barra, text="Probar conexion MongoDB",
            command=self.conectar_mongo
        ).pack(side="left", padx=5)

        estados = ttk.Frame(contenedor)
        estados.pack(fill="x", pady=4)
        ttk.Label(estados, textvariable=self.estado_sql).pack(
            side="left", padx=(0, 18)
        )
        ttk.Label(estados, textvariable=self.estado_mongo).pack(side="left")

        ttk.Label(
            contenedor, text="Editor de comandos",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=(10, 4))

        self.editor = tk.Text(
            contenedor, height=12, wrap="none",
            font=("Consolas", 10), undo=True
        )
        self.editor.pack(fill="both", expand=False)

        botones = ttk.Frame(contenedor)
        botones.pack(fill="x", pady=8)
        ttk.Button(
            botones, text="Ejecutar comando", command=self.ejecutar
        ).pack(side="left", padx=(0, 5))
        ttk.Button(
            botones, text="Cargar ejemplo", command=self.cargar_ejemplo
        ).pack(side="left", padx=5)
        ttk.Button(
            botones, text="Limpiar editor",
            command=lambda: self.editor.delete("1.0", "end")
        ).pack(side="left", padx=5)

        ttk.Label(
            contenedor, text="Resultados",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=(5, 4))

        marco_tabla = ttk.Frame(contenedor)
        marco_tabla.pack(fill="both", expand=True)
        self.tabla = ttk.Treeview(marco_tabla, show="headings")
        barra_y = ttk.Scrollbar(
            marco_tabla, orient="vertical", command=self.tabla.yview
        )
        barra_x = ttk.Scrollbar(
            marco_tabla, orient="horizontal", command=self.tabla.xview
        )
        self.tabla.configure(
            yscrollcommand=barra_y.set, xscrollcommand=barra_x.set
        )
        self.tabla.grid(row=0, column=0, sticky="nsew")
        barra_y.grid(row=0, column=1, sticky="ns")
        barra_x.grid(row=1, column=0, sticky="ew")
        marco_tabla.rowconfigure(0, weight=1)
        marco_tabla.columnconfigure(0, weight=1)

        ttk.Label(
            contenedor, textvariable=self.estado_general,
            relief="sunken", anchor="w"
        ).pack(fill="x", pady=(8, 0))

        self.cargar_ejemplo()

    def cambiar_modo(self, evento=None):
        self.cargar_ejemplo()
        self.estado_general.set(
            "Modo SQL seleccionado" if self.modo.get() == "SQL"
            else "Modo MongoDB seleccionado"
        )

    def cargar_ejemplo(self):
        self.editor.delete("1.0", "end")
        texto = SQL_EJEMPLO if self.modo.get() == "SQL" else MONGO_EJEMPLO
        self.editor.insert("1.0", texto)


    # RESULTADOS


    def limpiar_resultados(self):
        self.tabla.delete(*self.tabla.get_children())
        self.tabla["columns"] = ()

    def mostrar_resultados(self, columnas, filas):
        self.limpiar_resultados()
        self.tabla["columns"] = columnas
        for columna in columnas:
            self.tabla.heading(columna, text=columna)
            self.tabla.column(columna, width=150, minwidth=80)
        for fila in filas:
            self.tabla.insert("", "end", values=[a_texto(v) for v in fila])


    # SQL: UNA SENTENCIA POR EJECUCION


    def ejecutar_sql(self, comando):
        if self.sql_conn is None:
            raise sqlite3.Error("No existe una conexion SQL activa.")

        cursor = self.sql_conn.cursor()
        try:
            cursor.execute(comando)
            if cursor.description:
                columnas = [col[0] for col in cursor.description]
                filas = cursor.fetchall()
                self.mostrar_resultados(columnas, filas)
                mensaje = f"Consulta exitosa: {len(filas)} registro(s)."
            else:
                self.sql_conn.commit()
                self.limpiar_resultados()
                mensaje = (
                    "Comando ejecutado correctamente. "
                    f"Filas afectadas: {max(cursor.rowcount, 0)}."
                )
            self.estado_general.set(mensaje)
            messagebox.showinfo("SQL", mensaje)
        except sqlite3.Error:
            self.sql_conn.rollback()
            raise
        finally:
            cursor.close()


    # MONGODB: COMANDOS JSON CONTROLADOS
   

    def ejecutar_mongo(self, comando):
        if self.mongo_db is None:
            raise RuntimeError(
                "Primero conecta MongoDB con el boton de conexion."
            )

        try:
            operacion = json.loads(comando)
        except json.JSONDecodeError as error:
            raise ValueError(f"El comando no es JSON valido: {error}")

        if not isinstance(operacion, dict):
            raise ValueError("El comando debe ser un objeto JSON.")

        accion = operacion.get("action")
        coleccion = operacion.get("collection")
        acciones_validas = {
            "createCollection", "dropCollection", "insertOne",
            "find", "updateOne", "deleteOne", "countDocuments"
        }
        if accion not in acciones_validas:
            raise ValueError(
                "Accion no valida. Usa: " + ", ".join(sorted(acciones_validas))
            )
        if not isinstance(coleccion, str) or not coleccion.strip():
            raise ValueError("Debes indicar el nombre de la coleccion.")

        nombre = coleccion.strip()
        if nombre.startswith("system."):
            raise ValueError("No se permite modificar colecciones del sistema.")

        if accion == "createCollection":
            if nombre in self.mongo_db.list_collection_names():
                raise ValueError("La coleccion ya existe.")
            self.mongo_db.create_collection(nombre)
            mensaje = f"Coleccion '{nombre}' creada."
            self.mostrar_resultados(["resultado"], [[mensaje]])

        elif accion == "dropCollection":
            if nombre not in self.mongo_db.list_collection_names():
                raise ValueError("La coleccion no existe.")
            confirmar = messagebox.askyesno(
                "Confirmar eliminacion",
                f"Eliminar la coleccion '{nombre}' y todos sus documentos?"
            )
            if not confirmar:
                self.estado_general.set("Operacion cancelada.")
                return
            self.mongo_db.drop_collection(nombre)
            mensaje = f"Coleccion '{nombre}' eliminada."
            self.mostrar_resultados(["resultado"], [[mensaje]])

        elif accion == "insertOne":
            documento = operacion.get("document")
            if not isinstance(documento, dict):
                raise ValueError("'document' debe ser un objeto JSON.")
            resultado = self.mongo_db[nombre].insert_one(documento)
            mensaje = f"Documento insertado. ID: {resultado.inserted_id}"
            self.mostrar_resultados(["resultado"], [[mensaje]])

        elif accion == "find":
            filtro = operacion.get("filter", {})
            if not isinstance(filtro, dict):
                raise ValueError("'filter' debe ser un objeto JSON.")
            limite = operacion.get("limit", 100)
            if not isinstance(limite, int) or isinstance(limite, bool):
                raise ValueError("'limit' debe ser un numero entero.")
            if not 1 <= limite <= 1000:
                raise ValueError("'limit' debe estar entre 1 y 1000.")

            documentos = list(self.mongo_db[nombre].find(filtro).limit(limite))
            if documentos:
                columnas = list(dict.fromkeys(
                    clave for doc in documentos for clave in doc.keys()
                ))
                filas = [
                    [doc.get(columna, "") for columna in columnas]
                    for doc in documentos
                ]
                self.mostrar_resultados(columnas, filas)
            else:
                self.mostrar_resultados(["resultado"], [["Sin registros"]])
            mensaje = f"Consulta exitosa: {len(documentos)} documento(s)."
            self.estado_general.set(mensaje)
            messagebox.showinfo("MongoDB", mensaje)
            return

        elif accion == "updateOne":
            filtro = operacion.get("filter")
            cambios = operacion.get("update")
            if not isinstance(filtro, dict) or not isinstance(cambios, dict):
                raise ValueError("'filter' y 'update' deben ser objetos JSON.")
            if not cambios or not all(k.startswith("$") for k in cambios):
                raise ValueError("'update' debe usar operadores, por ejemplo '$set'.")
            resultado = self.mongo_db[nombre].update_one(filtro, cambios)
            mensaje = (
                f"Coincidencias: {resultado.matched_count}. "
                f"Modificados: {resultado.modified_count}."
            )
            self.mostrar_resultados(["resultado"], [[mensaje]])

        elif accion == "deleteOne":
            filtro = operacion.get("filter")
            if not isinstance(filtro, dict):
                raise ValueError("'filter' debe ser un objeto JSON.")
            if not filtro:
                raise ValueError(
                    "Para evitar borrar accidentalmente, 'filter' no puede estar vacio."
                )
            resultado = self.mongo_db[nombre].delete_one(filtro)
            mensaje = f"Documentos eliminados: {resultado.deleted_count}."
            self.mostrar_resultados(["resultado"], [[mensaje]])

        elif accion == "countDocuments":
            filtro = operacion.get("filter", {})
            if not isinstance(filtro, dict):
                raise ValueError("'filter' debe ser un objeto JSON.")
            cantidad = self.mongo_db[nombre].count_documents(filtro)
            mensaje = f"Total de documentos: {cantidad}."
            self.mostrar_resultados(["cantidad"], [[cantidad]])

        self.estado_general.set(mensaje)
        messagebox.showinfo("MongoDB", mensaje)

    def ejecutar(self):
        comando = self.editor.get("1.0", "end").strip()
        if not comando:
            messagebox.showwarning(
                "Comando vacio", "Escribe un comando antes de ejecutar."
            )
            return
        try:
            if self.modo.get() == "SQL":
                self.ejecutar_sql(comando)
            else:
                self.ejecutar_mongo(comando)
        except (sqlite3.Error, PyMongoError, ValueError, RuntimeError) as error:
            self.estado_general.set(f"Error: {error}")
            messagebox.showerror("Error al ejecutar", str(error))

    def cerrar(self):
        if self.sql_conn:
            self.sql_conn.close()
        if self.mongo_client:
            self.mongo_client.close()
        self.root.destroy()


if __name__ == "__main__":
    cargar_env()
    ventana = tk.Tk()
    aplicacion = MiniIDE(ventana)
    ventana.mainloop()
