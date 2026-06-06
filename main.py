import heapq

mapa = [
    [0, 0, 0],
    [0, 1, 0],
    [0, 0, 0]
]

inicio = (0, 0)
objetivo = (2, 2)

def heuristica(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(mapa, inicio, objetivo):

    fila = []
    heapq.heappush(fila, (0, inicio))

    visitados = set()

    while fila:

        _, atual = heapq.heappop(fila)

        if atual in visitados:
            continue

        visitados.add(atual)

        print("Visitando:", atual)

        if atual == objetivo:
            return [inicio, objetivo]

        x, y = atual

        vizinhos = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1)
        ]

        for nx, ny in vizinhos:

            if 0 <= nx < len(mapa) and 0 <= ny < len(mapa[0]):

                if mapa[nx][ny] == 0:

                    prioridade = heuristica((nx, ny), objetivo)

                    heapq.heappush(
                        fila,
                        (prioridade, (nx, ny))
                    )

    return None

caminho = a_star(mapa, inicio, objetivo)

print("Resultado:")
print(caminho)