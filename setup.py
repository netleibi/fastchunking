import codecs
import os
import re
import sys

from setuptools import setup, Extension
from setuptools.command.test import test as TestCommand

# Some general-purpose code stolen from
# https://github.com/jeffknupp/sandman/blob/5c4b7074e8ba5a60b00659760e222c57ad24ef91/setup.py

here = os.path.abspath(os.path.dirname(__file__))


class Tox(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import tox
        errcode = tox.cmdline(self.test_args)
        sys.exit(errcode)


def read(*parts):
    # intentionally *not* adding an encoding option to open
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

# Make sure build path exists.
build_path = os.path.join(here, 'build')
if not os.path.exists(build_path):
    os.mkdir(build_path)

# Generate Python bindings for bundled C++ library.
module_fname = os.path.join(build_path, "rabinkarprh.cpp")

try:
    import pybindgen #@UnusedImport
except ImportError:
    print("WARNING: Failed to import pybindgen. If you called setup.py egg_info,"
          "this is probably acceptable; otherwise, build will fail."
          "You can resolve this problem by installing pybindgen beforehand.")
else:
    with open(module_fname, "wt") as file_:
        print("Generating file {}".format(module_fname))
        from lib.rabinkarp_gen import generate
        generate(file_)

setup(
    name='fastchunking',
    version=find_version('fastchunking', '__init__.py'),

    description='Fast chunking library.',
    long_description=read('README.rst'),

    url='https://github.com/netleibi/fastchunking',

    author='Dominik Leibenger',
    author_email='python-fastchunking@mails.dominik-leibenger.de',

    license='Apache Software License',

    classifiers=[
            'Development Status :: 2 - Pre-Alpha',

            'Intended Audience :: Developers',
            'Topic :: Software Development :: Libraries :: Python Modules',

            'License :: OSI Approved :: Apache Software License',

            'Operating System :: OS Independent',

            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3'
    ],

    keywords=['text chunking', 'SC', 'static chunking', 'CDC', 'content-defined chunking', 'ML-*', 'multi-level chunking', 'ML-SC', 'ML-CDC', 'Rabin Karp', 'rolling hash'],

    packages=['fastchunking', 'lib'],

    setup_requires=['pybindgen'],
    install_requires=['pybindgen'],

    ext_modules=[
        Extension('fastchunking._rabinkarprh',
                  sources=[module_fname, 'lib/rabinkarp.cpp'],
                  include_dirs=['lib']
                  )
    ],

    test_suite='fastchunking.test',
    tests_require=['tox'],
    cmdclass={'test': Tox}
)
