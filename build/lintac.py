import sys; sys.path.insert(0,'.')
import figs, figs2, figs3
try: import figs4
except ImportError: pass
for m in ('figs5','figs6'):
    try: __import__(m)
    except ImportError: pass
pre = sys.argv[1] if len(sys.argv)>1 else 'ac_'
for k in [k for k in figs.FIG if k.startswith(pre)]:
    try: f = figs.FIG[k]()
    except Exception as e:
        import traceback; traceback.print_exc(); continue
    w = f.lint()
    print(k, len(w)); [print('   ', x) for x in w[:40]]
