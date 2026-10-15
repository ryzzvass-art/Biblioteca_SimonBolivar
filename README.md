# Biblioteca de Proyectos · Instituto Simón Bolívar

Sitio estático para GitHub Pages: `index.html` (bienvenida) → `biblioteca.html` (biblioteca).

## Cómo actualizar los PDFs
1. `pip install openpyxl`
2. Desde esta carpeta:
   `python preparar.py "C:\ruta\ACTAS_DE_DEFENSA_DE_GRADO.xlsx" "C:\ruta\BibliotecaProyetos\PROYECTOS"`
   (copia los PDFs a `pdfs/` y regenera `data/proyectos.json`; lista los que no encontró)
3. Sube todo a un repositorio de GitHub → Settings → Pages → Branch `main` / root.
