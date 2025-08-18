
from setuptools import setup, find_packages

setup(
    name="ssutxos",
    version="0.1.0",
    description="A CLI tool to inspect SideSwap UTXOs",
    author="Lucky",
    author_email="lucky.bear.dev@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests>=2.31",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "ssutxos=ssutxos.cli:app_entry",
        ],
    },
)
