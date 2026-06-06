import heapq

# Versão mais próxima da implementação final

def heuristica(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(mapa, inicio, objetivo):

    linhas = len(mapa)
    colunas = len(mapa[0])

    fila = []
    heapq.heappush(fila, (0, inicio))

    veio_de = {}
    custo = {inicio: 0}

    while fila:

        _, atual = heapq.heappop(fila)

        if atual == objetivo:

            caminho = []

            while atual in veio_de:
                caminho.append(atual)
                atual = veio_de[atual]

            caminho.append(inicio)
            caminho.reverse()

            return caminho

        x, y = atual

        vizinhos = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1)
        ]

        for nx, ny in vizinhos:

            if 0 <= nx < linhas and 0 <= ny < colunas:

                if mapa[nx][ny] == 1:
                    continue

                novo_custo = custo[atual] + 1

                if (nx, ny) not in custo or novo_custo < custo[(nx, ny)]:

                    custo[(nx, ny)] = novo_custo

                    prioridade = (
                        novo_custo +
                        heuristica((nx, ny), objetivo)
                    )

                    heapq.heappush(
                        fila,
                        (prioridade, (nx, ny))
                    )

                    veio_de[(nx, ny)] = atual

    return None


mapa = [
    [0, 0, 0, 0, 0],
    [1, 1, 0, 1, 0],
    [0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0]
]

inicio = (0, 0)
objetivo = (4, 4)

caminho = a_star(mapa, inicio, objetivo)

print("Caminho encontrado:")
print(caminho)