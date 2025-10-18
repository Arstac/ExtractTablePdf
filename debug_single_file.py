"""
Script de debug para analizar UN SOLO archivo y entender la estructura.
"""

import cv2
import pytesseract
import os

def analyze_single_file(file_path):
    """Analiza en detalle un archivo específico."""

    print("="*80)
    print(f"ANÁLISIS DE: {os.path.basename(file_path)}")
    print("="*80)

    # Leer imagen
    img = cv2.imread(file_path)
    if img is None:
        print(f"Error: no se puede leer {file_path}")
        return

    height, width = img.shape[:2]
    print(f"\nDimensiones: {width}x{height}px")

    # Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # OCR con bounding boxes
    ocr_data = pytesseract.image_to_data(
        gray,
        lang='cat+spa',
        output_type=pytesseract.Output.DICT
    )

    # Extraer todos los bloques con confianza > 20
    blocks = []
    for i in range(len(ocr_data['text'])):
        word = ocr_data['text'][i].strip()
        if word:
            conf = int(ocr_data['conf'][i])
            if conf > 20:
                blocks.append({
                    'word': word,
                    'x': ocr_data['left'][i],
                    'y': ocr_data['top'][i],
                    'w': ocr_data['width'][i],
                    'h': ocr_data['height'][i],
                    'conf': conf
                })

    print(f"\nTotal bloques detectados: {len(blocks)}")
    print("\nBLOQUES ORDENADOS POR POSICIÓN:")
    print("-"*80)

    # Ordenar por Y primero, luego por X (orden de lectura)
    blocks_sorted = sorted(blocks, key=lambda b: (b['y'], b['x']))

    current_y = -1
    line_num = 0

    for block in blocks_sorted:
        # Nueva línea si Y cambia significativamente
        if current_y == -1 or abs(block['y'] - current_y) > 10:
            line_num += 1
            current_y = block['y']
            print(f"\n--- Línea {line_num} (Y≈{block['y']}) ---")

        print(f"  '{block['word']:20s}' @ X={block['x']:4d}, Y={block['y']:3d}, W={block['w']:3d}, Conf={block['conf']:2d}")

    # Títulos esperados
    titles = {
        'tipus_criterio': ['Tipus', 'criteri'],
        'nom_criteri': ['Nom', 'criteri'],
        'descripcio': ['Descripció', 'criteri'],
        'on_incloure': ['On', 'incloure'],
        'doc_a_verificar_adj': ['Doc', 'a', 'verificar', 'per', 'adjudicació'],
        'doc_a_verificar_exec': ['Doc', 'a', 'verificar', 'execució'],
        'condicionants': ['Condicionant']
    }

    print("\n" + "="*80)
    print("ANÁLISIS DE TÍTULOS")
    print("="*80)

    for col_name, title_words in titles.items():
        print(f"\n{col_name}: {' '.join(title_words)}")
        print("  Buscando palabras:")

        found_blocks = []
        for word in title_words:
            word_lower = word.lower()
            for block in blocks:
                block_lower = block['word'].lower()
                if word_lower in block_lower or block_lower in word_lower:
                    found_blocks.append(block)
                    print(f"    '{word}' → '{block['word']}' @ X={block['x']}, Y={block['y']}")

        if found_blocks:
            # Agrupar por línea (mismo Y)
            lines = {}
            for block in found_blocks:
                y_key = round(block['y'] / 10) * 10  # Agrupar por decenas
                if y_key not in lines:
                    lines[y_key] = []
                lines[y_key].append(block)

            print(f"  → Encontrados en {len(lines)} línea(s):")
            for y_key, line_blocks in sorted(lines.items()):
                x_min = min(b['x'] for b in line_blocks)
                x_max = max(b['x'] + b['w'] for b in line_blocks)
                words = ', '.join([b['word'] for b in line_blocks])
                print(f"     Y≈{y_key}: X={x_min}-{x_max} ('{words}')")

            # Determinar X de inicio
            x_start = min(b['x'] for b in found_blocks)
            print(f"  ✓ X de inicio sugerida: {x_start}")
        else:
            print(f"  ✗ No se encontraron palabras del título")

    # Crear imagen visual con todos los bloques marcados
    img_debug = img.copy()

    # Dibujar todos los bloques
    for block in blocks:
        x, y, w, h = block['x'], block['y'], block['w'], block['h']
        cv2.rectangle(img_debug, (x, y), (x+w, y+h), (255, 0, 0), 2)
        cv2.putText(img_debug, block['word'], (x, y-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

    output_path = "debug_single_analysis.png"
    cv2.imwrite(output_path, img_debug)
    print(f"\n✓ Imagen de debug guardada: {output_path}")


if __name__ == "__main__":
    file_path = "output_sections/page_7_section_2.png"

    if not os.path.exists(file_path):
        print(f"Error: No existe {file_path}")
        print("Archivos disponibles:")
        for f in sorted(os.listdir("output_sections")):
            if f.endswith(".png"):
                print(f"  - {f}")
    else:
        analyze_single_file(file_path)
