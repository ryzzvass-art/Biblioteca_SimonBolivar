#!/usr/bin/env python3
"""
Genera data/proyectos.json a partir del Excel y enlaza cada proyecto con su PDF.

Uso (desde la carpeta del sitio):
    python preparar.py "RUTA\\ACTAS_DE_DEFENSA_DE_GRADO.xlsx" "RUTA\\BibliotecaProyetos\\PROYECTOS"

- Recorre PROYECTOS/<NOMBRE DEL ESTUDIANTE>/ y toma SOLO el .pdf.
- Copia cada PDF a pdfs/<nº>-<nombre>.pdf (nombre limpio, sin espacios ni tildes).
- Escribe data/proyectos.json. Informa qué proyectos quedaron sin PDF.
- NUEVO: extrae el texto de cada PDF y escribe data/busqueda.json (id -> texto normalizado)
  para poder buscar por palabras dentro del proyecto.
Requiere: pip install openpyxl pypdf
"""
import sys, re, json, shutil, unicodedata
from pathlib import Path
import openpyxl
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

ACRON = {"MIG","MAG","ESP32","CKP","CMP","NFC","ECU","ABS","CAN","GLP","GNC","OBD","USB","LED","PWM","EQ","NA","TIG",
         "GPS","GSM","IOT","PLC","CAN-BUS","DPF","EGR","TPS","MAP","MAF","CVT","ARDUINO","AC","DC","CC","II","III","IV","SRS","EPS","ADN","GNV","ECM","MPI","IMM","VE","SM2","BYD","APV","HR","AD","CC","JR","SCR","VVT","VVTI","DOHC","SOHC","4X4","4WD","AWD","GLP","IC","TDI","CRDI","HDI","TCU","BCM","ESP","EFI","MPFI","TBI","RPM"}
PROPIOS = {"toyota":"Toyota","nissan":"Nissan","suzuki":"Suzuki","hyundai":"Hyundai","kia":"Kia","mazda":"Mazda","honda":"Honda",
           "chevrolet":"Chevrolet","ford":"Ford","mitsubishi":"Mitsubishi","subaru":"Subaru","volkswagen":"Volkswagen","aicar":"AICAR",
           "android":"Android","bolivia":"Bolivia","alto":"Alto","paz":"Paz","tiida":"Tiida","tida":"Tida","ipsum":"Ipsum","bosch":"Bosch",
           "denso":"Denso","delphi":"Delphi","hino":"Hino","isuzu":"Isuzu","mercedes":"Mercedes","benz":"Benz","volvo":"Volvo","scania":"Scania",
           "wifi":"Wi-Fi","bluetooth":"Bluetooth","diesel":"diésel","pajero":"Pajero","landi":"Landi","renzo":"Renzo","forester":"Forester","subaru":"Subaru","mitsubishi":"Mitsubishi","xhorse":"Xhorse","godiag":"Godiag","trueno":"Trueno","buggy":"buggy","hr15":"HR15"}
MINUS = {"de","del","la","las","el","los","y","e","o","u","en","con","para","por","a","al","un","una","que","su","sus","sobre","como","entre","mediante"}

def sin_acentos(s): return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
def limpio(s): return re.sub(r"\s+", " ", str(s or "")).strip()
def clave(s): return sorted(re.findall(r"[A-Z0-9]+", sin_acentos(s).upper()))
def slug(s): return re.sub(r"[^a-z0-9]+","-",sin_acentos(s).lower()).strip("-")

def normaliza(s):
    """minúsculas, sin tildes, solo letras/números/espacios (para búsqueda)"""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9ñ ]+", " ", sin_acentos(str(s or "")).lower())).strip()

def texto_pdf(ruta):
    if PdfReader is None: return ""
    try:
        r = PdfReader(str(ruta))
        return normaliza(" ".join((pg.extract_text() or "") for pg in r.pages))
    except Exception as e:
        print("  ERROR leyendo", ruta, e); return ""

def nombre(s): return " ".join(w.capitalize() for w in limpio(s).lower().split())

def titulo(s):
    s = limpio(s)
    if not s: return s
    if sum(c.isupper() for c in s) < 0.5 * max(1, sum(c.isalpha() for c in s)):
        return s[0].upper()+s[1:]                      # ya viene en minúsculas/mixto
    out, nuevo = [], True
    for tok in re.split(r"(\s+)", s):
        if not tok.strip(): out.append(tok); continue
        m = re.match(r"^([^\wÁÉÍÓÚÑ]*)(.*?)([^\wÁÉÍÓÚÑ]*)$", tok, re.I)
        pre, core, suf = m.groups()
        up, low = core.upper(), core.lower()
        if up in ACRON or re.search(r"\d", core) and re.search(r"[A-Z]", up): w = up
        elif low in PROPIOS: w = PROPIOS[low]
        elif nuevo or low not in MINUS: w = low if low in MINUS else low
        else: w = low
        if nuevo and w == w.lower() and w not in PROPIOS.values(): w = w[:1].upper()+w[1:]
        out.append(pre+w+suf)
        nuevo = suf.endswith((":", ".")) or pre.endswith("(") and False
    t = "".join(out)
    t = re.sub(r"\(\s*caso\b", "(Caso", t, flags=re.I)
    return t

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    xlsx = Path(sys.argv[1]); root = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    base = Path(__file__).parent
    ws = openpyxl.load_workbook(xlsx).active
    carpetas = {}
    if root:
        for d in root.iterdir():
            if d.is_dir():
                pdfs = sorted(d.glob("*.pdf")) + sorted(d.glob("*.PDF"))
                if pdfs: carpetas[d.name] = pdfs[0]
    usados, lista = set(), []
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if not r[0]: continue
        n, ap, am = limpio(r[9]), limpio(r[10]), limpio(r[11])
        k = clave(f"{n} {ap} {am}")
        cand = None
        for nom in carpetas:
            if nom not in usados and clave(nom) == k: cand = nom; break
        if not cand:   # coincidencia aproximada
            mejor, ms = None, 0
            for nom in carpetas:
                if nom in usados: continue
                a, b = set(k), set(clave(nom)); sc = len(a & b) / len(a | b)
                if sc > ms: mejor, ms = nom, sc
            if ms >= 0.6: cand = mejor
        pdf = None
        if cand:
            usados.add(cand)
            dest = f"pdfs/{int(r[0]):03d}-{slug(cand)}.pdf"
            (base/"pdfs").mkdir(exist_ok=True); shutil.copyfile(carpetas[cand], base/dest); pdf = dest
        t = limpio(str(r[12]).replace("\n", " "))
        caso = None
        m = re.search(r"\(?\s*CASO\s*:?\s*(.+?)\)?\s*$", t, re.I)
        if m:
            caso = m.group(1).strip(" ()"); t0 = t[:m.start()].strip(" :.-")
            if t0: t = t0
            else: t, caso = t.strip("() "), None   # el Excel solo trae el "caso"
        lista.append({
            "id": int(r[0]), "titulo": titulo(t), "caso": titulo(caso) if caso else None,
            "autor": f"{nombre(n)} {nombre(ap)} {nombre(am)}".strip(),
            "nombres": nombre(n), "apellidos": f"{nombre(ap)} {nombre(am)}".strip(),
            "carrera": "Autotrónica" if "AUTOTRON" in sin_acentos(str(r[2]).upper()) else "Mecánica Automotriz",
            "nivel": nombre(r[3]).replace("Tecnico","Técnico"), "ciudad": nombre(r[4]), "departamento": nombre(r[5]),
            "fecha": re.sub(r"\s+"," ",str(r[6])).strip(), "inicio": limpio(r[7]).replace(" ",""), "fin": limpio(r[8]).replace(" ",""),
            "dia": nombre(r[1]).replace("Miercoles","Miércoles"), "pdf": pdf})
    lista.sort(key=lambda p: sin_acentos(p["autor"]))
    (base/"data").mkdir(exist_ok=True)
    (base/"data/proyectos.json").write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
    # Índice de búsqueda: texto completo de cada PDF
    if PdfReader is None: print("AVISO: instale pypdf (pip install pypdf) para buscar dentro de los PDF")
    indice, sin_texto = {}, []
    for p in lista:
        base_txt = normaliza(" ".join(filter(None, [p["titulo"], p["caso"], p["autor"], p["carrera"]])))
        cuerpo = texto_pdf(base/p["pdf"]) if p["pdf"] else ""
        if p["pdf"] and len(cuerpo) < 200: sin_texto.append(p["autor"])
        indice[p["id"]] = (base_txt + " " + cuerpo).strip()
    (base/"data/busqueda.json").write_text(json.dumps(indice, ensure_ascii=False), encoding="utf-8")
    print(f"Índice de búsqueda: {(base/'data/busqueda.json').stat().st_size/1e6:.1f} MB")
    for a in sin_texto: print("  PDF SIN TEXTO (escaneado, necesita OCR):", a)
    print(f"{len(lista)} proyectos · {sum(1 for p in lista if p['pdf'])} con PDF")
    for p in lista:
        if not p["pdf"]: print("  SIN PDF:", p["autor"])
    for nom in carpetas:
        if nom not in usados: print("  CARPETA SIN PROYECTO EN EXCEL:", nom)
if __name__ == "__main__": main()
