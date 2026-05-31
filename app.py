from datetime import datetime

from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from werkzeug.utils import secure_filename
from autos import Autos

app = Flask(__name__)

app.secret_key = "324234234"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

ADMIN_EMAIL = 'agenciaautos67@gmail.com'
ADMIN_PHONE = '6561234567'

autos = Autos()

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'agenciaautos67@gmail.com'
app.config['MAIL_PASSWORD'] = 'hjlernporwxwkbpl'

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def guardar_imagen(imagen):
    if imagen and imagen.filename:
        if not allowed_file(imagen.filename):
            return None

        fecha = datetime.now().strftime("%Y%m%d%H%M%S")
        nombre_archivo = fecha + "_" + secure_filename(imagen.filename)
        ruta_archivo = app.config['UPLOAD_FOLDER'] + '/' + nombre_archivo
        imagen.save(ruta_archivo)
        return "uploads/" + nombre_archivo

    return None


def login_requerido():
    if "usuario" not in session:
        flash("Debes iniciar sesión", "warning")
        return False
    return True


def admin_requerido():
    if not login_requerido():
        return False

    if session.get("rol") != "admin":
        flash("Solo el dueño o administrador puede hacer esta acción", "danger")
        return False

    return True


@app.route("/")
def index():
    if not login_requerido():
        return redirect(url_for("login"))

    return render_template(
        "index.html",
        usuario=session["usuario"],
        rol=session.get("rol"),
        total_autos=autos.contar_reportes(),
        total_cotizaciones=autos.contar_cotizaciones(),
        total_solicitudes=autos.contar_solicitudes_venta(),
        admin_phone=ADMIN_PHONE
    )


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        telefono = request.form.get("telefono", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not nombre or not email or not telefono or not password:
            flash("Completa todos los campos", "danger")
            return redirect(url_for("registro"))

        if password != confirm_password:
            flash("Las contraseñas no coinciden", "danger")
            return redirect(url_for("registro"))

        if len(password) < 6:
            flash("La contraseña debe tener mínimo 6 caracteres", "danger")
            return redirect(url_for("registro"))

        rol = "admin" if email == ADMIN_EMAIL else "cliente"
        usuario = autos.registrar_usuario(nombre, email, telefono, password, rol)

        if usuario:
            flash("Usuario registrado correctamente", "success")
            return redirect(url_for("login"))

        flash("Ese correo ya existe", "danger")
        return redirect(url_for("registro"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        usuario = autos.iniciar_sesion(email, password)

        if usuario:
            session["usuario"] = usuario["nombre"]
            session["usuario_id"] = usuario["_id"]
            session["rol"] = usuario.get("rol", "cliente")
            session["telefono"] = usuario.get("telefono", "")
            flash("Bienvenido", "success")
            return redirect(url_for("index"))

        flash("Correo o contraseña incorrectos", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route('/recuperar-contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        usuario = autos.usuarios.find_one({"email": email})

        if usuario and app.config['MAIL_PASSWORD']:
            token = s.dumps(email, salt='recuperacion-pass')
            enlace = url_for('restablecer_contrasena', token=token, _external=True)
            msg = Message('Recuperación de contraseña', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Para restablecer tu contraseña, entra al siguiente enlace. Caduca en 1 hora:\n\n{enlace}'

            try:
                mail.send(msg)
            except Exception as e:
                print(f"Error al enviar el correo: {e}")

        flash('Si el correo existe, se enviaron las instrucciones.', 'success')
        return redirect(url_for('login'))

    return render_template("recuperar.html")


@app.route('/restablecer-contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    try:
        email = s.loads(token, salt='recuperacion-pass', max_age=3600)
    except SignatureExpired:
        flash('El enlace de recuperación expiró. Solicita uno nuevo.', 'danger')
        return redirect(url_for('recuperar_contrasena'))
    except Exception:
        flash('Enlace inválido.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nueva_password = request.form.get('password', '')

        if len(nueva_password) < 6:
            flash('La contraseña debe tener mínimo 6 caracteres.', 'danger')
            return redirect(url_for('restablecer_contrasena', token=token))

        exito = autos.actualizar_contrasena(email, nueva_password)
        flash('Contraseña actualizada. Ya puedes iniciar sesión.' if exito else 'Hubo un problema actualizando la contraseña.', 'success' if exito else 'danger')
        return redirect(url_for('login'))

    return render_template("restablecer_contrasena.html", token=token)


@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if not admin_requerido():
        return redirect(url_for("index") if "usuario" in session else url_for("login"))

    if request.method == "POST":
        datos = leer_datos_vehiculo()
        imagen = request.files.get("imagen")
        imagen_url = guardar_imagen(imagen)

        if imagen and imagen.filename and not imagen_url:
            flash("Formato de imagen no permitido. Usa png, jpg, jpeg o gif.", "danger")
            return redirect(url_for("agregar"))

        if not validar_datos_vehiculo(datos):
            return redirect(url_for("agregar"))

        reporte_id = autos.subir_reporte(session["usuario_id"], imagen_url=imagen_url, **datos)

        if reporte_id:
            flash("Vehículo publicado correctamente", "success")
            return redirect(url_for("comprar"))

        flash("No se pudo publicar el vehículo. Intenta de nuevo.", "danger")
        return redirect(url_for("agregar"))

    return render_template("agregar_vehiculo.html")


def leer_datos_vehiculo():
    datos = {
        "titulo": request.form.get("titulo", "").strip(),
        "marca": request.form.get("marca", "").strip(),
        "modelo": request.form.get("modelo", "").strip(),
        "anio": request.form.get("anio", "").strip(),
        "precio": request.form.get("precio", "").strip(),
        "kilometraje": request.form.get("kilometraje", "").strip(),
        "color": request.form.get("color", "").strip(),
        "transmision": request.form.get("transmision", "").strip(),
        "telefono": request.form.get("telefono", "").strip(),
        "ubicacion": request.form.get("ubicacion", "").strip(),
        "descripcion": request.form.get("descripcion", "").strip(),
        "estado": request.form.get("estado", "Disponible").strip() or "Disponible"
    }

    try:
        datos["anio"] = int(datos["anio"])
        datos["precio"] = float(datos["precio"])
        datos["kilometraje"] = int(datos["kilometraje"])
    except ValueError:
        pass

    return datos


def validar_datos_vehiculo(datos):
    campos = ["titulo", "marca", "modelo", "anio", "precio", "kilometraje", "telefono", "descripcion"]
    if any(not datos.get(campo) for campo in campos):
        flash("Completa los campos obligatorios", "danger")
        return False

    if not isinstance(datos.get("anio"), int) or not isinstance(datos.get("precio"), float) or not isinstance(datos.get("kilometraje"), int):
        flash("Año, precio y kilometraje deben ser números", "danger")
        return False

    if datos["anio"] < 2000 or datos["anio"] > 2030:
        flash("Revisa el año del vehículo", "danger")
        return False

    return True


@app.route('/comprar')
def comprar():
    if not login_requerido():
        return redirect(url_for("login"))

    filtros = {
        "q": request.args.get("q", "").strip(),
        "marca": request.args.get("marca", "").strip(),
        "precio_max": request.args.get("precio_max", "").strip(),
        "anio_min": request.args.get("anio_min", "").strip(),
        "estado": request.args.get("estado", "").strip(),
    }
    reportes = autos.obtener_reportes(filtros)
    marcas = autos.obtener_marcas()
    return render_template("compar.html", reportes=reportes, marcas=marcas, filtros=filtros, rol=session.get("rol"), admin_phone=ADMIN_PHONE)


@app.route('/cotizar/<reporte_id>', methods=['GET', 'POST'])
def cotizar(reporte_id):
    if not login_requerido():
        return redirect(url_for("login"))

    reporte = autos.obtener_reporte_por_id(reporte_id)
    if not reporte:
        flash("Vehículo no encontrado", "danger")
        return redirect(url_for("comprar"))

    if request.method == "POST":
        datos = {
            "reporte_id": reporte_id,
            "vehiculo": reporte.get("titulo", ""),
            "nombre": request.form.get("nombre", "").strip(),
            "telefono": request.form.get("telefono", "").strip(),
            "email": request.form.get("email", "").strip(),
            "enganche": request.form.get("enganche", "").strip(),
            "mensaje": request.form.get("mensaje", "").strip(),
        }

        if not datos["nombre"] or not datos["telefono"]:
            flash("Nombre y teléfono son obligatorios", "danger")
            return redirect(url_for("cotizar", reporte_id=reporte_id))

        autos.guardar_cotizacion(datos)
        flash("Cotización enviada. El vendedor te contactará pronto.", "success")
        return redirect(url_for("comprar"))

    return render_template("cotizar.html", reporte=reporte, usuario=session.get("usuario"), telefono=session.get("telefono"), admin_phone=ADMIN_PHONE)


@app.route('/vender', methods=['GET', 'POST'])
def vender():
    if not login_requerido():
        return redirect(url_for("login"))

    if request.method == "POST":
        imagen = request.files.get("imagen")
        imagen_url = guardar_imagen(imagen)

        if imagen and imagen.filename and not imagen_url:
            flash("Formato de imagen no permitido. Usa png, jpg, jpeg o gif.", "danger")
            return redirect(url_for("vender"))

        datos = {
            "nombre": request.form.get("nombre", "").strip(),
            "telefono": request.form.get("telefono", "").strip(),
            "email": request.form.get("email", "").strip(),
            "marca": request.form.get("marca", "").strip(),
            "modelo": request.form.get("modelo", "").strip(),
            "anio": request.form.get("anio", "").strip(),
            "kilometraje": request.form.get("kilometraje", "").strip(),
            "precio_deseado": request.form.get("precio_deseado", "").strip(),
            "mensaje": request.form.get("mensaje", "").strip(),
            "imagen_url": imagen_url
        }

        if not datos["nombre"] or not datos["telefono"] or not datos["marca"] or not datos["modelo"]:
            flash("Completa nombre, teléfono, marca y modelo", "danger")
            return redirect(url_for("vender"))

        autos.guardar_solicitud_venta(datos)
        flash("Tu solicitud fue enviada. AutoLux te contactará para revisar tu vehículo.", "success")
        return redirect(url_for("comprar"))

    return render_template("vender.html", usuario=session.get("usuario"), telefono=session.get("telefono"), admin_phone=ADMIN_PHONE)


@app.route('/contacto')
def contacto():
    if not login_requerido():
        return redirect(url_for("login"))
    return render_template("contacto.html", admin_phone=ADMIN_PHONE)


@app.route('/admin/mensajes')
def mensajes_admin():
    if not admin_requerido():
        return redirect(url_for("index") if "usuario" in session else url_for("login"))

    cotizaciones = autos.obtener_cotizaciones()
    solicitudes = autos.obtener_solicitudes_venta()
    return render_template("mensajes_admin.html", cotizaciones=cotizaciones, solicitudes=solicitudes)


@app.route('/eliminar/<reporte_id>', methods=['POST'])
def eliminar(reporte_id):
    if not admin_requerido():
        return redirect(url_for("index") if "usuario" in session else url_for("login"))

    exito = autos.eliminar_reporte_admin(reporte_id)
    flash("Vehículo eliminado" if exito else "No se pudo eliminar el vehículo", "success" if exito else "danger")
    return redirect(url_for("comprar"))


@app.route("/editar/<reporte_id>", methods=["GET", "POST"])
def editar(reporte_id):
    if not admin_requerido():
        return redirect(url_for("index") if "usuario" in session else url_for("login"))

    reporte = autos.obtener_reporte_por_id(reporte_id)
    if not reporte:
        flash("Vehículo no encontrado", "danger")
        return redirect(url_for("comprar"))

    if request.method == "POST":
        datos = leer_datos_vehiculo()
        if not validar_datos_vehiculo(datos):
            return redirect(url_for("editar", reporte_id=reporte_id))

        imagen = request.files.get("imagen")
        imagen_url = guardar_imagen(imagen)

        if imagen and imagen.filename and not imagen_url:
            flash("Formato de imagen no permitido. Usa png, jpg, jpeg o gif.", "danger")
            return redirect(url_for("editar", reporte_id=reporte_id))

        if imagen_url:
            datos["imagen_url"] = imagen_url

        autos.editar_reporte(reporte_id, datos)
        flash("Vehículo actualizado correctamente", "success")
        return redirect(url_for("comprar"))

    return render_template("editar_vehiculo.html", reporte=reporte)


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "warning")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
