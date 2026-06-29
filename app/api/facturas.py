"""
Router de facturas: página de inicio + extracción de datos fiscales.
Dependencias: pdfplumber, pillow, pytesseract, pdf2image.
"""
from __future__ import annotations

import json
import io
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pdfplumber
import pytesseract
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from pdf2image import convert_from_bytes
from PIL import Image
from pydantic import BaseModel
from pytesseract import TesseractNotFoundError
from sqlalchemy.orm import Session

from app.ftra.database import get_db
from app.ftra.models.factura_correccion import FacturaCorreccion

router = APIRouter(prefix="/facturas", tags=["facturas"])
templates = Jinja2Templates(directory="app/templates")

# ──────────────────────────────────────────────
# Constantes de tamaño máximo (10 MB)
# ──────────────────────────────────────────────
MAX_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
}

# Idioma Tesseract: español + inglés para cubrir PDFs mixtos
_TESS_LANG = "spa+eng"


# ════════════════════════════════════════════════
# PÁGINA DE INICIO
# ════════════════════════════════════════════════
@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    return templates.TemplateResponse("facturas/inicio.html", {"request": request})


# ════════════════════════════════════════════════
# ENDPOINT: ANALIZAR FACTURA
# ════════════════════════════════════════════════
@router.post("/analizar", response_class=HTMLResponse)
async def analizar_factura(request: Request, factura: UploadFile = File(...)):
    resultado = await _procesar_factura_upload(factura)
    datos = resultado["datos"]
    confianza = resultado["confianza"]
    validacion = resultado["validacion"]
    texto_crudo = resultado["texto_crudo"]

    return templates.TemplateResponse(
        "facturas/resultado.html",
        {
            "request": request,
            "archivo": factura.filename,
            "datos": datos,
            "confianza": confianza,
            "validacion": validacion,
            "texto_crudo": texto_crudo,
        },
    )


@router.post("/analizar-json")
async def analizar_factura_json(factura: UploadFile = File(...)):
    """Devuelve extracción + validación en JSON para integraciones externas."""
    resultado = await _procesar_factura_upload(factura)
    return JSONResponse(
        {
            "archivo": factura.filename,
            "datos": resultado["datos"],
            "confianza": resultado["confianza"],
            "validacion": resultado["validacion"],
            "texto_crudo": resultado["texto_crudo"],
        }
    )


class RevalidarFacturaPayload(BaseModel):
    archivo: Optional[str] = None
    emisor_nombre: Optional[str] = None
    emisor_nif: Optional[str] = None
    emisor_direccion: Optional[str] = None
    receptor_nombre: Optional[str] = None
    receptor_nif: Optional[str] = None
    receptor_direccion: Optional[str] = None
    numero_factura: Optional[str] = None
    fecha: Optional[str] = None
    fecha_vencimiento: Optional[str] = None
    concepto: Optional[str] = None
    base_imponible: Optional[str] = None
    tipo_iva: Optional[str] = None
    cuota_iva: Optional[str] = None
    irpf: Optional[str] = None
    total: Optional[str] = None
    texto_crudo: Optional[str] = None


def _clean_manual_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _build_manual_datos(payload: RevalidarFacturaPayload) -> dict:
    return {
        "emisor_nombre": _clean_manual_value(payload.emisor_nombre),
        "emisor_nif": _clean_manual_value(payload.emisor_nif),
        "emisor_direccion": _clean_manual_value(payload.emisor_direccion),
        "receptor_nombre": _clean_manual_value(payload.receptor_nombre),
        "receptor_nif": _clean_manual_value(payload.receptor_nif),
        "receptor_direccion": _clean_manual_value(payload.receptor_direccion),
        "numero_factura": _clean_manual_value(payload.numero_factura),
        "fecha": _clean_manual_value(payload.fecha),
        "fecha_vencimiento": _clean_manual_value(payload.fecha_vencimiento),
        "concepto": _clean_manual_value(payload.concepto),
        "base_imponible": _clean_manual_value(payload.base_imponible),
        "tipo_iva": _clean_manual_value(payload.tipo_iva),
        "cuota_iva": _clean_manual_value(payload.cuota_iva),
        "irpf": _clean_manual_value(payload.irpf),
        "total": _clean_manual_value(payload.total),
    }


@router.post("/revalidar-json")
async def revalidar_factura_json(payload: RevalidarFacturaPayload):
    """Permite revalidar datos corregidos manualmente desde la UI."""
    datos = _build_manual_datos(payload)

    texto_crudo = _clean_manual_value(payload.texto_crudo) or ""
    confianza = _calcular_confianza(datos)
    validacion = _validar_factura_espania(datos, texto_crudo)

    return JSONResponse(
        {
            "datos": datos,
            "confianza": confianza,
            "validacion": validacion,
        }
    )


@router.post("/guardar-correccion-json")
async def guardar_correccion_factura_json(
    payload: RevalidarFacturaPayload,
    db: Session = Depends(get_db),
):
    """Guarda una corrección manual en BD (con fallback a JSONL)."""
    datos = _build_manual_datos(payload)
    texto_crudo = _clean_manual_value(payload.texto_crudo) or ""
    confianza = _calcular_confianza(datos)
    validacion = _validar_factura_espania(datos, texto_crudo)

    registro = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "archivo": _clean_manual_value(payload.archivo),
        "datos": datos,
        "confianza": confianza,
        "validacion": validacion,
    }

    try:
        fila = FacturaCorreccion(
            archivo=registro["archivo"],
            emisor_nombre=datos.get("emisor_nombre"),
            emisor_nif=datos.get("emisor_nif"),
            emisor_direccion=datos.get("emisor_direccion"),
            receptor_nombre=datos.get("receptor_nombre"),
            receptor_nif=datos.get("receptor_nif"),
            receptor_direccion=datos.get("receptor_direccion"),
            numero_factura=datos.get("numero_factura"),
            fecha=datos.get("fecha"),
            fecha_vencimiento=datos.get("fecha_vencimiento"),
            concepto=datos.get("concepto"),
            base_imponible=datos.get("base_imponible"),
            tipo_iva=datos.get("tipo_iva"),
            cuota_iva=datos.get("cuota_iva"),
            irpf=datos.get("irpf"),
            total=datos.get("total"),
            texto_crudo=texto_crudo,
            confianza=confianza,
            validacion=validacion,
        )
        db.add(fila)
        db.commit()
        db.refresh(fila)

        return JSONResponse(
            {
                "ok": True,
                "message": "Corrección guardada en base de datos",
                "storage": "database",
                "registro_id": fila.id,
                "registro": registro,
            }
        )
    except Exception:
        db.rollback()

        drafts_dir = Path("app/drafts")
        drafts_dir.mkdir(parents=True, exist_ok=True)
        log_path = drafts_dir / "facturas_correcciones.jsonl"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

        return JSONResponse(
            {
                "ok": True,
                "message": "Corrección guardada en archivo (fallback)",
                "storage": "file",
                "log_file": str(log_path),
                "registro": registro,
            }
        )


@router.post("/exportar-json")
async def exportar_factura_json(payload: RevalidarFacturaPayload):
    """Exporta los datos manuales en un JSON descargable."""
    datos = _build_manual_datos(payload)
    texto_crudo = _clean_manual_value(payload.texto_crudo) or ""
    confianza = _calcular_confianza(datos)
    validacion = _validar_factura_espania(datos, texto_crudo)

    body = {
        "archivo": _clean_manual_value(payload.archivo),
        "datos": datos,
        "confianza": confianza,
        "validacion": validacion,
    }
    filename = f"factura_corregida_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return Response(
        content=json.dumps(body, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/exportar-csv")
async def exportar_factura_csv(payload: RevalidarFacturaPayload):
    """Exporta los datos manuales en CSV descargable (una fila)."""
    datos = _build_manual_datos(payload)
    field_order = [
        "archivo",
        "emisor_nombre",
        "emisor_nif",
        "emisor_direccion",
        "receptor_nombre",
        "receptor_nif",
        "receptor_direccion",
        "numero_factura",
        "fecha",
        "fecha_vencimiento",
        "concepto",
        "base_imponible",
        "tipo_iva",
        "cuota_iva",
        "irpf",
        "total",
    ]
    row = {"archivo": _clean_manual_value(payload.archivo) or ""}
    row.update({k: (datos.get(k) or "") for k in datos})

    output = io.StringIO()
    output.write(";".join(field_order) + "\n")
    output.write(";".join(str(row.get(k, "")).replace(";", ",") for k in field_order) + "\n")

    filename = f"factura_corregida_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _procesar_factura_upload(factura: UploadFile) -> dict:
    """Pipeline único: valida fichero, extrae texto, extrae datos y valida factura."""
    # Validar tipo MIME
    content_type = factura.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de fichero no admitido: {content_type}. "
                   "Sube un PDF, JPG, PNG o TIFF.",
        )

    raw_bytes = await factura.read()

    # Validar tamaño
    if len(raw_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="El fichero supera el límite de 10 MB.",
        )

    # Extraer texto según tipo
    try:
        if content_type == "application/pdf":
            t_izq, t_der, t_full = _texto_desde_pdf(raw_bytes)
        else:
            _asegurar_tesseract_disponible()
            t_izq, t_der, t_full = _texto_desde_imagen(raw_bytes)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    datos = _extraer_datos_fiscales(t_izq, t_der, t_full)
    confianza = _calcular_confianza(datos)
    validacion = _validar_factura_espania(datos, t_full)

    return {
        "datos": datos,
        "confianza": confianza,
        "validacion": validacion,
        "texto_crudo": t_full[:3000] if t_full else "",
    }


# ════════════════════════════════════════════════
# EXTRACCIÓN DE TEXTO
# ════════════════════════════════════════════════
def _texto_desde_pdf(raw: bytes) -> str:
    """
    Devuelve (texto_izquierda, texto_derecha, texto_completo).
    1) Intenta pdfplumber (texto nativo).
    2) Si vacío, usa OCR con split de columnas.
    """
    partes: list[str] = []
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                partes.append(t)

    texto_nativo = "\n".join(partes).strip()

    if len(texto_nativo) < 40:
        _asegurar_tesseract_disponible()
        try:
            imagenes = convert_from_bytes(raw, dpi=300)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "No se pudo convertir el PDF a imagen para OCR. "
                "Verifica que Poppler esté instalado en el sistema."
            ) from exc
        return _ocr_columnas(imagenes)

    return texto_nativo, texto_nativo, texto_nativo


def _ocr_texto(img, *, config: str) -> str:
    try:
        return pytesseract.image_to_string(img, lang=_TESS_LANG, config=config)
    except TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR no está disponible en el sistema. "
            "Instálalo para procesar imágenes o PDFs escaneados."
        ) from exc


def _combinar_textos(*textos: str) -> str:
    """Une textos OCR evitando duplicados triviales por línea."""
    lineas_vistas: set[str] = set()
    lineas: list[str] = []
    for texto in textos:
        for linea in (texto or "").splitlines():
            limpia = re.sub(r"\s+", " ", linea).strip()
            if not limpia:
                continue
            clave = limpia.upper()
            if clave in lineas_vistas:
                continue
            lineas_vistas.add(clave)
            lineas.append(limpia)
    return "\n".join(lineas)


def _ocr_columnas(imagenes) -> tuple[str, str, str]:
    """
    Hace OCR en 3 zonas de cada página:
    - Mitad izquierda del tercio superior  → emisor
    - Mitad derecha del tercio superior    → receptor
    - Página completa                      → tabla, importes, totales
    """
    textos_izq, textos_der, textos_full = [], [], []
    cfg_col = "--psm 6"
    cfg_full = "--psm 3"
    cfg_full_alt = "--psm 11"
    for img in imagenes:
        w, h = img.size
        mid = w // 2
        cab = h // 3
        pad = max(20, w // 12)
        t_izq = _combinar_textos(
            _ocr_texto(img.crop((0, 0, min(w, mid + pad), cab)), config=cfg_col),
            _ocr_texto(img.crop((0, 0, w, cab)), config=cfg_full_alt),
        )
        t_der = _combinar_textos(
            _ocr_texto(img.crop((max(0, mid - pad), 0, w, cab)), config=cfg_col),
            _ocr_texto(img.crop((max(0, mid - pad), 0, w, h)), config=cfg_full_alt),
        )
        t_full = _combinar_textos(
            _ocr_texto(img, config=cfg_full),
            _ocr_texto(img, config=cfg_full_alt),
        )
        textos_izq.append(t_izq)
        textos_der.append(t_der)
        textos_full.append(t_full)
    return _combinar_textos(*textos_izq), _combinar_textos(*textos_der), _combinar_textos(*textos_full)


def _texto_desde_imagen(raw: bytes) -> tuple[str, str, str]:
    """OCR sobre imagen directa con split de columnas."""
    try:
        img = Image.open(io.BytesIO(raw))
        return _ocr_columnas([img])
    except Exception as exc:  # noqa: BLE001
        err = f"[Error OCR imagen: {exc}]"
        return err, err, err


def _asegurar_tesseract_disponible() -> None:
    """Verifica que el binario de Tesseract esté disponible."""
    try:
        _ = pytesseract.get_tesseract_version()
    except TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR no está instalado o no está en PATH. "
            "Instala 'tesseract' para habilitar OCR de facturas escaneadas."
        ) from exc


# ════════════════════════════════════════════════
# EXTRACCIÓN DE DATOS FISCALES MEDIANTE REGEX
# ════════════════════════════════════════════════
_NIF_RE = re.compile(
    r"\b([A-HJ-NP-SUVW]\d{7}[0-9A-J]"   # CIF  (ej: E47796107, B75841791)
    r"|\d{8}[A-HJ-NP-TV-Z]"              # NIF persona física
    r"|[XYZ]\d{7}[A-HJ-NP-TV-Z])\b",    # NIE
    re.IGNORECASE,
)

_FECHA_RE = re.compile(
    r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}"   # dd/mm/yyyy
    r"|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})\b",   # yyyy-mm-dd
)

# Número de factura: admite "000844", "2024/001", "F-001", etc.
_NUM_FACTURA_RE = re.compile(
    r"(?:factura|invoice|n[uú]mero|n[oº°]\.?|num\.?)[:\s#]*([A-Z0-9\/\-]{3,20})",
    re.IGNORECASE,
)
# También captura el campo "NÚMERO" de tabla (dos dígitos mínimo seguidos)
_NUM_FACTURA_ALT_RE = re.compile(
    r"n[uú]mero\s*\n\s*(\d{3,})",
    re.IGNORECASE,
)

_BASE_RE = re.compile(
    r"base(?:\s+imponible)?[:\s]*([0-9]+[.,][0-9]{2})\s*€?",
    re.IGNORECASE,
)
# BASE en tabla: busca la etiqueta BASE seguida del importe en la misma o siguiente línea
_BASE_TABLA_RE = re.compile(
    r"\bbase\b[^\n]*\n[^\n]*?([0-9]{2,}[.,][0-9]{2})",
    re.IGNORECASE,
)
_IVA_TIPO_RE = re.compile(
    r"(?:i\.?v\.?a\.?|iva)[:\s]*(\d{1,2})[,.]?\d*\s*%",
    re.IGNORECASE,
)
# IVA tipo en tabla: "21,00" en columna TIPO (número >= 4 sin ser precio grande)
_IVA_TIPO_TABLA_RE = re.compile(
    r"^\s*(1[0-9]|2[0-5])[,.]00\s*$",
    re.MULTILINE,
)
_CUOTA_IVA_RE = re.compile(
    r"(?:cuota\s+(?:de\s+)?iva|i\.?v\.?a\.?)\s*[:\s]*([0-9]+[.,][0-9]{2})\s*€?",
    re.IGNORECASE,
)
_TOTAL_RE = re.compile(
    r"total[:\s]*([0-9]+[.,][0-9]{2})\s*€?",
    re.IGNORECASE,
)
_TOTAL_FACTURA_RE = re.compile(
    r"total\s+factura[:\s]*([0-9]+[.,][0-9]{2})\s*€?",
    re.IGNORECASE,
)
_TOTAL_TICKET_RE = re.compile(
    r"(?:tot(?:al|a)\s*(?:reservad[oa]|suminist(?:rado|r\.?))|tot(?:al|a)\s*suminis[t]?\w*)\s*[^0-9]{0,20}([0-9]+[.,][0-9]{2})\s*(?:€|eur)?",
    re.IGNORECASE,
)
_IRPF_RE = re.compile(
    r"(?:retenci[oó]n|irpf)[:\s]*([-]?\d{1,2}\s*%[:\s]*[0-9.,]+\s*€?|[0-9]+[.,][0-9]{2}\s*€?)",
    re.IGNORECASE,
)
_CONCEPTO_RE = re.compile(
    r"(?:descripci[oó]n|concepto|servicio)[:\s]*([^\n]{5,120})",
    re.IGNORECASE,
)
_VENCIMIENTO_RE = re.compile(
    r"(?:vencimiento|fecha\s+de\s+pago)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
    re.IGNORECASE,
)
# Evita capturar fragmentos de fechas tipo 25.02.26 (no debe tomar 25.02 como importe)
_IMPORTE_RE = re.compile(r"\b(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})(?![.,]\d{2})\b")
# Número de factura: patrón específico para secuencias numéricas largas o alfanuméricas
_NUM_FACTURA_RE = re.compile(
    r"(?:factura|invoice|n[uú]mero|n[oº°]\.?|num\.?)\s*[:\s#]*([A-Z0-9\/\-]{3,20})(?!\s*(?:PAGINA|P[AÁ]GINA|PAGE))",
    re.IGNORECASE,
)
_NUM_FACTURA_SECUENCIA_RE = re.compile(
    r"\b(0{2,}\d{3,})\b"   # ej: 000844
)


def _first(match: Optional[re.Match]) -> Optional[str]:
    """Devuelve el primer grupo capturado o None."""
    if match:
        return match.group(1).strip()
    return None


def _numero_factura_valido(valor: Optional[str]) -> bool:
    """Valida formato mínimo del número de factura extraído."""
    if not valor:
        return False
    v = valor.strip().upper()
    # Evitar capturas de texto libre/branding (ej: "STOLES")
    if not re.search(r"\d", v):
        return False
    # Requerir una cantidad mínima de dígitos para evitar tokens espurios
    if len(re.findall(r"\d", v)) < 4:
        return False
    # Solo caracteres habituales en numeración de facturas
    if not re.fullmatch(r"[A-Z0-9/\-]{3,30}", v):
        return False
    if re.fullmatch(r"PAGINA|P[AÁ]GINA|PAGE|NUM|NUMERO|FACTURA", v, re.I):
        return False
    return True


def _extraer_numero_factura(texto: str) -> Optional[str]:
    """Intenta extraer número de factura con varias estrategias robustas de OCR."""
    candidatos: list[str] = []

    # 1) Patrones explícitos "Factura: XXXX"
    for m in re.finditer(
        r"(?:factura|invoice|n[uú]mero|n[oº°]\.?|num\.?)\s*[:#-]?\s*([A-Z0-9/\-]{3,30})",
        texto,
        re.IGNORECASE,
    ):
        c = (m.group(1) or "").strip()
        if c:
            candidatos.append(c)

    # 2) Etiqueta en una línea y valor en la siguiente (común en OCR)
    for m in re.finditer(r"(?im)^\s*factura\s*$\s*\n\s*([A-Z0-9/\-]{3,30})\s*$", texto):
        c = (m.group(1) or "").strip()
        if c:
            candidatos.append(c)

    # 3) Factura + token numérico intermedio + secuencia larga
    m_seq = re.search(r"\bfactura\s+\d\s+(\d{4,})\b", texto, re.IGNORECASE)
    if m_seq:
        candidatos.append(m_seq.group(1))

    # 4) Secuencias largas de ceros/dígitos típicas de numeración
    for m in _NUM_FACTURA_SECUENCIA_RE.finditer(texto):
        candidatos.append(m.group(1))

    for c in candidatos:
        if _numero_factura_valido(c):
            return c
    return None


# Tabla de sustituciones OCR frecuentes para NIFs/CIFs españoles
_OCR_FIXES = [
    # € al inicio de secuencia de 7-8 dígitos → E (CIF tipo E)
    (re.compile(r"€(\d{7}[0-9A-J])\b"), r"E\1"),
    # 0 confundido con O al inicio de CIF
    (re.compile(r"\b0([A-Z]\d{7}[0-9A-Z])\b"), r"O\1"),
    # 8 confundido con B al inicio de 9 dígitos (CIF B...)
    (re.compile(r"\b(8\d{7}[0-9A-J])\b"), lambda m: "B" + m.group(1)[1:] if len(m.group(1)) == 9 else m.group(1)),
    # I confundido con 1 en CIF
    (re.compile(r"\b([A-HJ-NP-SUVW])(\d{7})l\b", re.IGNORECASE), r"\g<1>\g<2>1"),
]


_ENTITY_STOPWORDS = {
    "FACTURA", "INVOICE", "PAGINA", "PÁGINA", "PAGE", "CLIENTE", "CLIENT",
    "VEHICULO", "VEHÍCULO", "MATRICULA", "MATRÍCULA", "MARCA", "MODELO",
    "KMS", "KM", "O.R.T", "ORT", "DESCRIPCION", "DESCRIPCIÓN", "CONCEPTO",
    "MATERIALES", "TRABAJOS", "MANO", "OBRA", "TOTAL", "BASE", "IVA",
    "IRPF", "REPARACION", "REPARACIÓN", "VENTA", "TALLER", "RECAMBIOS",
    "SERVICIO", "SERVICIOS", "ALBARAN", "ALBARÁN",
    "FECHA", "FECHA EMISION", "FECHA EMISIÓN", "FECHA DE EMISION", "FECHA DE EMISIÓN",
    "EMISION", "EMISIÓN", "EMISION FACTURA", "EMISION FACTURA", "NIF", "CIF",
    "DIRECCION", "DIRECCIÓN", "DOMICILIO", "CLIENTE FACTURA", "DATOS FISCALES",
    "BIKES", "EBIKES", "PATINES", "EPATINES", "SCOOTERS", "MOTOS",
}


def _normalizar_ocr(texto: str) -> str:
    """Corrige errores OCR frecuentes en NIFs/CIFs para mejorar detección."""
    for patron, reemplazo in _OCR_FIXES:
        texto = patron.sub(reemplazo, texto)
    return texto


def _extraer_total_ticket_combustible(texto: str) -> Optional[str]:
    """Extrae total en tickets de combustible cuando OCR rompe la línea de TOTAL."""
    # 0) Buscar por líneas de TOTAL con ruido OCR (guion largo, signos raros, etc.)
    lineas = [ln.strip() for ln in (texto or "").splitlines() if ln and ln.strip()]
    for ln in lineas:
        if not re.search(r"\btot(?:al|a)\b", ln, re.IGNORECASE):
            continue
        m_total_linea = re.search(r"([0-9]+[.,][0-9]{2})", ln)
        if m_total_linea:
            try:
                val = _parse_importes([m_total_linea.group(1)])[0]
                if val > 0:
                    return _fmt_eur(val)
            except Exception:
                pass

    # 1) Intentar por etiqueta directa de Importe
    m_importe = re.search(r"importe\s*[:;,\-\s]*([0-9]+[.,][0-9]{1,2})", texto, re.IGNORECASE)
    if m_importe:
        try:
            val = _parse_importes([m_importe.group(1)])[0]
            if val > 0:
                return _fmt_eur(val)
        except Exception:
            pass

    # 2) Inferir por Litros × Precio
    m_litros = re.search(r"litros\s*[:;,\-\s]*([0-9]+[.,][0-9]+)", texto, re.IGNORECASE)
    m_precio = re.search(r"precio\s*[:;,\-\s]*([0-9]+[.,][0-9]+)", texto, re.IGNORECASE)
    if m_litros and m_precio:
        try:
            litros = _parse_importes([m_litros.group(1)])[0]
            precio = _parse_importes([m_precio.group(1)])[0]
            total = round(litros * precio, 2)
            if total > 0:
                return _fmt_eur(total)
        except Exception:
            pass

    return None


def _extraer_datos_fiscales(t_izq: str, t_der: str, t_full: str) -> dict:
    """
    Extrae campos fiscales usando tres zonas de texto:
    - t_izq : tercio superior izquierdo  → emisor
    - t_der : tercio superior derecho    → receptor
    - t_full: página completa            → tabla, importes, totales
    """
    if not t_full:
        return _empty_datos()

    # Normalizar errores OCR comunes antes de procesar
    t_izq  = _normalizar_ocr(t_izq)
    t_der  = _normalizar_ocr(t_der)
    t_full = _normalizar_ocr(t_full)

    # ── NIFs: buscar en zona izquierda para emisor, derecha para receptor
    nifs_izq  = _NIF_RE.findall(t_izq)
    nifs_der  = _NIF_RE.findall(t_der)
    nifs_full = _NIF_RE.findall(t_full)

    nif_emisor   = nifs_izq[0] if nifs_izq else None
    nif_receptor = nifs_der[0] if nifs_der else None

    # Si no aparecen NIFs por zonas, usar el texto completo como último recurso.
    # Evitamos reutilizar un NIF del bloque derecho como emisor cuando la factura
    # solo muestra claramente el NIF del cliente/proveedor del lado derecho.
    if not nif_emisor and not nif_receptor and nifs_full:
        nif_emisor = nifs_full[0]
        if len(nifs_full) > 1:
            nif_receptor = nifs_full[1]

    # ── Nombre y dirección desde cada zona
    emisor_nombre,   emisor_direccion   = _extraer_entidad(t_izq,  nif_emisor,   es_emisor=True)
    receptor_nombre, receptor_direccion = _extraer_entidad(t_der,  nif_receptor, es_emisor=False)
    # Si no encontramos en la zona parcial, intentar en el texto completo
    if not emisor_nombre:
        emisor_nombre, emisor_direccion = _extraer_entidad(t_full, nif_emisor,   es_emisor=True)
    if not receptor_nombre:
        receptor_nombre, receptor_direccion = _extraer_entidad(t_full, nif_receptor, es_emisor=False)

    # Fallback específico para tickets (combustible): bloque Cliente + CIF/NIF
    if not receptor_nombre or not nif_receptor:
        tk_nombre, tk_nif, tk_dir = _extraer_receptor_ticket(t_full)
        if not receptor_nombre and tk_nombre:
            receptor_nombre = tk_nombre
        if not nif_receptor and tk_nif:
            nif_receptor = tk_nif
        if not receptor_direccion and tk_dir:
            receptor_direccion = tk_dir

    # Fallback emisor sin NIF claro: intentar extraer cabecera del bloque izquierdo.
    if not emisor_nombre:
        emisor_nombre = _detectar_nombre_cabecera(t_izq) or _detectar_nombre_cabecera(t_full)

    # Normalizaciones finales de campos entidad.
    emisor_nombre = _normalizar_linea_ocr(emisor_nombre or "") or None
    receptor_nombre = _normalizar_linea_ocr(receptor_nombre or "") or None
    emisor_direccion = _normalizar_linea_ocr(emisor_direccion or "") or None
    receptor_direccion = _normalizar_linea_ocr(receptor_direccion or "") or None

    # Si emisor y receptor quedan idénticos (ruido OCR frecuente), conservar receptor
    # y dejar emisor vacío para evitar información claramente incorrecta.
    if emisor_nombre and receptor_nombre and emisor_nombre.upper() == receptor_nombre.upper():
        if (nif_emisor or "").upper() == (nif_receptor or "").upper():
            emisor_nombre = None
            emisor_direccion = None
            nif_emisor = None
        elif not nif_emisor and nif_receptor:
            emisor_nombre = None
            emisor_direccion = None

    # ── Fechas (del texto completo)
    texto = t_full
    fechas = _FECHA_RE.findall(texto)
    fecha = fechas[0] if fechas else None
    fecha_venc = _first(_VENCIMIENTO_RE.search(texto)) or (fechas[1] if len(fechas) > 1 else None)

    # ── Número de factura
    numero_factura = _extraer_numero_factura(texto)

    # ── Importes
    base_match = _BASE_RE.search(texto) or _BASE_TABLA_RE.search(texto)
    cuota_match = _CUOTA_IVA_RE.search(texto)
    base      = _first(base_match)
    tipo_iva  = _first(_IVA_TIPO_RE.search(texto)) or _first(_IVA_TIPO_TABLA_RE.search(texto))
    cuota_iva = _first(cuota_match)
    total     = (
        _first(_TOTAL_TICKET_RE.search(texto))
        or _first(_TOTAL_FACTURA_RE.search(texto))
        or _first(_TOTAL_RE.search(texto))
    )
    irpf      = _first(_IRPF_RE.search(texto))

    # Inferir importes del conjunto de todos los números encontrados
    importes_raw = _IMPORTE_RE.findall(texto)
    importes_limpios = sorted(set(_parse_importes(importes_raw)))

    es_ticket_combustible = bool(
        re.search(r"surtidor|producto|litros|precio|aceptador", texto, re.IGNORECASE)
    )

    if not total and es_ticket_combustible:
        total = _extraer_total_ticket_combustible(texto)

    if importes_limpios:
        if not total:
            total = _fmt_eur(importes_limpios[-1])

        # Calcular base a partir de tipo IVA conocido (4, 10, 21%)
        if not base and tipo_iva and total:
            try:
                t = _parse_importes([total])[0]
                tasa = float(tipo_iva) / 100
                b = round(t / (1 + tasa), 2)
                # Verificar que el valor calculado existe en los importes detectados
                if any(abs(imp - b) < 0.02 for imp in importes_limpios):
                    base = _fmt_eur(b)
                else:
                    base = _fmt_eur(b)  # usar igualmente
            except Exception:
                pass

        # Cuota IVA = total - base
        if not cuota_iva and base and total:
            try:
                b = _parse_importes([base])[0]
                t = _parse_importes([total])[0]
                diff = round(t - b, 2)
                if 0 < diff < t:
                    cuota_iva = _fmt_eur(diff)
            except Exception:
                pass

    # Si no hay etiquetas fiscales claras y la suma no cuadra, limpiamos base/cuota
    # para no mostrar importes engañosos en tickets OCR ruidosos.
    if base and cuota_iva and total:
        try:
            b = _parse_importes([base])[0]
            c = _parse_importes([cuota_iva])[0]
            t = _parse_importes([total])[0]
            if abs((b + c) - t) > 0.05 and not base_match and not cuota_match:
                base = None
                cuota_iva = None
        except Exception:
            pass

        # IVA % inferido si no lo detectamos
        if not tipo_iva and base and cuota_iva:
            try:
                b = _parse_importes([base])[0]
                c = _parse_importes([cuota_iva])[0]
                pct = round(c / b * 100)
                if pct in (4, 5, 10, 21):
                    tipo_iva = str(pct)
            except Exception:
                pass

        # Si cuota_iva parece un porcentaje entero (ej: 21,00) y no tenemos tipo_iva,
        # es probable que se haya confundido la columna: moverlo a tipo_iva
        if cuota_iva and not tipo_iva:
            try:
                c = _parse_importes([cuota_iva])[0]
                if c in (4.0, 5.0, 10.0, 21.0):
                    tipo_iva = str(int(c))
                    # Recalcular cuota real desde base y total
                    if base and total:
                        b = _parse_importes([base])[0]
                        t = _parse_importes([total])[0]
                        diff = round(t - b, 2)
                        cuota_iva = _fmt_eur(diff) if 0 < diff < t else None
                    else:
                        cuota_iva = None
            except Exception:
                pass

    # Concepto
    concepto = _first(_CONCEPTO_RE.search(texto))
    return {
        "emisor_nombre":      _limpiar_campo(emisor_nombre),
        "emisor_nif":         nif_emisor,
        "emisor_direccion":   _limpiar_campo(emisor_direccion),
        "receptor_nombre":    _limpiar_campo(receptor_nombre),
        "receptor_nif":       nif_receptor,
        "receptor_direccion": _limpiar_campo(receptor_direccion),
        "numero_factura":     numero_factura,
        "fecha":              fecha,
        "fecha_vencimiento":  fecha_venc,
        "concepto":           concepto,
        "base_imponible":     _normalizar_importe_texto(base),
        "tipo_iva":           tipo_iva,
        "cuota_iva":          _normalizar_importe_texto(cuota_iva),
        "irpf":               irpf,
        "total":              _normalizar_importe_texto(total),
    }


def _fmt_eur(v: float) -> str:
    """Formatea un importe en formato europeo con símbolo €."""
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def _limpiar_campo(s: Optional[str]) -> Optional[str]:
    """Elimina caracteres basura OCR al inicio/fin de un campo de texto."""
    if not s:
        return s
    # Eliminar caracteres sueltos típicos de OCR: | ] [ ; : al inicio/fin
    s = re.sub(r"^[\s|;\[\]]+|[\s|;\[\]]+$", "", s)
    # Normalizar separador 'x' entre números en nombres comerciales: '100 x 100' -> '100X100'
    s = re.sub(r"(?<=\d)\s*[x×]\s*(?=\d)", "X", s, flags=re.IGNORECASE)
    # Reemplazar secuencias internas de ruido tipo "J) " → "JJ " (no hacemos aquí, demasiado arriesgado)
    return s.strip() or None


def _normalizar_linea_ocr(texto: str) -> str:
    """Limpia etiquetas y prefijos típicos de OCR para evaluar mejor nombres/direcciones."""
    texto = _limpiar_campo(texto) or ""
    if not texto:
        return texto
    texto = re.sub(r"^(?:fecha(?:\s+de)?\s+emisi[oó]n|fecha|nif|cif|direcci[oó]n|domicilio)\s*[:\-]??\s*", "", texto, flags=re.I)
    texto = re.sub(r"^\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\s+", "", texto)
    texto = re.sub(r"^\d{4,5}\s+", "", texto)
    texto = re.sub(r"\s{2,}", " ", texto).strip(" -:|\t")
    return texto


def _normalizar_importe_texto(v: Optional[str]) -> Optional[str]:
    if not v:
        return v
    try:
        return _fmt_eur(_parse_importes([v])[0])
    except Exception:
        return v


def _detectar_nombre_cabecera(texto: str) -> Optional[str]:
    """Devuelve la primera línea útil de la cabecera que parezca razón social."""
    for linea in (texto or "").splitlines()[:12]:
        linea = _normalizar_linea_ocr(linea)
        if not linea:
            continue
        if _es_ruido_menu(linea):
            continue
        if _es_linea_ciudad(linea) or _es_linea_direccion(linea):
            continue
        if _es_linea_nombre(linea):
            return linea
    return None


def _es_ruido_menu(texto: str) -> bool:
    t = texto.strip()
    if not t:
        return False
    if re.search(r"[\[\]{}<>]", t):
        return True
    if t.count("&") >= 2:
        return True
    # Menús/catálogos OCR: tokens cortos separados por símbolos
    tokens = re.split(r"\s+", re.sub(r"[^A-Za-zÁÉÍÓÚÑÜáéíóúñü0-9 ]+", " ", t))
    tokens = [x for x in tokens if x]
    if len(tokens) >= 4 and sum(1 for x in tokens if len(x) <= 3) >= 2 and re.search(r"[\]&|]", texto):
        return True
    return False


def _es_linea_ciudad(texto: str) -> bool:
    texto = texto.strip()
    if not texto:
        return False
    if re.match(r"^\d{4,5}\b", texto):
        return True
    if re.match(r"^(madrid|barcelona|valencia|sevilla|bilbao|zaragoza|malaga|málaga|murcia|alicante|valladolid|granada|córdoba|cordoba|salamanca|donostia|san sebasti[aá]n|manzanares del real)\b", texto, re.I):
        return True
    return False


def _es_linea_direccion(texto: str) -> bool:
    texto = texto.strip()
    if not texto:
        return False
    if re.search(
        r"\b(calle|c/|avda?|avenida|plaza|paseo|p\.o?\.?|cl\.?|carrer|pol\.?|polig|pol[ií]gono|carretera|crta|nave|local|portal|puerta)\b",
        texto,
        re.I,
    ):
        return True
    # Direcciones sin palabra clave pero con número y coma/punto suelen ser la calle
    if re.search(r"\b\d+[A-Za-z]?$", texto) and ("," in texto or "-" in texto or "/" in texto):
        return True
    # Línea tipo código postal al inicio + texto
    if re.match(r"^\d{4,5}\b", texto) and re.search(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü]", texto):
        return True
    return False


def _es_linea_nombre(texto: str) -> bool:
    texto = _normalizar_linea_ocr(texto)
    if not texto or len(texto) < 3:
        return False
    if _es_ruido_menu(texto):
        return False
    if _NIF_RE.fullmatch(texto.replace(" ", "")):
        return False
    texto_norm = re.sub(r"[^A-Z0-9ÁÉÍÓÚÜÑ ]+", "", texto.upper()).strip()
    if texto_norm in _ENTITY_STOPWORDS:
        return False
    if texto_norm.startswith("FECHA") or texto_norm.startswith("NIF") or texto_norm.startswith("CIF"):
        return False
    if re.search(r"@|https?://|www\.", texto, re.I):
        return False
    if re.match(r"^\d{4,5}\b", texto):
        return False
    if re.match(r"^\d{9,}$", texto):
        return False
    if re.search(r"\b(tel|fax|móvil|movil|email|correo)\b", texto, re.I):
        return False
    if re.search(r"\b\d{2}[\/\-\.]\d{2}[\/\-\.]\d{2,4}\b", texto):
        return False
    if re.search(r"\b(cantidad|uds?|precio|importe|subtotal|total)\b", texto, re.I):
        return False
    # Nombre comercial válido: muchas letras, puede incluir números (p.ej. 100X100)
    return bool(re.search(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü]", texto))


def _empty_datos() -> dict:
    return {k: None for k in [
        "emisor_nombre", "emisor_nif", "emisor_direccion",
        "receptor_nombre", "receptor_nif", "receptor_direccion",
        "numero_factura", "fecha", "fecha_vencimiento",
        "concepto", "base_imponible", "tipo_iva", "cuota_iva", "irpf", "total",
    ]}


def _parse_importes(raw: list[str]) -> list[float]:
    """Convierte cadenas de importe a float."""
    result = []
    for s in raw:
        s = s.replace("€", "").strip()
        # Detectar formato europeo (1.234,56) vs anglosajón (1,234.56)
        if "," in s and "." in s:
            if s.index(",") > s.index("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            result.append(float(s))
        except ValueError:
            pass
    return result


def _extraer_entidad(texto: str, nif: Optional[str], *, es_emisor: bool):
    """
    Busca el nombre y dirección asociados a un NIF/CIF.
    En facturas españolas el NIF suele aparecer DESPUÉS del nombre y dirección.
    Buscamos hacia atrás desde la línea del NIF.
    """
    if not nif:
        return None, None

    lineas = texto.splitlines()
    for i, linea in enumerate(lineas):
        if nif.upper() in linea.upper():
            # Recopilar hasta 14 líneas anteriores no vacías (facturas con imagen
            # tienen muchas líneas vacías entre el nombre y el NIF)
            anteriores = []
            for j in range(i - 1, max(i - 15, -1), -1):
                l = lineas[j].strip()
                if l:
                    anteriores.append(l)

            nombre = None
            direccion = None

            for ant in anteriores:
                ant = ant.strip()
                if len(ant) < 3:
                    continue
                if _es_linea_ciudad(ant):
                    continue
                if re.match(r"^\d{9,}$", ant):
                    continue
                if re.search(r"@|https?://|www\.", ant, re.I):
                    continue
                if _es_ruido_menu(ant):
                    continue

                es_direccion = _es_linea_direccion(ant) or bool(re.match(r"^\d{4,5}\b", ant) and re.search(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü]", ant))
                es_nombre = _es_linea_nombre(ant)

                if es_direccion and not direccion:
                    direccion = ant
                elif es_nombre and not nombre:
                    nombre = ant

                if nombre and direccion:
                    break

            # Fallback: el último elemento de anteriores válido
            if not nombre and anteriores:
                for ant in reversed(anteriores):
                    ant = ant.strip()
                    if len(ant) >= 3 and _es_linea_nombre(ant):
                        nombre = ant
                        break

            # Fallback extra para emisor: cabecera de la factura / primera línea útil.
            if not nombre and es_emisor:
                nombre = _detectar_nombre_cabecera(texto)

            return nombre, direccion

    return None, None


def _extraer_receptor_ticket(texto: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Extrae receptor en tickets OCR ruidosos (líneas Cliente/CIF-NIF)."""
    lineas = [ln.strip() for ln in (texto or "").splitlines() if ln and ln.strip()]
    if not lineas:
        return None, None, None

    nombre: Optional[str] = None
    nif: Optional[str] = None
    direccion: Optional[str] = None

    for i, ln in enumerate(lineas):
        if not re.search(r"\bcliente\b", ln, re.IGNORECASE):
            continue

        # Nombre en la misma línea, a menudo entre comillas o tras ':'/'-'
        m_q = re.search(r"cliente\s*[:\-]?\s*['\"]?([^'\"\n]{3,80})", ln, re.IGNORECASE)
        if m_q:
            cand = _normalizar_linea_ocr(m_q.group(1))
            if cand and _es_linea_nombre(cand):
                nombre = cand

        # Si no está en la misma línea, buscar en las siguientes líneas próximas
        if not nombre:
            for j in range(i + 1, min(i + 6, len(lineas))):
                cand = _normalizar_linea_ocr(lineas[j])
                if _es_linea_nombre(cand):
                    nombre = cand
                    break

        # Buscar NIF/CIF del receptor cerca del bloque cliente
        for j in range(i, min(i + 12, len(lineas))):
            m_id = re.search(r"(?:CIF\s*/?\s*NIF|NIF\s*/?\s*CIF|CIF|NIF)\s*[:\-]?\s*([A-Z0-9]{8,10})", lineas[j], re.IGNORECASE)
            if not m_id:
                continue
            cand_id = _normalizar_ocr(m_id.group(1).upper())
            # Si encontramos CIF/NIF explícito, lo usamos aunque sea formato no perfecto
            nif = cand_id
            break

        # Dirección (código postal + localidad) cerca del bloque cliente
        for j in range(i, min(i + 12, len(lineas))):
            cand_raw = lineas[j].strip()
            if re.match(r"^\d{4,5}\b", cand_raw):
                direccion = cand_raw
                break

        if nombre or nif:
            break

    return nombre, nif, direccion


def _calcular_confianza(datos: dict) -> str:
    """Devuelve alta / media / baja según campos extraídos."""
    campos_clave = ["emisor_nif", "fecha", "total", "numero_factura"]
    encontrados = sum(1 for k in campos_clave if datos.get(k))
    if encontrados >= 4:
        return "alta"
    if encontrados >= 2:
        return "media"
    return "baja"


def _detectar_tipo_factura(datos: dict, texto: str) -> str:
    t = (texto or "").upper()
    if re.search(r"RECTIFICATIV|ABONO|NOTA\s+DE\s+CR[ÉE]DITO", t):
        return "rectificativa"
    if re.search(r"FACTURA\s+SIMPLIFICADA|TICKET", t):
        return "simplificada"
    if datos.get("numero_factura") and datos.get("fecha") and datos.get("total"):
        return "completa"
    return "desconocida"


def _nif_control_letra(numero: int) -> str:
    return "TRWAGMYFPDXBNJZSQVHLCKE"[numero % 23]


def _validar_nif_nie(nif: str) -> bool:
    nif = (nif or "").upper().strip()
    if re.fullmatch(r"\d{8}[A-Z]", nif):
        return _nif_control_letra(int(nif[:8])) == nif[-1]
    if re.fullmatch(r"[XYZ]\d{7}[A-Z]", nif):
        pref = {"X": "0", "Y": "1", "Z": "2"}[nif[0]]
        return _nif_control_letra(int(pref + nif[1:8])) == nif[-1]
    return False


def _validar_cif(cif: str) -> bool:
    cif = (cif or "").upper().strip()
    if not re.fullmatch(r"[ABCDEFGHJKLMNPQRSUVW]\d{7}[0-9A-J]", cif):
        return False
    digitos = cif[1:8]
    suma_pares = sum(int(digitos[i]) for i in (1, 3, 5))
    suma_impares = 0
    for i in (0, 2, 4, 6):
        d = int(digitos[i]) * 2
        suma_impares += d // 10 + d % 10
    total = suma_pares + suma_impares
    control_num = (10 - (total % 10)) % 10
    control_letra = "JABCDEFGHI"[control_num]
    ultimo = cif[-1]
    tipo = cif[0]
    if tipo in "PQRSNW":
        return ultimo == control_letra
    if tipo in "ABEH":
        return ultimo == str(control_num)
    return ultimo in {str(control_num), control_letra}


def _validar_id_fiscal_es(valor: Optional[str]) -> bool:
    if not valor:
        return False
    v = valor.strip().upper()
    if _validar_nif_nie(v):
        return True
    if _validar_cif(v):
        return True
    # Permitir VAT intracomunitario básico (formato) como válido sintácticamente
    if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{3,14}", v):
        return True
    return False


def _to_float_importe(valor: Optional[str]) -> Optional[float]:
    if not valor:
        return None
    nums = _parse_importes([valor])
    return nums[0] if nums else None


def _validar_factura_espania(datos: dict, texto: str) -> dict:
    """
    Validación práctica para escaneo en España:
    - bloqueantes: campos críticos ausentes/inconsistentes
    - advertencias: patrones dudosos para revisión manual
    """
    bloqueantes: list[str] = []
    advertencias: list[str] = []
    tipo = _detectar_tipo_factura(datos, texto)

    # Campos mínimos transversales
    if not datos.get("numero_factura"):
        bloqueantes.append("Falta número de factura.")
    if not datos.get("fecha"):
        bloqueantes.append("Falta fecha de expedición.")
    if not datos.get("total"):
        bloqueantes.append("Falta importe total.")
    if not datos.get("emisor_nif"):
        bloqueantes.append("Falta NIF/CIF del emisor.")

    # Validación sintáctica de IDs fiscales
    if datos.get("emisor_nif") and not _validar_id_fiscal_es(datos.get("emisor_nif")):
        advertencias.append("El NIF/CIF del emisor no supera validación de formato/control.")
    if datos.get("receptor_nif") and not _validar_id_fiscal_es(datos.get("receptor_nif")):
        advertencias.append("El NIF/CIF del receptor no supera validación de formato/control.")

    # Reglas por tipo
    if tipo == "completa":
        if not datos.get("emisor_nombre"):
            bloqueantes.append("Factura completa sin nombre/razón social de emisor.")
        if not datos.get("receptor_nombre"):
            bloqueantes.append("Factura completa sin nombre/razón social de receptor.")
        if not datos.get("base_imponible"):
            advertencias.append("No se detecta base imponible en factura completa.")
        if not datos.get("tipo_iva"):
            advertencias.append("No se detecta tipo de IVA.")
    elif tipo == "simplificada":
        if not datos.get("numero_factura"):
            bloqueantes.append("Factura simplificada sin número de factura.")
        if not datos.get("fecha"):
            bloqueantes.append("Factura simplificada sin fecha de expedición.")
        if not datos.get("emisor_nif"):
            bloqueantes.append("Factura simplificada sin NIF/CIF de emisor.")
        if not datos.get("emisor_nombre"):
            bloqueantes.append("Factura simplificada sin identificación del emisor.")
        if not datos.get("total"):
            bloqueantes.append("Factura simplificada sin total.")
        if not datos.get("tipo_iva") and not datos.get("cuota_iva"):
            advertencias.append("Factura simplificada sin desglose claro de IVA.")
    elif tipo == "rectificativa":
        if not re.search(r"FACTURA\s+RECTIFICATIVA|RECTIFICATIV|ABONO", (texto or ""), re.I):
            advertencias.append("Parece rectificativa pero no se encuentra literal explícito.")
        # Nota: evitamos buscar "RECTIFICA" a secas porque da falsos positivos
        # con el literal "RECTIFICATIVA".
        if not re.search(
            r"\bSE\s+RECTIFICA\b|FACTURA\s+ORIGINAL|NUM(?:ERO|\.|º)?\s+FACTURA\s+RECTIFICADA",
            (texto or ""),
            re.I,
        ):
            bloqueantes.append("Factura rectificativa sin referencia clara a factura original.")

    # Coherencia matemática
    base = _to_float_importe(datos.get("base_imponible"))
    cuota = _to_float_importe(datos.get("cuota_iva"))
    total = _to_float_importe(datos.get("total"))

    if base is not None and cuota is not None and total is not None:
        esperado = round(base + cuota, 2)
        if abs(esperado - total) > 0.05:
            advertencias.append(
                f"Inconsistencia de importes: base + IVA = {esperado:.2f} y total = {total:.2f}."
            )

    if base and cuota and datos.get("tipo_iva"):
        try:
            tipo_iva = float(str(datos["tipo_iva"]).replace(",", "."))
            real = round((cuota / base) * 100, 2)
            if abs(real - tipo_iva) > 1.0:
                advertencias.append(
                    f"El IVA detectado ({tipo_iva:.2f}%) no cuadra con base/cuota ({real:.2f}%)."
                )
        except ValueError:
            advertencias.append("No se pudo interpretar el tipo de IVA detectado.")

    # Literales especiales (informativos)
    if re.search(r"INVERSI[ÓO]N\s+DEL\s+SUJETO\s+PASIVO", (texto or ""), re.I):
        advertencias.append("Se detecta 'inversión del sujeto pasivo': revisar régimen especial aplicable.")
    if re.search(r"R[ÉE]GIMEN\s+ESPECIAL|CRITERIO\s+DE\s+CAJA", (texto or ""), re.I):
        advertencias.append("Se detecta mención a régimen especial: revisar requisitos fiscales específicos.")

    puntuacion = max(0, 100 - (len(bloqueantes) * 30) - (len(advertencias) * 8))
    estado = "valida" if not bloqueantes else "incompleta"
    return {
        "estado": estado,
        "tipo_factura": tipo,
        "puntuacion": puntuacion,
        "bloqueantes": bloqueantes,
        "advertencias": advertencias,
    }
