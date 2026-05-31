# AutoLux

Proyecto Flask para agencia de autos.

Incluye:
- Login y registro con teléfono
- Catálogo de vehículos
- Cotizaciones
- Contactar vendedor por WhatsApp
- Solicitud para vender vehículo
- Panel de mensajes para admin
- Publicar, editar y eliminar vehículos solo como admin

Para que una cuenta sea admin, registra o edita el usuario con el correo:

`agenciaautos67@gmail.com`

En MongoDB debe tener:

```json
"rol": "admin"
```

Ejecutar:

```bash
pip install -r requirements.txt
python app.py
```
