import pandas as pd
import psycopg2

db_params = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'client_encoding': 'utf-8'
}

def import_data():
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cursor:
                print("Connected to database successfully")

                print("Importing Material Types...")
                material_types_df = pd.read_excel('C:/Users/Margo/Downloads/ПК 1_Bezverhaya/Прил_В5_КОД 09.02.07-2-2025-ПУ/Ресурсы/Material_type_import.xlsx', engine='openpyxl')

                print("Columns in material_types_df:", material_types_df.columns.tolist())  
                for _, row in material_types_df.iterrows():
                    cursor.execute(
                        "INSERT INTO material_types (type_name, waste_percentage) VALUES (%s, %s)",
                        (row['Тип материала'], row['Процент потерь сырья']) 
                    )


                print("Importing Materials...")
                materials_df = pd.read_excel(
                    'C:/Users/Margo/Downloads/ПК 1_Bezverhaya/Прил_В5_КОД 09.02.07-2-2025-ПУ/Ресурсы/Materials_import.xlsx', 
                    engine='openpyxl'
                )

                cursor.execute("SELECT material_type_id, type_name FROM material_types")
                type_map = {row[1]: row[0] for row in cursor.fetchall()}

                for _, row in materials_df.iterrows():
                    cursor.execute(
                        """
                        INSERT INTO materials 
                        (material_name, material_type_id, unit_price, stock_quantity, min_quantity, package_quantity, unit_of_measure) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            row['Наименование материала'], 
                            type_map[row['Тип материала']],
                            row['Цена единицы материала'],
                            row['Количество на складе'],
                            row['Минимальное количество'],
                            row['Количество в упаковке'],
                            row['Единица измерения']
                        )
                    )

                print("Importing Product Types...")
                product_types_df = pd.read_excel(
                    'C:/Users/Margo/Downloads/ПК 1_Bezverhaya/Прил_В5_КОД 09.02.07-2-2025-ПУ/Ресурсы/Product_type_import.xlsx', 
                    engine='openpyxl'
                )
                for _, row in product_types_df.iterrows():
                    cursor.execute(
                        "INSERT INTO product_types (type_name, type_coefficient) VALUES (%s, %s)",
                        (row['Тип продукции'], row['Коэффициент типа продукции'])
                    )

                print("Importing Products...")
                products_df = pd.read_excel(
                    'C:/Users/Margo/Downloads/ПК 1_Bezverhaya/Прил_В5_КОД 09.02.07-2-2025-ПУ/Ресурсы/Products_import.xlsx', 
                    engine='openpyxl'
                )

                cursor.execute("SELECT product_type_id, type_name FROM product_types")
                product_type_map = {row[1]: row[0] for row in cursor.fetchall()}

                for _, row in products_df.iterrows():
                    cursor.execute(
                        """
                        INSERT INTO products 
                        (product_type_id, product_name, article_number, min_partner_price) 
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            product_type_map[row['Тип продукции']],
                            row['Наименование продукции'],
                            row['Артикул'],
                            row['Минимальная стоимость для партнера']
                        )
                    )


                print("Importing Material Requirements...")
                requirements_df = pd.read_excel(
                    'C:/Users/Margo/Downloads/ПК 1_Bezverhaya/Прил_В5_КОД 09.02.07-2-2025-ПУ/Ресурсы/Material_products__import.xlsx', 
                    engine='openpyxl'
                )

                cursor.execute("SELECT product_id, product_name FROM products")
                product_map = {row[1]: row[0] for row in cursor.fetchall()}

                cursor.execute("SELECT material_id, material_name FROM materials")
                material_map = {row[1]: row[0] for row in cursor.fetchall()}

                for _, row in requirements_df.iterrows():
                    product_id = product_map.get(row['Продукция'])
                    material_id = material_map.get(row['Наименование материала'])

                    if product_id and material_id:
                        cursor.execute(
                            """
                            INSERT INTO material_requirements 
                            (product_id, material_id, required_quantity) 
                            VALUES (%s, %s, %s)
                            """,
                            (product_id, material_id, row['Необходимое количество материала'])
                        )
                    else:
                        print(f"Skipping row - product or material not found: {row}")

                conn.commit()
                print("Data imported successfully!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import_data()
