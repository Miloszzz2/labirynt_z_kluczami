// Labirynt z kluczami - wzorcowe rozwiazanie
// BFS po stanach (x, y, maska kluczy). Zlozonosc: O(n * m * 2^6).
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<string> g(n);
    for (auto &row : g) cin >> row;

    int sx = -1, sy = -1, mx = -1, my = -1;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++) {
            if (g[i][j] == 'S') sx = i, sy = j;
            if (g[i][j] == 'M') mx = i, my = j;
        }

    // stan zakodowany jako (komorka << 6) | maska
    auto id = [&](int x, int y, int mask) { return ((x * m + y) << 6) | mask; };

    const size_t total = (size_t)n * m * 64;
    vector<int> dist(total, -1);
    vector<int> q(total);
    size_t head = 0, tail = 0;

    int start = id(sx, sy, 0);
    dist[start] = 0;
    q[tail++] = start;

    const int dx[4] = {1, -1, 0, 0};
    const int dy[4] = {0, 0, 1, -1};

    while (head < tail) {
        int cur = q[head++];
        int mask = cur & 63;
        int cell = cur >> 6;
        int x = cell / m, y = cell % m;

        if (x == mx && y == my) {
            cout << dist[cur] << "\n";
            return 0;
        }

        for (int d = 0; d < 4; d++) {
            int nx = x + dx[d], ny = y + dy[d];
            if (nx < 0 || nx >= n || ny < 0 || ny >= m) continue;
            char c = g[nx][ny];
            if (c == '#') continue;

            int nmask = mask;
            if (c >= 'A' && c <= 'F') {
                if (!((mask >> (c - 'A')) & 1)) continue;  // brak klucza do drzwi
            } else if (c >= 'a' && c <= 'f') {
                nmask |= 1 << (c - 'a');  // podnosimy klucz
            }

            int nid = id(nx, ny, nmask);
            if (dist[nid] != -1) continue;
            dist[nid] = dist[cur] + 1;
            q[tail++] = nid;
        }
    }

    cout << -1 << "\n";
    return 0;
}
