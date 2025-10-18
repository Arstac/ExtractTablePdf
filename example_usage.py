"""
Ejemplo de uso de process_table.py con visualizaciones.

Este script muestra cómo usar el TableProcessor con diferentes configuraciones.
"""

from process_table import TableProcessor


def example_with_visualizations():
    """
    Procesar tabla CON visualizaciones de columnas.
    Genera 2 imágenes por cada fila:
      - *_columns_overlay.png: Con rectángulos de colores semi-transparentes
      - *_columns_borders.png: Con solo los bordes de las columnas
    """
    print("="*60)
    print("EJEMPLO: Procesamiento CON visualizaciones")
    print("="*60)

    processor = TableProcessor(
        sections_dir="output_sections",
        output_file="table_data.csv",
        generate_visualizations=True  # ← ACTIVAR visualizaciones
    )

    df = processor.process_all_sections(debug=False)

    if df is not None:
        print(f"\n✓ Visualizaciones generadas en: output_sections/visualizations/")
        print(f"✓ Total de archivos: {len(df) * 2} imágenes")
        print(f"  - {len(df)} imágenes con overlay (*_columns_overlay.png)")
        print(f"  - {len(df)} imágenes con bordes (*_columns_borders.png)")

    return df


def example_without_visualizations():
    """
    Procesar tabla SIN visualizaciones (más rápido).
    """
    print("="*60)
    print("EJEMPLO: Procesamiento SIN visualizaciones")
    print("="*60)

    processor = TableProcessor(
        sections_dir="output_sections",
        output_file="table_data.csv",
        generate_visualizations=False  # ← DESACTIVAR visualizaciones
    )

    df = processor.process_all_sections(debug=False)

    return df


if __name__ == "__main__":
    # Elegir uno de los ejemplos:

    # Opción 1: Con visualizaciones (más lento, genera imágenes)
    df = example_with_visualizations()

    # Opción 2: Sin visualizaciones (más rápido)
    # df = example_without_visualizations()

    if df is not None:
        print("\n" + "="*60)
        print("DATOS PROCESADOS")
        print("="*60)
        print(df.head())
