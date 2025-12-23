from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

# This package is a lightweight namespace package bootstrap so that
# local additions (like `exceptions.py`) can coexist with the
# installed `PyJWT` distribution. It intentionally does not
# import or define other symbols — it only extends the package
# search path.
