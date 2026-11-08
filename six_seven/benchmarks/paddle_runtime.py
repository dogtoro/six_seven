"""Activate an optional project-local Paddle runtime for this process only."""
import os
from pathlib import Path
import sys


def activate(directory):
    if not directory: return []
    root = Path(directory).resolve(strict=True)
    if not (root/'paddle/__init__.py').is_file(): raise ValueError('Paddle runtime directory has no paddle package')
    sys.path.insert(0,str(root))
    folders = [root/'nvidia/cudnn/bin',root/'paddle/libs',Path(sys.prefix)/'Lib/site-packages/torch/lib']
    folders = [str(path) for path in folders if path.is_dir()]
    handles = [os.add_dll_directory(path) for path in folders]
    os.environ['PATH'] = os.pathsep.join(folders)+os.pathsep+os.environ['PATH']
    return handles
