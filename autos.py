from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional, Dict


class Autos:

    def __init__(
        self,
        uri: str = "mongodb+srv://alanignacio17092000_db_user:xLdxNlTApaV2ClSI@cluster0.rr7fa9o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    ):
        

        try:
            self.cliente = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000
            )

            self.cliente.admin.command('ping')

            # Base de datos
            self.db = self.cliente['venta_autos']

            # Colecciones
            self.usuarios = self.db['usuarios']
            self.reportes = self.db['reportes']

            # Índices
            self._crear_indices()

            print("✅ Conectado a MongoDB Atlas")

        except ConnectionFailure:
            print("❌ Error conectando a MongoDB Atlas")
            raise

    def _crear_indices(self):
        """Crear índices"""

        self.usuarios.create_index(
            "email",
            unique=True
        )

        self.reportes.create_index(
            [("usuario_id", 1)]
        )

    # =========================================
    # REGISTRO
    # =========================================

    def registrar_usuario(
        self,
        nombre: str,
        email: str,
        password: str
    ) -> Optional[str]:

        """Registrar nuevo usuario"""

        try:

            resultado = self.usuarios.insert_one({
                "nombre": nombre,
                "email": email,
                "password": password,
                "fecha_registro": datetime.now(),
                "activo": True
            })

            print("✅ Usuario registrado")

            return str(resultado.inserted_id)

        except DuplicateKeyError:

            print("❌ Ese correo ya está registrado")

            return None

    # =========================================
    # LOGIN
    # =========================================

    def iniciar_sesion(
        self,
        email: str,
        password: str
    ) -> Optional[Dict]:

        """Login de usuario"""

        try:

            usuario = self.usuarios.find_one({
                "email": email
            })

            if usuario:

                if usuario.get("password") == password:

                    usuario["_id"] = str(usuario["_id"])

                    print("✅ Login correcto")

                    return usuario

            print("❌ Correo o contraseña incorrectos")

            return None

        except Exception as e:

            print(f"❌ Error: {e}")

            return None

    # =========================================
    # OBTENER USUARIO
    # =========================================

    def obtener_usuario(
        self,
        usuario_id: str
    ) -> Optional[Dict]:

        try:

            usuario = self.usuarios.find_one({
                "_id": ObjectId(usuario_id)
            })

            if usuario:
                usuario["_id"] = str(usuario["_id"])

            return usuario

        except Exception as e:

            print(f"❌ Error: {e}")

            return None

    # =========================================
    # SUBIR REPORTE / PUBLICACIÓN
    # =========================================

    def subir_reporte(
        self,
        usuario_id: str,
        titulo: str,
        descripcion: str
    ) -> Optional[str]:

        """Subir reporte/publicación de auto"""

        try:

            reporte = {
                "usuario_id": ObjectId(usuario_id),
                "titulo": titulo,
                "descripcion": descripcion,
                "fecha_publicacion": datetime.now(),
                "activo": True
            }

            resultado = self.reportes.insert_one(reporte)

            print("✅ Reporte publicado")

            return str(resultado.inserted_id)

        except Exception as e:

            print(f"❌ Error: {e}")

            return None

    # =========================================
    # CERRAR CONEXIÓN
    # =========================================

    def cerrar_conexion(self):

        if self.cliente:

            self.cliente.close()

            print("🔌 Conexión cerrada")




def ejemplo():

    sistema = GestorAutos()


    usuario_id = sistema.registrar_usuario(
        "Alan",
        "alan@gmail.com",
        "123456"
    )

    print(usuario_id)

    #
    usuario = sistema.iniciar_sesion(
        "alan@gmail.com",
        "123456"
    )

    print(usuario)




if __name__ == "__main__":
    ejemplo()