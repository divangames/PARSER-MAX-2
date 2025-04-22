import sys
import os
import requests
import xml.etree.ElementTree as ET
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QPushButton, 
                            QMessageBox, QProgressBar, QLabel, QSplashScreen,
                            QFrame, QGridLayout, QLineEdit)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QPoint
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut, QFont, QPalette, QColor, QFontDatabase, QIcon
from pathlib import Path
import concurrent.futures
import time
import subprocess

class FontManager:
    @staticmethod
    def setup_fonts():
        # Создаем папку для шрифтов, если её нет
        fonts_dir = Path("fonts")
        fonts_dir.mkdir(exist_ok=True)
        
        # Путь к файлу шрифта Montserrat
        montserrat_path = fonts_dir / "Montserrat-Regular.ttf"
        
        # Скачиваем шрифт, если его нет
        if not montserrat_path.exists():
            try:
                url = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Regular.ttf"
                response = requests.get(url)
                response.raise_for_status()
                
                with open(montserrat_path, 'wb') as f:
                    f.write(response.content)
                    
                print("✅ Шрифт Montserrat успешно загружен")
            except Exception as e:
                print(f"❌ Ошибка загрузки шрифта: {str(e)}")
                return None
        
        # Загружаем шрифт в приложение
        font_id = QFontDatabase.addApplicationFont(str(montserrat_path))
        if font_id != -1:
            return QFontDatabase.applicationFontFamilies(font_id)[0]
        return None

class ModernFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            ModernFrame {
                background-color: #242424;
                border-radius: 8px;
                padding: 15px;
            }
        """)

class ModernSplashScreen(QSplashScreen):
    def __init__(self):
        splash_pixmap = QPixmap(400, 200)
        splash_pixmap.fill(Qt.transparent)
        super().__init__(splash_pixmap, Qt.WindowStaysOnTopHint)
        
        # Создаем фрейм для сплэш-скрина
        self.frame = QFrame(self)
        self.frame.setGeometry(0, 0, 400, 200)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border-radius: 8px;
                border: 1px solid #404040;
            }
        """)
        
        # Добавляем заголовок
        self.title_label = QLabel("PARSER MAX 2", self)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                font-size: 24px;
                font-weight: normal;
                font-family: "{QApplication.font().family()}";
            }}
        """)
        self.title_label.setGeometry(0, 50, 400, 40)
        self.title_label.setAlignment(Qt.AlignCenter)
        
        # Добавляем статус-бар
        self.status_bar = QProgressBar(self)
        self.status_bar.setGeometry(50, 120, 300, 4)
        self.status_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #2C2C2C;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #404040;
                border-radius: 2px;
            }
        """)
        self.status_bar.setTextVisible(False)
        self.status_bar.setRange(0, 0)  # Бесконечная анимация
        
        # Добавляем текст статуса
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                font-size: 12px;
                font-family: "{QApplication.font().family()}";
            }}
        """)
        self.status_label.setGeometry(0, 140, 400, 30)
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Анимация для статус-бара
        self.animation = QPropertyAnimation(self.status_bar, b"value")
        self.animation.setDuration(1500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(100)
        self.animation.setLoopCount(-1)  # Бесконечное повторение
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()
        
    def showMessage(self, message, alignment=Qt.AlignCenter, color=Qt.white):
        self.status_label.setText(message)
        QApplication.processEvents()
        
    def mousePressEvent(self, event):
        pass  # Предотвращаем закрытие сплэш-скрина по клику

class FadeInWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 0.0
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, opacity):
        self._opacity = opacity
        self.setStyleSheet(f"background-color: rgba(30, 30, 30, {opacity})")

    opacity = Property(float, get_opacity, set_opacity)

    def showEvent(self, event):
        super().showEvent(event)
        self.animation.start()

class ParserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Устанавливаем иконку приложения
        self.setWindowIcon(QIcon("icon.ico"))
        
        # Устанавливаем шрифты
        self.font_family = FontManager.setup_fonts() or "Segoe UI"
        
        # Устанавливаем темную тему
        self.setup_dark_theme()
        
        # Создаем и показываем сплэш-скрин
        self.splash = ModernSplashScreen()
        self.splash.show()
        
        self.setWindowTitle("PARSER MAX 2")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #1A1A1A;
            }}
            QLabel {{
                color: #FFFFFF;
                font-size: 14px;
                font-family: "{self.font_family}";
            }}
            QPushButton {{
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #404040;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-family: "{self.font_family}";
            }}
            QPushButton:hover {{
                background-color: #353535;
                border: 1px solid #505050;
            }}
            QPushButton:pressed {{
                background-color: #404040;
            }}
            QPushButton:disabled {{
                background-color: #252525;
                color: #505050;
                border: 1px solid #303030;
            }}
            QLineEdit {{
                padding: 8px;
                border: 1px solid #404040;
                border-radius: 4px;
                background-color: #2C2C2C;
                color: white;
                font-size: 14px;
                font-family: "{self.font_family}";
            }}
            QLineEdit:focus {{
                border-color: #505050;
            }}
            QTextEdit {{
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                font-family: "{self.font_family}";
            }}
            QProgressBar {{
                border: 1px solid #404040;
                border-radius: 4px;
                text-align: center;
                background-color: #2C2C2C;
                font-family: "{self.font_family}";
            }}
            QProgressBar::chunk {{
                background-color: #404040;
            }}
        """)
        
        # Заголовки для запросов
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        # Создаем папку products, если её нет
        self.products_dir = Path("products")
        self.products_dir.mkdir(exist_ok=True)
        
        # Инициализируем XML данные
        self.xml_data = None
        
        # Основной виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Основной layout с отступами
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Заголовок приложения
        title_label = QLabel("PARSER MAX 2")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                font-size: 20px;
                font-weight: normal;
                padding: 10px;
                font-family: "{self.font_family}";
            }}
        """)
        layout.addWidget(title_label, alignment=Qt.AlignCenter)
        
        # Создаем основной контейнер
        main_container = ModernFrame()
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(15)
        
        # Обновляем стиль ModernFrame
        main_container.setStyleSheet("""
            ModernFrame {
                background-color: #242424;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        # Создаем поле ввода для списка артикулов
        input_layout = QGridLayout()
        input_layout.setSpacing(10)
        
        input_label = QLabel("Артикулы товаров")
        input_layout.addWidget(input_label, 0, 0)
        
        self.article_input = QTextEdit()
        self.article_input.setPlaceholderText("Введите артикулы товаров (каждый артикул с новой строки)")
        self.article_input.setMinimumHeight(100)
        input_layout.addWidget(self.article_input, 0, 1)
        
        main_layout.addLayout(input_layout)
        
        # Создаем кнопки
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Кнопка поиска
        search_button = QPushButton("🚀 Начать загрузку (Ctrl+Enter)")
        search_button.clicked.connect(self.process_articles)
        
        # Кнопка очистки
        clear_button = QPushButton("🗑️ Очистить")
        clear_button.clicked.connect(self.clear_all)
        
        # Кнопка открытия папки
        open_folder_button = QPushButton("📂 Перейти к файлам")
        open_folder_button.clicked.connect(self.open_products_folder)
        
        # Добавляем кнопки в layout
        button_layout.addWidget(search_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(open_folder_button)
        
        # Создаем контейнер для кнопок
        button_container = QWidget()
        button_container.setLayout(button_layout)
        main_layout.addWidget(button_container)
        
        # Добавляем горячие клавиши
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.process_articles)
        
        # Создаем прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #363636;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 5px;
            }
        """)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Создаем область для отображения информации
        info_container = ModernFrame()
        info_layout = QVBoxLayout(info_container)
        
        info_label = QLabel("Лог операций")
        info_layout.addWidget(info_label)
        
        self.info_area = QTextEdit()
        self.info_area.setReadOnly(True)
        self.info_area.setMinimumHeight(200)
        info_layout.addWidget(self.info_area)
        
        main_layout.addWidget(info_container)
        
        # Создаем статус бар
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                padding: 10px;
                border-radius: 4px;
                background-color: #2C2C2C;
                font-size: 13px;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # Добавляем основной контейнер в layout
        layout.addWidget(main_container)
        
        self.update_status("⏳ Загрузка приложения...")
        
        # Initialize animations
        self.button_animations = {}
        
        # Загружаем XML данные через таймер
        QTimer.singleShot(1000, self.initialize_app)

    def setup_dark_theme(self):
        # Устанавливаем темную тему для всего приложения
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor("#1A1A1A"))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor("#2C2C2C"))
        dark_palette.setColor(QPalette.AlternateBase, QColor("#2C2C2C"))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor("#2C2C2C"))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.Link, QColor("#404040"))
        dark_palette.setColor(QPalette.Highlight, QColor("#404040"))
        dark_palette.setColor(QPalette.HighlightedText, Qt.white)
        
        QApplication.setPalette(dark_palette)
        
        # Устанавливаем шрифт по умолчанию
        font = QFont(self.font_family, 9)
        QApplication.setFont(font)

    def update_status(self, message, is_error=False):
        style = "background-color: #3A2A2A;" if is_error else "background-color: #2A3A2A;"
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                padding: 10px;
                border-radius: 4px;
                {style}
                font-size: 13px;
            }}
        """)
        self.status_label.setText(message)
        
    def initialize_app(self):
        try:
            self.splash.showMessage("Загрузка каталога...", 
                                  Qt.AlignCenter | Qt.AlignBottom, Qt.white)
            QApplication.processEvents()
            
            self.load_xml_data()
            self.splash.finish(self)
            self.update_status("✅ Приложение готово к работе")
        except Exception as e:
            self.splash.finish(self)
            self.update_status(f"❌ Ошибка инициализации: {str(e)}", True)
        
    def clear_all(self):
        self.article_input.clear()
        self.info_area.clear()
        self.progress_bar.setVisible(False)
        self.update_status("🗑️ Все поля очищены")
            
    def load_xml_data(self):
        try:
            self.info_area.append("🔄 Загрузка каталога...")
            QApplication.processEvents()
            
            response = requests.get('https://outmaxshop.com/yml/all_new.yml', headers=self.headers)
            response.raise_for_status()
            self.xml_data = ET.fromstring(response.content)
            
            self.info_area.append("✅ Каталог успешно загружен")
        except Exception as e:
            error_msg = f"❌ Ошибка загрузки каталога: {str(e)}"
            self.info_area.append(error_msg)
            self.update_status(error_msg, True)
            raise
            
    def download_image(self, url, path):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            with open(path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception:
            return False
            
    def process_product(self, article):
        try:
            # Ищем товар
            product = None
            for offer in self.xml_data.findall('.//offer'):
                if offer.get('id') == article:
                    product = offer
                    break
                    
            if product is None:
                return f"❌ Артикул {article}: товар не найден"
                
            # Получаем информацию о товаре
            name = product.find('name').text if product.find('name') is not None else "Нет названия"
            
            # Создаем директорию для товара
            product_dir = self.products_dir / article
            product_dir.mkdir(exist_ok=True)
            
            # Собираем информацию о размерах
            sizes_info = []
            for param in product.findall('.//param'):
                if param.get('name') == 'Размер':
                    size = param.text
                    sizes_info.append(f'"{size}"')
            
            # Сохраняем информацию в файл
            with open(product_dir / f"{article}_info.txt", "w", encoding="utf-8") as f:
                f.write(f"Артикул: {article}\n")
                f.write(f"Название: {name}\n\n")
                f.write("Размеры:\n")
                for size in sizes_info:
                    f.write(f"{size}\n")
            
            # Загружаем изображения
            pictures = product.findall('.//picture')
            successful_downloads = 0
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future_to_url = {}
                for i, picture in enumerate(pictures, 1):
                    image_url = picture.text
                    # Возвращаем предыдущий формат названия с полным именем товара
                    safe_name = name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                    image_name = f"{article}_{safe_name}_{i}.jpg"
                    image_path = product_dir / image_name
                    
                    future = executor.submit(self.download_image, image_url, image_path)
                    future_to_url[future] = image_url
                
                for future in concurrent.futures.as_completed(future_to_url):
                    if future.result():
                        successful_downloads += 1
            
            return f"✅ Артикул {article}: загружено {successful_downloads} из {len(pictures)} изображений, найдено {len(sizes_info)} размеров"
            
        except Exception as e:
            return f"❌ Артикул {article}: ошибка обработки - {str(e)}"
            
    def process_articles(self):
        if self.xml_data is None:
            self.load_xml_data()
            if self.xml_data is None:
                self.update_status("❌ Ошибка: не удалось загрузить каталог", True)
                return
                
        # Получаем список артикулов
        articles = [art.strip() for art in self.article_input.toPlainText().split('\n') if art.strip()]
        
        if not articles:
            self.update_status("⚠️ Введите артикулы товаров", True)
            return
            
        self.info_area.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(articles))
        self.progress_bar.setValue(0)
        
        start_time = time.time()
        self.info_area.append(f"🚀 Начало обработки {len(articles)} артикулов...")
        self.update_status("⏳ Идет обработка товаров...")
        QApplication.processEvents()
        
        for i, article in enumerate(articles, 1):
            result = self.process_product(article)
            self.info_area.append(result)
            self.progress_bar.setValue(i)
            QApplication.processEvents()
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.info_area.append(f"\n✨ Обработка завершена за {duration:.1f} секунд")
        self.info_area.append(f"📊 Обработано артикулов: {len(articles)}")
        self.info_area.append(f"📁 Папка с товарами: {self.products_dir.absolute()}")
        self.update_status("✅ Обработка завершена")

    def open_products_folder(self):
        """Открывает папку с товарами в проводнике Windows"""
        try:
            abs_path = self.products_dir.absolute()
            if sys.platform == 'win32':
                os.startfile(abs_path)
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.run([opener, abs_path])
            self.update_status("✅ Папка с товарами открыта")
        except Exception as e:
            self.update_status(f"❌ Ошибка при открытии папки: {str(e)}", True)

    def init_app(self):
        self.init_ui()
        self.show()
        self.splash.finish(self)
    
    def init_ui(self):
        # Add button click animations
        for button in [search_button, clear_button, open_folder_button]:
            animation = QPropertyAnimation(button, b"pos")
            animation.setDuration(100)
            self.button_animations[button] = animation
            button.clicked.connect(lambda checked, b=button: self.animate_button_click(b))

    def animate_button_click(self, button):
        animation = self.button_animations[button]
        start_pos = button.pos()
        
        # Move down 2 pixels and back
        animation.setStartValue(start_pos)
        animation.setKeyValueAt(0.5, start_pos + QPoint(0, 2))
        animation.setEndValue(start_pos)
        animation.start()

    def show_message(self, message, error=False):
        self.info_area.append(message)
        
        # Анимация появления сообщения
        cursor = self.info_area.textCursor()
        cursor.movePosition(cursor.End)
        self.info_area.setTextCursor(cursor)
        
        # Кратковременная подсветка области информации
        original_style = self.info_area.styleSheet()
        flash_color = "#3A2A2A" if error else "#2A3A2A"
        self.info_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {flash_color};
                color: white;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
        """)
        QTimer.singleShot(200, lambda: self.info_area.setStyleSheet(original_style))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ParserApp()
    window.show()
    sys.exit(app.exec()) 