"""
Script para extraer y procesar el apartado 6.1 de un PDF.

Proceso:
1. Lee el PDF página por página
2. Encuentra las páginas del apartado 6.1 (entre 6.1 y 6.2)
3. Recorta encabezado y pie de página
4. Detecta 'Obligatori' y 'Opcional' en el margen izquierdo
5. Recorta las páginas por esas líneas
"""

import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import cv2
import io
import os


class PDFSectionExtractor:
    def __init__(self, pdf_path, output_dir="output"):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.doc = fitz.open(pdf_path)

        # Crear directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)

    def find_section_pages(self, start_marker="6.1", end_marker="6.2"):
        """
        Encuentra las páginas que contienen el apartado 6.1
        (desde que aparece 6.1 hasta que aparece 6.2)
        """
        start_page = None
        end_page = None

        print(f"Buscando apartado {start_marker}...")

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text()

            # Buscar el marcador de inicio
            if start_page is None:
                # Buscar "6.1 APLICACIÓ DE CRITERIS AMBIENTALS" o similar
                if start_marker in text and "APLICACIÓ DE CRITERIS AMBIENTALS" in text:
                    start_page = page_num
                    print(f"  Apartado {start_marker} encontrado en página {page_num + 1}")

            # Buscar el marcador de fin
            elif end_page is None:
                if end_marker in text and "INFORME JUSTIFICATIU" in text:
                    end_page = page_num
                    print(f"  Apartado {end_marker} encontrado en página {page_num + 1}")
                    break

        if start_page is None:
            raise ValueError(f"No se encontró el apartado {start_marker}")

        if end_page is None:
            print(f"  Advertencia: No se encontró el apartado {end_marker}, usando hasta el final del documento")
            end_page = len(self.doc)

        # Las páginas del apartado 6.1 son desde start_page hasta end_page-1
        section_pages = list(range(start_page, end_page))
        print(f"\nPáginas del apartado {start_marker}: {[p+1 for p in section_pages]}")

        return section_pages

    def crop_page_margins(self, page, header_height=50, footer_height=50):
        """
        Recorta el encabezado y pie de página de una página.
        Retorna un objeto pixmap con la página recortada.
        """
        # Obtener las dimensiones de la página
        rect = page.rect
        width = rect.width
        height = rect.height

        # Definir el área a recortar (excluir encabezado y pie)
        crop_rect = fitz.Rect(
            0,                    # x0 (izquierda)
            header_height,        # y0 (arriba, después del encabezado)
            width,                # x1 (derecha)
            height - footer_height  # y1 (abajo, antes del pie)
        )

        # Renderizar la página con el recorte
        mat = fitz.Matrix(2, 2)  # Matriz de zoom (2x para mejor calidad)
        pix = page.get_pixmap(matrix=mat, clip=crop_rect)

        return pix

    def find_blue_lines(self, pix, min_coverage_percent=70, debug_page_num=0):
        """
        Detecta líneas azules horizontales que van casi de banda a banda.
        Solo detecta líneas que cubren al menos min_coverage_percent del ancho de la página.

        Args:
            pix: Pixmap de la página
            min_coverage_percent: Porcentaje mínimo del ancho que debe cubrir la línea (default: 70%)
            debug_page_num: Número de página para debug
        """
        # Convertir pixmap a imagen PIL y luego a numpy array
        img_data = pix.tobytes("png")
        img_pil = Image.open(io.BytesIO(img_data))
        img_rgb = np.array(img_pil)

        # Convertir RGB a BGR para OpenCV
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        height, width = img_bgr.shape[:2]
        min_line_width = int(width * min_coverage_percent / 100)

        # Guardar imagen original para debug
        debug_dir = os.path.join(self.output_dir, "debug")
        os.makedirs(debug_dir, exist_ok=True)
        cv2.imwrite(os.path.join(debug_dir, f"page_{debug_page_num}_original.png"), img_bgr)

        print(f"    Dimensiones: {width}x{height}px")
        print(f"    Buscando líneas de al menos {min_line_width}px de ancho ({min_coverage_percent}% del ancho)")

        # Color objetivo: #8DB4DB (RGB: 141, 180, 219)
        # En BGR para OpenCV: (219, 180, 141)

        # Detección más estricta en BGR para el color exacto
        target_bgr = np.array([176, 176, 176])
        tolerance = 30  # Tolerancia moderada
        lower_blue_bgr = np.array([
            max(0, target_bgr[0] - tolerance),
            max(0, target_bgr[1] - tolerance),
            max(0, target_bgr[2] - tolerance)
        ])
        upper_blue_bgr = np.array([
            min(255, target_bgr[0] + tolerance),
            min(255, target_bgr[1] + tolerance),
            min(255, target_bgr[2] + tolerance)
        ])
        mask_bgr = cv2.inRange(img_bgr, lower_blue_bgr, upper_blue_bgr)

        # Detección en HSV para azul claro
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        lower_blue_hsv = np.array([95, 25, 140])   # Más específico para #8DB4DB
        upper_blue_hsv = np.array([110, 150, 240])
        mask_hsv = cv2.inRange(img_hsv, lower_blue_hsv, upper_blue_hsv)

        # Combinar máscaras
        mask = cv2.bitwise_or(mask_hsv, mask_bgr)

        # Guardar máscara original
        cv2.imwrite(os.path.join(debug_dir, f"page_{debug_page_num}_mask_raw.png"), mask)

        # Proyección vertical: sumar píxeles azules en cada fila
        vertical_projection = np.sum(mask, axis=1) / 255  # Número de píxeles azules por fila

        # Guardar gráfico de proyección
        max_val = max(vertical_projection) if len(vertical_projection) > 0 else 1
        proj_width = 1000
        proj_img = np.zeros((len(vertical_projection), proj_width, 3), dtype=np.uint8)

        # Dibujar línea del umbral mínimo
        threshold_x = int((min_line_width / width) * proj_width)
        cv2.line(proj_img, (threshold_x, 0), (threshold_x, height), (0, 0, 255), 2)

        # Dibujar proyección
        for y, val in enumerate(vertical_projection):
            norm_width = int((val / width) * proj_width) if width > 0 else 0
            if norm_width > 0:
                color = (0, 255, 0) if val >= min_line_width else (255, 255, 255)
                cv2.line(proj_img, (0, y), (norm_width, y), color, 1)

        # Encontrar líneas que cubren suficiente ancho
        line_positions = []

        i = 0
        while i < len(vertical_projection):
            # Solo considerar filas con suficientes píxeles azules (líneas de banda a banda)
            if vertical_projection[i] >= min_line_width:
                # Encontramos una línea
                start_y = i
                end_y = i
                max_val_in_line = vertical_projection[i]
                max_y = i

                # Expandir para encontrar toda la línea (pueden ser varios píxeles de grosor)
                while end_y < len(vertical_projection) - 1:
                    next_val = vertical_projection[end_y + 1]
                    # Continuar si la siguiente fila también tiene píxeles azules
                    if next_val >= min_line_width * 0.3:  # Al menos 30% del umbral
                        end_y += 1
                        if next_val > max_val_in_line:
                            max_val_in_line = next_val
                            max_y = end_y
                    else:
                        break

                # Usar la posición del pico máximo de la línea
                center_y = max_y
                line_width = vertical_projection[center_y]
                coverage_percent = (line_width / width) * 100

                line_positions.append({
                    'y': center_y,
                    'start_y': start_y,
                    'end_y': end_y,
                    'width': line_width,
                    'coverage': coverage_percent
                })

                print(f"    Línea detectada en Y={center_y} (grosor: {end_y-start_y+1}px, cobertura: {coverage_percent:.1f}%)")

                # Marcar en la imagen de proyección
                cv2.line(proj_img, (0, center_y), (proj_width, center_y), (255, 0, 255), 3)

                # Saltar al final de esta línea
                i = end_y + 1
            else:
                i += 1

        cv2.imwrite(os.path.join(debug_dir, f"page_{debug_page_num}_projection.png"), proj_img)

        # Crear imagen con líneas marcadas sobre la original
        img_with_lines = img_bgr.copy()
        for line in line_positions:
            cv2.line(img_with_lines, (0, line['y']), (width, line['y']), (0, 255, 0), 3)
            # Añadir texto con el porcentaje de cobertura
            cv2.putText(img_with_lines, f"{line['coverage']:.1f}%",
                       (10, line['y'] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.imwrite(os.path.join(debug_dir, f"page_{debug_page_num}_lines_detected.png"), img_with_lines)

        print(f"    Total líneas detectadas: {len(line_positions)}")

        return line_positions

    def split_and_crop_page(self, pix, positions, page_num):
        """
        Divide la página en secciones basándose en las posiciones de las líneas azules
        y guarda cada sección como una imagen separada.
        """
        # Convertir pixmap a imagen PIL
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        if not positions:
            # Si no hay posiciones, guardar la página completa
            output_path = os.path.join(self.output_dir, f"page_{page_num+1}_full.png")
            img.save(output_path)
            print(f"    Guardada página completa: {output_path}")
            return [output_path]

        # Ordenar posiciones por Y
        positions_sorted = sorted(positions, key=lambda x: x['y'])

        saved_files = []

        # Crear cortes en cada línea azul
        for i, pos in enumerate(positions_sorted):
            # El corte se hace en la posición de la línea azul
            cut_y = pos['y']

            if i == 0:
                # Primer corte: desde el inicio hasta la primera línea
                section = img.crop((0, 0, img.width, cut_y))
                output_path = os.path.join(self.output_dir, f"page_{page_num+1}_section_{i+1}_top.png")
                section.save(output_path)
                print(f"    Guardada sección superior: {output_path}")
                saved_files.append(output_path)

            # Sección desde esta línea hasta la siguiente (o hasta el final)
            if i < len(positions_sorted) - 1:
                next_cut_y = positions_sorted[i + 1]['y']
            else:
                next_cut_y = img.height

            section = img.crop((0, cut_y, img.width, next_cut_y))
            output_path = os.path.join(self.output_dir, f"page_{page_num+1}_section_{i+2}.png")
            section.save(output_path)
            print(f"    Guardada sección {i+2}: {output_path}")
            saved_files.append(output_path)

        return saved_files

    def process(self):
        """
        Ejecuta todo el proceso de extracción y procesamiento.
        """
        print("="*60)
        print("PROCESAMIENTO DEL PDF")
        print("="*60)

        # Paso 1: Encontrar páginas del apartado 6.1
        section_pages = self.find_section_pages()

        all_saved_files = []

        # Paso 2-5: Procesar cada página
        print("\n" + "="*60)
        print("PROCESANDO PÁGINAS")
        print("="*60)

        for page_num in section_pages:
            print(f"\nProcesando página {page_num + 1}...")
            page = self.doc[page_num]

            # Recortar márgenes (encabezado y pie)
            pix = self.crop_page_margins(page)
            print(f"  Página recortada (sin encabezado/pie)")

            # Buscar líneas azules horizontales
            positions = self.find_blue_lines(pix, debug_page_num=page_num+1)

            # Dividir y guardar secciones
            saved = self.split_and_crop_page(pix, positions, page_num)
            all_saved_files.extend(saved)

        print("\n" + "="*60)
        print("PROCESO COMPLETADO")
        print("="*60)
        print(f"\nArchivos generados: {len(all_saved_files)}")
        print(f"Directorio de salida: {self.output_dir}")

        return all_saved_files

    def close(self):
        """Cierra el documento PDF."""
        self.doc.close()


def main():
    # Configuración
    # Buscar el PDF en data/ o en la raíz
    pdf_path = "data/documento.pdf"
    if not os.path.exists(pdf_path):
        pdf_path = "documento.pdf"

    output_dir = "output/sections"

    # Verificar que existe el PDF
    if not os.path.exists(pdf_path):
        print(f"Error: No se encuentra el archivo '{pdf_path}'")
        print("Por favor, coloca el PDF en la carpeta 'data/' o en la raíz del proyecto")
        return

    # Crear el extractor y procesar
    extractor = PDFSectionExtractor(pdf_path, output_dir)

    try:
        saved_files = extractor.process()

        print("\nArchivos guardados:")
        for file in saved_files:
            print(f"  - {file}")

    except Exception as e:
        print(f"\nError durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()

    finally:
        extractor.close()


if __name__ == "__main__":
    main()
