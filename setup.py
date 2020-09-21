import setuptools

with open('README.md') as f:
    long_description = ''.join(f.readlines())


setuptools.setup(
    name='HVClient',
    version='1.0',
    packages=setuptools.find_packages(),
    include_package_data=True,
    description='HV Client',
    long_description=long_description,
    author='Michael Reichmann',
    author_email='micha.riechmann@gmail.com',
    url='https://github.com/diamondIPP/HVClient',

    # All versions are fixed just for case. Once in while try to check for new versions.
    install_requires=[
        'qdarkstyle',
        'numpy',
        'PyQt5',
        'pyserial',
        'matplotlib',
        'termcolor',
        'pyvisa']
)
