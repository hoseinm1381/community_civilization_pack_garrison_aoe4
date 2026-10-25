"""Start only the installed MCP bridge in a fresh, owned Blender session."""
import bpy,importlib,json
from pathlib import Path
module='bl_ext.user_default.blender_mcp'
bpy.ops.preferences.addon_enable(module=module)
addon=importlib.import_module(module)
bpy.context.scene.blendermcp_allow_ai_control=True
server=getattr(bpy.types,'blendermcp_server',None)
if not server or not server.running:
    server=addon.BlenderMCPServer();bpy.types.blendermcp_server=server;server.start()
out=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/blender')
out.mkdir(parents=True,exist_ok=True)
(out/'bootstrap.json').write_text(json.dumps({'owned_fresh_session':True,'file':bpy.data.filepath,'running':server.running,'port':server.port,'version':bpy.app.version_string}),encoding='utf-8')
