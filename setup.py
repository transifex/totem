from setuptools import find_packages, setup

import versioneer

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='totem',
    author='Transifex Devs',
    author_email='info@transifex.com',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description=(
        'Software to verify that PRs and commits follow expected Quality Standards'
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    url='https://github.com/transifex/totem',
    install_requires=[
        'Click',
        'PyGitHub==1.40a4',
        'pyaml==17.12.1',
        'GitPython==2.1.11',
    ],
    py_modules=['cli'],
    entry_points={'console_scripts': ['totem=cli:main']},
)
