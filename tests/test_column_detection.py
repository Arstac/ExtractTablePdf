"""
Script de prueba para visualizar la detección automática de columnas.
Genera imágenes con rectángulos mostrando dónde se detectaron las columnas.
"""

import os
import glob
import cv2
import numpy as np
import pytesseract


class ColumnDetectionTester:
    def __init__(self, sections_dir="output_sections"):
        self.sections_dir = sections_dir

        # Títulos de las columnas que buscamos
        self.header_titles = {
            'tipus_criterio': 'Tipus criteri',
            'nom_criteri': 'Nom criteri',
            'descripcio': 'Descripció criteri',
            'on_incloure': 'On incloure',
            'doc_a_verificar_adj': 'Doc a verificar per adjudicació',
            'doc_a_verificar_exec': 'Doc a verificar execució',
            'condicionants': 'Condicionant'
        }

    def find_exact_word_match(self, word, block_word):
        """Verifica si una palabra hace match exacto (no subcadena)."""
        word_norm = word.lower().replace('ó', 'o').replace('à', 'a').replace('í', 'i').strip()
        block_norm = block_word.lower().replace('ó', 'o').replace('à', 'a').replace('í', 'i').strip()

        # Match exacto
        if word_norm == block_norm:
            return True

        # Permitir variantes singular/plural
        if word_norm.endswith('s') and word_norm[:-1] == block_norm:
            return True
        if block_norm.endswith('s') and block_norm[:-1] == word_norm:
            return True

        return False

    def find_title_combination(self, title_words, all_blocks, used_block_indices):
        """
        Encuentra una combinación de bloques que contenga TODAS las palabras del título.
        """
        from itertools import product

        # Paso 1: Encontrar bloques que hacen match exacto con cada palabra
        matches_by_word = {}

        for word in title_words:
            matches_by_word[word] = []
            for idx, block in enumerate(all_blocks):
                if idx in used_block_indices:
                    continue
                if self.find_exact_word_match(word, block['word']):
                    matches_by_word[word].append((idx, block))

        # Verificar que todas las palabras tienen match
        for word in title_words:
            if not matches_by_word[word]:
                return None

        # Paso 2: Probar combinaciones
        all_combinations = list(product(*[matches_by_word[w] for w in title_words]))

        best_combination = None
        best_score = float('inf')

        for combination in all_combinations:
            indices = [idx for idx, block in combination]
            blocks = [block for idx, block in combination]

            x_coords = [b['x'] for b in blocks]
            y_coords = [b['y'] for b in blocks]

            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)

            x_spread = x_max - x_min
            y_spread = y_max - y_min

            # Detectar tipo de grupo
            is_vertical = all(abs(b['x'] - blocks[0]['x']) < 20 for b in blocks)
            is_horizontal = all(abs(b['y'] - blocks[0]['y']) < 10 for b in blocks)

            # Calcular score
            if is_vertical:
                score = y_spread + x_min * 0.01
            elif is_horizontal:
                score = x_spread + x_min * 0.01
            else:
                score = (x_spread + y_spread) * 10 + x_min * 0.01

            if score < best_score:
                best_score = score
                best_combination = {
                    'indices': indices,
                    'blocks': blocks,
                    'x_min': x_min,
                    'is_vertical': is_vertical,
                    'is_horizontal': is_horizontal
                }

        return best_combination

    @property
    def column_names(self):
        return list(self.header_titles.keys())

    @property
    def colors(self):
        return [
            (255, 100, 100),  # Azul claro
            (100, 255, 100),  # Verde claro
            (100, 100, 255),  # Rojo claro
            (255, 255, 100),  # Cyan claro
            (255, 100, 255),  # Magenta claro
            (100, 255, 255),  # Amarillo claro
            (200, 150, 255)   # Rosa claro
        ]

    def find_header_section(self):
        """Encuentra la sección que contiene los encabezados."""
        pattern = os.path.join(self.sections_dir, "page_*_section_*.png")
        files = glob.glob(pattern)
        files.sort()

        print("=" * 60)
        print("BUSCANDO ENCABEZADO DE TABLA")
        print("=" * 60)

        best_match = None
        best_score = 0

        for section_file in files[:10]:  # Revisar primeras 10 secciones
            img = cv2.imread(section_file)
            if img is None:
                continue

            # Extraer texto con OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray, lang='cat+spa').lower()

            # Normalizar texto
            text = text.replace('ó', 'o').replace('à', 'a').replace('\n', ' ')

            # Contar cuántos títulos aparecen
            score = 0
            found_titles = []
            for col_name, title in self.header_titles.items():
                title_normalized = title.lower().replace('ó', 'o').replace('à', 'a')
                if title_normalized in text:
                    score += 1
                    found_titles.append(title)

            basename = os.path.basename(section_file)
            print(f"\n{basename}:")
            print(f"  Títulos encontrados: {score}/{len(self.header_titles)}")
            if found_titles:
                print(f"  Títulos: {', '.join(found_titles)}")

            if score > best_score:
                best_score = score
                best_match = section_file

        print("\n" + "=" * 60)
        if best_match:
            print(f"✓ ENCABEZADO DETECTADO: {os.path.basename(best_match)}")
            print(f"  Score: {best_score}/{len(self.header_titles)}")
        else:
            print("⚠️  NO SE DETECTÓ ENCABEZADO")

        return best_match

    def detect_columns_new_logic(self, header_img, output_dir="test_debug"):
        """Detecta las posiciones X de las columnas usando bounding boxes."""
        print("\n" + "=" * 60)
        print("DETECTANDO POSICIONES DE COLUMNAS")
        print("=" * 60)

        # Convertir a escala de grises
        if len(header_img.shape) == 3:
            gray = cv2.cvtColor(header_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = header_img

        height, width = gray.shape[:2]
        print(f"\nDimensiones: {width}x{height}px")

        # Usar OCR para obtener texto y bounding boxes
        ocr_data = pytesseract.image_to_data(
            gray,
            lang='cat+spa',
            output_type=pytesseract.Output.DICT
        )

        # Crear imagen con todos los bloques OCR detectados
        os.makedirs(output_dir, exist_ok=True)
        img_all_blocks = header_img.copy()

        print("\nBloques de texto detectados por OCR:")
        for i in range(len(ocr_data['text'])):
            word = ocr_data['text'][i].strip()
            if word:
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                conf = int(ocr_data['conf'][i])
                if conf > 0:
                    cv2.rectangle(img_all_blocks, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.putText(img_all_blocks, word, (x, y - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
                    print(f"  '{word}' @ X={x}, Y={y}, W={w}, H={h}, Conf={conf}")

        cv2.imwrite(os.path.join(output_dir, "all_ocr_blocks.png"), img_all_blocks)
        print(f"\n✓ Bloques OCR guardados en: {output_dir}/all_ocr_blocks.png")

        # Función para normalizar texto
        def normalize_text(text):
            return text.lower().replace('ó', 'o').replace('à', 'a').replace('í', 'i').strip()

        # Crear lista de todos los bloques
        all_blocks = []
        for i in range(len(ocr_data['text'])):
            word = ocr_data['text'][i].strip()
            if word:
                conf = int(ocr_data['conf'][i])
                if conf > 20:
                    all_blocks.append({
                        'index': i,
                        'word': word,
                        'word_normalized': normalize_text(word),
                        'x': ocr_data['left'][i],
                        'y': ocr_data['top'][i],
                        'w': ocr_data['width'][i],
                        'h': ocr_data['height'][i],
                        'conf': conf
                    })

        # Agrupar bloques VERTICALMENTE (misma X, diferente Y)
        def group_vertical_blocks(blocks, x_tolerance=15, y_max_gap=60):
            """Agrupa bloques alineados verticalmente (misma columna)."""
            if not blocks:
                return []

            blocks_sorted = sorted(blocks, key=lambda b: (b['x'], b['y']))
            groups = []
            current_group = [blocks_sorted[0]]

            for block in blocks_sorted[1:]:
                if (abs(block['x'] - current_group[-1]['x']) <= x_tolerance and
                    block['y'] - current_group[-1]['y'] <= y_max_gap):
                    current_group.append(block)
                else:
                    groups.append(current_group)
                    current_group = [block]

            groups.append(current_group)
            return groups

        # Agrupar bloques HORIZONTALMENTE (misma Y, diferentes X)
        def group_horizontal_blocks(blocks, y_tolerance=5, x_max_gap=100):
            """Agrupa bloques en la misma línea horizontal que están cerca."""
            if not blocks:
                return []

            blocks_sorted = sorted(blocks, key=lambda b: (b['y'], b['x']))
            groups = []
            current_group = [blocks_sorted[0]]

            for block in blocks_sorted[1:]:
                prev_block = current_group[-1]
                x_gap = block['x'] - (prev_block['x'] + prev_block['w'])

                if (abs(block['y'] - current_group[-1]['y']) <= y_tolerance and
                    x_gap <= x_max_gap):
                    current_group.append(block)
                else:
                    groups.append(current_group)
                    current_group = [block]

            groups.append(current_group)
            return groups

        vertical_groups = group_vertical_blocks(all_blocks)
        horizontal_groups = group_horizontal_blocks(all_blocks)

        # Combinar ambos tipos
        all_groups = vertical_groups + horizontal_groups

        print(f"\n{len(vertical_groups)} grupos verticales + {len(horizontal_groups)} grupos horizontales = {len(all_groups)} total")

        # Buscar cada título (excluyendo grupos ya usados)
        column_positions = {}
        used_groups = set()

        print("\n" + "=" * 60)
        print("BUSCANDO TÍTULOS DE COLUMNAS")
        print("=" * 60)

        for col_name, title in self.header_titles.items():
            title_normalized = normalize_text(title)
            title_words = set(title_normalized.split())

            # Variantes del título (singular/plural)
            title_variants = [title_normalized]
            if title_normalized.endswith('s'):
                title_variants.append(title_normalized[:-1])
            else:
                title_variants.append(title_normalized + 's')

            print(f"\n{col_name} ('{title}'):")
            print(f"  Palabras buscadas: {title_words}")
            print(f"  Variantes: {title_variants}")

            best_match = None
            best_score = 0

            # Buscar en TODOS los grupos (verticales + horizontales)
            for idx, group in enumerate(all_groups):
                if idx in used_groups:
                    continue

                group_text = ' '.join([b['word_normalized'] for b in group])
                group_words = set(group_text.split())

                # Probar variantes
                max_variant_score = 0
                for variant in title_variants:
                    variant_words = set(variant.split())
                    matching_words = variant_words & group_words
                    variant_score = len(matching_words)
                    if variant_score > max_variant_score:
                        max_variant_score = variant_score

                score = max_variant_score

                if score > 0:
                    x_pos = min(b['x'] for b in group)
                    group_words_str = ', '.join([b['word'] for b in group])
                    group_type = "V" if idx < len(vertical_groups) else "H"
                    print(f"  Grupo {idx} [{group_type}]: '{group_words_str}' @ X={x_pos} - Score: {score}/{len(title_words)}")

                    # Match perfecto
                    if score == len(title_words):
                        if best_match is None or score > best_score or (score == best_score and x_pos < best_match['x']):
                            best_match = {'group': group, 'group_idx': idx, 'x': x_pos, 'score': score}
                            best_score = score
                    # Match parcial
                    else:
                        min_required = max(1, int(len(title_words) * 0.5))
                        if score >= min_required:
                            if best_match is None or score > best_score or (score == best_score and x_pos < best_match['x']):
                                best_match = {'group': group, 'group_idx': idx, 'x': x_pos, 'score': score}
                                best_score = score

            if best_match:
                margin = 5
                column_positions[col_name] = max(0, best_match['x'] - margin)
                used_groups.add(best_match['group_idx'])

                words_found = ', '.join([b['word'] for b in best_match['group']])
                group_type = "V" if best_match['group_idx'] < len(vertical_groups) else "H"
                print(f"  ✓ DETECTADO: X={best_match['x']} → {column_positions[col_name]} [{group_type}] ('{words_found}', score={best_score}/{len(title_words)})")
            else:
                print(f"  ✗ NO DETECTADO")

        # Añadir posición final
        column_positions['_end'] = width

        return column_positions

    def visualize_columns(self, img, column_positions, output_path):
        """Genera imagen con rectángulos de colores mostrando las columnas."""
        height, width = img.shape[:2]

        # Crear copia para overlay
        overlay = img.copy()
        img_with_borders = img.copy()

        print("\n" + "=" * 60)
        print("DIVISIÓN DE COLUMNAS")
        print("=" * 60)

        for i, col_name in enumerate(self.column_names):
            if col_name not in column_positions:
                continue

            x_start = column_positions[col_name]

            # Determinar x_end
            if i < len(self.column_names) - 1:
                next_col = self.column_names[i + 1]
                x_end = column_positions.get(next_col, width)
            else:
                x_end = column_positions.get('_end', width)

            col_width = x_end - x_start

            print(f"{i+1}. {col_name:25s} | X: {x_start:4d} - {x_end:4d} | Ancho: {col_width:4d}px")

            # Dibujar rectángulo relleno en overlay
            color = self.colors[i % len(self.colors)]
            cv2.rectangle(overlay, (x_start, 0), (x_end, height), color, -1)

            # Dibujar borde
            cv2.rectangle(img_with_borders, (x_start, 0), (x_end, height), color, 3)

            # Línea separadora vertical
            if i > 0:
                cv2.line(img_with_borders, (x_start, 0), (x_start, height), (0, 0, 0), 2)

            # Añadir texto con nombre de columna
            text_y = 30 + (i * 50) % (height - 60)
            cv2.putText(
                img_with_borders,
                col_name,
                (x_start + 5, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                3  # Fondo negro
            )
            cv2.putText(
                img_with_borders,
                col_name,
                (x_start + 5, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2  # Texto en color
            )

        # Mezclar overlay con imagen original (transparencia)
        alpha = 0.3
        img_blended = cv2.addWeighted(overlay, alpha, img_with_borders, 1 - alpha, 0)

        # Guardar imagen con overlay
        cv2.imwrite(output_path, img_blended)
        print(f"\n✓ Imagen con overlay guardada: {output_path}")

        # Guardar versión solo con bordes
        output_borders = output_path.replace('.png', '_borders.png')
        cv2.imwrite(output_borders, img_with_borders)
        print(f"✓ Imagen solo bordes guardada: {output_borders}")

        return img_blended

    def test_on_all_sections(self, column_positions, max_sections=5):
        """Aplica la detección a varias secciones para verificar."""
        pattern = os.path.join(self.sections_dir, "page_*_section_*.png")
        files = glob.glob(pattern)
        files.sort()

        print("\n" + "=" * 60)
        print(f"PROBANDO EN {max_sections} SECCIONES")
        print("=" * 60)

        output_dir = os.path.join(self.sections_dir, "test_columns")
        os.makedirs(output_dir, exist_ok=True)

        count = 0
        for section_file in files:
            basename = os.path.basename(section_file)

            # Saltar secciones "_top"
            if "_top" in basename:
                continue

            img = cv2.imread(section_file)
            if img is None:
                continue

            print(f"\n{count + 1}. {basename}")

            output_path = os.path.join(output_dir, f"test_{basename}")
            self.visualize_columns(img, column_positions, output_path)

            count += 1
            if count >= max_sections:
                break

        print(f"\n✓ {count} imágenes de prueba guardadas en: {output_dir}/")

    def run_test(self):
        """Ejecuta el test completo."""
        print("\n" + "=" * 60)
        print("TEST DE DETECCIÓN DE COLUMNAS")
        print("=" * 60)

        # Paso 1: Encontrar encabezado
        header_file = self.find_header_section()

        if not header_file:
            print("\n❌ No se pudo encontrar el encabezado")
            return

        # Paso 2: Detectar columnas
        header_img = cv2.imread(header_file)
        column_positions = self.detect_columns(header_img)

        if len(column_positions) < 2:
            print("\n❌ No se detectaron suficientes columnas")
            return

        # Paso 3: Visualizar en encabezado
        print("\n" + "=" * 60)
        print("VISUALIZANDO ENCABEZADO")
        print("=" * 60)

        output_header = "test_header_columns.png"
        self.visualize_columns(header_img, column_positions, output_header)

        # Paso 4: Probar en otras secciones
        self.test_on_all_sections(column_positions, max_sections=5)

        print("\n" + "=" * 60)
        print("✓ TEST COMPLETADO")
        print("=" * 60)
        print("\nRevisa los archivos generados:")
        print("  - test_header_columns.png (encabezado con columnas detectadas)")
        print("  - test_header_columns_borders.png (solo bordes)")
        print("  - output_sections/test_columns/ (otras secciones de prueba)")


def main():
    tester = ColumnDetectionTester()
    tester.run_test()


if __name__ == "__main__":
    main()
