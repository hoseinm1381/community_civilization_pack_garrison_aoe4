"""Vietnamese light infantry: continuous tailored cloth, donor-derived anatomy."""
import math,bpy
from mathutils import Vector
from mesh import charts
C=charts()
def torso_weight(z):
    if z<1.04:return {'metarig_pelvis':1}
    if z<1.16:return {'metarig_spine1':.6,'metarig_spine2':.4}
    if z<1.29:return {'metarig_spine2':.5,'metarig_ribcage':.5}
    return {'metarig_ribcage':1}
def body(w,age):
    pelvis='metarig_pelvis';chest='metarig_ribcage';head='metarig_head'
    # One continuous, shaped cloth shell with a stitched flared hem and waist.
    profile=[(.72,.25,.148),(.76,.252,.15),(.82,.246,.147),(.89,.233,.14),(.96,.199,.125),(1.01,.179,.116),(1.06,.180,.117),(1.12,.191,.125),(1.20,.210,.135),(1.30,.226,.140),(1.39,.235,.132),(1.48,.221,.112),(1.53,.176,.092),(1.57,.085,.071)]
    w.loft('Tailored cross-collar tunic',[((0,0,z),rx,ry) for z,rx,ry in profile],[torso_weight(z) for z,_,_ in profile],C['tunic'],sides=40,fold=.035,caps=False)
    w.loft('Collar seated inner neck',[((0,y,z),rx,ry) for z,y,rx,ry in [(1.55,0,.070,.067),(1.59,-.005,.067,.063),(1.63,-.018,.062,.061),(1.66,-.025,.058,.059)]], 'metarig_neck2',C['neck'],sides=24,tag='skin')
    w.loft('Integrated jaw and rear cranium',[((0,-.015,z),rx,ry) for z,rx,ry in [(1.635,.055,.062),(1.67,.069,.079),(1.73,.092,.094),(1.80,.100,.101),(1.86,.094,.089),(1.90,.068,.067)]],head,C['neck'],sides=28,tag='skin')
    # Slight overlap is the sewn contact between sleeve root and tunic shoulder.
    for side,sgn in [('l',1),('r',-1)]:
        prefix='metarig_'+side
        names=[prefix+n for n in ['armupper1','armupper2','armlower1','armlower2','armpalm']];p=[w.bone(n) for n in names]
        centers=[p[0]+Vector((-.018*sgn,0,.004)),p[0].lerp(p[1],.4),p[1],p[1].lerp(p[2],.60),p[2],p[2].lerp(p[3],.35)]
        radii=[(.078,.086),(.105,.098),(.105,.10),(.098,.09),(.085,.081),(.076,.071)]
        groups=[{names[0]:1},{names[0]:.5,names[1]:.5},{names[1]:1},{names[1]:.35,names[2]:.65},{names[2]:1},{names[2]:.6,names[3]:.4}]
        w.loft('Layered outer sleeve '+side,[(p,*r) for p,r in zip(centers,radii)],groups,C['sleeve_'+side],sides=24,fold=.055,axis='path')
        end=p[4].lerp(p[3],.13)
        w.loft('Bound forearm cuff '+side,[(centers[-1],.074,.071),(p[3],.065,.058),(p[3].lerp(end,.55),.052,.046),(end,.043,.035)], [{names[2]:.5,names[3]:.5},{names[3]:1},{names[3]:.5,names[4]:.5},{names[4]:1}],C['linen'],axis='path',sides=20,fold=.025)
        # Folded cuff rings sit on, rather than float above, the sleeve surface.
        for t in [.33,.52,.72]:
            a=p[3].lerp(end,t);b=p[3].lerp(end,t+.055);r=.065*(1-t)+.043*t
            w.loft('Cuff overlap '+side+str(t),[(a,r+.001,r*.90+.001),(b,r,r*.9)],names[3],C['linen'],sides=16,axis='path')
        hip=w.bone(prefix+'leg1');knee=w.bone(prefix+'leg2');ankle=w.bone(prefix+'legankle')
        legpoints=[hip,hip.lerp(knee,.28),hip.lerp(knee,.60),knee,knee.lerp(ankle,.25),knee.lerp(ankle,.48)]
        radii=[(.080,.070),(.085,.075),(.089,.080),(.087,.080),(.078,.073),(.064,.060)]
        groups=[{prefix+'leg1':1},{prefix+'leg1':1},{prefix+'leg1':1},{prefix+'leg1':.4,prefix+'leg2':.6},{prefix+'leg2':1},{prefix+'leg2':1}]
        w.loft('Gathered trousers '+side,[(p,*r) for p,r in zip(legpoints,radii)],groups,C['trousers_'+side],sides=24,fold=.07,axis='path')
        calf=legpoints[-1];wrapend=ankle
        w.loft('Cloth gaiter '+side,[(calf,.068,.064),(calf.lerp(wrapend,.5),.059,.057),(wrapend,.048,.047)],prefix+'leg2',C['linen'],sides=20,axis='path',fold=.02)
        for j in range(6):
            t=j/6;a=calf.lerp(wrapend,t);b=calf.lerp(wrapend,t+.075);r=.069*(1-t)+.049*t
            w.loft('Gaiter turn '+side+str(j),[(a,r,r*.95),(b,r-.001,r*.95-.001)],prefix+'leg2',C['linen'],sides=16,axis='path')
        x=ankle.x;y=ankle.y
        # Shaped, flattened leather shoe; top follows instep rather than an oval.
        outline=[(-.052,.065),(.052,.065),(.060,-.055),(.053,-.165),(.027,-.190),(-.032,-.190),(-.060,-.145),(-.061,-.045)]
        vs=[];uv=[]
        for ring,(z,scale,shift) in enumerate([(.025,1,0),(.045,1.02,0),(.085,.94,.005)]):
            for j,(dx,dy) in enumerate(outline):
                height=z if ring<2 else .082+.05*(dy+.19)/.255
                vs.append((x+dx*scale,y+dy*scale+shift,height));uv.append((j/8,height/.14))
        fs=[]
        for k in range(2):
            for j in range(8):fs.append((k*8+j,k*8+(j+1)%8,(k+1)*8+(j+1)%8,(k+1)*8+j))
        fs.extend([tuple(reversed(range(8))),tuple(range(16,24))])
        w.mesh('Soft leather shoe '+side,vs,fs,uv,[{prefix+'legankle':1} for _ in vs],C['leather'],'sole')
        w.contacts.append({'interface':'sleeve/tunic '+side,'intentional_overlap':.018,'cuff_to_palm_distance':(end-p[4]).length,'shoe_min_z':.025})
    # A structured diagonal collar has width and follows the chest surface.
    for name,points,widths in [
      ('Cross-collar upper',[(.074,-.055,1.568),(.10,-.103,1.49),(.045,-.144,1.39),(-.035,-.148,1.29),(-.13,-.133,1.17)],[.045,.05,.047,.043,.035]),
      ('Under collar',[(-.076,-.055,1.566),(-.108,-.102,1.49),(-.057,-.143,1.40),(.02,-.148,1.30)],[.037,.04,.037,.025])]:w.ribbon(name,points,widths,chest,C['linen'])
    w.loft('Wide waist belt',[((0,0,z),rx,ry) for z,rx,ry in [(.972,.210,.142),(.99,.200,.140),(1.025,.198,.139)]],pelvis,C['leather'],sides=40)
    w.ribbon('Layered cloth sash tail',[(-.11,-.134,.998),(-.14,-.151,.91),(-.145,-.153,.81),(-.12,-.146,.747)],[.067,.07,.066,.045],pelvis,C['headcloth'])
    # Low folded cloth cap, broad owner band and flat knotted tails.
    w.loft('Wrapped headcloth',[((0,-.035,z+.02),rx,ry) for z,rx,ry in [(1.835,.113,.125),(1.856,.121,.130),(1.887,.123,.133),(1.91,.111,.120),(1.935,.083,.094),(1.945,.025,.025)]],head,C['headcloth'],sides=32,fold=.025)
    for z in [1.876,1.901]:w.loft('Headwrap folded seam '+str(z),[((0,-.035,z),.123,.131),((0,-.035,z+.006),.124,.132)],head,C['headcloth'],sides=32)
    w.ribbon('Headwrap knot tail',[(.098,.068,1.865),(.118,.10,1.80),(.107,.119,1.711)],[.05,.048,.031],head,C['headcloth'],normal=(1,0,0))
    # A padded contact and two seated straps support the spare-javelin carrier.
    w.loft('Carrier contact pad',[((-.065,.163,z),.105,.025) for z in [1.08,1.14,1.33]],chest,C['leather'],sides=16)
    w.loft('Leather javelin carrier',[((-.065,.205,z),rx,ry) for z,rx,ry in [(1.03,.075,.034),(1.07,.10,.045),(1.32,.105,.045),(1.36,.11,.048)]],chest,C['leather'],sides=20)
    for z in [1.10,1.315]:w.loft('Carrier retaining band '+str(z),[((-.065,.205,z),.109,.049),((-.065,.205,z+.018),.111,.050)],chest,C['linen'],sides=20)
    w.ribbon('Carrier shoulder sling',[(.14,-.115,1.48),(.09,-.150,1.38),(-.02,-.15,1.22),(-.14,-.14,1.04)],[.029]*4,chest,C['leather'])
    for i in range(3 if age==4 else 2):
        x=-.13+i*.063;y=.205;top=1.88+i*.043
        w.loft('Spare bamboo javelin '+str(i),[((x,y,1.08),.009,.009),((x,y,top),.010,.010)],chest,C['wood'],sides=10)
        w.loft('Spare forged point '+str(i),[((x,y,top-.02),.012,.007),((x,y,top+.025),.026,.006),((x,y,top+.135),.001,.001)],chest,C['iron'],tag='blade',sides=4)
    w.contacts.append({'interface':'carrier/padded back contact','pad_front_y':.138,'pad_back_y':.188,'carrier_front_y':.160,'pad_carrier_overlap':.028})
    if age>=3:
        profile=[(1.07,.191,.130),(1.16,.218,.148),(1.27,.240,.157),(1.38,.246,.148),(1.46,.227,.123)]
        w.loft('Padded sleeveless brigandine',[((0,0,z),rx,ry) for z,rx,ry in profile],[torso_weight(z) for z,_,_ in profile],C['leather'],sides=40,fold=.015,caps=False)
        for s in [-1,1]:
            w.ribbon('Padded vest edge '+str(s),[(s*.046,-.150,1.10),(s*.05,-.167,1.25),(s*.062,-.156,1.39),(s*.075,-.12,1.465)],[.018]*4,chest,C['linen'])
        for z in [1.12,1.225,1.335]:w.ribbon('Vest closure '+str(z),[(-.057,-.169,z),(.057,-.169,z)],[.014,.014],chest,C['brass'])
    if age==4:
        # Overlapping flat rectangular lamellae around a measured padded backing.
        backing=[(1.07,.191,.130),(1.16,.218,.148),(1.27,.240,.157),(1.38,.246,.148),(1.46,.227,.123)]
        def armour_radius(z):
            for a,b in zip(backing,backing[1:]):
                if z<=b[0]:
                    t=max(0,min(1,(z-a[0])/(b[0]-a[0])));return a[1]*(1-t)+b[1]*t+.009,a[2]*(1-t)+b[2]*t+.009
            return backing[-1][1]+.009,backing[-1][2]+.009
        for row,z in enumerate([1.115,1.19,1.265,1.34,1.415]):
            for column in range(24):
                a=column/24*math.tau;half=math.tau/24*.47
                points=[]
                for shell in [0,-.003]:
                    for dz in [-.046,.037]:
                        rx,ry=armour_radius(z+dz)
                        for angle,dr in [(a-half,0),(a,.003),(a+half,0)]:points.append(((rx+dr+shell)*math.cos(angle),(ry+dr+shell)*math.sin(angle),z+dz))
                faces=[(0,1,4,3),(1,2,5,4),(9,10,7,6),(10,11,8,7),(0,6,7,1),(1,7,8,2),(3,4,10,9),(4,5,11,10),(0,3,9,6),(2,8,11,5)]
                uv=[(0,0),(.5,0),(1,0),(0,1),(.5,1),(1,1)]*2
                w.mesh('Flat lamella %02d %02d'%(row,column),points,faces,uv,[torso_weight(z)]*12,C['armour'],'plate')
        for side,sgn in [('l',1),('r',-1)]:
            n='metarig_'+side+'armupper1';p=w.bone(n);end=w.bone('metarig_'+side+'armupper2')
            for j in range(2):
                a=.12+j*.22;b=a+.18
                w.loft('Seated shoulder lame '+side+str(j),[(p.lerp(end,t),.086+.045*t,.091+.03*t) for t in [a,b]],n,C['iron'],sides=16,axis='path',caps=False)
        w.contacts.append({'interface':'lamella/backing','minimum_radial_clearance':.006,'plate_thickness':.003,'row_overlap':.008})
        # Shallow segmented iron cap, retaining an owner-colour brow band below.
        w.loft('Elite iron cap',[((0,-.035,z+.02),rx,ry) for z,rx,ry in [(1.891,.114,.118),(1.919,.108,.112),(1.947,.087,.092),(1.967,.052,.057),(1.973,.009,.009)]],head,C['iron'],sides=16)

def weapon(w,age,projectile=False):
    # Native throwing origin and -Z tip; flight resource gets its separate -Y map.
    shaft=[(.19,.014),(.29,.016),(.55,.0165),(.78,.016),(1.05,.0145),(1.35,.0125),(1.62,.010),(1.685,.008)]
    w.loft('Tapered bamboo throwing shaft',[((z*.037,z*.027,z),r,r) for z,r in shaft],None,C['wood'],sides=12)
    # Forged blade: connected profile rings with a raised central ridge.
    vs=[];uv=[]
    for j,(z,half,thick) in enumerate([(-.12,.0005,.0005),(-.055,.027,.005),(.015,.043,.010),(.08,.031,.009),(.14,.013,.007),(.20,.013,.007)]):
        for i,(x,y) in enumerate([(-half,0),(0,-thick),(half,0),(0,thick)]):vs.append((x,y,z));uv.append((i/4,j/5))
    faces=[]
    for j in range(5):
        for i in range(4):faces.append((j*4+i,j*4+(i+1)%4,(j+1)*4+(i+1)%4,(j+1)*4+i))
    faces.extend([tuple(reversed(range(4))),tuple(range(20,24))]);w.mesh('Forged ridged leaf blade',vs,faces,uv,[{} for _ in vs],C['iron'],'blade')
    w.loft('Seated iron ferrule',[((.006,.004,z),.019,.019) for z in [.17,.20,.26,.285]],None,C['iron'],sides=12)
    w.loft('Compact bound grip',[((z*.037,z*.027,z),r,r) for z,r in [(.52,.020),(.55,.021),(.65,.021),(.69,.019)]],None,C['leather'],sides=12)
    for j in range(8):
        z=.535+j*.019;w.loft('Grip wrapping turn '+str(j),[((z*.037,z*.027,z),.022,.022),(((z+.005)*.037,(z+.005)*.027,z+.005),.022,.022)],None,C['linen'],sides=10)
    if age>=3:w.loft('Reinforced blade collar',[((.007,.005,z),.024,.024) for z in [.248,.268]],None,C['brass'],sides=12)
    if age==4:w.loft('Butt reinforcement',[((z*.037,z*.027,z),.012,.012) for z in [1.625,1.68]],None,C['iron'],sides=12)
    if projectile:
        for obj in w.parts:
            for v in obj.data.vertices:
                z=v.co.z;v.co=Vector((v.co.x,(z+.12)/1.805*1.709-.3535,-v.co.y))
    w.contacts.append({'interface':'blade/socket/shaft','shaft_start':.19,'blade_socket_end':.20,'overlap':.01,'grip_z':[.52,.69],'tip_axis':'-Y' if projectile else '-Z'})
