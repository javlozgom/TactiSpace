from src.ui.views import comparative as _view

globals().update({name: value for name, value in vars(_view).items() if not name.startswith("__")})
