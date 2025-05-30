from PySide6.QtGui import QTextDocument, QPdfWriter, QPainter, QFont
from PySide6.QtCore import Qt
from datetime import datetime
import os

def save_report(model, start_date, end_date, file_name):
    try:
        # Создаём документ
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Arial", 10))

        # Формируем HTML-содержимое
        html = """
        <h1 style='text-align: center;'>Отчёт по мероприятиям</h1>
        <p style='text-align: center;'>Период: {start_date} - {end_date}</p>
        <table border='1' style='width: 100%; border-collapse: collapse;'>
            <tr style='background-color: #f2f2f2;'>
        """

        # Заголовки таблицы
        for col in range(model.columnCount()):
            header = model.headerData(col, Qt.Horizontal) or "Колонка"
            html += f"<th style='padding: 5px;'>{header}</th>"
        html += "</tr>"

        # Данные таблицы
        for row in range(model.rowCount()):
            html += "<tr>"
            for col in range(model.columnCount()):
                data = model.index(row, col).data() or ""
                html += f"<td style='padding: 5px;'>{data}</td>"
            html += "</tr>"

        html += """
        </table>
        <p style='text-align: right; margin-top: 20px;'>Дата формирования: {current_date}</p>
        """
        html = html.format(
            start_date=start_date.strftime("%d.%m.%Y"),
            end_date=end_date.strftime("%d.%m.%Y"),
            current_date=datetime.now().strftime("%d.%m.%Y")
        )

        doc.setHtml(html)

        # Сохраняем в PDF
        pdf_writer = QPdfWriter(file_name)
        pdf_writer.setPageSize(QPdfWriter.A4)
        pdf_writer.setResolution(96)

        painter = QPainter(pdf_writer)
        doc.drawContents(painter)
        painter.end()

        return True, "Отчёт успешно сохранён"
    except Exception as e:
        return False, f"Ошибка при сохранении отчёта: {str(e)}"