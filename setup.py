from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cmm-measurement-parser",
    version="1.1.0",
    author="shuhei",
    author_email="kinugasa.hirata@gmail.com",
    description="Professional CMM measurement data parser for coordinate measuring machines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["cmm_measurement_parser"],
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.18.0",
        "openpyxl>=3.0.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)