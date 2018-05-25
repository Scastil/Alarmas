#!/usr/bin/env python
import os
from numpy.distutils.core import setup, Extension

ext1 = Extension(name = 'al',
                 sources = ['alarmas/alarmas.py'],
        f2py_options = ['--opt = O3'])
ext2 = Extension(name = 'fs',
                 sources = ['alarmas/funciones_sora.py'])

setup(
    name='hidro_alarmas',
    version='0.0.1',
    author='Hidro SIATA',
    author_email='hidrosiata@gmail.com',    
    packages=['alarmas'],
    package_data={'alarmas':['al.so','fs.so']},
    url='https://github.com/SIATAhidro/Alarmas.git',
    license='LICENSE.txt',
    description='Despliegue de archivos para pagina de Alarmas Comunitarias',
    long_description=open('README.md').read(),
    install_requires=[ ],
    ext_modules=[ext1, ext2],
    )
