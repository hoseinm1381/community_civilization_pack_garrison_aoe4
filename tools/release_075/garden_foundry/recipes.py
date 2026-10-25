"""Bounded recipes: real contacts, fixed access corridors, no native mutations."""
import math,random
import bpy,bmesh,numpy as np
from mathutils import Vector
from runner import Batch,components,discard,append,category,remap_planar,normals

def leaf(batch,a,d,length,width):
 a=Vector(a);d=Vector(d).normalized();side=d.cross(Vector((0,0,1))).normalized();n=d.cross(side).normalized();mid=a+d*length*.48
 batch.add([a,mid+side*width*.5,a+d*length,mid-side*width*.5,mid+n*.024,mid-n*.014],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],'foliage')

def trim_box_component(obj,c,axis,newlo=None,newhi=None):
 oldlo=c['lo'][axis];oldhi=c['hi'][axis]
 for vi in c['ids']:
  v=obj.data.vertices[vi]
  if newlo is not None and abs(v.co[axis]-oldlo)<1e-5:v.co[axis]=newlo
  if newhi is not None and abs(v.co[axis]-oldhi)<1e-5:v.co[axis]=newhi

def garden(parts,col,mat):
 changes=[];contacts=[]
 # Equal-height perpendicular wall tops overlap at exactly these source
 # corners. Trim the long north/south caps to the inner face of the side wall.
 obj=parts[1]
 for c in components(obj):
  lo,hi,mid,span=c['lo'],c['hi'],c['center'],c['span']
  if len(c['ids'])==8 and abs(span.z-1.5)<.001 and abs(abs(mid.x)-11)<.001 and span.y>.9:
   trim_box_component(obj,c,1,-11.25 if lo.y<-10.9 else None,11.25 if hi.y>10.9 else None)
   changes.append({'repair':'side wall end fills corner to existing exterior face','old':[list(lo),list(hi)]})
  if len(c['ids'])==8 and abs(span.z-1.5)<.001 and span.x>5 and abs(abs(mid.y)-11)<.001:
   newlo=-10.75 if lo.x<-10.8 else None;newhi=10.75 if hi.x>10.8 else None
   trim_box_component(obj,c,0,newlo,newhi)
   changes.append({'repair':'remove coplanar perimeter corner overlap','old':[list(lo),list(hi)],'new_x_limits':[newlo,newhi]})
  if len(c['ids'])==8 and abs(span.z-1.1)<.001 and span.x>8 and abs(mid.y-2.6)<.001:
   # South service wall abuts west service wall inside face x=2.71.
   trim_box_component(obj,c,0,2.71,None);changes.append({'repair':'service enclosure corner overlap','x_min':2.71})
 # Pond coping runs along both axes. Shorten the Y-spanning returns to
 # meet the horizontal run inner face. No surface is moved over a void.
 land=parts[5]
 # Retained pond-wall boxes overlap at their coplanar .09 top corners.
 for c in components(parts[0]):
  if len(c['ids'])==8 and abs(c['hi'].z-.09)<.001 and c['span'].y>5:
   trim_box_component(parts[0],c,1,-5.60,0.0)
   changes.append({'repair':'pond foundation return meets horizontal inner face','signed_gap':0})
 # Two historical paver paths cross at the same .055 top plane. Retain the
 # first slab at each overlap; remove only the redundant closed island.
 kept=[];paving_remove=[]
 for c in components(land):
  if len(c['ids'])==14 and abs(c['hi'].z-.055)<.001 and c['span'].x<1.5:
   overlap=any(c['lo'].x<k['hi'].x and c['hi'].x>k['lo'].x and c['lo'].y<k['hi'].y and c['hi'].y>k['lo'].y for k in kept)
   if overlap:paving_remove+=c['ids']
   else:kept.append(c)
 discard(land,paving_remove);changes.append({'removed_coplanar_paver_vertices':len(paving_remove)})
 for c in components(land):
  lo,hi,span=c['lo'],c['hi'],c['span']
  if len(c['ids'])==8 and .20<span.x<.22 and 5<span.y<6 and -.3<c['center'].z<.2:
   trim_box_component(land,c,1,lo.y+.105,hi.y-.105)
   changes.append({'repair':'coping return to horizontal run without overlap','old':[list(lo),list(hi)],'signed_gap':0.0})
 # Resolve contact-independent shading: assign UVs per actual wall face,
 # preserving category and keeping every UV inside its atlas zone.
 for i in (0,1,5,6):
  o=parts[i]
  for c in components(o):
   if not c['faces']:continue
   cat=category(o,o.data.polygons[c['faces'][0]])
   if cat==0 and max(c['span'])>1.4:remap_planar(o,c['faces'],0)
   elif cat==1:remap_planar(o,c['faces'],1,grain=True)
 # Remove only six r2 saucer groups. Trunks, lotus, paving and architecture
 # remain; new soil borders are entirely in the ornament margin.
 oldbeds=[(-6.8,8.8),(-8,1.7),(-9.5,-5.8),(.6,-9),(8.9,-6.5),(8.3,-2.5)]
 remove=[]
 for c in components(land):
  near=any(abs(c['center'].x-x)<.85 and abs(c['center'].y-y)<.75 for x,y in oldbeds)
  cat=category(land,land.data.polygons[c['faces'][0]]) if c['faces'] else -1
  if near and c['hi'].z<.65 and c['lo'].z>-.03 and cat in (5,7):remove+=c['ids']
 discard(land,remove)
 batch=Batch('coherent_borders_and_crown_tiers',col,mat,land.location);rng=random.Random(750753)
 # Rooted foliage in two connected crown tiers, same retained trunk anchors.
 trees=[(-9.25,8.1,3.25,.88),(-9.1,3.5,2.55,.77),(-9.2,-1.4,2.8,.83),(-8.45,-8.2,2.65,.73),(1.15,-8.7,3,.84),(4.25,-7.7,2.6,.72),(7.9,-7.2,2.3,.72)]
 for ti,(x,y,h,r) in enumerate(trees):
  anchor=Vector((x,y,h*.56))
  for tier in range(2):
   for sprig in range(9):
    a=sprig*2.399963+ti*.71+tier*.43
    start=anchor+Vector((0,0,.14+tier*.20))
    end=start+Vector((math.cos(a)*r*(.80 if tier==0 else .55),math.sin(a)*r*(.65 if tier==0 else .48),.12))
    batch.tube([start,end],[.026,.006],'wood',5)
    for k in range(5):
     base=start.lerp(end,.45+k*.12);ang=a+(-1 if k%2 else 1)*1.1
     leaf(batch,base,(math.cos(ang),math.sin(ang),.22),.32+rng.random()*.13,.21+rng.random()*.06)
  contacts.append({'tree':ti,'retained_trunk_top':h*.56,'new_tier_stems_begin':h*.56+.14,'contact':'branches enter existing stem which extends from anchor-.10 to anchor+.25h'})
 # Deliberate low border beds avoid main bridge axis x[-4,-2], east exit and
 # service lane. Bed tops .065; plant bases .055 overlap soil .010m.
 beds=[(-10.45,-9.75,-5.8,-2.6),(-10.45,-9.75,2.0,7.3),(1.8,8.5,-10.05,-9.4)]
 for idx,(x0,x1,y0,y1) in enumerate(beds):
  batch.slab([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],.065,.08,'clay')
  length=max(x1-x0,y1-y0);count=round(length/.40)
  for k in range(count):
   t=(k+.5)/count;x=x0+(x1-x0)*(.5 if y1-y0>x1-x0 else t);y=y0+(y1-y0)*(t if y1-y0>x1-x0 else .5)
   for j in range(9):
    az=j*2.399963+k*.33
    leaf(batch,(x,y,.055),(math.cos(az),math.sin(az),.6),.26+rng.random()*.13,.13)
  contacts.append({'border':idx,'bounds':[x0,x1,y0,y1],'soil_top':.065,'plant_base':.055,'overlap':.010})
 append(land,batch)
 # The original geometry is closed. Recalculate only changed healthy parts.
 for i in (0,1,5,6):normals(parts[i])
 return {'changes':changes,'contacts':contacts,'removed_saucer_vertices':len(remove),'new_border_count':3,'crown_tiers_added':2,'known_remaining':['Roof decorative framing and pond material still require matched render critique','Official full-compound comparison and native owner colour remain root-owned']}

def foundry(parts,col,mat):
 fixture=parts[5];remove=[];changes=[];contacts=[]
 # The ridge cylinders beyond the retained main roof have no support.
 roof=parts[4];unsupported=[]
 for c in components(roof):
  if len(c['ids'])==16 and c['hi'].z>5 and c['span'].z<.2 and c['lo'].x<-9.25:
   unsupported+=c['ids']
 discard(roof,unsupported);changes.append({'removed_unsupported_ridge_vertices':len(unsupported)})
 # The historical broad square stack intersects its later stepped shells.
 # Remove both duplicate versions and replace with one tapering hollow flue.
 for c in components(fixture):
  mid,lo,hi,span=c['center'],c['lo'],c['hi'],c['span']
  for x in (-6.4,-.8):
   if abs(mid.x-(x-.8))<.08 and abs(mid.y+4.36)<.08 and lo.z>.5 and hi.z>1.5 and span.x<1.02 and span.y<1.02:
    remove+=c['ids'];changes.append({'removed_duplicate_chimney_component':[list(lo),list(hi)]});break
 discard(fixture,remove)
 b=Batch('masonry_flues_and_fuel',col,mat,fixture.location)
 for index,x in enumerate((-6.4,-.8)):
  cx=x-.8;cy=-4.36;z0=.65;ztop=4.15 if index==0 else 3.60
  # Four tapered walls plus the inset dark flue floor, with truly open top.
  outer0=.47;outer1=.34;inner=.19;verts=[]
  for z,r in ((z0,outer0),(ztop,outer1),(ztop,inner),(ztop-.55,inner)):
   verts.extend([(cx-r,cy-r,z),(cx+r,cy-r,z),(cx+r,cy+r,z),(cx-r,cy+r,z)])
  faces=[]
  for i in range(4):
   j=(i+1)%4;faces.extend([(i,j,j+4,i+4),(i+4,j+4,j+8,i+8),(i+8,j+8,j+12,i+12)])
  faces.extend([(3,2,1,0),(12,13,14,15)])
  b.add(verts,faces,'clay')
  # The lip surrounds the actual flue. No cap covers its opening.
  for side in (-1,1):
   b.box((cx+side*.33,cy,ztop-.055),(.13,.80,.15),'stone')
   b.box((cx,cy+side*.33,ztop-.055),(.54,.13,.15),'stone')
  contacts.append({'flue':index,'bottom_z':z0,'existing_hearth_support_top':1.405,'intentional_base_insertion':.755,'top_z':ztop,'flue_opening_width':.38})
  # Fuel laid immediately beside each hearth, outside the open centre lane.
  for row in range(3):
   for k in range(4-row):
    y=-7.50+k*.20;xx=x-1.22+row*.06
    b.tube([(xx,y,.07+row*.13),(xx+.72,y+.03,.07+row*.13)],[.08,.075],'wood',7)
  contacts.append({'fuel_stack':index,'bottom_z':-.01,'court_top':0,'intentional_overlap':.01})
 append(fixture,b)
 # Brick furnace faces receive consistent scale instead of stretched stone.
 for c in components(fixture):
  mid=c['center'];near=any(abs(mid.x-x)<1.6 and -7<mid.y<-3.7 for x in (-6.4,-.8))
  if near and c['faces']:
   cat=category(fixture,fixture.data.polygons[c['faces'][0]])
   if cat in (0,5):remap_planar(fixture,c['faces'],5)
 # Purposeful billet rack in the store margin; aisle and casting pits untouched.
 court=parts[6];b=Batch('billet_rack',col,mat,court.location)
 for y in (-7.95,-7.35):
  b.box((7.8,y,.29),(2.35,.10,.12),'wood')
 for x in (6.85,8.75):b.box((x,-7.65,.15),(.13,.78,.32),'wood')
 for k in range(6):b.box((6.95+k*.32,-7.65,.40),(.22,.70,.12),'metal')
 contacts.append({'rack':'billet stock','feet_bottom':-.01,'floor_top':0,'overlap':.01,'billet_bottom':.34,'rail_top':.35})
 append(court,b)
 # Retain object-PBR. The unused water atlas zone becomes a dark oxidized
 # masonry ramp, then only flue/hearth faces are explicitly mapped into it.
 # Check actual UV use before reserving this slot.
 usage=sum(1 for i in (0,1,4,5,6) for p in parts[i].data.polygons if category(parts[i],p)==4)
 changes.append({'water_zone_existing_face_count':usage})
 if usage==0:
  images=[n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'albedo' in (n.image.name+n.image.filepath).lower()]
  assert len(images)==1
  img=images[0];w,h=img.size;pixels=np.array(img.pixels[:],dtype=np.float32).reshape(h,w,4)
  hh=h//2;ww=w//4;yy,xx=np.mgrid[:hh,:ww]
  # Authoring material explicitly flips V; category4 is bottom image half.
  for ch,base in enumerate((.12,.085,.055)):pixels[:hh,:ww,ch]=base+.06*(yy/hh)+.009*np.sin(xx*.23+yy*.17)
  img.pixels.foreach_set(pixels.ravel())
  for c in components(fixture):
   mid=c['center'];near=any(abs(mid.x-(x-.8))<.65 and abs(mid.y+4.36)<.65 for x in (-6.4,-.8))
   mouth=any(abs(mid.x-x)<1.15 and mid.y<-6.3 and c['hi'].z>1 for x in (-6.4,-.8))
   if near or mouth:remap_planar(fixture,c['faces'],4)
 for i in (0,1,5,6):
  for c in components(parts[i]):
   if c['faces'] and category(parts[i],parts[i].data.polygons[c['faces'][0]])==1:remap_planar(parts[i],c['faces'],1,grain=True)
  normals(parts[i])
 return {'changes':changes,'contacts':contacts,'known_remaining':['Soot ramp and added fuel need visual review','Stock full-compound and native owner colour remain pending'],'preserved_access':'Main centre lane and both casting pit extents unchanged'}
