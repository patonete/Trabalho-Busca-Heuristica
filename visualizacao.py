"""
Visualização interativa do algoritmo A* com PyQt6.

Funcionalidades até agora:
  - Grid visual do mapa com obstáculos
  - Algoritmo A* como gerador (passo a passo)
  - Estados visuais para exploração (aberto, fechado, atual)
  - Exibição de custos g(n) e f(n) em cada célula
  - Controles: Iniciar, Pausar, Passo, Reiniciar e Velocidade
  - Painel lateral com legenda, estatísticas e modos de edição
  - Clique para editar obstáculos, início e objetivo
"""

import sys
import heapq
from enum import Enum, auto
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFrame, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
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

    # Exploração
    ABERTO          = QColor(60, 130, 220)     # nós na fila (azul)
    FECHADO         = QColor(80, 80, 130)      # nós já explorados
    CAMINHO         = QColor(0, 220, 130)      # caminho final (verde)
    ATUAL           = QColor(255, 180, 40)     # nó sendo explorado agora

    # Início / Objetivo
    INICIO          = QColor(100, 220, 255)
    OBJETIVO        = QColor(255, 80, 120)

    # Texto
    TEXTO_PRIMARIO  = QColor(230, 230, 245)
    TEXTO_SECUNDARIO= QColor(140, 140, 170)

    # Botões
    BTN_PRIMARIO    = QColor(80, 160, 255)
    BTN_HOVER       = QColor(100, 180, 255)
    BTN_PERIGO      = QColor(255, 90, 90)
    BTN_SUCESSO     = QColor(50, 200, 120)

    # Acento
    ACENTO          = QColor(130, 90, 255)


# ─── Estado da célula ─────────────────────────────────────────────────

class EstadoCelula(Enum):
    LIVRE    = auto()
    OBSTACULO= auto()
    ABERTO   = auto()
    FECHADO  = auto()
    CAMINHO  = auto()
    ATUAL    = auto()
    INICIO   = auto()
    OBJETIVO = auto()


# ─── Gerador A* (passo a passo) ──────────────────────────────────────

def heuristica(a, b):
    """Distância Manhattan."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star_gerador(mapa, inicio, objetivo):
    """
    Versão geradora do A* que produz o estado a cada passo.
    Cada yield entrega:
      (tipo, dados)
    onde tipo pode ser:
      'explorar'  -> dados = (pos_atual, abertos_set, fechados_set, custo_g, custo_f)
      'caminho'   -> dados = lista de posições do caminho
      'sem_caminho' -> dados = None
    """
    linhas = len(mapa)
    colunas = len(mapa[0])

    fila = []
    heapq.heappush(fila, (0, inicio))

    veio_de = {}
    custo_g = {inicio: 0}
    custo_f = {inicio: heuristica(inicio, objetivo)}

    abertos = {inicio}
    fechados = set()

    while fila:
        _, atual = heapq.heappop(fila)

        if atual in fechados:
            continue

        abertos.discard(atual)
        fechados.add(atual)

        # Entrega estado atual para visualização
        yield ('explorar', (atual, set(abertos), set(fechados), dict(custo_g), dict(custo_f)))

        if atual == objetivo:
            caminho = []
            pos = atual
            while pos in veio_de:
                caminho.append(pos)
                pos = veio_de[pos]
            caminho.append(inicio)
            caminho.reverse()
            yield ('caminho', caminho)
            return

        x, y = atual
        vizinhos = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]

        for nx, ny in vizinhos:
            if 0 <= nx < linhas and 0 <= ny < colunas:
                if mapa[nx][ny] == 1:
                    continue
                if (nx, ny) in fechados:
                    continue

                novo_custo = custo_g[atual] + 1

                if (nx, ny) not in custo_g or novo_custo < custo_g[(nx, ny)]:
                    custo_g[(nx, ny)] = novo_custo
                    f = novo_custo + heuristica((nx, ny), objetivo)
                    custo_f[(nx, ny)] = f
                    heapq.heappush(fila, (f, (nx, ny)))
                    abertos.add((nx, ny))
                    veio_de[(nx, ny)] = atual

    yield ('sem_caminho', None)


# ─── Widget da célula ─────────────────────────────────────────────────

class CelulaWidget(QWidget):
    """Widget individual de cada célula do grid."""

    def __init__(self, linha, coluna, parent_grid):
        super().__init__()
        self.linha = linha
        self.coluna = coluna
        self.parent_grid = parent_grid
        self.estado = EstadoCelula.LIVRE
        self.g_custo = None
        self.f_custo = None
        self.setMinimumSize(60, 60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _cor_base(self):
        cores = {
            EstadoCelula.LIVRE:     Cores.LIVRE,
            EstadoCelula.OBSTACULO: Cores.OBSTACULO,
            EstadoCelula.ABERTO:    Cores.ABERTO,
            EstadoCelula.FECHADO:   Cores.FECHADO,
            EstadoCelula.CAMINHO:   Cores.CAMINHO,
            EstadoCelula.ATUAL:     Cores.ATUAL,
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

        # Custos g e f
        elif self.g_custo is not None and self.estado not in (EstadoCelula.OBSTACULO, EstadoCelula.LIVRE):
            font_small = QFont("Segoe UI", 7)
            p.setFont(font_small)

            # g no canto superior esquerdo
            p.setPen(QPen(QColor(255, 255, 255, 180)))
            p.drawText(margem + 4, margem + 2, w // 2, h // 2,
                       Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                       f"g:{self.g_custo}")

            # f no canto inferior direito
            if self.f_custo is not None:
                p.setPen(QPen(QColor(255, 255, 200, 160)))
                p.drawText(w // 2 - 4, h // 2 - 2, w // 2 - margem, h // 2 - margem,
                           Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
                           f"f:{self.f_custo}")

        p.end()

    def mousePressEvent(self, event):
        self.parent_grid.celula_clicada(self.linha, self.coluna)


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
        self.editavel = True
        self.modo_edicao = 'obstaculo'  # 'obstaculo', 'inicio', 'objetivo'
        self._callback_mudanca = None

        layout = QGridLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(10, 10, 10, 10)

        for i in range(self.linhas):
            for j in range(self.colunas):
                cel = CelulaWidget(i, j, self)
                if (i, j) == inicio:
                    cel.estado = EstadoCelula.INICIO
                elif (i, j) == objetivo:
                    cel.estado = EstadoCelula.OBJETIVO
                elif mapa[i][j] == 1:
                    cel.estado = EstadoCelula.OBSTACULO
                layout.addWidget(cel, i, j)
                self.celulas[(i, j)] = cel

        self.setLayout(layout)

    def set_callback_mudanca(self, cb):
        self._callback_mudanca = cb

    def celula_clicada(self, linha, coluna):
        if not self.editavel:
            return

        pos = (linha, coluna)

        if self.modo_edicao == 'inicio':
            # Remove início antigo
            old = self.inicio
            self.celulas[old].estado = EstadoCelula.LIVRE
            self.celulas[old].update()
            # Novo início
            self.inicio = pos
            self.mapa[linha][coluna] = 0
            self.celulas[pos].estado = EstadoCelula.INICIO
            self.celulas[pos].update()

        elif self.modo_edicao == 'objetivo':
            old = self.objetivo
            self.celulas[old].estado = EstadoCelula.LIVRE
            self.celulas[old].update()
            self.objetivo = pos
            self.mapa[linha][coluna] = 0
            self.celulas[pos].estado = EstadoCelula.OBJETIVO
            self.celulas[pos].update()

        else:  # obstaculo toggle
            if pos == self.inicio or pos == self.objetivo:
                return
            if self.mapa[linha][coluna] == 0:
                self.mapa[linha][coluna] = 1
                self.celulas[pos].estado = EstadoCelula.OBSTACULO
            else:
                self.mapa[linha][coluna] = 0
                self.celulas[pos].estado = EstadoCelula.LIVRE
            self.celulas[pos].update()

        if self._callback_mudanca:
            self._callback_mudanca()

    def resetar_visual(self):
        """Reseta o visual para o estado do mapa atual."""
        for i in range(self.linhas):
            for j in range(self.colunas):
                cel = self.celulas[(i, j)]
                cel.g_custo = None
                cel.f_custo = None
                if (i, j) == self.inicio:
                    cel.estado = EstadoCelula.INICIO
                elif (i, j) == self.objetivo:
                    cel.estado = EstadoCelula.OBJETIVO
                elif self.mapa[i][j] == 1:
                    cel.estado = EstadoCelula.OBSTACULO
                else:
                    cel.estado = EstadoCelula.LIVRE
                cel.update()


# ─── Legenda ──────────────────────────────────────────────────────────

class LegendaItem(QWidget):
    def __init__(self, cor, texto):
        super().__init__()
        self.cor = cor
        self.texto = texto
        self.setFixedHeight(24)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Quadradinho colorido
        p.setBrush(QBrush(self.cor))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 4, 16, 16, 3, 3)

        # Texto
        p.setPen(QPen(Cores.TEXTO_SECUNDARIO))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(22, 0, 200, 24, Qt.AlignmentFlag.AlignVCenter, self.texto)
        p.end()


# ─── Janela Principal ────────────────────────────────────────────────

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 Visualização A* — Busca Heurística")
        self.setMinimumSize(750, 650)

        # Estilo global
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {Cores.BG_ESCURO.name()};
            }}
            QWidget {{
                color: {Cores.TEXTO_PRIMARIO.name()};
                font-family: 'Segoe UI', sans-serif;
            }}
            QPushButton {{
                background-color: {Cores.BG_CARD.name()};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: 600;
                color: {Cores.TEXTO_PRIMARIO.name()};
            }}
            QPushButton:hover {{
                background-color: {Cores.BTN_PRIMARIO.name()};
                border-color: {Cores.BTN_HOVER.name()};
            }}
            QPushButton:pressed {{
                background-color: {Cores.ACENTO.name()};
            }}
            QPushButton:disabled {{
                background-color: {Cores.BG_PAINEL.name()};
                color: {Cores.TEXTO_SECUNDARIO.name()};
                border-color: rgba(255, 255, 255, 0.03);
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {Cores.BG_CARD.name()};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {Cores.BTN_PRIMARIO.name()};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {Cores.ACENTO.name()};
                border-radius: 3px;
            }}
            QLabel {{
                font-size: 12px;
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

        # ─── Área central (grid + painel lateral) ─────────────
        area_central = QHBoxLayout()
        area_central.setSpacing(16)

        # Grid
        self.grid = GridWidget(mapa, inicio, objetivo)
        self.grid.set_callback_mudanca(self._ao_mudar_mapa)

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

        area_central.addWidget(grid_frame, stretch=3)

        # ─── Painel lateral ───────────────────────────────────
        painel = QFrame()
        painel.setStyleSheet(f"""
            QFrame {{
                background-color: {Cores.BG_PAINEL.name()};
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            }}
        """)
        painel_layout = QVBoxLayout(painel)
        painel_layout.setContentsMargins(16, 16, 16, 16)
        painel_layout.setSpacing(10)

        # Status
        self.lbl_status = QLabel("⏸  Pronto para iniciar")
        self.lbl_status.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_status.setWordWrap(True)
        painel_layout.addWidget(self.lbl_status)

        # Info passos
        self.lbl_passos = QLabel("Passos: 0")
        self.lbl_passos.setStyleSheet(f"color: {Cores.TEXTO_SECUNDARIO.name()};")
        painel_layout.addWidget(self.lbl_passos)

        self.lbl_abertos = QLabel("Abertos: 0")
        self.lbl_abertos.setStyleSheet(f"color: {Cores.ABERTO.name()};")
        painel_layout.addWidget(self.lbl_abertos)

        self.lbl_fechados = QLabel("Fechados: 0")
        self.lbl_fechados.setStyleSheet(f"color: {Cores.FECHADO.name()};")
        painel_layout.addWidget(self.lbl_fechados)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(255,255,255,0.08); max-height: 1px;")
        painel_layout.addWidget(sep)

        # Legenda
        lbl_legenda = QLabel("Legenda")
        lbl_legenda.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painel_layout.addWidget(lbl_legenda)

        legendas = [
            (Cores.INICIO,    "A — Início"),
            (Cores.OBJETIVO,  "★ — Objetivo"),
            (Cores.OBSTACULO, "✕ — Obstáculo"),
            (Cores.ABERTO,    "Aberto (na fila)"),
            (Cores.FECHADO,   "Fechado (visitado)"),
            (Cores.ATUAL,     "Nó atual"),
            (Cores.CAMINHO,   "Caminho final"),
        ]
        for cor, texto in legendas:
            painel_layout.addWidget(LegendaItem(cor, texto))

        # Separador
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: rgba(255,255,255,0.08); max-height: 1px;")
        painel_layout.addWidget(sep2)

        # Modo de edição
        lbl_edicao = QLabel("Modo de Edição")
        lbl_edicao.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painel_layout.addWidget(lbl_edicao)

        self.btn_modo_obstaculo = QPushButton("✕  Obstáculo")
        self.btn_modo_inicio = QPushButton("A  Início")
        self.btn_modo_objetivo = QPushButton("★  Objetivo")

        self.btn_modo_obstaculo.setStyleSheet(f"""
            QPushButton {{
                background-color: {Cores.ACENTO.name()};
                border: 2px solid {Cores.ACENTO.name()};
            }}
        """)

        self.btn_modo_obstaculo.clicked.connect(lambda: self._set_modo('obstaculo'))
        self.btn_modo_inicio.clicked.connect(lambda: self._set_modo('inicio'))
        self.btn_modo_objetivo.clicked.connect(lambda: self._set_modo('objetivo'))

        for btn in [self.btn_modo_obstaculo, self.btn_modo_inicio, self.btn_modo_objetivo]:
            btn.setFixedHeight(32)
            painel_layout.addWidget(btn)

        painel_layout.addStretch()

        area_central.addWidget(painel, stretch=1)
        layout_principal.addLayout(area_central, stretch=1)

        # ─── Barra de controles inferior ──────────────────────
        barra = QFrame()
        barra.setStyleSheet(f"""
            QFrame {{
                background-color: {Cores.BG_PAINEL.name()};
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            }}
        """)
        barra_layout = QHBoxLayout(barra)
        barra_layout.setContentsMargins(16, 10, 16, 10)
        barra_layout.setSpacing(10)

        self.btn_iniciar = QPushButton("▶  Iniciar")
        self.btn_iniciar.setStyleSheet(f"""
            QPushButton {{
                background-color: {Cores.BTN_SUCESSO.name()};
                color: white;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: #28d87a; }}
        """)
        self.btn_iniciar.clicked.connect(self.iniciar)
        barra_layout.addWidget(self.btn_iniciar)

        self.btn_pausar = QPushButton("⏸  Pausar")
        self.btn_pausar.setEnabled(False)
        self.btn_pausar.clicked.connect(self.pausar)
        barra_layout.addWidget(self.btn_pausar)

        self.btn_passo = QPushButton("⏭  Passo")
        self.btn_passo.clicked.connect(self.passo_unico)
        barra_layout.addWidget(self.btn_passo)

        self.btn_reiniciar = QPushButton("↺  Reiniciar")
        self.btn_reiniciar.setStyleSheet(f"""
            QPushButton {{
                background-color: {Cores.BTN_PERIGO.name()};
                color: white;
            }}
            QPushButton:hover {{ background-color: #ff6060; }}
        """)
        self.btn_reiniciar.clicked.connect(self.reiniciar)
        barra_layout.addWidget(self.btn_reiniciar)

        # Separador vertical
        sep_v = QFrame()
        sep_v.setFrameShape(QFrame.Shape.VLine)
        sep_v.setStyleSheet("background-color: rgba(255,255,255,0.1); max-width: 1px;")
        barra_layout.addWidget(sep_v)

        # Slider de velocidade
        lbl_vel = QLabel("🕐 Velocidade:")
        lbl_vel.setStyleSheet(f"color: {Cores.TEXTO_SECUNDARIO.name()};")
        barra_layout.addWidget(lbl_vel)

        self.slider_vel = QSlider(Qt.Orientation.Horizontal)
        self.slider_vel.setRange(1, 20)
        self.slider_vel.setValue(5)
        self.slider_vel.setFixedWidth(120)
        self.slider_vel.valueChanged.connect(self._atualizar_velocidade)
        barra_layout.addWidget(self.slider_vel)

        self.lbl_vel_valor = QLabel("200ms")
        self.lbl_vel_valor.setFixedWidth(50)
        self.lbl_vel_valor.setStyleSheet(f"color: {Cores.TEXTO_SECUNDARIO.name()};")
        barra_layout.addWidget(self.lbl_vel_valor)

        layout_principal.addWidget(barra)

        # ─── Timer de animação ────────────────────────────────
        self.timer = QTimer()
        self.timer.timeout.connect(self._proximo_passo)
        self.intervalo = 200  # ms

        # ─── Estado do algoritmo ──────────────────────────────
        self.gerador = None
        self.passos = 0
        self.rodando = False
        self.finalizado = False

    def _set_modo(self, modo):
        self.grid.modo_edicao = modo
        estilo_normal = f"""
            QPushButton {{
                background-color: {Cores.BG_CARD.name()};
                border: 1px solid rgba(255, 255, 255, 0.08);
            }}
        """
        estilo_ativo = f"""
            QPushButton {{
                background-color: {Cores.ACENTO.name()};
                border: 2px solid {Cores.ACENTO.name()};
            }}
        """
        self.btn_modo_obstaculo.setStyleSheet(estilo_ativo if modo == 'obstaculo' else estilo_normal)
        self.btn_modo_inicio.setStyleSheet(estilo_ativo if modo == 'inicio' else estilo_normal)
        self.btn_modo_objetivo.setStyleSheet(estilo_ativo if modo == 'objetivo' else estilo_normal)

    def _ao_mudar_mapa(self):
        """Reseta a execução ao modificar o mapa."""
        if self.rodando:
            self.timer.stop()
            self.rodando = False
        self.gerador = None
        self.finalizado = False
        self.passos = 0
        self.grid.resetar_visual()
        self.lbl_status.setText("⏸  Mapa modificado — pronto")
        self.lbl_passos.setText("Passos: 0")
        self.lbl_abertos.setText("Abertos: 0")
        self.lbl_fechados.setText("Fechados: 0")
        self.btn_iniciar.setEnabled(True)
        self.btn_pausar.setEnabled(False)
        self.btn_passo.setEnabled(True)

    def _atualizar_velocidade(self, val):
        self.intervalo = max(20, 420 - val * 20)
        self.lbl_vel_valor.setText(f"{self.intervalo}ms")
        if self.rodando:
            self.timer.setInterval(self.intervalo)

    def _criar_gerador(self):
        """Cria um novo gerador do A*."""
        self.grid.resetar_visual()
        self.passos = 0
        self.finalizado = False
        self.gerador = a_star_gerador(
            self.grid.mapa,
            self.grid.inicio,
            self.grid.objetivo
        )

    def iniciar(self):
        if self.finalizado:
            self._criar_gerador()

        if self.gerador is None:
            self._criar_gerador()

        self.rodando = True
        self.grid.editavel = False
        self.timer.start(self.intervalo)
        self.lbl_status.setText("▶  Explorando...")
        self.lbl_status.setStyleSheet(f"color: {Cores.ATUAL.name()};")
        self.btn_iniciar.setEnabled(False)
        self.btn_pausar.setEnabled(True)
        self.btn_passo.setEnabled(False)

    def pausar(self):
        self.rodando = False
        self.timer.stop()
        self.lbl_status.setText("⏸  Pausado")
        self.lbl_status.setStyleSheet(f"color: {Cores.TEXTO_PRIMARIO.name()};")
        self.btn_iniciar.setEnabled(True)
        self.btn_pausar.setEnabled(False)
        self.btn_passo.setEnabled(True)

    def passo_unico(self):
        """Avança um único passo."""
        if self.finalizado:
            self._criar_gerador()

        if self.gerador is None:
            self._criar_gerador()

        self.grid.editavel = False
        self._proximo_passo()

    def reiniciar(self):
        self.timer.stop()
        self.rodando = False
        self.gerador = None
        self.finalizado = False
        self.passos = 0
        self.grid.editavel = True
        self.grid.resetar_visual()
        self.lbl_status.setText("⏸  Pronto para iniciar")
        self.lbl_status.setStyleSheet(f"color: {Cores.TEXTO_PRIMARIO.name()};")
        self.lbl_passos.setText("Passos: 0")
        self.lbl_abertos.setText("Abertos: 0")
        self.lbl_fechados.setText("Fechados: 0")
        self.btn_iniciar.setEnabled(True)
        self.btn_pausar.setEnabled(False)
        self.btn_passo.setEnabled(True)

    def _proximo_passo(self):
        """Processa o próximo passo do gerador."""
        if self.gerador is None:
            return

        try:
            tipo, dados = next(self.gerador)
        except StopIteration:
            self.timer.stop()
            self.rodando = False
            self.finalizado = True
            self.grid.editavel = True
            self.btn_iniciar.setEnabled(True)
            self.btn_pausar.setEnabled(False)
            self.btn_passo.setEnabled(True)
            return

        if tipo == 'explorar':
            atual, abertos, fechados, custo_g, custo_f = dados
            self.passos += 1

            # Atualiza todas as células
            for i in range(self.grid.linhas):
                for j in range(self.grid.colunas):
                    pos = (i, j)
                    cel = self.grid.celulas[pos]

                    if pos == self.grid.inicio:
                        cel.estado = EstadoCelula.INICIO
                    elif pos == self.grid.objetivo:
                        cel.estado = EstadoCelula.OBJETIVO
                    elif self.grid.mapa[i][j] == 1:
                        cel.estado = EstadoCelula.OBSTACULO
                    elif pos == atual:
                        cel.estado = EstadoCelula.ATUAL
                    elif pos in fechados:
                        cel.estado = EstadoCelula.FECHADO
                    elif pos in abertos:
                        cel.estado = EstadoCelula.ABERTO
                    else:
                        cel.estado = EstadoCelula.LIVRE

                    # Custos
                    if pos in custo_g:
                        cel.g_custo = custo_g[pos]
                        cel.f_custo = custo_f.get(pos)
                    else:
                        cel.g_custo = None
                        cel.f_custo = None

                    cel.update()

            self.lbl_passos.setText(f"Passos: {self.passos}")
            self.lbl_abertos.setText(f"Abertos: {len(abertos)}")
            self.lbl_fechados.setText(f"Fechados: {len(fechados)}")

        elif tipo == 'caminho':
            caminho = dados
            for pos in caminho:
                cel = self.grid.celulas[pos]
                if pos == self.grid.inicio:
                    cel.estado = EstadoCelula.INICIO
                elif pos == self.grid.objetivo:
                    cel.estado = EstadoCelula.OBJETIVO
                else:
                    cel.estado = EstadoCelula.CAMINHO
                cel.update()

            self.timer.stop()
            self.rodando = False
            self.finalizado = True
            self.grid.editavel = True
            self.lbl_status.setText(f"✅  Caminho encontrado! ({len(caminho)} passos)")
            self.lbl_status.setStyleSheet(f"color: {Cores.CAMINHO.name()};")
            self.btn_iniciar.setEnabled(True)
            self.btn_pausar.setEnabled(False)
            self.btn_passo.setEnabled(True)

        elif tipo == 'sem_caminho':
            self.timer.stop()
            self.rodando = False
            self.finalizado = True
            self.grid.editavel = True
            self.lbl_status.setText("❌  Nenhum caminho encontrado!")
            self.lbl_status.setStyleSheet(f"color: {Cores.BTN_PERIGO.name()};")
            self.btn_iniciar.setEnabled(True)
            self.btn_pausar.setEnabled(False)
            self.btn_passo.setEnabled(True)


# ─── Ponto de entrada ────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
