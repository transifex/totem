from setuptools import find_packages, setup

setup(
    author='Transifex Devs',
    author_email='info@transifex.com',
    description='Software to verify that PRs and commits follow '
    'expected Quality Standards',
    name='totem',
    version='0.2',
    packages=find_packages(),
    install_requires=[
        'Click',
        'PyGitHub==1.40a4',
        'pyaml==17.12.1',
        'gitpython==2.1.11',
    ],
    py_modules=['cli'],
    entry_points='''
         [console_scripts]
         totem=cli:main
      ''',
)
