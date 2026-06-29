from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from app.api.facturas import (
    _detectar_tipo_factura,
    _extraer_datos_fiscales,
    _validar_factura_espania,
    _validar_id_fiscal_es,
)
from app.main import app


class TestFacturasValidacion(unittest.TestCase):
    def test_validar_id_fiscal_es(self) -> None:
        self.assertTrue(_validar_id_fiscal_es("12345678Z"))
        self.assertTrue(_validar_id_fiscal_es("B99286320"))
        self.assertFalse(_validar_id_fiscal_es("12345678A"))

    def test_validacion_factura_completa_ok(self) -> None:
        datos = {
            "emisor_nombre": "Proveedor Demo, S.L.",
            "emisor_nif": "B99286320",
            "emisor_direccion": "Calle Mayor 1, Madrid",
            "receptor_nombre": "Cliente Demo, S.L.",
            "receptor_nif": "B12345674",
            "receptor_direccion": "Calle Cliente 2, Madrid",
            "numero_factura": "F-2026-001",
            "fecha": "02/06/2026",
            "fecha_vencimiento": None,
            "concepto": "Servicios de consultoría",
            "base_imponible": "100,00 €",
            "tipo_iva": "21",
            "cuota_iva": "21,00 €",
            "irpf": None,
            "total": "121,00 €",
        }
        texto = "FACTURA F-2026-001 FECHA 02/06/2026 BASE 100,00 IVA 21% TOTAL 121,00"

        out = _validar_factura_espania(datos, texto)
        self.assertEqual(out["estado"], "valida")
        self.assertEqual(out["tipo_factura"], "completa")
        self.assertEqual(len(out["bloqueantes"]), 0)

    def test_validacion_factura_incompleta(self) -> None:
        datos = {
            "emisor_nombre": None,
            "emisor_nif": None,
            "emisor_direccion": None,
            "receptor_nombre": None,
            "receptor_nif": None,
            "receptor_direccion": None,
            "numero_factura": None,
            "fecha": None,
            "fecha_vencimiento": None,
            "concepto": None,
            "base_imponible": None,
            "tipo_iva": None,
            "cuota_iva": None,
            "irpf": None,
            "total": None,
        }

        out = _validar_factura_espania(datos, "")
        self.assertEqual(out["estado"], "incompleta")
        self.assertGreaterEqual(len(out["bloqueantes"]), 3)

    def test_validacion_rectificativa_sin_referencia_original(self) -> None:
        datos = {
            "emisor_nombre": "Proveedor Demo, S.L.",
            "emisor_nif": "B99286320",
            "emisor_direccion": "Calle Mayor 1, Madrid",
            "receptor_nombre": "Cliente Demo, S.L.",
            "receptor_nif": "B12345674",
            "receptor_direccion": "Calle Cliente 2, Madrid",
            "numero_factura": "R-2026-004",
            "fecha": "02/06/2026",
            "fecha_vencimiento": None,
            "concepto": "Regularización",
            "base_imponible": "100,00 €",
            "tipo_iva": "21",
            "cuota_iva": "21,00 €",
            "irpf": None,
            "total": "121,00 €",
        }
        texto = "FACTURA RECTIFICATIVA R-2026-004 FECHA 02/06/2026 TOTAL 121,00"

        out = _validar_factura_espania(datos, texto)
        self.assertEqual(out["tipo_factura"], "rectificativa")
        self.assertIn(
            "Factura rectificativa sin referencia clara a factura original.",
            out["bloqueantes"],
        )

    def test_validacion_detecta_inconsistencia_importes(self) -> None:
        datos = {
            "emisor_nombre": "Proveedor Demo, S.L.",
            "emisor_nif": "B99286320",
            "emisor_direccion": "Calle Mayor 1, Madrid",
            "receptor_nombre": "Cliente Demo, S.L.",
            "receptor_nif": "B12345674",
            "receptor_direccion": "Calle Cliente 2, Madrid",
            "numero_factura": "F-2026-010",
            "fecha": "02/06/2026",
            "fecha_vencimiento": None,
            "concepto": "Servicios",
            "base_imponible": "100,00 €",
            "tipo_iva": "21",
            "cuota_iva": "21,00 €",
            "irpf": None,
            "total": "130,00 €",
        }

        out = _validar_factura_espania(datos, "FACTURA F-2026-010")
        advertencias = "\n".join(out["advertencias"])
        self.assertIn("Inconsistencia de importes", advertencias)


class TestFacturasExtraccion(unittest.TestCase):
    def test_extraer_numero_factura_con_token_intermedio(self) -> None:
        texto = "Factura 1 000844\nFecha 02/06/2026\nNIF B12345674\nTOTAL 121,00"
        datos = _extraer_datos_fiscales(texto, texto, texto)
        self.assertEqual(datos["numero_factura"], "000844")

    def test_corrige_ocr_cif_con_simbolo_euro(self) -> None:
        texto = "PROVEEDOR DEMO SL\nNIF €47796107\nTOTAL 99,99"
        datos = _extraer_datos_fiscales(texto, "", texto)
        self.assertEqual(datos["emisor_nif"], "E47796107")

    def test_descarta_numero_factura_solo_letras(self) -> None:
        texto = "FACTURA STOLES\nFECHA 25/02/2026\nNIF B12345674\nTOTAL 25,02"
        datos = _extraer_datos_fiscales(texto, texto, texto)
        self.assertIsNone(datos["numero_factura"])

    def test_no_clasifica_como_simplificada_por_heuristica_de_ausencia_receptor(self) -> None:
        datos = {
            "receptor_nif": None,
            "receptor_direccion": None,
            "total": "25,02 €",
            "emisor_nif": "B12345674",
            "numero_factura": None,
            "fecha": "25/02/2026",
        }
        tipo = _detectar_tipo_factura(datos, "FACTURA 2026")
        self.assertEqual(tipo, "desconocida")

    def test_extrae_numero_factura_desde_texto_ocr_reportado(self) -> None:
        texto = (
            "PLENERGY GRUPO, S.L.\n"
            "CIF :893275394\n"
            "Fecha: 25/02/2026 20:46\n"
            "Albaran : R2612690084454\n"
            "Factura : 26102600003356\n"
            "Total: 25,02 Eur\n"
        )
        datos = _extraer_datos_fiscales(texto, texto, texto)
        self.assertEqual(datos["numero_factura"], "26102600003356")

    def test_no_infiere_base_cuota_sin_etiquetas_fiscales_claras(self) -> None:
        texto = (
            "Factura : 26102600003356\n"
            "Fecha: 25/02/2026\n"
            "Importe : 5,00\n"
            "Imp. : 16,15\n"
            "Total: 25,02 Eur\n"
        )
        datos = _extraer_datos_fiscales(texto, texto, texto)
        self.assertEqual(datos["total"], "25,02 €")
        self.assertIsNone(datos["base_imponible"])
        self.assertIsNone(datos["cuota_iva"])

    def test_extrae_receptor_desde_bloque_cliente_ticket(self) -> None:
        texto = (
            "PLENERGY GRUPO, S.L.\n"
            "CIF :893275394\n"
            "Cliente - \" activos cienxcien jj sl\n"
            "Panadero\n"
            "28418 Manzanares el Real\n"
            "CIF/NIF 875841791\n"
            "Factura : 26102600003356\n"
            "Total: 25,02 Eur\n"
        )
        datos = _extraer_datos_fiscales(texto, "", texto)
        self.assertIsNotNone(datos["receptor_nombre"])
        self.assertIn("cienxcien", datos["receptor_nombre"].lower())
        self.assertEqual(datos["receptor_nif"], "B75841791")
        self.assertIsNotNone(datos["receptor_direccion"])

    def test_ticket_ocr_prioriza_total_reservado_5_eur(self) -> None:
        texto = (
            "PLENERGY GRUPO, S.L.\n"
            "CIF :893275394\n"
            "Fecha: 25/02/2026 20:46\n"
            "Turno: 598\n"
            "Cliente - \" activos cienxcien jj sl\n"
            "28418 Manzanares el Real\n"
            "CIF/NIF 875841791\n"
            "Factura : 26102600003356\n"
            "Total reservado; — 5,00 Eur\n"
            "Fecha: 25.02.26 Hora: 20:46\n"
        )
        datos = _extraer_datos_fiscales(texto, "", texto)
        self.assertEqual(datos["total"], "5,00 €")

    def test_ticket_ocr_total_linea_ruidosa_no_cae_en_8_87(self) -> None:
        texto = (
            "Surtidor : 1\n"
            "Producto : S/P 95\n"
            "Precio : 1,369\n"
            "Imp. : 8,87\n"
            "Total reservado; — 5,00 Eur\n"
        )
        datos = _extraer_datos_fiscales(texto, "", texto)
        self.assertEqual(datos["total"], "5,00 €")

    def test_ticket_ocr_infiere_total_desde_litros_por_precio(self) -> None:
        texto = (
            "Factura : 26102600003356\n"
            "Surtidor : 1\n"
            "Producto : S/P 95\n"
            "Litros : 3,6\n"
            "Precio : 1,369\n"
            "Imp. : 8,87\n"
            "Fecha: 25.02.26 Hora: 20:46\n"
        )
        datos = _extraer_datos_fiscales(texto, "", texto)
        self.assertEqual(datos["total"], "4,93 €")


class TestFacturasValidacionSimplificada(unittest.TestCase):
    def test_simplificada_sin_numero_se_marca_incompleta(self) -> None:
        datos = {
            "emisor_nombre": "Proveedor Demo, S.L.",
            "emisor_nif": "B99286320",
            "emisor_direccion": "Calle Mayor 1, Madrid",
            "receptor_nombre": None,
            "receptor_nif": None,
            "receptor_direccion": None,
            "numero_factura": None,
            "fecha": "02/06/2026",
            "fecha_vencimiento": None,
            "concepto": "Venta al detalle",
            "base_imponible": None,
            "tipo_iva": None,
            "cuota_iva": None,
            "irpf": None,
            "total": "25,02 €",
        }

        texto = "FACTURA SIMPLIFICADA FECHA 02/06/2026 TOTAL 25,02"
        out = _validar_factura_espania(datos, texto)
        self.assertEqual(out["tipo_factura"], "simplificada")
        self.assertEqual(out["estado"], "incompleta")
        self.assertIn("Factura simplificada sin número de factura.", out["bloqueantes"])


class TestFacturasAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_analizar_json_png(self) -> None:
        img = Image.new("RGB", (1200, 500), "white")
        draw = ImageDraw.Draw(img)
        draw.text(
            (20, 20),
            "FACTURA F-2026-003\nFecha 02/06/2026\nNIF B12345674\nTOTAL 121,00",
            fill="black",
        )
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        resp = self.client.post(
            "/facturas/analizar-json",
            files={"factura": ("factura_test.png", buf.getvalue(), "image/png")},
        )

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("datos", body)
        self.assertIn("validacion", body)
        self.assertIn("confianza", body)

    def test_analizar_json_mime_no_soportado(self) -> None:
        resp = self.client.post(
            "/facturas/analizar-json",
            files={"factura": ("nota.txt", b"hola", "text/plain")},
        )
        self.assertEqual(resp.status_code, 415)

    def test_analizar_json_fichero_muy_grande(self) -> None:
        payload = b"0" * (10 * 1024 * 1024 + 1)
        resp = self.client.post(
            "/facturas/analizar-json",
            files={"factura": ("factura.png", payload, "image/png")},
        )
        self.assertEqual(resp.status_code, 413)

    def test_analizar_json_error_dependencia_ocr_devuelve_503(self) -> None:
        with patch(
            "app.api.facturas._asegurar_tesseract_disponible",
            side_effect=RuntimeError("Tesseract OCR no está instalado o no está en PATH."),
        ):
            resp = self.client.post(
                "/facturas/analizar-json",
                files={"factura": ("factura.png", b"abc", "image/png")},
            )

        self.assertEqual(resp.status_code, 503)
        self.assertIn("Tesseract OCR", resp.json().get("detail", ""))

    def test_revalidar_json_actualiza_estado_con_datos_manuales(self) -> None:
        payload = {
            "emisor_nombre": "Proveedor Demo, S.L.",
            "emisor_nif": "B99286320",
            "receptor_nombre": "Cliente Demo, S.L.",
            "receptor_nif": "B12345674",
            "numero_factura": "F-2026-100",
            "fecha": "02/06/2026",
            "base_imponible": "100,00",
            "tipo_iva": "21",
            "cuota_iva": "21,00",
            "total": "121,00",
            "texto_crudo": "FACTURA F-2026-100",
        }

        resp = self.client.post("/facturas/revalidar-json", json=payload)
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertEqual(body["validacion"]["estado"], "valida")
        self.assertEqual(body["validacion"]["tipo_factura"], "completa")
        self.assertEqual(body["datos"]["numero_factura"], "F-2026-100")

    def test_revalidar_json_limpia_vacios(self) -> None:
        payload = {
            "emisor_nif": "   ",
            "numero_factura": "",
            "fecha": " ",
            "total": "",
        }
        resp = self.client.post("/facturas/revalidar-json", json=payload)
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertIsNone(body["datos"]["emisor_nif"])
        self.assertIsNone(body["datos"]["numero_factura"])
        self.assertEqual(body["validacion"]["estado"], "incompleta")

    def test_guardar_correccion_json_genera_registro(self) -> None:
        payload = {
            "archivo": "factura_demo.pdf",
            "emisor_nif": "B99286320",
            "numero_factura": "F-2026-200",
            "fecha": "02/06/2026",
            "total": "121,00",
        }
        resp = self.client.post("/facturas/guardar-correccion-json", json=payload)
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertTrue(body.get("ok"))
        self.assertIn("log_file", body)
        self.assertTrue(Path(body["log_file"]).exists())

    def test_exportar_json_devuelve_adjunto(self) -> None:
        payload = {
            "archivo": "factura_demo.pdf",
            "emisor_nif": "B99286320",
            "numero_factura": "F-2026-200",
            "fecha": "02/06/2026",
            "total": "121,00",
        }
        resp = self.client.post("/facturas/exportar-json", json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("attachment; filename=", resp.headers.get("content-disposition", ""))
        exported = json.loads(resp.text)
        self.assertEqual(exported["archivo"], "factura_demo.pdf")
        self.assertEqual(exported["datos"]["numero_factura"], "F-2026-200")

    def test_exportar_csv_devuelve_adjunto(self) -> None:
        payload = {
            "archivo": "factura_demo.pdf",
            "emisor_nif": "B99286320",
            "numero_factura": "F-2026-200",
            "fecha": "02/06/2026",
            "total": "121,00",
        }
        resp = self.client.post("/facturas/exportar-csv", json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("attachment; filename=", resp.headers.get("content-disposition", ""))
        self.assertIn("archivo;emisor_nombre;emisor_nif", resp.text)
        self.assertIn("factura_demo.pdf", resp.text)


if __name__ == "__main__":
    unittest.main()
