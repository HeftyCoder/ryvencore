pip uninstall --yes ryvencore
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q ryvencore.egg-info
python setup.py install