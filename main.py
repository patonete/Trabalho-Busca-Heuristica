import heapq  # Biblioteca usada para criar uma fila de prioridade (min-heap)

# Função heurística (distância Manhattan)
# Estima quantos passos faltam para chegar ao objetivo
def heuristica(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# Implementação do algoritmo A*
def a_star(mapa, inicio, objetivo):

    # Obtém o tamanho do mapa
    linhas = len(mapa)
    colunas = len(mapa[0])

    # Fila de prioridade que armazenará os nós a serem explorados
    fila = []

    # Adiciona o ponto inicial na fila
    heapq.heappush(fila, (0, inicio))

    # Guarda de qual nó cada posição veio
    # Será usado para reconstruir o caminho final
    veio_de = {}

    # Armazena o custo para chegar em cada posição
    custo = {inicio: 0}

    # Enquanto houver nós para explorar
    while fila:

        # Remove o nó com menor prioridade
        _, atual = heapq.heappop(fila)

        # Se chegamos ao objetivo
        if atual == objetivo:

            # Reconstrói o caminho percorrido
            caminho = []

            while atual in veio_de:
                caminho.append(atual)
                atual = veio_de[atual]

            caminho.append(inicio)
            caminho.reverse()

            return caminho

        # Coordenadas atuais
        x, y = atual

        # Possíveis movimentos:
        # baixo, cima, direita e esquerda
        vizinhos = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1)
        ]

        # Analisa cada vizinho
        for nx, ny in vizinhos:

            # Verifica se o vizinho está dentro dos limites do mapa
            if 0 <= nx < linhas and 0 <= ny < colunas:

                # Se for obstáculo (1), ignora
                if mapa[nx][ny] == 1:
                    continue

                # Calcula o custo para chegar ao vizinho
                novo_custo = custo[atual] + 1

                # Se ainda não visitamos esse nó
                # ou encontramos um caminho melhor
                if (nx, ny) not in custo or novo_custo < custo[(nx, ny)]:

                    # Atualiza o custo
                    custo[(nx, ny)] = novo_custo

                    # Calcula a prioridade do nó
                    # f(n) = g(n) + h(n)
                    prioridade = (
                        novo_custo +
                        heuristica((nx, ny), objetivo)
                    )

                    # Adiciona o vizinho à fila
                    heapq.heappush(
                        fila,
                        (prioridade, (nx, ny))
                    )

                    # Guarda o nó anterior
                    veio_de[(nx, ny)] = atual

    # Caso não exista caminho
    return None


# ==========================
# MAPA DE TESTE
# ==========================
# 0 = caminho livre
# 1 = obstáculo

mapa = [
    [0, 0, 0, 0, 0],
    [1, 1, 0, 1, 0],
    [0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0]
]

# Ponto inicial
inicio = (0, 0)

# Ponto final
objetivo = (4, 4)

# Executa o algoritmo
caminho = a_star(mapa, inicio, objetivo)

# Mostra o resultado
if caminho:
    print("Caminho encontrado:")
    print(caminho)
else:
    print("Nenhum caminho encontrado.")