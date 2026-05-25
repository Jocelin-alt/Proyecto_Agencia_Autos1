import os
import uuid

from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from autos import Autos

app = Flask(__name__)

app.secret_key = "secret123"
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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


@app.route("/")
def index():

    if "usuario" not in session:

        flash(" Debes iniciar sesión", "warning")

        return redirect(url_for("login"))

    return render_template(
        "index.html",
        usuario=session["usuario"]
    )


@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form["nombre"]

        email = request.form["email"]

        password = request.form["password"]

        confirm_password = request.form["confirm_password"]

        
        if password != confirm_password:

            flash(" Las contraseñas no coinciden", "danger")

            return redirect(url_for("registro"))

        usuario = autos.registrar_usuario(
            nombre,
            email,
            password
        )

        if usuario:

            flash("Usuario registrado correctamente", "success")

            return redirect(url_for("login"))

        flash(" Ese correo ya existe", "danger")

        return redirect(url_for("registro"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        usuario = autos.iniciar_sesion(
            email,
            password
        )

        if usuario:

            session["usuario"] = usuario["nombre"]

            session["usuario_id"] = usuario["_id"]

            flash("Bienvenido", "success")

            return redirect(url_for("index"))

        flash(" Correo o contraseña incorrectos", "danger")

        return redirect(url_for("login"))

    return render_template("login.html")

@app.route('/recuperar-contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        
        usuario = autos.usuarios.find_one({"email": email})
        
        if usuario:
            
            token = s.dumps(email, salt='recuperacion-pass')
            enlace = url_for('restablecer_contrasena', token=token, _external=True)
            
            
            msg = Message('Recuperación de contraseña', 
                        sender=app.config['MAIL_USERNAME'], 
                        recipients=[email])
            msg.body = f'Para restablecer tu contraseña, haz clic en el siguiente enlace. Este enlace caducará en 1 hora:\n\n{enlace}'
            
            
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Error al enviar el correo: {e}")
        
        
        flash('Si el correo existe en nuestro sistema, hemos enviado las instrucciones.', 'success')
        return redirect(url_for('login'))

    return render_template("recuperar.html")


@app.route('/restablecer-contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    try:
        email = s.loads(token, salt='recuperacion-pass', max_age=3600)
    except SignatureExpired:
        flash('El enlace de recuperación ha expirado. Solicita uno nuevo.', 'danger')
        return redirect(url_for('recuperar_contrasena'))
    except Exception:
        flash('Enlace inválido.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nueva_password = request.form['password']
        
        
        exito = autos.actualizar_contrasena(email, nueva_password)
        
        if exito:
            flash('¡Tu contraseña ha sido actualizada exitosamente! Ya puedes iniciar sesión.', 'success')
        else:
            flash('Hubo un problema actualizando la contraseña.', 'danger')
            
        return redirect(url_for('login'))

    return render_template("restablecer_contrasena.html", token=token)

@app.route('/Agregar', methods=['GET', 'POST'])
@app.route('/agregar', methods=['GET', 'POST'])
def agregar():

    if "usuario" not in session:
        flash(" Debes iniciar sesión", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        imagen = request.files.get("imagen")
        imagen_url = None

        if not titulo or not descripcion:
            flash("Debes completar todos los campos", "danger")
            return redirect(url_for("agregar"))

        if imagen and imagen.filename:
            if not allowed_file(imagen.filename):
                flash("Formato de imagen no permitido. Usa png, jpg, jpeg o gif.", "danger")
                return redirect(url_for("agregar"))

            nombre_archivo = f"{uuid.uuid4().hex}_{secure_filename(imagen.filename)}"
            ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
            imagen.save(ruta_archivo)
            imagen_url = f"uploads/{nombre_archivo}"

        reporte_id = autos.subir_reporte(
            session["usuario_id"],
            titulo,
            descripcion,
            imagen_url
        )

        if reporte_id:
            flash("Vehículo agregado correctamente", "success")
            return redirect(url_for("comprar"))

        flash("No se pudo agregar el vehículo. Intenta de nuevo.", "danger")
        return redirect(url_for("agregar"))

    return render_template("agregar_vehiculo.html")


@app.route('/comprar')
def comprar():

    if "usuario" not in session:
        flash(" Debes iniciar sesión", "warning")
        return redirect(url_for("login"))

    reportes = autos.obtener_reportes()
    return render_template("compar.html", reportes=reportes)


@app.route("/logout")
def logout():

    session.clear()

    flash(" Sesión cerrada", "warning")

    return redirect(url_for("login"))


if __name__ == "__main__":

    app.run(debug=True)