## setup.py build_ext --inplace
import sys
sys.argv.extend(["build_ext","--inplace"])

print("Importing setuptools...")
from setuptools import setup
print("[+] Done (setuptools import)\n")
print("Importing Cython...")
from Cython.Build import cythonize
print("[+] Done (Cython import)\n")

print("Compiling the program into Cython...\n\n###")
setup(
    name='Scraper',
    ext_modules=cythonize(
        [
            "Core/*.py",
            "Core/utils/*.py",
            "Extensions/*.py",
            #"gui.py",
        ],
        language_level=3,
        exclude_failures=True,
        #show_all_warnings=True,
    ),
    zip_safe=False,
)
print("###\n\n[+] Done (Compilation)\n")