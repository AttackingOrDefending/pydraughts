import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pydraughts",
    version="0.0.2",
    author="AttackingOrDefending",
    description="A draughts library for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AttackingOrDefending/pydraughts",
    project_urls={
        "Bug Tracker": "https://github.com/AttackingOrDefending/pydraughts/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "draughts"},
    packages=setuptools.find_packages(where="draughts"),
    python_requires=">=3",
)
