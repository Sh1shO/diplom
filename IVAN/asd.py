from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel

app = QApplication([])

window = QWidget()
layout = QVBoxLayout()

label = QLabel("Фильтр:")
combo = QComboBox()
combo.addItems(["Поставщик", "Производитель", "Клиент"])

layout.addWidget(label)
layout.addWidget(combo)
window.setLayout(layout)
window.show()

app.exec()