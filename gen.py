#!/usr/bin/env python3
"""Generator testow do zadania "Labirynt z kluczami".

Uzycie:  g++ -O2 -std=c++17 wzor.cpp -o wzor && python3 gen.py
Tworzy foldery tests/in/ oraz tests/out/ (pliki NN.in / NN.out).
Male i srednie testy sa dodatkowo weryfikowane niezaleznym brute-force'em w Pythonie.
"""
import os
import random
import subprocess
import sys
from collections import deque

ROOT = os.path.dirname(os.path.abspath(__file__))
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
tests = []  # (opis, siatka jako lista list znakow)


def grid(s):
    return [list(r) for r in s.strip().split("\n")]


def add(name, rows):
    tests.append((name, rows))


# ---------------------------------------------------------------- brute force
def brute(rows):
    n, m = len(rows), len(rows[0])
    for i in range(n):
        for j in range(m):
            if rows[i][j] == "S":
                s = (i, j)
            if rows[i][j] == "M":
                t = (i, j)
    seen = {(s[0], s[1], frozenset())}
    q = deque([(s[0], s[1], frozenset(), 0)])
    while q:
        x, y, ks, d = q.popleft()
        if (x, y) == t:
            return d
        for dx, dy in DIRS:
            a, b = x + dx, y + dy
            if not (0 <= a < n and 0 <= b < m):
                continue
            c = rows[a][b]
            if c == "#":
                continue
            if "A" <= c <= "F" and c.lower() not in ks:
                continue
            nk = ks | {c} if "a" <= c <= "f" else ks
            key = (a, b, nk)
            if key in seen:
                continue
            seen.add(key)
            q.append((a, b, nk, d + 1))
    return -1


# ------------------------------------------------------------ generatory losowe
def rand_grid(rng, n, m, k, wall, keyp, doorp):
    g = []
    for _ in range(n):
        row = []
        for _ in range(m):
            r = rng.random()
            if r < wall:
                row.append("#")
            elif r < wall + keyp:
                row.append(rng.choice("abcdef"[:k]))
            elif r < wall + keyp + doorp:
                row.append(rng.choice("ABCDEF"[:k]))
            else:
                row.append(".")
        g.append(row)
    cells = [(i, j) for i in range(n) for j in range(m)]
    a, b = rng.sample(cells, 2)
    g[a[0]][a[1]] = "S"
    g[b[0]][b[1]] = "M"
    return g


def until(rng, make, want, tries=300):
    """Losuje, az brute da pozadany rodzaj odpowiedzi ('ok' = osiagalne, 'no' = -1, None = dowolne)."""
    g = None
    for _ in range(tries):
        g = make()
        if want is None:
            return g
        r = brute(g)
        if (want == "ok" and r != -1) or (want == "no" and r == -1):
            return g
    raise AssertionError("until(): nie udalo sie wylosowac planszy typu %r" % want)


# ------------------------------------------------------- labirynt idealny + drzwi
def perfect_maze(h, w, rng):
    g = [["#"] * w for _ in range(h)]
    g[1][1] = "."
    st = [(1, 1)]
    while st:
        x, y = st[-1]
        nb = []
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            a, b = x + dx, y + dy
            if 0 < a < h - 1 and 0 < b < w - 1 and g[a][b] == "#":
                nb.append((a, b, dx, dy))
        if not nb:
            st.pop()
            continue
        a, b, dx, dy = rng.choice(nb)
        g[x + dx // 2][y + dy // 2] = "."
        g[a][b] = "."
        st.append((a, b))
    return g


def reach(g, h, w, src, opened):
    dist = [[-1] * w for _ in range(h)]
    dist[src[0]][src[1]] = 0
    q = deque([src])
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS:
            a, b = x + dx, y + dy
            if 0 <= a < h and 0 <= b < w and dist[a][b] < 0:
                c = g[a][b]
                if c == "#":
                    continue
                if "A" <= c <= "F" and c.lower() not in opened:
                    continue
                dist[a][b] = dist[x][y] + 1
                q.append((a, b))
    return dist


def gen_maze(h, w, k, rng, mode="ok", decoys=0):
    """Drzwi leza na jedynej sciezce S->M (labirynt jest drzewem), klucz j lezy
    gdzies osiagalnym przed drzwiami j (czesto w dalekiej slepej uliczce).
    mode: 'ok' - rozwiazanie istnieje; 'nokey' - brak klucza do ostatnich drzwi;
          'behind' - klucz do ostatnich drzwi lezy ZA tymi drzwiami."""
    g = perfect_maze(h, w, rng)
    S, M = (1, 1), (h - 2, w - 2)
    d = reach(g, h, w, S, set())
    path = [M]
    x, y = M
    while (x, y) != S:
        for dx, dy in DIRS:
            a, b = x + dx, y + dy
            if 0 <= a < h and 0 <= b < w and d[a][b] == d[x][y] - 1:
                x, y = a, b
                break
        path.append((x, y))
    path.reverse()
    L = len(path)
    idxs = sorted(rng.sample(range(2, L - 2), k))
    letters = list("abcdef"[:k])
    rng.shuffle(letters)
    for i, l in zip(idxs, letters):
        g[path[i][0]][path[i][1]] = l.upper()
    g[S[0]][S[1]] = "S"
    g[M[0]][M[1]] = "M"

    opened = set()
    for j, l in enumerate(letters):
        if mode == "nokey" and j == k - 1:
            break
        dist = reach(g, h, w, S, opened)
        if mode == "behind" and j == k - 1:
            full = reach(g, h, w, S, opened | {l})
            cand = [(i, jj) for i in range(h) for jj in range(w)
                    if full[i][jj] >= 0 and dist[i][jj] < 0 and g[i][jj] == "."]
        else:
            cand = [(i, jj) for i in range(h) for jj in range(w)
                    if dist[i][jj] >= 0 and g[i][jj] == "."]
        cand.sort(key=lambda p: max(dist[p[0]][p[1]], 0))
        p = rng.choice(cand[len(cand) * 3 // 4:])
        g[p[0]][p[1]] = l
        opened.add(l)

    pool = [c for c in "abcdef"[:k] if not (mode != "ok" and c == letters[-1])]
    empt = [(i, j) for i in range(h) for j in range(w) if g[i][j] == "."]
    for p in rng.sample(empt, decoys):
        g[p[0]][p[1]] = rng.choice(pool)
    return g


# ------------------------------------------------- pokoje oddzielone scianami z drzwiami
def gen_rooms(n, m, k, rng, mode="ok"):
    g = [["."] * m for _ in range(n)]
    cols = [(m * (i + 1)) // (k + 1) for i in range(k)]
    letters = list("abcdef"[:k])
    rng.shuffle(letters)
    for c, l in zip(cols, letters):
        for r in range(n):
            g[r][c] = "#"
        g[rng.randrange(n)][c] = l.upper()
    S = (rng.randrange(n), rng.randrange(0, cols[0]))
    M = (rng.randrange(n), rng.randrange(cols[-1] + 1, m))
    g[S[0]][S[1]] = "S"
    g[M[0]][M[1]] = "M"
    for j, l in enumerate(letters):
        if mode == "nokey" and j == k - 1:
            continue
        room = rng.randrange(0, j + 1)
        lo = 0 if room == 0 else cols[room - 1] + 1
        hi = cols[room]
        while True:
            x, y = rng.randrange(n), rng.randrange(lo, hi)
            if g[x][y] == ".":
                g[x][y] = l
                break
    return g


def comb(order, depth=4):
    """Korytarz z drzwiami; przed kazdymi drzwiami odnoga do gory z kluczem na koncu.
    Kazdy klucz jest potrzebny tylko do jednej pary drzwi, wiec pominiecie
    sprawdzania ktorychkolwiek drzwi skraca wynik."""
    w = 2 * len(order) + 2
    g = [["#"] * w for _ in range(depth + 1)]
    for c in range(w):
        g[depth][c] = "."
    g[depth][0] = "S"
    g[depth][w - 1] = "M"
    for i, l in enumerate(order):
        bc = 1 + 2 * i
        for r in range(depth):
            g[r][bc] = "."
        g[0][bc] = l
        g[depth][bc + 1] = l.upper()
    return g


# ------------------------------------------------------------------- walidacja
def validate(g):
    n, m = len(g), len(g[0])
    assert 1 <= n <= 500 and 1 <= m <= 500 and n * m >= 2
    assert all(len(r) == m for r in g)
    flat = [c for r in g for c in r]
    assert flat.count("S") == 1 and flat.count("M") == 1
    assert all(c in "#.SMabcdefABCDEF" for c in flat)


# ---------------------------------------------------------------------- testy
def build():
    rng = random.Random(20261122)

    # --- recznie (pierwsze dwa to przyklady z tresci)
    add("przyklad 1: klucz w slepej uliczce, drzwi blokuja meta", grid("""
S...#M
.##.#A
.a#.#.
.##...
......"""))
    add("przyklad 2: klucz lezy za drzwiami tej samej litery", grid("S.AaM"))
    add("sasiednie pola", grid("SM"))
    add("sciana miedzy S i M", grid("S#M"))
    add("kolejne drzwi, klucze po drodze", grid("S.a.A.b.B.M"))
    add("drzwi bez klucza, trzeba isc naokolo", grid("""
S.A.M
.###.
....."""))
    add("klucze i drzwi na przemian", grid("SaAbBM"))
    add("klucz do drzwi lezy za drzwiami innej litery", grid("SbAaBM"))

    # --- losowe male (weryfikowane brute-force'em)
    for i in range(10):
        n, m = rng.randint(1, 7), rng.randint(2, 7)
        k = rng.randint(1, 6)
        want = "ok" if i % 3 != 2 else None
        g = until(rng, lambda: rand_grid(rng, n, m, k, 0.2, 0.12, 0.15), want)
        add("losowy maly %d" % (i + 1), g)

    # --- losowe srednie
    for i in range(6):
        n, m = rng.randint(15, 35), rng.randint(15, 35)
        k = rng.randint(3, 6)
        want = "no" if i == 5 else "ok"
        g = until(rng, lambda: rand_grid(rng, n, m, k, 0.25, 0.03, 0.08), want)
        add("losowy sredni %d" % (i + 1), g)

    # --- duze
    add("labirynt 499x499, 6 par klucz-drzwi, wiele falszywych kluczy",
        gen_maze(499, 499, 6, rng, "ok", 60))
    add("labirynt 301x499, 3 pary klucz-drzwi",
        gen_maze(301, 499, 3, rng, "ok", 30))
    add("labirynt 499x499, brak klucza do ostatnich drzwi (-1)",
        gen_maze(499, 499, 6, rng, "nokey", 60))
    add("labirynt 499x499, klucz za wlasnymi drzwiami (-1)",
        gen_maze(499, 499, 5, rng, "behind", 60))
    add("pokoje 500x500, 6 drzwi, klucze w roznych pokojach",
        gen_rooms(500, 500, 6, rng, "ok"))
    add("pokoje 500x500, brak ostatniego klucza (-1, pelne przeszukanie)",
        gen_rooms(500, 500, 6, rng, "nokey"))
    g = [["."] * 500 for _ in range(500)]
    g[0][0], g[499][499] = "S", "M"
    add("pusta plansza 500x500, bez kluczy", g)
    add("losowa plansza 500x500 z kluczami i drzwiami",
        rand_grid(rng, 500, 500, 6, 0.2, 0.01, 0.05))
    add("korytarz 1x500", [list("S" + "".join(rng.choice(".abcdef") for _ in range(498)) + "M")])
    col = ["S"] + [rng.choice("....") for _ in range(498)] + ["M"]
    add("korytarz 500x1", [[c] for c in col])

    # --- uzupelnienie po testach mutacyjnych (dopisane na koncu, numeracja bez zmian)
    add("powrot przez pole startowe po klucz", grid("aS.AM"))
    add("jeden klucz otwiera dwoje drzwi tej samej litery", grid("SaA.AM"))
    add("wszystkie litery po kolei", grid("SfFeEdDcCbBaAM"))
    add("pionowo 2x1", grid("S\nM"))
    add("powrot przez S w 2D, klucz za plecami, drzwi jedyna droga", grid("""
aS.#
##.#
##AM"""))
    for l in "ABCDEF":
        add("drzwi %s bez klucza (-1)" % l, grid("S.%s.M" % l))
    rng2 = random.Random(7)
    for _ in range(2):
        order = list("abcdef")
        rng2.shuffle(order)
        add("grzebien: 6 odnog z kluczami i 6 drzwi", comb(order))
    add("grzebien: dluzsze odnogi", comb(list("fedcba"), 12))

    # --- poprawki (testy 49-54): wynik > 65535, maksymalna przestrzen stanow
    rng3 = random.Random(57)
    def serp(n=500, m=500):
        g = [["#"]*m for _ in range(n)]
        for i in range(0, n, 2):
            for j in range(m): g[i][j] = "."
            if i+2 < n: g[i+1][m-1 if (i//2) % 2 == 0 else 0] = "."
        return g
    # 49: waz 500x500 bez kluczy, wynik > 65535 (lapie int16/uint16 w odleglosciach)
    g = serp(); g[0][0] = "S"; g[498][499 if (498//2) % 2 == 0 else 0] = "M"; add("waz 500x500 bez kluczy, wynik > 65535", g)
    # 50: waz, S w srodku, klucz na samym poczatku weza, drzwi tuz za S (w strone konca) -> powrot ~2x
    g = serp(); cells = []
    for i in range(0, 500, 2):
        row = [(i, j) for j in range(500)]
        if (i//2) % 2: row.reverse()
        cells += row
        if i+2 < 500: cells.append((i+1, 499 if (i//2) % 2 == 0 else 0))
    L = len(cells); s = L//2
    g[cells[0][0]][cells[0][1]] = "a"; g[cells[s][0]][cells[s][1]] = "S"
    g[cells[s+1][0]][cells[s+1][1]] = "A"; g[cells[-1][0]][cells[-1][1]] = "M"; add("waz 500x500, S w srodku, klucz na poczatku, drzwi za S (wynik ~187k)", g)
    # 51: maksymalna przestrzen stanow: pusta 500x500, po 3 kopie kazdego klucza, meta zamurowana -> -1
    g = [["."]*500 for _ in range(500)]
    for l in "abcdef":
        for _ in range(3):
            while True:
                x, y = rng3.randrange(500), rng3.randrange(500)
                if g[x][y] == ".": g[x][y] = l; break
    g[0][0] = "S"; g[250][250] = "M"
    for a, b in ((249,250),(251,250),(250,249),(250,251)): g[a][b] = "#"
    add("pusta 500x500, 18 kluczy, meta zamurowana (-1, ~16 mln stanow)", g)
    # 52: jw., ale meta otoczona drzwiami F, jedyny klucz f w rogu (499,499)
    g = [r[:] for r in tests[-1][1]]
    for (a, b), d in zip(((249,250),(251,250),(250,249),(250,251)), "FFFF"): g[a][b] = d
    for x in range(500):
        for y in range(500):
            if g[x][y] == "f": g[x][y] = "."
    g[499][499] = "f"; add("pusta 500x500, meta za drzwiami F, klucz f w rogu (~12 mln stanow)", g)
    # 53: klucz tylko "za meta" - nie trzeba go brac; drzwi bez klucza obok S; 1x7
    add("klucz za meta, drzwi bez klucza przy S", [list("AS..Ma.")])
    # 54: S i M sasiaduja przez drzwi A; objazd i droga przez klucz a daja po 4 (nie 1)
    add("S i M rozdzielone drzwiami A; objazd i droga po klucz - obie po 4 ruchy", [list("aSAM"), list("#..."), list("....")])


def main():
    sol = os.environ.get("SOL") or os.path.join(ROOT, "wzor")
    if not os.path.exists(sol):
        sys.exit("Najpierw skompiluj: g++ -O2 -std=c++17 wzor.cpp -o wzor (lub ustaw zmienna SOL)")
    os.makedirs(os.path.join(ROOT, "tests", "in"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "tests", "out"), exist_ok=True)
    build()
    for idx, (name, g) in enumerate(tests, 1):
        validate(g)
        text = "%d %d\n%s\n" % (len(g), len(g[0]), "\n".join("".join(r) for r in g))
        fin = os.path.join(ROOT, "tests", "in", "%02d.in" % idx)
        fout = os.path.join(ROOT, "tests", "out", "%02d.out" % idx)
        with open(fin, "w") as f:
            f.write(text)
        res = subprocess.run([sol], input=text, capture_output=True, text=True, check=True).stdout.strip()
        if len(g) * len(g[0]) <= 2500:
            b = brute(g)
            assert str(b) == res, "ROZBIEZNOSC w tescie %d: wzor=%s brute=%s" % (idx, res, b)
        with open(fout, "w") as f:
            f.write(res + "\n")
        print("%02d  %3dx%-3d  odp=%-7s %s" % (idx, len(g), len(g[0]), res, name))


if __name__ == "__main__":
    main()
