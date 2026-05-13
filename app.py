from flask import Flask, render_template, request, redirect, session, url_for, flash
from autos import Autos

app = Flask(__name__)

app.secret_key = "secret123"

autos = Autos()


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


@app.route("/logout")
def logout():

    session.clear()

    flash(" Sesión cerrada", "warning")

    return redirect(url_for("login"))


if __name__ == "__main__":

    app.run(debug=True)