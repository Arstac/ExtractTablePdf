"""
Test de detección en un solo archivo específico.
"""

import sys
sys.path.insert(0, '.')

from process_table import TableProcessor
import cv2
import os

def test_single_file():
    # Permitir especificar archivo por argumento
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "output_sections/page_7_section_2.png"

    # Si solo se dio el nombre sin path, buscar en output_sections
    if not os.path.exists(file_path) and not file_path.startswith("output_sections/"):
        file_path = os.path.join("output_sections", file_path)

    print("="*80)
    print(f"PROBANDO: {file_path}")
    print("="*80)

    processor = TableProcessor()
    img = cv2.imread(file_path)

    if img is None:
        print(f"Error: no se puede leer {file_path}")
        return

    result = processor.detect_header_columns(img, debug=True)

    if result:
        # Generar imagen con rectángulos de columnas
        height, width = img.shape[:2]

        # Crear overlay con rectángulos
        overlay = img.copy()
        img_with_borders = img.copy()

        colors = [
            (255, 100, 100),  # Azul claro
            (100, 255, 100),  # Verde claro
            (100, 100, 255),  # Rojo claro
            (255, 255, 100),  # Cyan claro
            (255, 100, 255),  # Magenta claro
            (100, 255, 255),  # Amarillo claro
            (200, 150, 255)   # Rosa claro
        ]

        sorted_cols = sorted(
            [(col, x) for col, x in result.items() if col != '_end'],
            key=lambda item: item[1]
        )

        for idx, (col_name, x_start) in enumerate(sorted_cols):
            # Determinar x_end
            if idx < len(sorted_cols) - 1:
                x_end = sorted_cols[idx + 1][1]
            else:
                x_end = result.get('_end', width)

            col_width = x_end - x_start
            color = colors[idx % len(colors)]

            # Dibujar rectángulo relleno
            cv2.rectangle(overlay, (x_start, 0), (x_end, height), color, -1)

            # Dibujar borde
            cv2.rectangle(img_with_borders, (x_start, 0), (x_end, height), color, 3)

            # Línea separadora
            if idx > 0:
                cv2.line(img_with_borders, (x_start, 0), (x_start, height), (0, 0, 0), 2)

            # Texto con nombre de columna
            text_y = 30 + (idx * 40) % (height - 60)
            cv2.putText(img_with_borders, col_name, (x_start + 5, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
            cv2.putText(img_with_borders, col_name, (x_start + 5, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Mezclar overlay con imagen
        alpha = 0.3
        img_blended = cv2.addWeighted(overlay, alpha, img_with_borders, 1 - alpha, 0)

        # Guardar imágenes
        cv2.imwrite("test_single_page_result.png", img_blended)
        cv2.imwrite("test_single_page_result_borders.png", img_with_borders)

        print(f"\n✓ Imágenes guardadas:")
        print(f"  - test_single_page_result.png (con overlay)")
        print(f"  - test_single_page_result_borders.png (solo bordes)")

    if result:
        print('\n' + "="*80)
        print('COLUMNAS DETECTADAS (ordenadas por X)')
        print("="*80)

        sorted_cols = sorted(
            [(col, x) for col, x in result.items() if col != '_end'],
            key=lambda item: item[1]
        )

        for col, x in sorted_cols:
            print(f'{col:30s}: X={x:4d}')

        # Verificar con valores esperados
        expected = {
            'tipus_criterio': 119,
            'nom_criteri': 218,
            'descripcio': 368,
            'on_incloure': 702,
            'doc_a_verificar_adj': 780,
            'doc_a_verificar_exec': 1021,
            'condicionants': 1229
        }

        print('\n' + "="*80)
        print('VERIFICACIÓN')
        print("="*80)

        for col, expected_x in expected.items():
            if col in result:
                detected_x = result[col]
                diff = abs(detected_x - expected_x)
                status = "✓" if diff <= 10 else "✗"
                print(f'{status} {col:30s}: Esperado={expected_x:4d}, Detectado={detected_x:4d}, Diff={diff:3d}')
            else:
                print(f'✗ {col:30s}: NO DETECTADO (esperado X={expected_x})')
    else:
        print("No se detectaron columnas")


if __name__ == "__main__":
    test_single_file()
