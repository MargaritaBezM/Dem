import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QScrollArea, QPushButton, QDialog, QComboBox, QLineEdit,
    QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
import psycopg2


class MaterialCard(QFrame):
    def __init__(self, material_data, edit_callback, parent=None):
        super().__init__(parent)
        self.material_data = material_data
        self.edit_callback = edit_callback

        self.setFrameShape(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
            QLabel {
                font-size: 12px;
            }
        """)

        material_id, name, unit, current_qty, min_qty = material_data
        self.material_id = material_id

        self.create_layout(material_id, name, unit, current_qty, min_qty)

    def create_layout(self, material_id, name, unit, current_qty, min_qty):
        header_layout = QHBoxLayout()
        title = QLabel(f"<b>Материал ID: {material_id} | {name}</b>")
        header_layout.addWidget(title)

        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"Минимальный запас: {min_qty} {unit}"))
        info_layout.addWidget(QLabel(f"Количество на складе: {current_qty} {unit}"))
        info_layout.addWidget(QLabel(f"Единица измерения: {unit}"))

        layout = QVBoxLayout()
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        layout.addLayout(info_layout)
        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.edit_callback(self.material_id)


class MaterialForm(QDialog):
    def __init__(self, db_connection, refresh_callback, material_id=None, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.refresh_callback = refresh_callback
        self.material_id = material_id

        self.setWindowTitle("Добавить / Редактировать материал")
        self.setGeometry(150, 150, 400, 300)

        self.init_ui()

        if self.material_id is not None:
            self.load_material_data()

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            
            QLabel {
                color: #405C73;
            }
            
            QPushButton {
                background-color: #405C73;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }

            QPushButton:hover {
                background-color: #304656;
            }

            QScrollArea {
                background-color: #FFFFFF;
            }
            
            QFrame {
                background-color: #BFD6F6;
                border-radius: 8px;
                padding: 12px;
            }
        """)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.type_combo = QComboBox()
        self.name_edit = QLineEdit()
        self.price_edit = QLineEdit()
        self.unit_edit = QLineEdit()
        self.package_qty_edit = QLineEdit()
        self.stock_qty_edit = QLineEdit()
        self.min_qty_edit = QLineEdit()

        self.load_material_types()

        form_layout.addRow("Тип материала:", self.type_combo)
        form_layout.addRow("Наименование:", self.name_edit)
        form_layout.addRow("Цена за единицу:", self.price_edit)
        form_layout.addRow("Единица измерения:", self.unit_edit)
        form_layout.addRow("Кол-во в упаковке:", self.package_qty_edit)
        form_layout.addRow("Кол-во на складе:", self.stock_qty_edit)
        form_layout.addRow("Минимальное кол-во:", self.min_qty_edit)

        layout.addLayout(form_layout)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_material)

        layout.addWidget(save_btn)
        self.setLayout(layout)


    def load_material_types(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT material_type_id, type_name FROM material_types ORDER BY type_name")
            self.material_types = cursor.fetchall()
            for mt_id, mt_name in self.material_types:
                self.type_combo.addItem(mt_name, mt_id)
            cursor.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки типов материала: {e}")

    def load_material_data(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT material_type_id, material_name, unit_price, unit_of_measure, package_quantity, stock_quantity, min_quantity
                FROM materials
                WHERE material_id = %s
            """, (self.material_id,))
            row = cursor.fetchone()
            if row:
                material_type_id, name, price, unit, package_qty, stock_qty, min_qty = row
                index = self.type_combo.findData(material_type_id)
                self.type_combo.setCurrentIndex(index)
                self.name_edit.setText(name)
                self.price_edit.setText(f"{price:.2f}")
                self.unit_edit.setText(unit)
                self.package_qty_edit.setText(str(package_qty))
                self.stock_qty_edit.setText(str(stock_qty))
                self.min_qty_edit.setText(str(min_qty))
            cursor.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных материала: {e}")

    def save_material(self):
        try:
            material_type_id = self.type_combo.currentData()
            name = self.name_edit.text().strip()
            try:
                price = float(self.price_edit.text())
                if price < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Цена должна быть неотрицательным числом!")
                return

            unit = self.unit_edit.text().strip()
            try:
                package_qty = int(self.package_qty_edit.text())
                stock_qty = int(self.stock_qty_edit.text())
                min_qty = int(self.min_qty_edit.text())
                if min_qty < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Количество (упаковка, склад, минимум) должно быть целым неотрицательным числом!")
                return

            cursor = self.db_connection.cursor()

            if self.material_id is None:
                cursor.execute("""
                    INSERT INTO materials
                    (material_type_id, material_name, unit_price, unit_of_measure, package_quantity, stock_quantity, min_quantity)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (material_type_id, name, price, unit, package_qty, stock_qty, min_qty))
            else:
                cursor.execute("""
                    UPDATE materials
                    SET material_type_id=%s, material_name=%s, unit_price=%s, unit_of_measure=%s,
                        package_quantity=%s, stock_quantity=%s, min_quantity=%s
                    WHERE material_id = %s
                """, (material_type_id, name, price, unit, package_qty, stock_qty, min_qty, self.material_id))

            self.db_connection.commit()
            cursor.close()

            QMessageBox.information(self, "Успех", "Материал успешно сохранён.")
            self.refresh_callback()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения материала: {e}")


class MaterialWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление материалами на складе")
        self.setGeometry(100, 100, 800, 600)


        try:
            self.setWindowIcon(QIcon("C:/Users/Margo/Downloads/ПК 1_Bezverhaya/Прил_В5_КОД 09.02.07-2-2025-ПУ/Ресурсы/Образ плюс.png"))
        except:
            pass

        self.db_connection = self.connect_to_db()
        self.init_ui()
        self.load_materials()

    def connect_to_db(self):
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="postgres",
                client_encoding="UTF-8"
            )
            return conn
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            return None

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        title_label = QLabel("Список материалов на складе")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.materials_container = QWidget()
        self.materials_layout = QVBoxLayout()
        self.materials_container.setLayout(self.materials_layout)

        scroll_area.setWidget(self.materials_container)
        main_layout.addWidget(scroll_area)

        buttons_layout = QHBoxLayout()

        refresh_btn = QPushButton("Обновить данные")
        refresh_btn.clicked.connect(self.load_materials)
        buttons_layout.addWidget(refresh_btn)

        add_btn = QPushButton("Добавить материал")
        add_btn.clicked.connect(self.open_add_material_form)
        buttons_layout.addWidget(add_btn)

        main_layout.addLayout(buttons_layout)

    def load_materials(self):
        if not self.db_connection:
            print("Нет подключения к БД")
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT material_id, material_name, unit_of_measure, stock_quantity, min_quantity
                FROM materials
                ORDER BY material_id
            """)
            materials = cursor.fetchall()
            cursor.close()

            for i in reversed(range(self.materials_layout.count())):
                widget = self.materials_layout.takeAt(i).widget()
                if widget:
                    widget.deleteLater()

            for material in materials:
                card = MaterialCard(material, self.open_edit_material_form)
                self.materials_layout.addWidget(card)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки материалов: {e}")

    def open_add_material_form(self):
        form = MaterialForm(self.db_connection, self.load_materials, material_id=None, parent=self)
        form.exec_()

    def open_edit_material_form(self, material_id):
        form = MaterialForm(self.db_connection, self.load_materials, material_id=material_id, parent=self)
        form.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MaterialWindow()
    window.show()
    sys.exit(app.exec_())
