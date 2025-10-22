from setuptools import setup, find_packages

setup(
    name="promptscribe",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "rich",
        "ptyprocess",
        "wexpect",
        "sqlalchemy",
        "rapidfuzz",
        "pyyaml",
        "python-dotenv",
        "openai"
    ],
    entry_points={
        "console_scripts": [
            "promptscribe=promptscribe.cli:main",
            "pv=promptscribe.cli:main"
        ]
    },
    python_requires=">=3.11",
)
