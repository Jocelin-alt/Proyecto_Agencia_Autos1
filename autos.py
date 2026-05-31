from datetime import datetime
from typing import Optional, Dict

from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from werkzeug.security import generate_password_hash, check_password_hash


class Autos:
    def __init__(self, uri: str = "mongodb+srv://alanignacio17092000_db_user:xLdxNlTApaV2ClSI@cluster0.rr7fa9o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"):
        try:
            self.cliente = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.cliente.admin.command('ping')

            self.db = self.cliente['venta_autos']
            self.usuarios = self.db['usuarios']
            self.reportes = self.db['reportes']
            self.cotizaciones = self.db['cotizaciones']
            self.solicitudes_venta = self.db['solicitudes_venta']

            self._crear_indices()
            print("✅ Conectado a MongoDB Atlas")

        except ConnectionFailure:
            print("❌ Error conectando a MongoDB Atlas")
            raise

    def _crear_indices(self):
        self.usuarios.create_index("email", unique=True)
        self.reportes.create_index([("usuario_id", 1)])
        self.reportes.create_index([("activo", 1), ("fecha_publicacion", -1)])
        self.cotizaciones.create_index([("fecha", -1)])
        self.solicitudes_venta.create_index([("fecha", -1)])

    def registrar_usuario(self, nombre: str, email: str, telefono: str, password: str, rol: str = "cliente") -> Optional[str]:
        try:
            password_encriptada = generate_password_hash(password)
            resultado = self.usuarios.insert_one({
                "nombre": nombre,
                "email": email,
                "telefono": telefono,
                "password": password_encriptada,
                "rol": rol,
                "fecha_registro": datetime.now(),
                "activo": True
            })
            return str(resultado.inserted_id)

        except DuplicateKeyError:
            print("❌ Ese correo ya está registrado")
            return None

    def iniciar_sesion(self, email: str, password: str) -> Optional[Dict]:
        try:
            usuario = self.usuarios.find_one({"email": email, "activo": True})

            if usuario and check_password_hash(usuario.get("password", ""), password):
                usuario["_id"] = str(usuario["_id"])
                return usuario

            return None

        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def actualizar_contrasena(self, email: str, nueva_password: str) -> bool:
        try:
            password_encriptada = generate_password_hash(nueva_password)
            resultado = self.usuarios.update_one(
                {"email": email},
                {"$set": {"password": password_encriptada}}
            )
            return resultado.modified_count > 0

        except Exception as e:
            print(f"❌ Error al actualizar contraseña: {e}")
            return False

    def subir_reporte(
        self,
        usuario_id: str,
        titulo: str,
        marca: str,
        modelo: str,
        anio: int,
        precio: float,
        kilometraje: int,
        color: str,
        transmision: str,
        telefono: str,
        ubicacion: str,
        descripcion: str,
        estado: str = "Disponible",
        imagen_url: str = None
    ) -> Optional[str]:
        try:
            reporte = {
                "usuario_id": ObjectId(usuario_id),
                "titulo": titulo,
                "marca": marca,
                "modelo": modelo,
                "anio": anio,
                "precio": precio,
                "kilometraje": kilometraje,
                "color": color,
                "transmision": transmision,
                "telefono": telefono,
                "ubicacion": ubicacion,
                "descripcion": descripcion,
                "estado": estado,
                "imagen_url": imagen_url,
                "fecha_publicacion": datetime.now(),
                "activo": True
            }

            resultado = self.reportes.insert_one(reporte)
            return str(resultado.inserted_id)

        except Exception as e:
            print(f"❌ Error al subir vehículo: {e}")
            return None

    def obtener_reporte_por_id(self, reporte_id):
        try:
            reporte = self.reportes.find_one({"_id": ObjectId(reporte_id)})
            if reporte:
                return self._limpiar_reporte(reporte)
            return None
        except Exception as e:
            print(f"❌ Error al obtener vehículo: {e}")
            return None

    def editar_reporte(self, reporte_id, datos):
        try:
            resultado = self.reportes.update_one(
                {"_id": ObjectId(reporte_id)},
                {"$set": datos}
            )
            return resultado.modified_count > 0
        except Exception as e:
            print(f"❌ Error al editar vehículo: {e}")
            return False

    def obtener_reportes(self, filtros=None):
        try:
            consulta = {"activo": True}
            filtros = filtros or {}

            if filtros.get("marca"):
                consulta["marca"] = filtros["marca"]

            if filtros.get("precio_max"):
                try:
                    consulta["precio"] = {"$lte": float(filtros["precio_max"])}
                except ValueError:
                    pass

            if filtros.get("anio_min"):
                try:
                    consulta["anio"] = {"$gte": int(filtros["anio_min"])}
                except ValueError:
                    pass

            if filtros.get("estado"):
                consulta["estado"] = filtros["estado"]

            if filtros.get("q"):
                texto = filtros["q"]
                consulta["$or"] = [
                    {"titulo": {"$regex": texto, "$options": "i"}},
                    {"marca": {"$regex": texto, "$options": "i"}},
                    {"modelo": {"$regex": texto, "$options": "i"}},
                    {"descripcion": {"$regex": texto, "$options": "i"}}
                ]

            reportes = list(self.reportes.find(consulta).sort("fecha_publicacion", -1))
            return [self._limpiar_reporte(reporte) for reporte in reportes]

        except Exception as e:
            print(f"❌ Error al obtener reportes: {e}")
            return []

    def contar_reportes(self):
        return self.reportes.count_documents({"activo": True})

    def contar_cotizaciones(self):
        return self.cotizaciones.count_documents({})

    def contar_solicitudes_venta(self):
        return self.solicitudes_venta.count_documents({})

    def obtener_marcas(self):
        try:
            marcas = self.reportes.distinct("marca", {"activo": True})
            return sorted([m for m in marcas if m])
        except Exception:
            return []

    def eliminar_reporte_admin(self, reporte_id: str) -> bool:
        try:
            resultado = self.reportes.update_one(
                {"_id": ObjectId(reporte_id)},
                {"$set": {"activo": False, "estado": "Eliminado"}}
            )
            return resultado.modified_count > 0
        except Exception as e:
            print(f"❌ Error al eliminar: {e}")
            return False

    def guardar_cotizacion(self, datos):
        try:
            datos["fecha"] = datetime.now()
            datos["atendido"] = False
            resultado = self.cotizaciones.insert_one(datos)
            return str(resultado.inserted_id)
        except Exception as e:
            print(f"❌ Error al guardar cotización: {e}")
            return None

    def guardar_solicitud_venta(self, datos):
        try:
            datos["fecha"] = datetime.now()
            datos["atendido"] = False
            resultado = self.solicitudes_venta.insert_one(datos)
            return str(resultado.inserted_id)
        except Exception as e:
            print(f"❌ Error al guardar solicitud de venta: {e}")
            return None

    def obtener_cotizaciones(self):
        try:
            cotizaciones = list(self.cotizaciones.find().sort("fecha", -1))
            for c in cotizaciones:
                c["_id"] = str(c["_id"])
                if "reporte_id" in c:
                    c["reporte_id"] = str(c["reporte_id"])
            return cotizaciones
        except Exception as e:
            print(f"❌ Error al obtener cotizaciones: {e}")
            return []

    def obtener_solicitudes_venta(self):
        try:
            solicitudes = list(self.solicitudes_venta.find().sort("fecha", -1))
            for s in solicitudes:
                s["_id"] = str(s["_id"])
            return solicitudes
        except Exception as e:
            print(f"❌ Error al obtener solicitudes: {e}")
            return []

    def _limpiar_reporte(self, reporte):
        reporte["_id"] = str(reporte["_id"])

        if "usuario_id" in reporte:
            reporte["usuario_id"] = str(reporte["usuario_id"])
        else:
            reporte["usuario_id"] = ""

        reporte.setdefault("estado", "Disponible")
        reporte.setdefault("imagen_url", "")
        reporte.setdefault("telefono", "")
        reporte.setdefault("ubicacion", "")
        reporte.setdefault("color", "")
        reporte.setdefault("transmision", "")
        reporte.setdefault("descripcion", "")
        reporte.setdefault("precio", 0)
        reporte.setdefault("kilometraje", 0)
        reporte.setdefault("anio", "")
        reporte.setdefault("marca", "")
        reporte.setdefault("modelo", "")
        reporte.setdefault("titulo", "Vehículo")

        return reporte

    def cerrar_conexion(self):
        if self.cliente:
            self.cliente.close()
