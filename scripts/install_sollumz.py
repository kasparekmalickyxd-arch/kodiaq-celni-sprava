import bpy
import os
from pathlib import Path

repo = Path.cwd()
zip_path = repo / 'sollumz.zip'
print('Installing Sollumz from', zip_path)

# Legacy add-on install is still supported in Blender 4.2 and lets us run the add-on headlessly.
bpy.ops.preferences.addon_install(filepath=str(zip_path), overwrite=True)

# Discover the installed module name, normally 'Sollumz'.
mods = [m.module for m in bpy.context.preferences.addons]
try:
    bpy.ops.preferences.addon_enable(module='Sollumz')
except Exception as e:
    print('Direct enable failed:', e)
    # Try any installed add-on containing sollumz.
    import addon_utils
    candidates = [name for name, _ in [(m.__name__, m) for m in addon_utils.modules()] if 'sollumz' in name.lower()]
    print('Candidates:', candidates)
    if not candidates:
        raise
    bpy.ops.preferences.addon_enable(module=candidates[0])

# Sollumz detects CI=1 and installs/mounts szio + pymateria automatically on Windows.
# Reload once so the full operator set is registered after dependency install.
try:
    bpy.ops.script.reload()
except Exception as e:
    print('Reload note:', e)

bpy.ops.wm.save_userpref()
print('Sollumz installed and enabled')
