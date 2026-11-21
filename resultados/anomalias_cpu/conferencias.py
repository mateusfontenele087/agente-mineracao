# Conferências descritivas para explicar os candidatos (Python, só contagens).
L = open("dados/cpu.arff").read().split("@data")[1].splitlines()
D = [list(map(float, l.split(","))) for l in L if l.strip() and not l.startswith("%")]
alta = [i+1 for i, r in enumerate(D) if r[2] >= 32000]
print("MMAX >= 32000:", len(alta), "máquinas; dessas com CACH = 0:", [i for i in alta if D[i-1][3] == 0])
print("MYCT <= 30:", sum(r[0] <= 30 for r in D), "; dessas com CACH = 0:", [i+1 for i, r in enumerate(D) if r[0] <= 30 and r[3] == 0])
print("CHMIN = 0 ou CHMAX = 0:", [(i+1, r) for i, r in enumerate(D) if r[4] == 0 or r[5] == 0])
print("MMAX <= 512:", [(i+1, r) for i, r in enumerate(D) if r[2] <= 512])
print("CACH >= 200:", [(i+1, r) for i, r in enumerate(D) if r[3] >= 200])
print("CHMAX >= 100:", [(i+1, r) for i, r in enumerate(D) if r[5] >= 100])
