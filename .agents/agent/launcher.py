import os
import sys

# Ensure the agent package is importable from the install dir
install_dir = r"C:\MissionControlAgent"
if install_dir not in sys.path:
    sys.path.insert(0, install_dir)

os.chdir(install_dir)

from agent.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
