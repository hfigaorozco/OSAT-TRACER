# IMPLEMENTACION DE QR Y PDF

# 1. Instalar dependencias
    pip install qrcode[pil]
    pip install reportlab

# 2. Hacer migraciones para actualizar modelo de OBLEA
    python manage.py makemigrations
### Si es necesario hacer
    python manage.py makemigrations --merge
### Luego:
    python manage.py migrate

# 3.Para probar se puede hacer una Oblea desde terminal con: 
$body = @{
  diesGenerados = 120
  orden = 1
  estado = "proce"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8001/api/v1/create/Oblea/" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body

# 4. Para generar los QR faltantes y cargarlos a la BD:
# Correr los siguientes comandos en terminal linea por linea:
python manage.py shell
    exec(open("fixtures_v2/generar_qr.py").read())
    exit()