import gspread
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import os
import html

from PIL import Image, ImageDraw, ImageFont
import requests
import io
import subprocess
from PyPDF2 import PdfReader, PdfWriter
import tempfile
from pdf2image import convert_from_path

# ===== КОНФИГУРАЦИЯ =====
# Путь к файлу с ключами сервисного аккаунта
CREDENTIALS_FILE = './omnibot-478116-722a7107c571.json'

# ID таблицы (из URL: https://docs.google.com/spreadsheets/d/ВАШ_ID/edit)
SPREADSHEET_ID = '1r4gUJZrPoVP4GfmcPjmTTFz45Yo3JiorgMykb-4YV3w'

# Или название таблицы (раскомментировать если используете название)
# SPREADSHEET_NAME = 'Название вашей таблицы'

# Диапазон для тестирования
TEST_RANGE = 'A1'

# Scopes для доступа
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# ===== ФУНКЦИИ =====
def setup_google_sheets():
    """Настройка подключения к Google Sheets"""
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        print("✅ Google Sheets client authorized")
        return client
    except Exception as e:
        print(f"❌ Authorization failed: {e}")
        return None

def open_spreadsheet(client):
    """Открытие таблицы"""
    try:
        # Вариант 1: По ID (рекомендуется)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        
        # Вариант 2: По названию (раскомментировать если нужно)
        # spreadsheet = client.open(SPREADSHEET_NAME)
        
        print(f"✅ Spreadsheet opened: {spreadsheet.title}")
        return spreadsheet
    except Exception as e:
        print(f"❌ Failed to open spreadsheet: {e}")
        return None

def get_worksheet(spreadsheet, sheet_index=0):
    """Получение рабочего листа"""
    try:
        worksheet = spreadsheet.get_worksheet(sheet_index)
        print(f"✅ Worksheet accessed: {worksheet.title}")
        return worksheet
    except Exception as e:
        print(f"❌ Failed to get worksheet: {e}")
        return None

def test_connection(worksheet):
    """Тестирование подключения и прав"""
    try:
        # Тест чтения
        current_value = worksheet.acell(TEST_RANGE).value
        print(f"✅ Read test passed. Current value in {TEST_RANGE}: '{current_value}'")
        
        # Тест записи
        test_data = [['Hello from Python!']]
        worksheet.update(TEST_RANGE, test_data)
        print(f"✅ Write test passed. Updated {TEST_RANGE}")
        
        return True
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def read_data(worksheet, range_name='A1:B10'):
    """Чтение данных из указанного диапазона"""
    try:
        data = worksheet.get(range_name)
        print(f"✅ Data read from {range_name}: {len(data)} rows")
        return data
    except Exception as e:
        print(f"❌ Failed to read data: {e}")
        return None

def write_data(worksheet, range_name, data):
    """Запись данных в указанный диапазон"""
    try:
        worksheet.update(range_name, data)
        print(f"✅ Data written to {range_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to write data: {e}")
        return False

def append_row(worksheet, row_data):
    """Добавление новой строки в конец"""
    try:
        worksheet.append_row(row_data)
        print(f"✅ Row appended: {row_data}")
        return True
    except Exception as e:
        print(f"❌ Failed to append row: {e}")
        return False

def show_service_account_info():
    """Показывает информацию о сервисном аккаунте"""
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            creds_data = json.load(f)
            print(f"🔧 Service account email: {creds_data['client_email']}")
            print(f"🔧 Project ID: {creds_data['project_id']}")
    except Exception as e:
        print(f"❌ Failed to read credentials file: {e}")


def create_table_snapshot(worksheet, range_name='E1:G13', output_file=None):
    """
    Создает HTML-скриншот указанного диапазона таблицы
    
    Args:
        worksheet: объект рабочего листа
        range_name: диапазон для скриншота (по умолчанию 'E1:G13')
        output_file: путь к файлу для сохранения (если None, генерируется автоматически)
    
    Returns:
        str: путь к сохраненному файлу
    """
    try:
        # Получаем данные из указанного диапазона
        data = worksheet.get(range_name)
        
        if not data:
            print("❌ No data found in the specified range")
            return None
        
        # Создаем имя файла если не указано
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"table_snapshot_{timestamp}.html"
        
        # Создаем HTML-таблицу
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Снимок таблицы - {range_name}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    border-bottom: 2px solid #4285f4;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    color: #4285f4;
                    margin: 0;
                }}
                .metadata {{
                    color: #666;
                    font-size: 14px;
                    margin: 5px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background-color: #4285f4;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                    border: 1px solid #357ae8;
                }}
                td {{
                    padding: 10px;
                    border: 1px solid #ddd;
                    vertical-align: top;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                tr:hover {{
                    background-color: #e8f0fe;
                }}
                .cell-address {{
                    font-size: 10px;
                    color: #999;
                    font-family: monospace;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 10px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Снимок Google Таблицы</h1>
                    <div class="metadata">
                        <strong>Диапазон:</strong> {range_name} | 
                        <strong>Дата:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                        <strong>Строк:</strong> {len(data)} | 
                        <strong>Колонок:</strong> {len(data[0]) if data else 0}
                    </div>
                </div>
                
                <table>
        """
        
        # Добавляем строки таблицы
        start_col = ord(range_name[0]) - ord('A') + 1  # Первая колонка диапазона
        start_row = int(range_name[1:].split(':')[0])  # Первая строка диапазона
        
        for i, row in enumerate(data):
            html_content += "<tr>\n"
            for j, cell in enumerate(row):
                cell_address = f"{chr(65 + j)}{start_row + i}"  # Вычисляем адрес ячейки
                escaped_cell = html.escape(str(cell)) if cell else ""
                html_content += f'    <td title="{cell_address}">{escaped_cell}'
                html_content += f'<div class="cell-address">{cell_address}</div>'
                html_content += '</td>\n'
            html_content += "</tr>\n"
        
        html_content += """
                </table>
                
                <div class="footer">
                    Сгенерировано автоматически из Google Sheets | 
                    <a href="https://docs.google.com/spreadsheets" target="_blank">Открыть Google Sheets</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Сохраняем файл
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Получаем абсолютный путь для вывода
        abs_path = os.path.abspath(output_file)
        
        print(f"✅ Скриншот сохранен: {abs_path}")
        print(f"📊 Диапазон: {range_name}")
        print(f"📁 Размер: {len(data)} строк × {len(data[0]) if data else 0} колонок")
        
        return abs_path
        
    except Exception as e:
        print(f"❌ Ошибка при создании скриншота: {e}")
        return None
    

def create_range_screenshot(credentials_file, spreadsheet_id, range_name='E1:G13', output_file=None):
    """
    Создает PDF скриншот и оставляет только последнюю страницу
    """
    try:
        # Настройка аутентификации
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Создаем временный PDF файл
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        # Экспортируем всю таблицу в PDF
        request = drive_service.files().export_media(
            fileId=spreadsheet_id,
            mimeType='application/pdf'
        )
        
        # Сохраняем полный PDF
        with open(temp_pdf_path, 'wb') as f:
            f.write(request.execute())
        
        # Читаем PDF и оставляем только последнюю страницу
        reader = PdfReader(temp_pdf_path)
        writer = PdfWriter()
        
        if len(reader.pages) > 0:
            # Берем последнюю страницу
            last_page = reader.pages[-1]
            writer.add_page(last_page)
            
            # Сохраняем результат
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"table_screenshot_{timestamp}.pdf"
            
            with open(output_file, 'wb') as output_pdf:
                writer.write(output_pdf)
            
            abs_path = os.path.abspath(output_file)
            print(f"✅ PDF скриншот сохранен: {abs_path}")
            print(f"📊 Диапазон: {range_name}")
            print(f"📄 Оставлена только последняя страница из {len(reader.pages)}")
            
        else:
            print("❌ В PDF нет страниц")
            return None
        
        # Удаляем временный файл
        os.unlink(temp_pdf_path)
        
        return abs_path
        
    except Exception as e:
        print(f"❌ Ошибка при создании скриншота: {e}")
        # Пытаемся удалить временный файл при ошибке
        try:
            if 'temp_pdf_path' in locals():
                os.unlink(temp_pdf_path)
        except:
            pass
        return None

def create_table_screenshot(credentials_file, spreadsheet_id, range_name='E1:G13', output_file=None):
    """
    Создает PNG скриншот указанного диапазона через временный лист
    """
    try:
        # Настройка аутентификации
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        sheets_service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Создаем временный лист с нужным диапазоном
        temp_sheet_name = "tmp_screenshot"
        
        # Парсим диапазон для определения размеров
        range_parts = range_name.split(':')
        start_cell = range_parts[0]
        end_cell = range_parts[1] if len(range_parts) > 1 else start_cell
        
        def column_to_index(col):
            index = 0
            for char in col:
                if char.isalpha():
                    index = index * 26 + (ord(char.upper()) - ord('A') + 1)
            return index - 1
        
        start_col = ''.join(filter(str.isalpha, start_cell))
        start_row = int(''.join(filter(str.isdigit, start_cell))) - 1
        end_col = ''.join(filter(str.isalpha, end_cell))
        end_row = int(''.join(filter(str.isdigit, end_cell)))
        
        num_cols = column_to_index(end_col) - column_to_index(start_col) + 1
        num_rows = end_row - start_row
        
        # Удаляем временный лист если он уже существует
        try:
            existing_sheet_id = get_sheet_id_by_name(sheets_service, spreadsheet_id, temp_sheet_name)
            if existing_sheet_id:
                delete_request = {
                    'requests': [{
                        'deleteSheet': {
                            'sheetId': existing_sheet_id
                        }
                    }]
                }
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=delete_request
                ).execute()
        except:
            pass  # Лист не существует, это нормально
        
        # Создаем новый временный лист
        create_sheet_request = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': temp_sheet_name,
                        'gridProperties': {
                            'rowCount': num_rows + 5,
                            'columnCount': num_cols + 2
                        }
                    }
                }
            }]
        }
        
        result = sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=create_sheet_request
        ).execute()
        
        temp_sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']
        
        # Копируем нужный диапазон на временный лист
        copy_request = {
            'requests': [{
                'copyPaste': {
                    'source': {
                        'sheetId': 0,  # исходный лист
                        'startRowIndex': start_row,
                        'endRowIndex': end_row,
                        'startColumnIndex': column_to_index(start_col),
                        'endColumnIndex': column_to_index(end_col) + 1
                    },
                    'destination': {
                        'sheetId': temp_sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': num_rows,
                        'startColumnIndex': 0,
                        'endColumnIndex': num_cols
                    },
                    'pasteType': 'PASTE_NORMAL'
                }
            }]
        }
        
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=copy_request
        ).execute()
        
        # Создаем временный PDF файл
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        # ЭКСПОРТИРУЕМ ТОЛЬКО ВРЕМЕННЫЙ ЛИСТ В PDF
        # Для этого указываем gid (ID листа) в URL
        request = drive_service.files().export_media(
            fileId=spreadsheet_id,
            mimeType='application/pdf'
        )
        
        # Получаем PDF данные
        pdf_data = request.execute()
        
        # Сохраняем полный PDF
        with open(temp_pdf_path, 'wb') as f:
            f.write(pdf_data)
        
        # Читаем PDF и находим страницу с нашим временным листом
        reader = PdfReader(temp_pdf_path)
        
        if len(reader.pages) == 0:
            print("❌ В PDF нет страниц")
            os.unlink(temp_pdf_path)
            return None
        
        # Предполагаем, что временный лист будет последней страницей
        # (так как мы его создали последним)
        target_page = reader.pages[-1]
        
        # Создаем новый PDF только с нужной страницей
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as single_page_pdf:
            single_page_path = single_page_pdf.name
        
        writer = PdfWriter()
        writer.add_page(target_page)
        
        with open(single_page_path, 'wb') as output_pdf:
            writer.write(output_pdf)
        
        # Конвертируем PDF в PNG и обрезаем белые поля
        images = convert_from_path(single_page_path, dpi=200)
        if not images:
            print("❌ Не удалось конвертировать PDF в изображение")
            os.unlink(temp_pdf_path)
            os.unlink(single_page_path)
            return None
        
        image = images[0]
        
        # Автоматически обрезаем белые поля
        def autocrop_image(img, threshold=240):
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_data = img.load()
            width, height = img.size
            
            left = width
            right = 0
            top = height
            bottom = 0
            
            for y in range(height):
                for x in range(width):
                    r, g, b = img_data[x, y]
                    if r < threshold or g < threshold or b < threshold:
                        if x < left: left = x
                        if x > right: right = x
                        if y < top: top = y
                        if y > bottom: bottom = y
            
            padding = 5
            left = max(0, left - padding)
            right = min(width, right + padding)
            top = max(0, top - padding)
            bottom = min(height, bottom + padding)
            
            if left < right and top < bottom:
                return img.crop((left, top, right, bottom))
            else:
                return img
        
        cropped_image = autocrop_image(image)
        
        # Сохраняем PNG
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"table_screenshot_{timestamp}.png"
        elif not output_file.endswith('.png'):
            output_file += '.png'
        
        cropped_image.save(output_file, 'PNG', optimize=True)
        abs_path = os.path.abspath(output_file)
        
        # Удаляем временный лист
        try:
            delete_request = {
                'requests': [{
                    'deleteSheet': {
                        'sheetId': temp_sheet_id
                    }
                }]
            }
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=delete_request
            ).execute()
        except Exception as e:
            print(f"⚠️  Не удалось удалить временный лист: {e}")
        
        # Удаляем временные PDF файлы
        os.unlink(temp_pdf_path)
        os.unlink(single_page_path)
        
        print(f"✅ PNG скриншот сохранен: {abs_path}")
        print(f"📊 Диапазон: {range_name}")
        print(f"🖼️  Размер: {cropped_image.size[0]}x{cropped_image.size[1]} пикселей")
        print(f"📝 Временный лист создан и удален")
        
        return abs_path
        
    except Exception as e:
        print(f"❌ Ошибка при создании скриншота: {e}")
        # Пытаемся удалить временные файлы при ошибке
        try:
            if 'temp_pdf_path' in locals():
                os.unlink(temp_pdf_path)
            if 'single_page_path' in locals():
                os.unlink(single_page_path)
        except:
            pass
        return None

def get_sheet_id_by_name(sheets_service, spreadsheet_id, sheet_name):
    """Получает ID листа по названию"""
    try:
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        return None
    except:
        return None

# ===== ОСНОВНАЯ ПРОГРАММА =====
def main():
    print("🚀 Starting Google Sheets integration...")
    
    # Показываем информацию о сервисном аккаунте
    show_service_account_info()
    
    # Настройка подключения
    client = setup_google_sheets()
    if not client:
        return
    
    # Открытие таблицы
    spreadsheet = open_spreadsheet(client)
    if not spreadsheet:
        return
    
    # Получение рабочего листа
    worksheet = get_worksheet(spreadsheet)
    if not worksheet:
        return
    
    # Тестирование подключения
    if not test_connection(worksheet):
        return
    
    # Примеры использования:
    print("\n📋 Examples of operations:")
    
    # Пример 1: Чтение данных
    data = read_data(worksheet, 'A1:C5')
    if data:
        for i, row in enumerate(data):
            print(f"Row {i+1}: {row}")
    
    # Пример 2: Запись данных
    sample_data = [
        ['Name', 'Age', 'City'],
        ['Alice', '25', 'New York'],
        ['Bob', '30', 'London'],
        ['Charlie', '35', 'Tokyo']
    ]
    #write_data(worksheet, 'E1:G4', sample_data)
    
    # Пример 3: Добавление строки
    new_row = ['David', '28', 'Berlin']
    #append_row(worksheet, new_row)

    #snapshot_path = create_table_snapshot(worksheet, 'E1:G13')

    snapshot_path = create_table_screenshot(
        credentials_file=CREDENTIALS_FILE,  # путь к вашему JSON файлу
        spreadsheet_id=SPREADSHEET_ID,  # ID вашей таблицы
        range_name='E1:G13',                  # диапазон для скриншота
        output_file='screenshot.png'    # имя выходного файла (опционально)
    )
    
    print("\n🎯 All operations completed successfully!")

if __name__ == "__main__":
    main()