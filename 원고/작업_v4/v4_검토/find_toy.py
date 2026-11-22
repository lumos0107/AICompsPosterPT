"""그림 2(반환점 선택)용 예시 찾기: 진출 경로·다리 위치를 바꿔 가며 깔끔한 예를 고른다.
조건: 반환점이 멈춘 곳이 아님, 되밟기 0, 반환 구간이 버린 부분을 지나지 않음, 1단계 값과 2단계 값이 다른 후보가 있음.
비용: 지나온 간선 x6, 근처 x4, 90° 꺾임마다 60 m(수식 (3)과 같은 회전 비용, 간선 상태 다익스트라)."""
import heapq
import itertools
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
W, H, D, T, CT = 10, 8, 100, 2600, 60
S = (1, 1)


def make_nbrs(bridges, ry):
    def nbrs(n):
        x, y = n
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + dx < W and 0 <= y + dy < H:
                if dy and {y, y + dy} == {ry, ry + 1} and x not in bridges:
                    continue
                yield (x + dx, y + dy)
    return nbrs


def ek(a, b):
    return tuple(sorted((a, b)))


def search(OUT, k, nbrs):
    pre = OUT[:k + 1]
    out_e = {ek(pre[i], pre[i + 1]) for i in range(len(pre) - 1)}
    near_n = set(pre) | {m for p in pre for m in nbrs(p)}
    START = (None, S)
    dist, prev = {START: 0.0}, {}
    pq = [(0.0, START)]
    best = {S: START}
    while pq:
        d, st = heapq.heappop(pq)
        if d > dist[st]:
            continue
        pu, u = st
        for v in nbrs(u):
            if v == pu:
                continue
            e = ek(u, v)
            mult = 1 + (5 if e in out_e else 0) + (3 if (u in near_n and v in near_n and e not in out_e) else 0)
            c = D * mult
            if pu is not None and (u[0] - pu[0], u[1] - pu[1]) != (v[0] - u[0], v[1] - u[1]):
                c += CT
            ns = (u, v)
            if d + c < dist.get(ns, 1e18):
                dist[ns], prev[ns] = d + c, st
                heapq.heappush(pq, (d + c, ns))
                if v not in best or d + c < dist[best[v]]:
                    best[v] = ns
    def path(n):
        st, p = best.get(n), []
        if st is None:
            return None
        while st != START:
            p.append(st[1]); st = prev[st]
        p.append(S)
        return p          # n → ... → S
    return path, out_e


def turns(p):
    return sum(1 for a, b, c in zip(p, p[1:], p[2:]) if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]))


def evaluate(OUT, bridges, ry):
    nbrs = make_nbrs(bridges, ry)
    for a, b in zip(OUT, OUT[1:]):
        if b not in set(nbrs(a)):
            return None
    path1, _ = search(OUT, len(OUT) - 1, nbrs)
    rows = []
    for i, n in enumerate(OUT[1:], 1):
        p = path1(n)
        if p is None:
            return None
        rows.append((i, n, i * D + (len(p) - 1) * D))
    top5 = sorted(rows, key=lambda r: abs(r[2] - T))[:5]
    ref = []
    for i, n, rough in top5:
        pth, oute = search(OUT, i, nbrs)
        p = pth(n)
        back = (len(p) - 1) * D
        retr = sum(D for a, b in zip(p, p[1:]) if ek(a, b) in oute)
        ref.append(dict(i=i, rough=rough, exact=i * D + back, retr=retr, ret=p))
    ok = [r for r in ref if abs(r["exact"] - T) <= 0.1 * T]
    if not ok:
        return None
    best = min(ok, key=lambda r: (r["retr"], abs(r["exact"] - T)))
    k = best["i"]
    disc = {ek(a, b) for a, b in zip(OUT[k:], OUT[k + 1:])}
    disc_nodes = set(OUT[k + 1:])
    if k == len(OUT) - 1 or best["retr"] or any(ek(a, b) in disc for a, b in zip(best["ret"], best["ret"][1:])):
        return None
    if disc_nodes & set(best["ret"]):
        return None
    changed = sum(1 for r in ref if r["rough"] != r["exact"])
    first_pick = min(top5, key=lambda r: abs(r[2] - T))[0]
    return dict(k=k, best=best, ref=ref, turns=turns(best["ret"]), changed=changed, first_pick=first_pick)


found = []
ry = 2
for ups in itertools.combinations(range(13), 6):
    # 출발점에서 오른쪽·위로만 가는 계단 13칸(같은 모양은 한 번만)
    OUT = [S]
    for j in range(13):
        m = (0, 1) if j in ups else (1, 0)
        OUT.append((OUT[-1][0] + m[0], OUT[-1][1] + m[1]))
    if max(p[0] for p in OUT) >= W or max(p[1] for p in OUT) >= H:
        continue
    if len(found) >= 60:
        break
    for _ in (0,):
        cross = [a[0] for a, b in zip(OUT, OUT[1:]) if {a[1], b[1]} == {ry, ry + 1}]
        if len(cross) != 1:
            continue
        for b2 in range(cross[0] + 4, W):
            bridges = {cross[0], b2}
            r = evaluate(OUT, bridges, ry)
            if r and r["changed"] >= 1 and r["first_pick"] != r["k"]:
                found.append((r["turns"], -r["changed"], tuple(OUT), tuple(sorted(bridges)), ry, r))
found.sort(key=lambda f: (f[0], f[1]))
seen = set()
for f in found[:400]:
    key = (f[2], f[3], f[4])
    if key in seen:
        continue
    seen.add(key)
    t, c, OUT, br, ry, r = f
    print("turns", t, "changed", -c, "ry", ry, "bridges", br, "k", r["k"], "OUT", OUT)
    for x in sorted(r["ref"], key=lambda x: x["i"]):
        print("   P", x["i"], x["rough"], "→", x["exact"], "되밟기", x["retr"])
    if len(seen) >= 8:
        break
print("총", len(found))
