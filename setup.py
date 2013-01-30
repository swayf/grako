# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='Grako',
    version='1.0rc1',
    author='Juancarlo Añez',
    author_email='apalala@gmail.com',
    packages=['grako', 'grako.model', 'grako.test'],
    scripts=[],
    url='http://bitbucket.org/apalala/grako',
    license='LICENSE.txt',
    description='EBNF to PEG parser generator.',
    long_description=open('README.rst').read(),
    install_requires=[]
)
