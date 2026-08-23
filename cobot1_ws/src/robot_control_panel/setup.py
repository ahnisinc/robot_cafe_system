from setuptools import setup, find_packages

package_name = "robot_control_panel"

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
        "share/" + package_name + "/ui",
        ["ui/robot_control_panel.ui"],
    ),

    ],

    install_requires=[
        "setuptools",
"PyQt5"
    ],

    zip_safe=True,

    entry_points={
        "console_scripts": [
            "robot_control_panel = robot_control_panel.main:main"
        ],
    },
)
