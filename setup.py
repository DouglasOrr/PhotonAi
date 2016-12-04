import setuptools

setuptools.setup(
    name='photonai',
    version='0.1',
    packages=setuptools.find_packages(),
    install_requires=[
        # A minimal subset of requirements.txt
        'click',
        'fastavro',
        'flask',
        'numpy',
        'pymssql',
        'pyyaml',
    ],
)
