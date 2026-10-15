import sys; sys.path.insert(0,'.')
import figs, importlib
for m in sys.argv[2:]: importlib.import_module(m)
for k in [k for k in figs.FIG if k.startswith(sys.argv[1])]:
    f = figs.FIG[k](); w = f.lint(); print(k, len(w), f'{f.w}x{f.h}'); [print('   ', x) for x in w[:30]]
