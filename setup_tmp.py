## setup.py build_ext --inplace
import sys
sys.argv.extend(["build_ext","--inplace"])

print("Importing setuptools...")
from setuptools import setup
print("[+] Done (setuptools import)\n")
print("Importing Cython...")
from Cython.Build import cythonize
print("[+] Done (Cython import)\n")
print("Importing Extension...")
from distutils.extension import Extension
print("[+] Done (Extension import)\n")

print("Compiling the program into Cython...\n\n###")
setup(
    name='Scraper',
    ext_modules=cythonize([
                            "Core/Data_storage.py",
                            "Core/Browser.py",
                            "Core/Crawler.py",
                            "Tests/basic_open_browser.py",
                            "Tests/basic_crawl_websites.py",
                            ],
                            language="c++", language_level=3),
    zip_safe=False,
    extra_compile_args=["-Ofast", 
                        "-march=native",
                        "-std=c++20",
                        "CPPFLAGS=\"-D_GLIBCXX_USECXX11_ABI=0\"",
                        "-auto-profile",
                        "-whole-program"]
)
print("###\n\n[+] Done (Compilation)\n")