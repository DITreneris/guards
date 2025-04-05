from setuptools import setup, find_packages

setup(
    name="guards_robbers_ml",
    version="0.1.0",
    description="Machine Learning Framework for Guards & Robbers",
    author="Guards & Robbers Team",
    author_email="info@guardsandrobbers.com",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "regex>=2021.4.4",
        "pyyaml>=6.0",
        "pyspellchecker>=0.7.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.3.0",
            "flake8>=4.0.1",
            "mypy>=0.942",
        ],
        "docs": [
            "sphinx>=4.4.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "nlp": [
            "nltk>=3.6.0",
            "spacy>=3.2.0",
        ],
        "ml": [
            "scikit-learn>=1.0.0",
            "tensorflow>=2.8.0",
            "transformers>=4.16.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.9",
) 