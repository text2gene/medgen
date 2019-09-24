import subprocess
from setuptools import setup, find_packages
import medgen

from setuptools.command.build_ext import build_ext as _build_ext

class build_ext(_build_ext):
    # http://stackoverflow.com/questions/21605927/why-doesnt-setup-requires-work-properly-for-numpy/21621493
    def finalize_options(self):
        _build_ext.finalize_options(self)
        # Prevent numpy from thinking it is still in its setup process:
        __builtins__.__NUMPY_SETUP__ = False
        import numpy
        self.include_dirs.append(numpy.get_include())

setup(
    name = 'medgen-prime',
    version = medgen.__version__,
    description = 'MedGen is the NCBI primary source for Medical Genomics information',
    long_description = 'Modules in medgen.* provide access to the databases and concepts found in medgen-mysql.',
    url = 'https://bitbucket.org/text2gene/medgen',
    author = 'Dr. Andy McMurry',
    maintainer = 'Naomi Most',
    author_email = 'andymc@apache.org',
    maintainer_email = 'naomi@text2gene.com',
    license = 'Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)',
    packages = find_packages(),
    package_data={'medgen': ['config/*.ini']},
    cmdclass = {'build_ext': build_ext},
    setup_requires = ['numpy'],
    install_requires = [
        'setuptools',
        'wheel',
        'configparser',
        'mysql-connector-python',
        'mysqlclient',
        'metapub',
        'numpy',
        'nose',
        'coverage',
        'mock',
        'PyHamcrest',
        'requests',
        'pyrfc3339',
        'ipython',
        ],
    )

