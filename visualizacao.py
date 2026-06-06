"""
Visualização interativa do algoritmo A* com PyQt6.

Commit 1: Estrutura base — janela, grid e renderização das células.
"""

import sys
from enum import Enum, auto
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QGridLayout, QSizePolicy, QLabel, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont, QBrush, QPen, QRadialGradient


# ─── Paleta de cores ──────────────────────────────────────────────────

class Cores:
    # Fundo
    BG_ESCURO       = QColor(18, 18, 24)
    BG_PAINEL       = QColor(28, 28, 40)
    BG_CARD         = QColor(38, 38, 54)

    # Células
    LIVRE           = QColor(42, 42, 62)
    OBSTACULO       = QColor(30, 30, 44)
    OBSTACULO_BORDA = QColor(60, 40, 60)

    # Início / Objetivo
    INICIO          = QColor(100, 220, 255)
    OBJETIVO        = QColor(255, 80, 120)

    # Texto
    TEXTO_PRIMARIO  = QColor(230, 230, 245)
    TEXTO_SECUNDARIO= QColor(140, 140, 170)


# ─── Estado da célula ─────────────────────────────────────────────────

class EstadoCelula(Enum):
    LIVRE    = auto()
    OBSTACULO= auto()
    INICIO   = auto()
    OBJETIVO = auto()


# ─── Widget da célula ─────────────────────────────────────────────────

class CelulaWidget(QWidget):
    """Widget individual de cada célula do grid."""

    def __init__(self, linha, coluna):
        super().__init__()
        self.linha = linha
        self.coluna = coluna
        self.estado = EstadoCelula.LIVRE
        self.setMinimumSize(60, 60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _cor_base(self):
        cores = {
            EstadoCelula.LIVRE:     Cores.LIVRE,
            EstadoCelula.OBSTACULO: Cores.OBSTACULO,
            EstadoCelula.INICIO:    Cores.INICIO,
            EstadoCelula.OBJETIVO:  Cores.OBJETIVO,
        }
        return cores.get(self.estado, Cores.LIVRE)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margem = 2
        raio = 8

        cor_base = self._cor_base()

        # Gradiente radial sutil
        grad = QRadialGradient(w / 2, h / 2, max(w, h) / 1.5)
        cor_clara = QColor(
            min(255, cor_base.red() + 20),
            min(255, cor_base.green() + 20),
            min(255, cor_base.blue() + 20)
        )
        grad.setColorAt(0, cor_clara)
        grad.setColorAt(1, cor_base)

        # Desenha o retângulo arredondado
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(margem, margem, w - 2*margem, h - 2*margem, raio, raio)

        # Borda para obstáculos
        if self.estado == EstadoCelula.OBSTACULO:
            pen = QPen(Cores.OBSTACULO_BORDA, 2)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(margem, margem, w - 2*margem, h - 2*margem, raio, raio)

            # Ícone X para obstáculo
            p.setPen(QPen(QColor(100, 60, 80), 2))
            cx, cy = w // 2, h // 2
            sz = 8
            p.drawLine(cx - sz, cy - sz, cx + sz, cy + sz)
            p.drawLine(cx + sz, cy - sz, cx - sz, cy + sz)

        # Texto de início / objetivo
        if self.estado == EstadoCelula.INICIO:
            p.setPen(QPen(QColor(20, 20, 30)))
            font = QFont("Segoe UI", 11, QFont.Weight.Bold)
            p.setFont(font)
            p.drawText(margem, margem, w - 2*margem, h - 2*margem,
                       Qt.AlignmentFlag.AlignCenter, "A")

        elif self.estado == EstadoCelula.OBJETIVO:
            p.setPen(QPen(QColor(20, 20, 30)))
            font = QFont("Segoe UI", 11, QFont.Weight.Bold)
            p.setFont(font)
            p.drawText(margem, margem, w - 2*margem, h - 2*margem,
                       Qt.AlignmentFlag.AlignCenter, "★")

        p.end()


# ─── Widget do Grid ──────────────────────────────────────────────────

class GridWidget(QWidget):
    """Contém todas as células do mapa."""

    def __init__(self, mapa, inicio, objetivo):
        super().__init__()
        self.mapa = [row[:] for row in mapa]
        self.inicio = inicio
        self.objetivo = objetivo
        self.linhas = len(mapa)
        self.colunas = len(mapa[0])
        self.celulas = {}

        layout = QGridLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(10, 10, 10, 10)

        for i in range(self.linhas):
            for j in range(self.colunas):
                cel = CelulaWidget(i, j)
                if (i, j) == inicio:
                    cel.estado = EstadoCelula.INICIO
                elif (i, j) == objetivo:
                    cel.estado = EstadoCelula.OBJETIVO
                elif mapa[i][j] == 1:
                    cel.estado = EstadoCelula.OBSTACULO
                layout.addWidget(cel, i, j)
                self.celulas[(i, j)] = cel

        self.setLayout(layout)


# ─── Janela Principal ────────────────────────────────────────────────

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 Visualização A* — Busca Heurística")
        self.setMinimumSize(550, 500)

        # Estilo global
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {Cores.BG_ESCURO.name()};
            }}
            QWidget {{
                color: {Cores.TEXTO_PRIMARIO.name()};
                font-family: 'Segoe UI', sans-serif;
            }}
        """)

        # Mapa padrão
        mapa = [
            [0, 0, 0, 0, 0],
            [1, 1, 0, 1, 0],
            [0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0]
        ]
        inicio = (0, 0)
        objetivo = (4, 4)

        # ─── Layout principal ─────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        layout_principal = QVBoxLayout(central)
        layout_principal.setContentsMargins(16, 16, 16, 16)
        layout_principal.setSpacing(12)

        # ─── Título ───────────────────────────────────────────
        titulo = QLabel("✦  Algoritmo A* — Busca Heurística")
        titulo.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {Cores.TEXTO_PRIMARIO.name()}; padding: 4px 0;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(titulo)

        subtitulo = QLabel("Visualização passo a passo com distância Manhattan")
        subtitulo.setFont(QFont("Segoe UI", 11))
        subtitulo.setStyleSheet(f"color: {Cores.TEXTO_SECUNDARIO.name()};")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(subtitulo)

        # Grid
        self.grid = GridWidget(mapa, inicio, objetivo)

        grid_frame = QFrame()
        grid_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Cores.BG_PAINEL.name()};
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            }}
        """)
        grid_layout = QVBoxLayout(grid_frame)
        grid_layout.setContentsMargins(8, 8, 8, 8)
        grid_layout.addWidget(self.grid)

        layout_principal.addWidget(grid_frame, stretch=1)


# ─── Ponto de entrada ────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
