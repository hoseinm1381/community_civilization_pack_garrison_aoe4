"""Pin authoring-tool and historical-tool dependencies without copying assets."""
from pathlib import Path
import json
from common import ROOT, CFG, OUT, CORE, ARCH, guard, files, sha, write

def main():
    guard()
    target = OUT/'baseline/preparation-dependencies.json'
    if target.exists():
        print(json.dumps({'status':'existing-freeze-preserved','path':str(target)}))
        return
    ext = Path(CFG['garrison_extension'])
    named = {'garrison_core':CORE, 'archive_tool':ARCH,
             'blender':Path(CFG['blender']), 'content_editor':Path(CFG['content_editor']),
             'configured_art_editor':Path(CFG['art_editor']),
             'extension_manifest':ext/'blender_manifest.toml',
             'unit_export':ext/'unit_export.py', 'model_tools':ext/'model_tools.py',
             'project_storage':ROOT/'STORAGE.md', 'project_instructions':ROOT.parent/'AGENTS.md'}
    records = {name:{'path':str(p),'present':p.is_file(),
                     'sha256':sha(p) if p.is_file() else None}
               for name,p in named.items()}
    previous_tools = files(ROOT/'tools')
    write(target, {'schema':'ccp-060-preparation-dependencies/v1',
        'dependencies':records, 'previous_tools':previous_tools,
        'notes':['The missing configured art editor is regenerable using Garrison model_tools._ensure_model_tools; no cook passed.',
                 'Concurrent landmark work may legitimately change its own tooling. Preserve this observation and attribute drift; do not edit older work to satisfy it.']})
    print(json.dumps({'status':'frozen','path':str(target),'previous_tool_files':len(previous_tools),
                      'missing':[name for name,r in records.items() if not r['present']]}))

if __name__=='__main__':
    main()
