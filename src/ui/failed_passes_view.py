from src.ui.views import failed_passes as _view

globals().update({name: value for name, value in vars(_view).items() if not name.startswith("__")})
