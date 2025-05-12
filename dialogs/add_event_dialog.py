from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDateEdit, QTextEdit, QPushButton, QDialogButtonBox
from PySide6.QtCore import QDate
from styles.styles import STYLESHEET

class AddEventDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить мероприятие")
        self.setup_ui()
        self.setStyleSheet(STYLESHEET)  # Применяем стили ко всем элементам диалога

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        form_layout.addRow("Название:", self.name_input)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        form_layout.addRow("Дата:", self.date_input)

        self.description_input = QTextEdit()
        form_layout.addRow("Описание:", self.description_input)

        self.organizer_combo = QComboBox()
        form_layout.addRow("Учреждение:", self.organizer_combo)

        self.format_combo = QComboBox()
        form_layout.addRow("Формат:", self.format_combo)

        self.classification_combo = QComboBox()
        form_layout.addRow("Классификация:", self.classification_combo)

        self.direction_combo = QComboBox()
        form_layout.addRow("Направление:", self.direction_combo)

        self.event_type_combo = QComboBox()
        form_layout.addRow("Тип:", self.event_type_combo)

        self.audience_combo = QComboBox()
        form_layout.addRow("Аудитория:", self.audience_combo)

        self.venue_combo = QComboBox()
        form_layout.addRow("Место:", self.venue_combo)

        self.total_attendees_input = QLineEdit()
        form_layout.addRow("Всего посетителей:", self.total_attendees_input)

        self.child_attendees_input = QLineEdit()
        form_layout.addRow("Детей:", self.child_attendees_input)

        self.volunteers_input = QLineEdit()
        form_layout.addRow("Волонтёров:", self.volunteers_input)

        self.at_risk_teens_input = QLineEdit()
        form_layout.addRow("Подростков группы риска:", self.at_risk_teens_input)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def set_data(self, institutions, formats, classifications, directions, event_types, audiences, venues):
        self.organizer_combo.addItems([i.name for i in institutions])
        self.format_combo.addItems([f.name for f in formats])
        self.classification_combo.addItems([c.name for c in classifications])
        self.direction_combo.addItems([d.name for d in directions])
        self.event_type_combo.addItems([et.name for et in event_types])
        self.audience_combo.addItems([a.name for a in audiences])
        self.venue_combo.addItems([v.name for v in venues])

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "date": self.date_input.date().toPython(),
            "description": self.description_input.toPlainText(),
            "organizer_id": self.organizer_combo.currentIndex() + 1,
            "format_id": self.format_combo.currentIndex() + 1,
            "classification_id": self.classification_combo.currentIndex() + 1,
            "direction_id": self.direction_combo.currentIndex() + 1,
            "event_type_id": self.event_type_combo.currentIndex() + 1,
            "target_audience_id": self.audience_combo.currentIndex() + 1,
            "venue_id": self.venue_combo.currentIndex() + 1,
            "total_attendees": self.total_attendees_input.text(),
            "child_attendees": self.child_attendees_input.text(),
            "volunteers": self.volunteers_input.text(),
            "at_risk_teens": self.at_risk_teens_input.text()
        }