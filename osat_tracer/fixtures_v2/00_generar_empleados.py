"""
Genera 03_empleados_real.json con los 12 empleados del catálogo
y contraseñas reales hasheadas por Django.

USO (desde la raíz del proyecto osat_tracer):
  python manage.py shell -c "exec(open('00_generar_empleados.py').read())" > fixtures_v2/03_empleados_real.json
"""
import json
from django.contrib.auth.hashers import make_password

PASSWORD = "Osat2026!"
hashed = make_password(PASSWORD)


empleados = [
    {"pk": 1,  "num": 1,  "first": "Hector Armando",  "primerApell": "Figueroa",       "seguApell": "Orozco",   "username": "hfigueroa",   "email": "hfigueroa@osat.mx",     "rfc": "FAOH900315KX7", "rol": "admin", "estado": "act"},
    {"pk": 2,  "num": 2,  "first": "Jose Manuel",      "primerApell": "Flores",         "seguApell": "Ruiz",     "username": "jflores",     "email": "jfloresruiz@osat.mx",   "rfc": "FORM881122QJ4", "rol": "admin", "estado": "act"},
    {"pk": 3,  "num": 3,  "first": "Arturo Javier",    "primerApell": "Jimenez de Lara", "seguApell": "Rizo",     "username": "arturjm",     "email": "arturjm@osat.mx",       "rfc": "JIRA920807MT9", "rol": "admin", "estado": "act"},
    {"pk": 4,  "num": 4,  "first": "Fabian Oswaldo",   "primerApell": "Saiz",           "seguApell": "Gonzalez", "username": "fabiansaiz",  "email": "fabiansaiz@osat.mx",    "rfc": "SAGF950418DL2", "rol": "admin", "estado": "act"},
    {"pk": 5,  "num": 5,  "first": "Sofia Isabel",     "primerApell": "Hernandez",      "seguApell": "Espinoza", "username": "isabelhdez",  "email": "isabelhdez@osat.mx",    "rfc": "HEES930926PN8", "rol": "super", "estado": "act"},
    {"pk": 6,  "num": 6,  "first": "Alan",             "primerApell": "Santaolaya",     "seguApell": "Gaxiola",  "username": "asantaolaya", "email": "asantaolaya@osat.mx",   "rfc": "SGAF180418HJ3", "rol": "super", "estado": "ina"},
    {"pk": 7,  "num": 7,  "first": "Zury Andrea",      "primerApell": "Medina",         "seguApell": "Serrano",  "username": "zmedina",     "email": "zmedina@osat.mx",       "rfc": "MSZA210426UJ7", "rol": "super", "estado": "act"},
    {"pk": 8,  "num": 8,  "first": "Juan Manuel",      "primerApell": "Hernandez",      "seguApell": "Medina",   "username": "jhdez",       "email": "jhdezmedina@osat.mx",   "rfc": "HEMJ891210VC5", "rol": "opera", "estado": "act"},
    {"pk": 9,  "num": 9,  "first": "Brayan Jaciel",    "primerApell": "Marin",          "seguApell": "Loyo",     "username": "bmaryn",      "email": "bmaryn@osat.mx",        "rfc": "MALB970731RW1", "rol": "opera", "estado": "act"},
    {"pk": 10, "num": 10, "first": "Karen Sherlyn",    "primerApell": "Coria",          "seguApell": "Peña",     "username": "kcoriap",     "email": "karencoriap@osat.mx",   "rfc": "COPK940214HF6", "rol": "opera", "estado": "act"},
    {"pk": 11, "num": 11, "first": "Luis David",       "primerApell": "Gallardo",       "seguApell": "Ramirez",  "username": "lgallardo",   "email": "luisdgallardo@osat.mx", "rfc": "GARL910603ZT3", "rol": "opera", "estado": "act"},
    {"pk": 12, "num": 12, "first": "Jesus Rafael",     "primerApell": "Mendivil",       "seguApell": "Perez",    "username": "rmendivil",   "email": "rafaelmendivil@osat.mx","rfc": "MEPJ880925BX0", "rol": "opera", "estado": "ina"},
]

fixture = []
for e in empleados:
    last_name = f'{e["primerApell"]} {e["seguApell"]}'.strip()
    fixture.append({
        "model": "auth.user",
        "pk": e["pk"],
        "fields": {
            "username":     e["username"],
            "first_name":   e["first"],
            "last_name":    last_name,
            "email":        e["email"],
            "is_active":    e["estado"] == "act",
            "is_staff":     False,
            "is_superuser": False,
            "password":     hashed
        }
    })
    fixture.append({
        "model": "api_usuarios.empleado",
        "pk": e["num"],
        "fields": {
            "nombre":      e["first"],
            "primerApell": e["primerApell"],
            "seguApell":   e["seguApell"],
            "rfc":         e["rfc"],
            "estado":      e["estado"],
            "rol":         e["rol"],
            "usuario":     e["pk"]
        }
    })


with open('fixtures_v2/03_empleados_real.json', 'w', encoding='utf-8') as f:
    json.dump(fixture, f, indent=2, ensure_ascii=False)
print("Archivo generado: fixtures_v2/03_empleados_real.json")