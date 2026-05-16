
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.whatsapp.templates import enviar_template

# Datos de prueba para la plantilla notificacio_cobro

telefono = "34685133624"  # Número internacional
parametros = [
    "Carlos Pérez",                   # {{1}} Nombre completo del empleado
    "15 de abril",                    # {{2}} Fecha de corte (Time Collection)
    "100",                            # {{3}} Monto
    "123",                            # {{4}} Código de Activo
    "123-5",                          # {{5}} Concepto (código del activo - semana iso)
    "BBVA: ES69 0182 9051 6702 0184 5144 - ACTIVOS CIENXCIEN JJ",         # {{6}}
    "SANTANDER: ES50 0049 5068 1626 1652 2442 - JULIETH VANNESA LUQUE PRADA", # {{7}}
    "CAIXA: ES06 2100 8029 6702 0023 2573 - ACTIVOS CIENXCIEN JJ SL",     # {{8}}
]

resp = enviar_template(
    telefono,
    template_name="notificacio_cobro",
    language_code="es",
    parametros=parametros
)
print(resp.status_code, resp.text)
