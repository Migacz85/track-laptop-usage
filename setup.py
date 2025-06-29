from setuptools import setup, find_packages

setup(
    name="laptop-tracker",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=7.0",
        "matplotlib>=3.1.2",
        "pandas>=1.0.0",
        "seaborn>=0.10.0",
        "numpy>=1.22,<1.25",
        "psutil>=5.8.0",
    ],
    entry_points={
        "console_scripts": [
            "laptop-tracker=laptop_tracker.cli:cli",
        ],
    },
    python_requires=">=3.6",
    include_package_data=True,
)
