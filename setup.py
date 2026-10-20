from setuptools import setup, find_packages

setup(
    name="openapi-spec-linter",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "rich>=12.0.0",
    ],
    entry_points={
        "console_scripts": [
            "openapi-spec-linter = openapi_spec_linter.cli:main",
        ],
    },
)
