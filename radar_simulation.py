
import sys
import random
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QBrush
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout


class RadarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 400)
        self.angle = 0  # Ângulo do ponteiro
        self.radius = 150  # Raio do círculo
        self.objects = self.generate_objects()

    def generate_objects(self):
        """Gera objetos detectados com posições e distâncias aleatórias."""
        objects = []
        for _ in range(random.randint(3, 7)):  # 3 a 7 pontos aleatórios
            angle = random.uniform(0, 360)  # Ângulo em graus
            distance = random.uniform(10, self.radius * 0.8)  # Distância até 80% do raio
            objects.append((angle, distance))
        return objects

    def update_radar(self):
        """Atualiza o ângulo e os objetos no radar."""
        self.angle = (self.angle + 2) % 360  # Incrementa o ângulo do ponteiro
        self.objects = self.generate_objects()  # Gera novos objetos detectados
        self.update()  # Re-renderiza o radar

    def paintEvent(self, event):
        """Desenha o radar, ponteiro e objetos detectados."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() // 2
        center_y = self.height() // 2

        # Fundo preto
        painter.setBrush(QBrush(Qt.black))
        painter.drawRect(0, 0, self.width(), self.height())

        # Desenha o círculo
        painter.setPen(QPen(Qt.white, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center_x - self.radius, center_y - self.radius, self.radius * 2, self.radius * 2)

        # Desenha o ponteiro
        pointer_x = center_x + self.radius * 0.8 * Qt.cos(self.angle * 3.14 / 180)
        pointer_y = center_y - self.radius * 0.8 * Qt.sin(self.angle * 3.14 / 180)
        painter.setPen(QPen(Qt.green, 4))
        painter.drawLine(center_x, center_y, pointer_x, pointer_y)

        # Desenha objetos detectados
        for angle, distance in self.objects:
            obj_x = center_x + distance * Qt.cos(angle * 3.14 / 180)
            obj_y = center_y - distance * Qt.sin(angle * 3.14 / 180)
            painter.setBrush(QBrush(Qt.red))
            painter.drawEllipse(obj_x - 5, obj_y - 5, 10, 10)


class RadarSimulation(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Radar Simulation")
        self.setGeometry(100, 100, 900, 500)

        # Layout principal
        main_layout = QHBoxLayout()

        # Primeira instância do radar
        self.radar1 = RadarWidget()
        self.label1 = QLabel("Detected objects:\n", self)
        self.label1.setStyleSheet("color: white; font-size: 14px;")

        # Segunda instância do radar
        self.radar2 = RadarWidget()
        self.label2 = QLabel("Detected objects:\n", self)
        self.label2.setStyleSheet("color: white; font-size: 14px;")

        # Configurando layouts dos radares e labels
        radar1_layout = QVBoxLayout()
        radar1_layout.addWidget(self.radar1)
        radar1_layout.addWidget(self.label1)

        radar2_layout = QVBoxLayout()
        radar2_layout.addWidget(self.radar2)
        radar2_layout.addWidget(self.label2)

        main_layout.addLayout(radar1_layout)
        main_layout.addLayout(radar2_layout)

        self.setLayout(main_layout)

        # Timer para atualizar os radares
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(100)  # Atualiza a cada 100 ms

    def update_simulation(self):
        """Atualiza os radares e as labels de distância."""
        self.radar1.update_radar()
        self.radar2.update_radar()

        # Atualiza informações para o radar 1
        radar1_text = "Detected objects:\n"
        for i, (angle, distance) in enumerate(self.radar1.objects, 1):
            radar1_text += f"{i}. {distance:.1f} m\n"
        self.label1.setText(radar1_text)

        # Atualiza informações para o radar 2
        radar2_text = "Detected objects:\n"
        for i, (angle, distance) in enumerate(self.radar2.objects, 1):
            radar2_text += f"{i}. {distance:.1f} m\n"
        self.label2.setText(radar2_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    simulation = RadarSimulation()
    simulation.show()
    sys.exit(app.exec_())
