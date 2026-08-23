from setuptools import setup, find_packages

package_name = "coffee_process"

setup(
    name=package_name,
    version="0.1.0",

    packages=find_packages(),

    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        (
            "share/" + package_name,
            ["package.xml"],
        ),

    (
        "share/" + package_name + "/config/recipes",
        [
            "config/recipes/americano.yaml",
            "config/recipes/latte.yaml",
            "config/recipes/cappuccino.yaml",
        ],
    ),

    ],

    install_requires=[
        "setuptools",
"PyYAML"
    ],

    zip_safe=True,

    entry_points={
        "console_scripts": [
            "coffee_process_node = coffee_process.coffee_process_node:main"
        ],
    },
)
