"""
Script para procesar las secciones de tabla extraídas y convertirlas en DataFrame.
Divide cada fila en columnas y extrae el texto con OCR.
"""

import os
import glob
from PIL import Image
import pytesseract
import pandas as pd
import cv2
import numpy as np


class TableProcessor:
    def __init__(self, sections_dir="output/sections", output_file="output/table_data.csv", generate_visualizations=False):
        self.sections_dir = sections_dir
        self.output_file = output_file
        self.generate_visualizations = generate_visualizations

        # Títulos de las columnas que buscamos en el encabezado
        # (sin saltos de línea, normalizados)
        self.header_titles = {
            'tipus_criterio': 'Tipus criteri',
            'nom_criteri': 'Nom criteri',
            'descripcio': 'Descripció criteri',
            'on_incloure': 'On incloure',
            'doc_a_verificar_adj': 'Doc a verificar per adjudicació',
            'doc_a_verificar_exec': 'Doc a verificar execució',
            'condicionants': 'Condicionant'
        }

        self.column_names = [
            'tipus_criterio',
            'nom_criteri',
            'descripcio',
            'on_incloure',
            'doc_a_verificar_adj',
            'doc_a_verificar_exec',
            'condicionants'
        ]

        # Coordenadas X de las columnas (se detectarán automáticamente)
        self.column_x_positions = None

    def is_image_mostly_blank(self, img_path, threshold=0.95):
        """
        Detecta si una imagen está mayormente en blanco o vacía.
        Retorna True si más del threshold% de la imagen es fondo claro.
        """
        img = cv2.imread(img_path)
        if img is None:
            return False

        # Convertir a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Contar píxeles claros (> 240 es casi blanco)
        total_pixels = gray.shape[0] * gray.shape[1]
        white_pixels = np.sum(gray > 240)
        white_ratio = white_pixels / total_pixels

        return white_ratio > threshold

    def has_meaningful_content(self, img_path):
        """
        Verifica si una imagen tiene contenido significativo mediante OCR.
        Retorna False si solo tiene texto basura o está vacía.
        """
        img = cv2.imread(img_path)
        if img is None:
            return False

        # Extraer texto
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, lang='cat+spa').strip()

        # Si no hay texto, no tiene contenido
        if len(text) < 5:
            return False

        # Detectar patrones de texto basura
        text_lower = text.lower().replace('\n', ' ')
        garbage_patterns = ['na a do ja', 'na do ja', 'anar', 'ona do']

        # Si el texto es muy corto (menos de 50 caracteres), verificar patrones de basura
        if len(text) < 50:
            for pattern in garbage_patterns:
                if pattern in text_lower:
                    return False

            # Si solo tiene palabras muy cortas y sin sentido
            words = text_lower.split()
            if len(words) <= 3 and all(len(w) <= 4 for w in words):
                return False

        return True

    def get_section_files(self):
        """
        Obtiene todos los archivos de secciones ordenados y filtrados.
        Excluye archivos _top y archivos en blanco/con poco contenido.
        """
        pattern = os.path.join(self.sections_dir, "page_*_section_*.png")
        files = glob.glob(pattern)

        # Ordenar por página y sección
        def sort_key(filename):
            basename = os.path.basename(filename)
            parts = basename.replace('.png', '').split('_')
            try:
                page = int(parts[1])
                section = int(parts[3])
                return (page, section)
            except:
                return (0, 0)

        files.sort(key=sort_key)

        # Filtrar archivos no válidos
        valid_files = []
        print("\n--- VALIDACIÓN DE IMÁGENES ---")

        for f in files:
            basename = os.path.basename(f)

            # Filtro 1: Excluir archivos _top
            if '_top' in basename:
                print(f"  ❌ {basename}: Archivo _top (encabezado de página)")
                continue

            # Filtro 2: Excluir imágenes mayormente en blanco
            if self.is_image_mostly_blank(f, threshold=0.97):
                print(f"  ❌ {basename}: Imagen en blanco (>97% fondo claro)")
                continue

            # Filtro 3: Verificar contenido significativo
            if not self.has_meaningful_content(f):
                print(f"  ❌ {basename}: Sin contenido válido (texto basura o vacío)")
                continue

            valid_files.append(f)
            print(f"  ✓ {basename}: Válido")

        print(f"\nImágenes válidas: {len(valid_files)}/{len(files)}")
        return valid_files

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
        Retorna el grupo de bloques y la X mínima.
        """
        # Paso 1: Encontrar bloques que hacen match exacto con cada palabra del título
        matches_by_word = {}

        for word in title_words:
            matches_by_word[word] = []
            for idx, block in enumerate(all_blocks):
                if idx in used_block_indices:
                    continue
                if self.find_exact_word_match(word, block['word']):
                    matches_by_word[word].append((idx, block))

        # Verificar que todas las palabras tienen al menos un match
        for word in title_words:
            if not matches_by_word[word]:
                return None  # Falta al menos una palabra

        # Paso 2: Probar todas las combinaciones posibles
        from itertools import product

        all_combinations = list(product(*[matches_by_word[w] for w in title_words]))

        best_combination = None
        best_score = float('inf')

        for combination in all_combinations:
            indices = [idx for idx, block in combination]
            blocks = [block for idx, block in combination]

            # Verificar si los bloques forman un grupo cohesivo
            # Calcular dispersión espacial
            x_coords = [b['x'] for b in blocks]
            y_coords = [b['y'] for b in blocks]

            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)

            # Calcular score (menor es mejor)
            # Preferir grupos compactos
            x_spread = x_max - x_min
            y_spread = y_max - y_min

            # Detectar si es vertical (mismo X, diferentes Y)
            is_vertical = all(abs(b['x'] - blocks[0]['x']) < 20 for b in blocks)

            # Detectar si es horizontal (mismo Y, diferentes X)
            is_horizontal = all(abs(b['y'] - blocks[0]['y']) < 10 for b in blocks)

            # Score: priorizar grupos alineados y compactos
            if is_vertical:
                score = y_spread + x_min * 0.01  # Preferir más a la izquierda
            elif is_horizontal:
                score = x_spread + x_min * 0.01  # Preferir más a la izquierda
            else:
                # Grupo disperso, penalizar
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

    def detect_header_columns(self, header_img, debug=False, from_top_file=False):
        """
        Detecta las posiciones X de los títulos de columnas usando matching exacto.
        Retorna un diccionario con las coordenadas X de inicio de cada columna.

        Args:
            header_img: Imagen del encabezado
            debug: Si True, genera imágenes de debug
            from_top_file: Si True, busca en toda la imagen (no solo primeros 60px)
        """
        print("\n--- DETECCIÓN AUTOMÁTICA DE COLUMNAS ---")

        # Convertir a escala de grises
        if len(header_img.shape) == 3:
            gray = cv2.cvtColor(header_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = header_img

        height, width = gray.shape[:2]

        # Usar OCR para obtener texto y bounding boxes
        ocr_data = pytesseract.image_to_data(
            gray,
            lang='cat+spa',
            output_type=pytesseract.Output.DICT
        )

        # Si viene de archivo _top, buscar en toda la imagen; si no, solo en primeros 60px
        if from_top_file:
            HEADER_Y_MAX = height  # Toda la imagen
            print(f"  ℹ️  Buscando en toda la imagen (archivo _top)")
        else:
            HEADER_Y_MAX = 60  # Solo primeros 60px

        # Crear lista de bloques en la zona del encabezado
        all_blocks = []
        for i in range(len(ocr_data['text'])):
            word = ocr_data['text'][i].strip()
            if word:
                conf = int(ocr_data['conf'][i])
                y = ocr_data['top'][i]

                # FILTRO: Solo bloques en la zona de encabezado
                if conf > 20 and y <= HEADER_Y_MAX:
                    all_blocks.append({
                        'word': word,
                        'x': ocr_data['left'][i],
                        'y': y,
                        'w': ocr_data['width'][i],
                        'h': ocr_data['height'][i],
                        'conf': conf
                    })

        print(f"Bloques en zona de encabezado (Y≤{HEADER_Y_MAX}): {len(all_blocks)}")

        # Crear imagen de debug
        if debug:
            debug_dir = os.path.join(self.sections_dir, "debug_header")
            os.makedirs(debug_dir, exist_ok=True)

            img_all_blocks = header_img.copy()
            for block in all_blocks:
                x, y, w, h = block['x'], block['y'], block['w'], block['h']
                cv2.rectangle(img_all_blocks, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(img_all_blocks, block['word'], (x, y - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
            cv2.imwrite(os.path.join(debug_dir, "all_ocr_blocks.png"), img_all_blocks)
            print(f"✓ Bloques OCR guardados en: {debug_dir}/all_ocr_blocks.png")

        # Buscar cada título usando matching exacto
        column_positions = {}
        used_block_indices = set()

        for col_name, title in self.header_titles.items():
            title_words = title.split()

            # Buscar combinación de bloques que contenga TODAS las palabras
            combination = self.find_title_combination(title_words, all_blocks, used_block_indices)

            if combination:
                margin = 5
                x_pos = combination['x_min']
                column_positions[col_name] = max(0, x_pos - margin)

                # Marcar bloques como usados
                for idx in combination['indices']:
                    used_block_indices.add(idx)

                words_found = ', '.join([b['word'] for b in combination['blocks']])
                group_type = "V" if combination['is_vertical'] else ("H" if combination['is_horizontal'] else "M")
                print(f"  {col_name:25s}: X={x_pos:4d} → {column_positions[col_name]:4d} [{group_type}] ('{words_found}')")
            else:
                print(f"  {col_name:25s}: ⚠️  No detectado")

        # Verificar que se detectaron suficientes columnas
        if len(column_positions) < len(self.column_names) * 0.6:  # Al menos 60%
            print(f"\n⚠️  Solo se detectaron {len(column_positions)}/{len(self.column_names)} columnas")
            return None

        # Añadir la posición final (ancho de la imagen)
        column_positions['_end'] = width

        # Ordenar columnas por posición X para verificar orden
        sorted_positions = sorted(
            [(k, v) for k, v in column_positions.items() if k != '_end'],
            key=lambda x: x[1]
        )

        print(f"\nColumnas detectadas (ordenadas por X):")
        for col_name, x_pos in sorted_positions:
            print(f"  {col_name:25s}: X={x_pos}")

        # Guardar imagen de debug
        if debug:
            img_debug = header_img.copy()
            colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0),
                     (255, 0, 255), (0, 255, 255), (128, 128, 255)]

            for idx, (col_name, x_pos) in enumerate(sorted_positions):
                color = colors[idx % len(colors)]
                cv2.line(img_debug, (x_pos, 0), (x_pos, height), color, 3)
                cv2.putText(img_debug, col_name, (x_pos + 5, 30 + (idx * 30) % (height - 40)),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            cv2.imwrite(os.path.join(debug_dir, "header_detection.png"), img_debug)
            print(f"✓ Detección guardada en: {debug_dir}/header_detection.png")

        return column_positions

    def divide_into_columns(self, img):
        """
        Divide una imagen (fila de tabla) en columnas usando las posiciones detectadas.
        Retorna una lista de imágenes, una por columna.
        """
        if self.column_x_positions is None:
            print("⚠️  Error: No se han detectado las posiciones de columnas")
            return []

        height, width = img.shape[:2]
        columns = []

        for i, col_name in enumerate(self.column_names):
            x_start = self.column_x_positions.get(col_name, 0)

            # Determinar x_end: inicio de la siguiente columna o final de imagen
            if i < len(self.column_names) - 1:
                next_col = self.column_names[i + 1]
                x_end = self.column_x_positions.get(next_col, width)
            else:
                x_end = self.column_x_positions.get('_end', width)

            # Asegurarse de no exceder el ancho de la imagen
            x_start = max(0, min(x_start, width))
            x_end = max(x_start, min(x_end, width))

            # Recortar columna
            col_img = img[:, x_start:x_end]

            columns.append({
                'name': col_name,
                'image': col_img,
                'x_start': x_start,
                'x_end': x_end,
                'width': x_end - x_start
            })

        return columns

    def extract_text_from_column(self, col_img, col_name):
        """
        Extrae texto de una imagen de columna usando OCR.
        """
        # Convertir a escala de grises si es necesario
        if len(col_img.shape) == 3:
            gray = cv2.cvtColor(col_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = col_img

        # Mejorar contraste para mejor OCR
        # Aplicar umbral adaptativo
        processed = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # OCR con configuración para catalán/español
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(
            processed,
            lang='cat+spa',
            config=custom_config
        )

        # Limpiar texto
        text = text.strip()

        # Reemplazar múltiples saltos de línea por uno solo
        import re
        text = re.sub(r'\n\s*\n', '\n', text)

        # Reemplazar saltos de línea simples por espacios
        # Esto hace que el CSV sea más legible en una sola línea por celda
        # Si prefieres mantener los saltos de línea, comenta esta línea
        text = text.replace('\n', ' ')

        # Limpiar espacios múltiples
        text = re.sub(r'\s+', ' ', text)

        # Limpiar texto final
        text = text.strip()

        return text

    def _create_column_visualization(self, img, columns, section_path):
        """
        Crea una imagen de visualización con rectángulos de colores sobre las columnas detectadas.
        """
        # Crear directorio de visualizaciones
        viz_dir = os.path.join(self.sections_dir, "visualizations")
        os.makedirs(viz_dir, exist_ok=True)

        basename = os.path.basename(section_path).replace('.png', '')

        # Crear imagen con overlay semi-transparente
        img_overlay = img.copy()
        overlay = img.copy()

        # Colores para cada columna (BGR)
        colors = [
            (0, 255, 0),      # Verde
            (255, 0, 0),      # Azul
            (0, 0, 255),      # Rojo
            (255, 255, 0),    # Cyan
            (255, 0, 255),    # Magenta
            (0, 255, 255),    # Amarillo
            (128, 128, 255)   # Rosa
        ]

        height = img.shape[0]

        for idx, col_info in enumerate(columns):
            color = colors[idx % len(colors)]
            x_start = col_info['x_start']
            x_end = col_info['x_end']

            # Dibujar rectángulo semi-transparente
            cv2.rectangle(overlay, (x_start, 0), (x_end, height), color, -1)

            # Dibujar línea vertical en el borde izquierdo
            cv2.line(img_overlay, (x_start, 0), (x_start, height), color, 3)

            # Añadir etiqueta del nombre de columna
            cv2.putText(img_overlay, col_info['name'],
                       (x_start + 10, 30 + (idx * 30) % (height - 40)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Mezclar overlay con transparencia
        alpha = 0.3
        cv2.addWeighted(overlay, alpha, img_overlay, 1 - alpha, 0, img_overlay)

        # Guardar imagen con overlay
        viz_file_overlay = os.path.join(viz_dir, f"{basename}_columns_overlay.png")
        cv2.imwrite(viz_file_overlay, img_overlay)

        # Crear imagen con solo bordes (sin relleno)
        img_borders = img.copy()
        for idx, col_info in enumerate(columns):
            color = colors[idx % len(colors)]
            x_start = col_info['x_start']
            x_end = col_info['x_end']

            # Dibujar rectángulo sin relleno
            cv2.rectangle(img_borders, (x_start, 0), (x_end, height), color, 2)

            # Añadir etiqueta
            cv2.putText(img_borders, col_info['name'],
                       (x_start + 10, 30 + (idx * 30) % (height - 40)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Guardar imagen con solo bordes
        viz_file_borders = os.path.join(viz_dir, f"{basename}_columns_borders.png")
        cv2.imwrite(viz_file_borders, img_borders)

    def is_header_row(self, row_data):
        """
        Detecta si una fila es un encabezado repetido (no datos reales).
        Retorna True si la fila contiene títulos de columnas.
        """
        # Normalizar todos los textos de la fila
        all_text = ' '.join([str(v).lower() for v in row_data.values()]).replace('\n', ' ')

        # Normalizar caracteres
        all_text = all_text.replace('ó', 'o').replace('à', 'a').replace('í', 'i')

        # Contar cuántos títulos de columna aparecen en los datos
        header_keywords = [
            'tipus criteri',
            'nom criteri',
            'descripcio criteri',
            'on incloure',
            'doc a verificar per adjudicacio',
            'doc a verificar execucio',
            'condicionant'
        ]

        matches = 0
        for keyword in header_keywords:
            keyword_norm = keyword.replace('ó', 'o').replace('à', 'a').replace('í', 'i')
            if keyword_norm in all_text:
                matches += 1

        # Si encuentra 4 o más títulos, es probablemente un encabezado repetido
        if matches >= 4:
            return True

        return False

    def detect_and_crop_header(self, img):
        """
        Detecta si hay un encabezado de tabla en la parte superior de la imagen.
        Si lo encuentra, retorna la imagen recortada sin el encabezado.
        Retorna: (imagen_recortada, tiene_encabezado)
        """
        height, width = img.shape[:2]

        # Solo revisar los primeros 100 píxeles (zona donde aparecen los encabezados)
        MAX_HEADER_ZONE = min(100, height)

        if height < 50:
            return img, False

        # Extraer zona del encabezado
        header_zone = img[:MAX_HEADER_ZONE, :]

        # Convertir a escala de grises
        if len(header_zone.shape) == 3:
            gray = cv2.cvtColor(header_zone, cv2.COLOR_BGR2GRAY)
        else:
            gray = header_zone

        # Extraer texto de la zona del encabezado
        text = pytesseract.image_to_string(gray, lang='cat+spa').lower()
        text = text.replace('\n', ' ').replace('ó', 'o').replace('à', 'a').replace('í', 'i')

        # Verificar si contiene títulos de columnas
        header_keywords = ['tipus criteri', 'nom criteri', 'descripcio criteri']
        matches = sum(1 for keyword in header_keywords if keyword in text)

        if matches >= 2:
            # Tiene encabezado, buscar la línea horizontal negra que lo separa
            # Buscar en los primeros 100px una línea horizontal gruesa
            search_zone = img[:MAX_HEADER_ZONE, :]
            if len(search_zone.shape) == 3:
                search_gray = cv2.cvtColor(search_zone, cv2.COLOR_BGR2GRAY)
            else:
                search_gray = search_zone

            # Aplicar umbral para detectar líneas oscuras
            _, binary = cv2.threshold(search_gray, 100, 255, cv2.THRESH_BINARY_INV)

            # Proyección vertical para encontrar líneas horizontales
            vertical_projection = np.sum(binary, axis=1)
            max_projection = np.max(vertical_projection)

            # Buscar la línea más prominente (que cubre al menos 70% del ancho)
            min_line_width = width * 0.7

            crop_y = MAX_HEADER_ZONE  # Por defecto, recortar en MAX_HEADER_ZONE

            # Buscar desde arriba hacia abajo la primera línea prominente
            for i in range(30, MAX_HEADER_ZONE):  # Empezar desde píxel 30 (después del texto)
                if vertical_projection[i] >= min_line_width:
                    # Encontrada línea horizontal, recortar justo debajo
                    crop_y = i + 12  # +12 para dejar margen suficiente y evitar texto del encabezado
                    break

            cropped_img = img[crop_y:, :]
            print(f"  📋 Encabezado detectado, recortando en Y={crop_y}px")
            return cropped_img, True

        return img, False

    def process_section(self, section_path, debug=False):
        """
        Procesa una sección (fila de tabla) y extrae los datos de todas las columnas.
        Retorna un diccionario con los datos de la fila.
        """
        # Leer imagen
        img = cv2.imread(section_path)

        if img is None:
            print(f"  Error: No se pudo leer {section_path}")
            return None

        # Detectar y recortar encabezado si existe
        img, had_header = self.detect_and_crop_header(img)

        # Si después de recortar la imagen es muy pequeña, omitir
        if img.shape[0] < 20:
            print(f"  ⚠️  Imagen muy pequeña después de recortar encabezado, se omitirá")
            return None

        # Dividir en columnas
        columns = self.divide_into_columns(img)

        # Generar visualización si está habilitado
        if self.generate_visualizations:
            self._create_column_visualization(img, columns, section_path)

        # Extraer datos de cada columna
        row_data = {}

        for col_info in columns:
            col_name = col_info['name']
            col_img = col_info['image']

            # Extraer texto
            text = self.extract_text_from_column(col_img, col_name)
            row_data[col_name] = text

            # Debug: guardar imágenes de columnas
            if debug:
                debug_dir = os.path.join(self.sections_dir, "debug_columns")
                os.makedirs(debug_dir, exist_ok=True)

                basename = os.path.basename(section_path).replace('.png', '')
                col_filename = f"{basename}_{col_name}.png"
                cv2.imwrite(os.path.join(debug_dir, col_filename), col_img)

        # Verificar si es un encabezado repetido (solo si no tenía encabezado que recortamos)
        if not had_header and self.is_header_row(row_data):
            print(f"  ⚠️  Fila detectada como encabezado repetido, se omitirá")
            return None

        return row_data

    def merge_continuation_rows(self, df):
        """
        Fusiona filas de continuación con la fila anterior.
        Las filas sin tipus_criterio y nom_criteri son continuaciones
        y su contenido debe agregarse a la fila anterior.
        """
        print("\n--- FUSIONANDO FILAS DE CONTINUACIÓN ---")

        if df.empty:
            return df

        # Lista para almacenar índices de filas a eliminar
        rows_to_remove = []

        # Iterar desde la segunda fila
        for idx in range(1, len(df)):
            current_row = df.iloc[idx]

            # Verificar si es una fila de continuación
            # (tipus_criterio y nom_criteri vacíos o NaN)
            tipus_empty = pd.isna(current_row['tipus_criterio']) or str(current_row['tipus_criterio']).strip() == ''
            nom_empty = pd.isna(current_row['nom_criteri']) or str(current_row['nom_criteri']).strip() == ''

            if tipus_empty and nom_empty:
                # Es una fila de continuación, fusionar con la fila anterior
                prev_idx = idx - 1

                # Buscar la última fila principal (en caso de múltiples continuaciones)
                while prev_idx in rows_to_remove and prev_idx > 0:
                    prev_idx -= 1

                print(f"  📎 Fusionando fila {idx} (source: {current_row['_source_file']}) con fila {prev_idx}")

                # Concatenar contenido de cada columna (excepto tipus_criterio y nom_criteri)
                for col in self.column_names[2:]:  # Saltar tipus_criterio y nom_criteri
                    prev_value = df.at[prev_idx, col]
                    curr_value = current_row[col]

                    # Si ambos tienen contenido, concatenar con espacio
                    if pd.notna(prev_value) and str(prev_value).strip() and \
                       pd.notna(curr_value) and str(curr_value).strip():
                        df.at[prev_idx, col] = str(prev_value) + ' ' + str(curr_value)
                    # Si solo el actual tiene contenido, usar ese
                    elif pd.notna(curr_value) and str(curr_value).strip():
                        df.at[prev_idx, col] = curr_value

                # Marcar esta fila para eliminar
                rows_to_remove.append(idx)

        # Eliminar filas de continuación
        if rows_to_remove:
            print(f"\n  ✓ Eliminando {len(rows_to_remove)} filas de continuación fusionadas")
            df = df.drop(rows_to_remove).reset_index(drop=True)
        else:
            print("  ℹ️  No se encontraron filas de continuación")

        return df

    def extract_bottom_region(self, img, bottom_pixels=200):
        """
        Extrae la región inferior de una imagen.
        Útil para buscar encabezados en archivos _top.
        """
        height = img.shape[0]
        if height <= bottom_pixels:
            return img

        # Extraer los últimos N píxeles
        return img[height - bottom_pixels:, :]

    def find_header_in_top_files(self):
        """
        Busca el encabezado en archivos _top (parte inferior de las imágenes).
        Se usa cuando no se encuentra en las secciones normales.
        """
        print("\n--- BUSCANDO ENCABEZADO EN ARCHIVOS _TOP ---")

        pattern = os.path.join(self.sections_dir, "page_*_top.png")
        top_files = glob.glob(pattern)

        if not top_files:
            print("  ⚠️  No se encontraron archivos _top")
            return None

        # Ordenar archivos
        top_files.sort()

        best_match = None
        best_score = 0
        best_region = None

        for top_file in top_files[:3]:  # Revisar los primeros 3 archivos _top
            img = cv2.imread(top_file)
            if img is None:
                continue

            # Buscar en diferentes regiones de la parte inferior
            # Probar 150px, 200px, 250px desde abajo
            for bottom_height in [150, 200, 250]:
                bottom_region = self.extract_bottom_region(img, bottom_height)

                # Extraer texto con OCR
                gray = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2GRAY)
                text = pytesseract.image_to_string(gray, lang='cat+spa').lower()

                # Normalizar texto
                text = text.replace('ó', 'o').replace('à', 'a').replace('\n', ' ')

                # Contar cuántos títulos de columna aparecen
                score = 0
                for col_name, title in self.header_titles.items():
                    title_normalized = title.lower().replace('ó', 'o').replace('à', 'a')
                    if title_normalized in text:
                        score += 1

                if score > best_score:
                    best_score = score
                    best_match = top_file
                    best_region = bottom_region

            basename = os.path.basename(top_file)
            print(f"  {basename}: {best_score}/{len(self.header_titles)} títulos encontrados")

        if best_match and best_score >= len(self.header_titles) * 0.6:  # Al menos 60% de títulos
            print(f"\n✓ Encabezado detectado en: {os.path.basename(best_match)} (región inferior)")

            # Guardar la región del encabezado como archivo temporal
            header_temp_path = os.path.join(self.sections_dir, "_header_from_top.png")
            cv2.imwrite(header_temp_path, best_region)

            return header_temp_path
        else:
            print(f"\n⚠️  No se encontró encabezado en archivos _top")
            return None

    def find_header_section(self, section_files):
        """
        Encuentra la sección que contiene los encabezados de la tabla.
        Busca la que contenga más títulos de columnas.
        Si no encuentra en secciones normales, busca en archivos _top.
        """
        print("\n--- BUSCANDO ENCABEZADO DE TABLA ---")

        best_match = None
        best_score = 0

        for section_file in section_files[:5]:  # Solo revisar las primeras 5 secciones
            img = cv2.imread(section_file)
            if img is None:
                continue

            # Extraer texto con OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray, lang='cat+spa').lower()

            # Normalizar texto
            text = text.replace('ó', 'o').replace('à', 'a').replace('\n', ' ')

            # Contar cuántos títulos de columna aparecen
            score = 0
            for col_name, title in self.header_titles.items():
                title_normalized = title.lower().replace('ó', 'o').replace('à', 'a')
                if title_normalized in text:
                    score += 1

            print(f"  {os.path.basename(section_file)}: {score}/{len(self.header_titles)} títulos encontrados")

            if score > best_score:
                best_score = score
                best_match = section_file

        if best_match and best_score >= len(self.header_titles) * 0.6:  # Al menos 60% de títulos
            print(f"\n✓ Encabezado detectado: {os.path.basename(best_match)}")
            return best_match
        else:
            print(f"\n⚠️  No se pudo detectar el encabezado en secciones normales")

            # Intentar buscar en archivos _top
            header_from_top = self.find_header_in_top_files()
            if header_from_top:
                return header_from_top

            return None

    def process_all_sections(self, debug=False):
        """
        Procesa todas las secciones y crea un DataFrame.
        """
        print("="*60)
        print("PROCESAMIENTO DE TABLA")
        print("="*60)

        section_files = self.get_section_files()
        print(f"\nSecciones encontradas: {len(section_files)}")

        if len(section_files) == 0:
            print("No se encontraron secciones para procesar.")
            return None

        # Paso 1: Encontrar y procesar el encabezado
        header_file = self.find_header_section(section_files)

        if header_file:
            header_img = cv2.imread(header_file)

            # Verificar si el encabezado viene de un archivo _top
            from_top_file = '_header_from_top' in header_file

            self.column_x_positions = self.detect_header_columns(
                header_img,
                debug=debug,
                from_top_file=from_top_file
            )

            if self.column_x_positions:
                print(f"\n✓ Posiciones de columnas detectadas:")
                for col_name in self.column_names:
                    x_pos = self.column_x_positions.get(col_name, '?')
                    print(f"  {col_name:25s}: X={x_pos}")
            else:
                print("\n⚠️  No se pudieron detectar las columnas automáticamente")
                return None
        else:
            print("\n⚠️  No se encontró el encabezado")
            return None

        # Paso 2: Procesar todas las secciones (incluyendo el encabezado si tiene datos debajo)
        all_rows = []

        for i, section_file in enumerate(section_files):
            basename = os.path.basename(section_file)

            # Saltar secciones "_top" (pero NO saltar el encabezado, porque puede tener datos debajo)
            if "_top" in basename:
                print(f"\n[{i+1}/{len(section_files)}] Saltando: {basename} (archivo top)")
                continue

            print(f"\nProcesando [{i+1}/{len(section_files)}]: {basename}")

            # Si es el encabezado, indicarlo pero procesarlo igual (tiene datos debajo del encabezado)
            if section_file == header_file:
                print(f"  ℹ️  Esta imagen contiene el encabezado + datos debajo")

            row_data = self.process_section(section_file, debug=debug)

            if row_data:
                # Añadir metadatos
                row_data['_source_file'] = basename

                all_rows.append(row_data)

                # Mostrar preview de datos extraídos
                print(f"  Datos extraídos:")
                for col_name in self.column_names:
                    text = row_data.get(col_name, '')
                    preview = text[:50].replace('\n', ' ') if text else '(vacío)'
                    print(f"    {col_name}: {preview}")

        # Crear DataFrame
        df = pd.DataFrame(all_rows)

        # Reordenar columnas
        column_order = self.column_names + ['_source_file']
        df = df[column_order]

        # Fusionar filas de continuación
        df = self.merge_continuation_rows(df)

        print("\n" + "="*60)
        print("RESULTADO")
        print("="*60)
        print(f"\nFilas procesadas: {len(df)}")
        print(f"Columnas: {len(df.columns)}")

        # Guardar a CSV con formato correcto
        # quoting=csv.QUOTE_ALL asegura que todos los campos estén entre comillas
        # esto evita problemas con saltos de línea y caracteres especiales
        df.to_csv(
            self.output_file,
            index=False,
            encoding='utf-8-sig',
            quoting=1,  # QUOTE_ALL
            escapechar='\\',
            doublequote=True
        )
        print(f"\n✓ Datos guardados en: {self.output_file}")

        # Guardar también en Excel para mejor visualización
        excel_file = self.output_file.replace('.csv', '.xlsx')
        df.to_excel(excel_file, index=False, engine='openpyxl')
        print(f"✓ Datos guardados en: {excel_file}")

        return df


def main():
    processor = TableProcessor(
        sections_dir="output/sections",
        output_file="output/table_data.csv",
        generate_visualizations=True  # Cambiar a False para desactivar visualizaciones
    )

    # Procesar con debug=True para guardar imágenes de columnas individuales
    df = processor.process_all_sections(debug=True)

    if df is not None:
        print("\n" + "="*60)
        print("PREVIEW DE DATOS")
        print("="*60)
        print(df.head())


if __name__ == "__main__":
    main()
