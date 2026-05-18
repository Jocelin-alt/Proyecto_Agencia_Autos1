from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional, Dict
from werkzeug.security import generate_password_hash, check_password_hash

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

        """Registrar nuevo usuario con contraseña encriptada"""
        try:
            
            password_encriptada = generate_password_hash(password)

            resultado = self.usuarios.insert_one({
                "nombre": nombre,
                "email": email,
                "password": password_encriptada, 
                "fecha_registro": datetime.now(),
                "activo": True
            })

            print("✅ Usuario registrado de forma segura")
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

        """Login de usuario verificando el hash"""
        try:
            usuario = self.usuarios.find_one({
                "email": email
            })

            
            if usuario and check_password_hash(usuario.get("password", ""), password):
                usuario["_id"] = str(usuario["_id"])
                print("✅ Login correcto")
                return usuario

            print("❌ Correo o contraseña incorrectos")
            return None

        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    # =========================================
    # ACTUALIZAR CONTRASEÑA (NUEVO)
    # =========================================

    def actualizar_contrasena(self, email: str, nueva_password: str) -> bool:
        """Encripta y actualiza la contraseña de un usuario existente"""
        try:
           
            password_encriptada = generate_password_hash(nueva_password)
            
          
            resultado = self.usuarios.update_one(
                {"email": email},
                {"$set": {"password": password_encriptada}}
            )
            
            if resultado.modified_count > 0:
                print("✅ Contraseña actualizada en la base de datos")
                return True
            else:
                print("⚠️ No se actualizó. El correo no existe o la contraseña es la misma.")
                return False
                
        except Exception as e:
            print(f"❌ Error al actualizar contraseña: {e}")
            return False

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
    
    sistema = Autos()

    usuario_id = sistema.registrar_usuario(
        "Alan",
        "alan@gmail.com",
        "123456"
    )
    print(usuario_id)

    usuario = sistema.iniciar_sesion(
        "alan@gmail.com",
        "123456"
    )
    print(usuario)

if __name__ == "__main__":
    ejemplo()