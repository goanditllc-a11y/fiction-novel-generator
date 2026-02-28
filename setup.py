from setuptools import setup, find_packages

setup(
    name="fiction-novel-editor",
    version="1.0.0",
    description="A full-featured Windows desktop application for editing fiction novels",
    author="Fiction Novel Editor",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.4.0",
        "python-docx>=0.8.11",
        "markdown>=3.4.1",
        "transformers>=4.30.0",
        "torch>=2.0.0",
        "spacy>=3.5.0",
        "Pillow>=9.5.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "fiction-novel-editor=src.main:main",
        ],
    },
)
