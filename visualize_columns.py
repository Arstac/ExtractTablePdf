"""
Script para visualizar la división de columnas sobre una sección de tabla.
"""

import os
import glob
import cv2
import numpy as np


def visualize_column_division(section_path, output_path="column_division_preview.png"):
    """
    Genera una imagen con rectángulos superpuestos mostrando la división de columnas.
    """
    # Leer imagen
    img = cv2.imread(section_path)

    if img is None:
        print(f"Error: No se pudo leer {section_path}")
        return

    height, width = img.shape[:2]

    # Definir anchos relativos de las columnas (igual que en process_table.py)
    column_widths = {
        'tipus_criterio': .7,
        'nom_criteri': .85,
        'descripcio': 2.55,
        'on_incloure': 0.25,
        'doc_a_verificar_adj': 1,
        'doc_a_verificar_exec': 0.95,
        'condicionants': 1.05
    }

    column_names = [
        'tipus_criterio',
        'nom_criteri',
        'descripcio',
        'on_incloure',
        'doc_a_verificar_adj',
        'doc_a_verificar_exec',
        'condicionants'
    ]

    total_units = sum(column_widths.values())
    unit_width = width / total_units

    # Crear una copia de la imagen para dibujar
    img_with_rectangles = img.copy()

    # Crear una capa transparente para los rectángulos
    overlay = img.copy()

    # Colores para cada columna (diferentes colores para diferenciar)
    colors = [
        (255, 0, 0),      # Azul
        (0, 255, 0),      # Verde
        (0, 0, 255),      # Rojo
        (255, 255, 0),    # Cyan
        (255, 0, 255),    # Magenta
        (0, 255, 255),    # Amarillo
        (128, 128, 255)   # Rosa
    ]

    x_start = 0

    print(f"\nDivisión de columnas para: {os.path.basename(section_path)}")
    print(f"Ancho total: {width}px, Alto: {height}px")
    print(f"Unidad base: {unit_width:.2f}px\n")

    for i, col_name in enumerate(column_names):
        col_width_units = column_widths[col_name]
        col_width_px = int(unit_width * col_width_units)

        x_end = int(x_start + col_width_px)

        if x_end > width:
            x_end = width

        # Dibujar rectángulo
        color = colors[i % len(colors)]
        cv2.rectangle(overlay, (int(x_start), 0), (x_end, height), color, -1)

        # Dibujar borde
        cv2.rectangle(img_with_rectangles, (int(x_start), 0), (x_end, height), color, 3)

        # Añadir texto con el nombre de la columna
        text_y = 30 + (i * 40) % (height - 40)
        cv2.putText(
            img_with_rectangles,
            col_name,
            (int(x_start) + 5, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )

        # Añadir línea vertical en el borde
        if i > 0:
            cv2.line(img_with_rectangles, (int(x_start), 0), (int(x_start), height), (0, 0, 0), 2)

        print(f"{i+1}. {col_name:25s} | X: {int(x_start):4d} - {x_end:4d} | Ancho: {x_end - int(x_start):4d}px ({col_width_units} unidades)")

        x_start = x_end

    # Mezclar la imagen original con la capa de rectángulos (transparencia)
    alpha = 0.3  # Transparencia de los rectángulos
    img_blended = cv2.addWeighted(overlay, alpha, img_with_rectangles, 1 - alpha, 0)

    # Guardar imagen
    cv2.imwrite(output_path, img_blended)
    print(f"\n✓ Visualización guardada en: {output_path}")

    # También guardar una versión solo con bordes (sin relleno)
    output_path_borders = output_path.replace('.png', '_borders_only.png')
    cv2.imwrite(output_path_borders, img_with_rectangles)
    print(f"✓ Versión solo bordes en: {output_path_borders}")

    return img_blended


def main():
    # Buscar la primera sección disponible
    pattern = "output_sections/page_*_section_*.png"
    files = glob.glob(pattern)

    if not files:
        print("No se encontraron secciones en 'output_sections/'")
        print("Ejecuta primero extract_section.py para generar las secciones")
        return

    # Ordenar y tomar la primera
    files.sort()

    # Usar la primera sección que no sea "_top"
    section_file = None
    for f in files:
        if "_top" not in f:
            section_file = f
            break

    if not section_file:
        section_file = files[8]

    print(f"Usando sección: {section_file}")

    # Generar visualización
    visualize_column_division(section_file, "column_division_preview.png")

    print("\nAhora revisa las imágenes generadas:")
    print("  - column_division_preview.png (con rectángulos de colores)")
    print("  - column_division_preview_borders_only.png (solo bordes)")


if __name__ == "__main__":
    main()
