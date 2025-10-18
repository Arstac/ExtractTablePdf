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
    def __init__(self, sections_dir="output_sections", output_file="table_data.csv"):
        self.sections_dir = sections_dir
        self.output_file = output_file

        # Definir anchos relativos de las columnas
        # Basado en condicionants = 1 unidad
        self.column_widths = {
            'tipus_criterio': .7,
            'nom_criteri': .85,
            'descripcio': 2.55,
            'on_incloure': 0.25,
            'doc_a_verificar_adj': 1,
            'doc_a_verificar_exec': 0.95,
            'condicionants': 1.05
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

        # Total de unidades
        self.total_units = sum(self.column_widths.values())

    def get_section_files(self):
        """
        Obtiene todos los archivos de secciones ordenados.
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
        return files

    def divide_into_columns(self, img):
        """
        Divide una imagen (fila de tabla) en 7 columnas según los anchos definidos.
        Retorna una lista de imágenes, una por columna.
        """
        height, width = img.shape[:2]

        # Calcular ancho de una unidad
        unit_width = width / self.total_units

        columns = []
        x_start = 0

        for col_name in self.column_names:
            col_width_units = self.column_widths[col_name]
            col_width_px = int(unit_width * col_width_units)

            x_end = int(x_start + col_width_px)

            # Asegurarse de no exceder el ancho de la imagen
            if x_end > width:
                x_end = width

            # Recortar columna
            col_img = img[:, int(x_start):x_end]
            columns.append({
                'name': col_name,
                'image': col_img,
                'x_start': int(x_start),
                'x_end': x_end,
                'width': x_end - int(x_start)
            })

            x_start = x_end

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

        # Dividir en columnas
        columns = self.divide_into_columns(img)

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

        return row_data

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

        all_rows = []

        for i, section_file in enumerate(section_files):
            basename = os.path.basename(section_file)
            print(f"\nProcesando [{i+1}/{len(section_files)}]: {basename}")

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
        sections_dir="output_sections",
        output_file="table_data.csv"
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
