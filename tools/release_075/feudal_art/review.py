"""Bounded matched before/after review, presentation scene only, never saved."""
import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
key=sys.argv[sys.argv.index('--')+1]
code=(ROOT/'tools/release_075/render_review.py').read_text()
code=code.replace('s.cycles.samples=16','s.cycles.samples=8').replace('resolution_x=1100','resolution_x=880').replace('resolution_y=850','resolution_y=680')
code=code.replace("((-.6,-.8,.65),40)","((-.6,-.8,.65),40),((0,1,1),30)")
for phase in ('before','after'):
 if phase=='before':source=ROOT/('art/authoring/buildings_021/ministry/ministry.blend' if key=='ministry' else 'art/authoring/landmarks_040/'+key+'/'+key+'.blend')
 else:source=ROOT/'art/authoring/release_075'/key/'r3'/(key+'.blend')
 out=ROOT/'output/release_075/art'/key/'r3'/('views-'+phase)
 sys.argv=['render_review.py','--',str(source),str(out)]
 exec(compile(code,'presentation_review','exec'),{'__name__':'__main__'})
