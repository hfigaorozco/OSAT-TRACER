# OSAT-TRACER
Sistema de trazabilidad del control de ensamblado de semiconductores.

## Si ya tenian datos cargados
python manage.py flush --no-input

## Actualice el modelo de kpi en unidad porque era unique y eso no permite que varios kpis se midan en porcentaje.

## Orden de carga

```powershell
cd OSAT-TRACER\osat_tracer

# PASO 1 — Genera los empleados con contraseña real primero
python manage.py shell -c "exec(open('fixtures_v2/00_generar_empleados.py').read())"

# PASO 2 — Carga en orden
python manage.py loaddata fixtures_v2/01_catalogos_base.json
python manage.py loaddata fixtures_v2/02_procesos_pasos.json
python manage.py loaddata fixtures_v2/03_inventario.json
python manage.py loaddata fixtures_v2/03_empleados_real.json
python manage.py loaddata fixtures_v2/04_maquinaria.json
python manage.py loaddata fixtures_v2/05_ordenes_lotes.json
python manage.py loaddata fixtures_v2/06_alertas_kpi_trazabilidad.json
```

## Credenciales de prueba

Todos comparten la misma contraseña: `Osat2026!`

| Username | Nombre | Rol |
|---|---|---|
| `hfigueroa` | Hector Armando Figueroa | Admin |
| `jflores` | Jose Manuel Flores | Admin |
| `arturjm` | Arturo Javier Jimenez | Admin |
| `fabiansaiz` | Fabian Oswaldo Saiz | Admin |
| `isabelhdez` | Sofia Isabel Hernandez | Supervisor |
| `jhdez` | Juan Manuel Hernandez | Operador |
| `bmaryn` | Brayan Jaciel Marin | Operador |
| `kcoriap` | Karen Sherlyn Coria | Operador |
| `lgallardo` | Luis David Gallardo | Operador |
| `rmendivil` | Jesus Rafael Mendivil | Operador (inactivo) |


## Verificar que cargó bien

```python
python manage.py shell
>>> from api_produccion.models import Paso_Realizado, Oblea
>>> from api_usuarios.models import Empleado
>>> Empleado.objects.count()   # 10
>>> Oblea.objects.count()      # 4
>>> Paso_Realizado.objects.count()  # 18
```

## Comandos para correr el backend
pip install waitress
waitress-serve --port=8001 --threads=8 osat_tracer.wsgi:application