from setuptools import setup
import os
from glob import glob

package_name = "panda_pick_and_place"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Chiamaka",
    maintainer_email="user@example.com",
    description="MoveIt 2 pick and place pipeline with Franka Panda",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "pick_and_place_node = panda_pick_and_place.pick_and_place_node:main",
        ],
    },
)
