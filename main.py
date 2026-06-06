# matriz simples pra teste
mapa = [
    [0, 0, 0],
    [0, 1, 0],
    [0, 0, 0]
]

inicio = (0, 0)
objetivo = (2, 2)

def heuristica(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

distancia = heuristica(inicio, objetivo)

print("Início:", inicio)
print("Objetivo:", objetivo)
print("Distância estimada:", distancia)