# Biblioteca de Proyectos · Instituto Simón Bolívar

Sitio estático para GitHub Pages: `index.html` (bienvenida) → `biblioteca.html` (biblioteca).

## Cómo actualizar los PDFs
1. `pip install openpyxl pypdf`
2. Desde esta carpeta:
   `python preparar.py "C:\ruta\ACTAS_DE_DEFENSA_DE_GRADO.xlsx" "C:\ruta\BibliotecaProyetos\PROYECTOS"`
   (copia los PDFs a `pdfs/`, regenera `data/proyectos.json` y `data/busqueda.json`, y lista los que no encontró). Si la columna de título del Excel contiene solo un número, toma el título de la portada del PDF.
3. Sube todo a un repositorio de GitHub → Settings → Pages → Branch `main` / root.
