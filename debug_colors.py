"""
Script de debug para analizar los colores en el PDF y detectar líneas.
"""

import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import cv2
import io
import os


def analyze_page_colors(pdf_path, page_num=0, output_dir="debug_analysis"):
    """
    Analiza una página del PDF para entender qué colores hay
    y detectar líneas horizontales.
    """
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)

    # Buscar página del apartado 6.1
    print("Buscando apartado 6.1...")
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        if "6.1" in text and "APLICACIÓ DE CRITERIS AMBIENTALS" in text:
            page_num = i
            print(f"Encontrado apartado 6.1 en página {i+1}")
            break

    page = doc[page_num]

    # Renderizar página con alta resolución
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)

    # Convertir a imagen
    img_data = pix.tobytes("png")
    img_pil = Image.open(io.BytesIO(img_data))
    img_rgb = np.array(img_pil)
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    height, width = img_bgr.shape[:2]
    print(f"\nDimensiones de la página: {width}x{height}px")

    # Guardar imagen original
    cv2.imwrite(os.path.join(output_dir, "original.png"), img_bgr)
    print(f"Guardada: {output_dir}/original.png")

    # Analizar colores únicos en la imagen
    print("\n--- ANÁLISIS DE COLORES ---")

    # Crear histograma de colores azulados (B > R y B > G)
    blue_mask = (img_bgr[:,:,0] > img_bgr[:,:,2]) & (img_bgr[:,:,0] > img_bgr[:,:,1])
    blue_pixels = img_bgr[blue_mask]

    if len(blue_pixels) > 0:
        print(f"Píxeles azulados encontrados: {len(blue_pixels)}")
        print(f"Color azul promedio (BGR): {np.mean(blue_pixels, axis=0)}")
        print(f"Color azul mínimo (BGR): {np.min(blue_pixels, axis=0)}")
        print(f"Color azul máximo (BGR): {np.max(blue_pixels, axis=0)}")

        # Visualizar píxeles azules
        blue_visualization = np.zeros_like(img_bgr)
        blue_visualization[blue_mask] = [255, 255, 255]
        cv2.imwrite(os.path.join(output_dir, "blue_pixels.png"), blue_visualization)
        print(f"Guardada: {output_dir}/blue_pixels.png (todos los píxeles azulados)")

    # Probar diferentes rangos de detección de azul
    target_bgr = np.array([219, 180, 141])  # #8DB4DB

    print(f"\n--- PROBANDO DIFERENTES TOLERANCIAS ---")
    for tolerance in [20, 35, 50, 70, 100]:
        lower = np.array([max(0, target_bgr[i] - tolerance) for i in range(3)])
        upper = np.array([min(255, target_bgr[i] + tolerance) for i in range(3)])

        mask = cv2.inRange(img_bgr, lower, upper)
        pixel_count = np.sum(mask > 0)

        cv2.imwrite(os.path.join(output_dir, f"mask_tol_{tolerance}.png"), mask)
        print(f"Tolerancia ±{tolerance}: {pixel_count} píxeles detectados -> {output_dir}/mask_tol_{tolerance}.png")

        # Proyección vertical
        vertical_proj = np.sum(mask, axis=1) / 255
        max_coverage = np.max(vertical_proj) if len(vertical_proj) > 0 else 0
        max_coverage_pct = (max_coverage / width) * 100

        print(f"  -> Máxima cobertura horizontal: {max_coverage:.0f}px ({max_coverage_pct:.1f}%)")

        # Encontrar filas con más del 50% de cobertura
        threshold_50 = width * 0.5
        lines_50 = np.where(vertical_proj >= threshold_50)[0]
        if len(lines_50) > 0:
            print(f"  -> Filas con >50% cobertura: {len(lines_50)}")

        # Encontrar filas con más del 70% de cobertura
        threshold_70 = width * 0.7
        lines_70 = np.where(vertical_proj >= threshold_70)[0]
        if len(lines_70) > 0:
            print(f"  -> Filas con >70% cobertura: {len(lines_70)}")

    print(f"\n--- ANÁLISIS DE LÍNEAS HORIZONTALES ---")

    # Detectar bordes
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    cv2.imwrite(os.path.join(output_dir, "edges.png"), edges)
    print(f"Guardada: {output_dir}/edges.png (detección de bordes)")

    # Detectar líneas con Hough Transform
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=width*0.5, maxLineGap=10)

    if lines is not None:
        print(f"\nLíneas detectadas con Hough: {len(lines)}")
        img_with_lines = img_bgr.copy()

        horizontal_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # Filtrar solo líneas horizontales (diferencia Y pequeña)
            if abs(y2 - y1) < 5:
                line_length = abs(x2 - x1)
                coverage_pct = (line_length / width) * 100
                if coverage_pct > 50:  # Solo líneas que cubren >50%
                    horizontal_lines.append((y1, line_length, coverage_pct))
                    cv2.line(img_with_lines, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.imwrite(os.path.join(output_dir, "hough_lines.png"), img_with_lines)
        print(f"Líneas horizontales largas: {len(horizontal_lines)}")
        for y, length, pct in sorted(horizontal_lines):
            print(f"  Y={y}, longitud={length}px, cobertura={pct:.1f}%")

    doc.close()

    print(f"\n✓ Análisis completado. Revisa los archivos en '{output_dir}/'")


if __name__ == "__main__":
    analyze_page_colors("documento.pdf")
