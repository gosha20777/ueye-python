from setuptools import setup, find_packages

setup(
    name='ueye-python',
    version='0.1.0',
    description='Python wrapper for the ueye camera SDK',
    author='Georgy Perevozchikov',
    author_email='gosha20777@live.ru',
    license='MIT',
    classifiers=[
        'Development Status :: Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
    ],
    keywords='ueye camera ids pyueye',
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'samples']),
    install_requires=['pyueye', 'numpy'],
    extras_require={},
)