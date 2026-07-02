# DEPRECATED. Superseded by ../master_chamber_model.py, which is the single
# source of truth. This shim re-exports the canonical module so any existing
# `import chamber_model` keeps working against the patched code. Do not add
# logic here; edit master_chamber_model.py instead.
import importlib.util, os
_p = os.path.join(os.path.dirname(__file__), os.pardir, "master_chamber_model.py")
_spec = importlib.util.spec_from_file_location("master_chamber_model", _p)
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
globals().update({k: v for k, v in vars(_m).items() if not k.startswith("__")})
