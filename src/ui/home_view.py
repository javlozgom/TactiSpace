from src.ui.views import home as _view

globals().update({name: value for name, value in vars(_view).items() if not name.startswith("__")})
