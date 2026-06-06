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

    visitados = set()
    visitados.add(inicio)

    atual = inicio

    x, y = atual

    vizinhos = [
        (x + 1, y),
        (x - 1, y),
        (x, y + 1),
        (x, y - 1)
    ]

    vizinhos_validos = []

    for nx, ny in vizinhos:

        if 0 <= nx < len(mapa) and 0 <= ny < len(mapa[0]):

            if mapa[nx][ny] == 0:

                vizinhos_validos.append((nx, ny))

    print("Visitados:", visitados)
    print("Vizinhos válidos:", vizinhos_validos)

    return [inicio]

caminho = a_star(mapa, inicio, objetivo)

print("Caminho encontrado:")
print(caminho)