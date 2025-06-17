from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDateEdit, QPushButton, QTextEdit, QHBoxLayout
from PySide6.QtCore import QDate

class AddEventDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить мероприятие")
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.description_input = QTextEdit()
        self.organizer_combo = QComboBox()
        self.format_combo = QComboBox()
        self.classification_combo = QComboBox()
        self.direction_combo = QComboBox()
        self.event_type_combo = QComboBox()
        self.audience_combo = QComboBox()
        self.venue_combo = QComboBox()
        self.total_attendees_input = QLineEdit()
        self.child_attendees_input = QLineEdit()
        self.volunteers_input = QLineEdit()
        self.at_risk_teens_input = QLineEdit()
        
        self.form_layout.addRow("Название:", self.name_input)
        self.form_layout.addRow("Дата:", self.date_input)
        self.form_layout.addRow("Описание:", self.description_input)
        self.form_layout.addRow("Организатор:", self.organizer_combo)
        self.form_layout.addRow("Формат:", self.format_combo)
        self.form_layout.addRow("Классификация:", self.classification_combo)
        self.form_layout.addRow("Направление:", self.direction_combo)
        self.form_layout.addRow("Форма мероприятия:", self.event_type_combo)
        self.form_layout.addRow("Аудитория:", self.audience_combo)
        self.form_layout.addRow("Место проведения:", self.venue_combo)
        self.form_layout.addRow("Всего посетителей:", self.total_attendees_input)
        self.form_layout.addRow("Детей:", self.child_attendees_input)
        self.form_layout.addRow("Волонтёров:", self.volunteers_input)
        self.form_layout.addRow("Подростков группы риска:", self.at_risk_teens_input)
        
        self.layout.addLayout(self.form_layout)
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)
    
    def set_data(self, institutions, formats, classifications, directions, event_types, audiences, venues):
        self.organizer_combo.addItems([i.name for i in institutions])
        self.organizer_combo.setProperty("ids", [i.id for i in institutions])
        self.format_combo.addItems([f.name for f in formats])
        self.format_combo.setProperty("ids", [f.id for f in formats])
        self.classification_combo.addItems([c.name for c in classifications])
        self.classification_combo.setProperty("ids", [c.id for c in classifications])
        self.direction_combo.addItems([d.name for d in directions])
        self.direction_combo.setProperty("ids", [d.id for d in directions])
        self.event_type_combo.addItems([et.name for et in event_types])
        self.event_type_combo.setProperty("ids", [et.id for et in event_types])
        self.audience_combo.addItems([a.name for a in audiences])
        self.audience_combo.setProperty("ids", [a.id for a in audiences])
        self.venue_combo.addItems([v.name for v in venues])
        self.venue_combo.setProperty("ids", [v.id for v in venues])
    
    def get_data(self):
        return {
            "name": self.name_input.text(),
            "date": self.date_input.date().toPython(),
            "description": self.description_input.toPlainText(),
            "organizer_id": self.organizer_combo.property("ids")[self.organizer_combo.currentIndex()],
            "format_id": self.format_combo.property("ids")[self.format_combo.currentIndex()],
            "classification_id": self.classification_combo.property("ids")[self.classification_combo.currentIndex()],
            "direction_id": self.direction_combo.property("ids")[self.direction_combo.currentIndex()],
            "event_type_id": self.event_type_combo.property("ids")[self.event_type_combo.currentIndex()],
            "audience_id": self.audience_combo.property("ids")[self.audience_combo.currentIndex()],
            "venue_id": self.venue_combo.property("ids")[self.venue_combo.currentIndex()],
            "total_attendees": self.total_attendees_input.text(),
            "child_attendees": self.child_attendees_input.text(),
            "volunteers": self.volunteers_input.text(),
            "at_risk_teens": self.at_risk_teens_input.text()
        }