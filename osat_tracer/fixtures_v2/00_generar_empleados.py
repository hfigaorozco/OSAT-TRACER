"""
Genera 03_empleados_real.json con los 10 empleados del catálogo
y contraseñas reales hasheadas por Django.

USO (desde la raíz del proyecto osat_tracer):
  python manage.py shell -c "exec(open('00_generar_empleados.py').read())" > fixtures_v2/03_empleados_real.json
"""
import json
from django.contrib.auth.hashers import make_password

PASSWORD = "Osat2026!"
hashed = make_password(PASSWORD)

empleados = [
    {"pk": 1,  "num": 1,  "first": "Hector Armando", "last": "Figueroa Orozco",       "username": "hfigueroa",  "email": "hfigueroa@osat.mx",      "rfc": "FAOH900315KX7", "rol": "admin", "estado": "act"},
    {"pk": 2,  "num": 2,  "first": "Jose Manuel",     "last": "Flores Ruiz",           "username": "jflores",    "email": "jfloresruiz@osat.mx",     "rfc": "FORM881122QJ4", "rol": "admin", "estado": "act"},
    {"pk": 3,  "num": 3,  "first": "Arturo Javier",   "last": "Jimenez de Lara Rizo",  "username": "arturjm",    "email": "arturjm@osat.mx",         "rfc": "JIRA920807MT9", "rol": "admin", "estado": "act"},
    {"pk": 4,  "num": 4,  "first": "Fabian Oswaldo",  "last": "Saiz Gonzalez",         "username": "fabiansaiz", "email": "fabiansaiz@osat.mx",      "rfc": "SAGF950418DL2", "rol": "admin", "estado": "act"},
    {"pk": 5,  "num": 5,  "first": "Sofia Isabel",    "last": "Hernandez Espinoza",    "username": "isabelhdez", "email": "isabelhdez@osat.mx",      "rfc": "HEES930926PN8", "rol": "super", "estado": "act"},
    {"pk": 6,  "num": 6,  "first": "Juan Manuel",     "last": "Hernandez Medina",      "username": "jhdez",      "email": "jhdezmedina@osat.mx",     "rfc": "HEMJ891210VC5", "rol": "opera", "estado": "act"},
    {"pk": 7,  "num": 7,  "first": "Brayan Jaciel",   "last": "Marin Loyo",            "username": "bmaryn",     "email": "bmaryn@osat.mx",          "rfc": "MALB970731RW1", "rol": "opera", "estado": "act"},
    {"pk": 8,  "num": 8,  "first": "Karen Sherlyn",   "last": "Coria Peña",            "username": "kcoriap",    "email": "karencoriap@osat.mx",     "rfc": "COPK940214HF6", "rol": "opera", "estado": "act"},
    {"pk": 9,  "num": 9,  "first": "Luis David",      "last": "Gallardo Ramirez",      "username": "lgallardo",  "email": "luisdgallardo@osat.mx",   "rfc": "GARL910603ZT3", "rol": "opera", "estado": "act"},
    {"pk": 10, "num": 10, "first": "Jesus Rafael",    "last": "Mendivil Perez",        "username": "rmendivil",  "email": "rafaelmendivil@osat.mx",  "rfc": "MEPJ880925BX0", "rol": "opera", "estado": "ina"},
]

fixture = []
for e in empleados:
    nombre_parts = e["first"].split(" ", 1)
    apell_parts  = e["last"].split(" ", 1)
    fixture.append({
        "model": "auth.user",
        "pk": e["pk"],
        "fields": {
            "username":     e["username"],
            "first_name":   e["first"],
            "last_name":    e["last"],
            "email":        e["email"],
            "is_active":    e["estado"] == "act",
            "is_staff":     False,
            "is_superuser": False,
            "password":     hashed
        }
    })
    primerApell = apell_parts[0]
    seguApell   = apell_parts[1] if len(apell_parts) > 1 else ""
    fixture.append({
        "model": "api_usuarios.empleado",
        "pk": e["num"],
        "fields": {
            "nombre":      e["first"],
            "primerApell": primerApell,
            "seguApell":   seguApell,
            "rfc":         e["rfc"],
            "estado":      e["estado"],
            "rol":         e["rol"],
            "usuario":     e["pk"]
        }
    })


with open('fixtures_v2/03_empleados_real.json', 'w', encoding='utf-8') as f:
    json.dump(fixture, f, indent=2, ensure_ascii=False)
print("Archivo generado: fixtures_v2/03_empleados_real.json")
