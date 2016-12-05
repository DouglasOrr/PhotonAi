import setuptools

setuptools.setup(
    name='photonai',
    version='0.1',
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # A minimal subset of requirements.txt
        'click',
        'fastavro',
        'flask',
        'numpy',
        'pymssql',
        'pyyaml',
    ],
    entry_points='''
    [console_scripts]
    photonai=photonai:cli
    pai=photonai:cli
    '''
)
