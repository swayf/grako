# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from distutils.core import setup

setup(
    name='grako',
    version='1.4.0',
    author='Juancarlo Añez',
    author_email='apalala@gmail.com',
    packages=['grako', 'grako.model', 'grako.test'],
    scripts=['scripts/grako'],
    url='http://bitbucket.org/apalala/grako',
    license='GNU General Public License v3 (GPLv3)',
    description='A generator of PEG/Packrat parsers from EBNF grammars.',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Text Processing :: General'
    ],
)
