"""New 0.7.9 surface recipes; only the official skeleton is reused."""
import math
from mathutils import Vector

def human(w,age):
    pelvis='metarig_pelvis';chest='metarig_ribcage';head='metarig_head'
    zs=[(.83,.22,.135),(.90,.205,.13),(.99,.175,.113),(1.08,.174,.12),(1.18,.195,.13),(1.31,.224,.143),(1.43,.235,.133),(1.51,.208,.11),(1.56,.095,.074)]
    weights=[{pelvis:1},{pelvis:1},{pelvis:.8,'metarig_spine1':.2},{'metarig_spine1':.6,'metarig_spine2':.4},{'metarig_spine2':.5,chest:.5},{chest:1},{chest:1},{chest:1},{chest:1}]
    w.loft('Cross-collar linen tunic',[((0,0,z),rx,ry) for z,rx,ry in zs],4,weights,32,subdiv=3,ripple=.025)
    w.loft('Lower tunic hem',[((0,0,z),rx,ry) for z,rx,ry in [(.815,.225,.14),(.83,.226,.14),(.85,.224,.139)]],15,pelvis,32)
    w.loft('Neck',[((0,.008,1.50),.071,.069),((0,.008,1.57),.066,.067),((0,.008,1.66),.062,.066),((0,.005,1.70),.07,.07)],6,'metarig_neck2',24,subdiv=2)
    # A shaped jaw, cheek, brow and forehead surface, rather than an oval head primitive.
    face=[(1.65,.041,.048,-.019),(1.675,.063,.064,-.014),(1.71,.083,.079,-.006),(1.75,.099,.086,.0),(1.79,.103,.088,.004),(1.83,.102,.089,.008),(1.87,.098,.086,.010),(1.905,.085,.076,.014),(1.93,.052,.05,.015),(1.938,.009,.012,.015)]
    w.loft('Face and skull',[((0,y,z),rx,ry) for z,rx,ry,y in face],6,head,40,subdiv=2)
    w.loft('Nose bridge',[((0,-.081,1.75),.021,.016),((0,-.108,1.765),.024,.026),((0,-.103,1.79),.015,.019),((0,-.082,1.824),.010,.009)],6,head,20,subdiv=2)
    for sign in (-1,1):
        w.oval('Nose wing '+str(sign),(sign*.019,-.099,1.766),(.013,.018,.011),6,head,16,7)
        w.oval('Nostril '+str(sign),(sign*.019,-.114,1.76),(.006,.0035,.003),13,head,12,5)
        w.oval('Eye white '+str(sign),(sign*.041,-.079,1.809),(.022,.010,.008),14,head,20,8)
        w.oval('Eye iris '+str(sign),(sign*.040,-.0885,1.809),(.0065,.003,.007),3,head,16,7)
        w.path('Upper eyelid '+str(sign),[(sign*.021,-.082,1.811),(sign*.039,-.09,1.818),(sign*.059,-.078,1.812)],[.0035,.004,.003],6,head,8,3)
        w.path('Eyebrow '+str(sign),[(sign*.02,-.081,1.831),(sign*.04,-.085,1.835),(sign*.064,-.071,1.83)],[.004,.005,.0025],7,head,8,3)
        w.oval('Ear outer '+str(sign),(sign*.103,.003,1.792),(.019,.029,.044),6,head,20,10)
        w.oval('Ear inner '+str(sign),(sign*.116,-.005,1.792),(.005,.017,.027),13,head,16,8)
    w.path('Upper lip',[(-.029,-.078,1.72),(-.009,-.088,1.724),(0,-.09,1.721),(.009,-.088,1.724),(.029,-.078,1.72)],[.002,.0035,.003,.0035,.002],13,head,8,2)
    w.path('Lower lip',[(-.025,-.080,1.716),(0,-.089,1.713),(.025,-.080,1.716)],[.002,.004,.002],13,head,8,3)
    w.loft('Indigo wrapped headcloth',[((0,.012,z),rx,ry) for z,rx,ry in [(1.85,.107,.097),(1.865,.111,.100),(1.89,.109,.097),(1.914,.096,.087),(1.938,.07,.062),(1.95,.012,.015)]],5,head,40,subdiv=2,ripple=.008)
    for i in range(3):
        z=1.866+i*.018
        w.loft('Headcloth folded edge '+str(i),[((0,.012,z),.111-i*.002,.100-i*.002),((0,.012,z+.004),.112-i*.002,.101-i*.002)],5,head,40)
    w.oval('Headcloth knot',(.087,.069,1.877),(.028,.027,.023),5,head,20,8)
    w.path('Headcloth tail',[(.09,.077,1.88),(.105,.095,1.83),(.095,.1,1.75)],[.018,.017,.008],5,head,10,3)
    for side in ('l','r'):
        prefix='metarig_'+side
        hip=w.bone(prefix+'leg1');knee=w.bone(prefix+'leg2');ankle=w.bone(prefix+'legankle')
        points=[hip,hip.lerp(knee,.22),hip.lerp(knee,.6),knee,knee.lerp(ankle,.26),knee.lerp(ankle,.65),ankle]
        radii=[.107,.113,.106,.087,.084,.065,.052]
        wb=[{prefix+'leg1':1},{prefix+'leg1':1},{prefix+'leg1':1},{prefix+'leg1':.45,prefix+'leg2':.55},{prefix+'leg2':1},{prefix+'leg2':1},{prefix+'legankle':1}]
        w.loft('Loose indigo trousers '+side,[(p,r,r*.87) for p,r in zip(points,radii)],5,wb,24,'path',3,ripple=.025)
        w.loft('Ankle wrapping '+side,[((ankle.x,ankle.y,z),.062,.057) for z in (.09,.13,.17)],4,prefix+'legankle',20,subdiv=2)
        foot=(ankle.x,ankle.y-.065,.047)
        w.oval('Bare foot '+side,(foot[0],foot[1],.060),(.062,.128,.042),6,prefix+'legankle',24,9)
        w.oval('Woven sandal sole '+side,(foot[0],foot[1],.022),(.069,.138,.018),8,prefix+'legankle',24,7)
        for offset in (-.04,.037):w.path('Sandal strap '+side+str(offset),[(foot[0]-.06,foot[1]+offset,.045),(foot[0],foot[1]+offset,.099),(foot[0]+.06,foot[1]+offset,.045)],[.009,.009,.009],8,prefix+'legankle',8,3)
        names=[prefix+n for n in ('armupper1','armupper2','armlower1','armlower2','armpalm')];p=[w.bone(n) for n in names]
        w.loft('Tunic sleeve '+side,[(p[0],.111,.10),(p[0].lerp(p[1],.7),.109,.1),(p[1],.10,.092),(p[1].lerp(p[2],.82),.086,.081)],4,[{names[0]:1},{names[0]:.6,names[1]:.4},{names[1]:1},{names[1]:.3,names[2]:.7}],24,'path',3,ripple=.03)
        w.path('Forearm '+side,[p[1].lerp(p[2],.72),p[2],p[2].lerp(p[3],.55),p[3],p[4]],[.073,.071,.065,.051,.038],6,[{names[1]:.3,names[2]:.7},{names[2]:1},{names[2]:.4,names[3]:.6},{names[3]:1},{names[4]:1}],24,3)
        direction=(p[4]-p[3]).normalized()
        w.loft('Palm '+side,[(p[4],.034,.022),(p[4]+direction*.045,.044,.024),(p[4]+direction*.082,.041,.02)],6,names[4],20,'path',3)
        for finger in ('thumb','index','middle'):
            ns=[prefix+'arm'+finger+str(i) for i in (1,2,3)];pts=[w.bone(n) for n in ns];end=pts[-1]+(pts[-1]-pts[-2])*.7
            w.path(side+' '+finger,pts+[end],[.012,.0115,.010,.0065],6,[{ns[0]:1},{ns[0]:.35,ns[1]:.65},{ns[1]:.25,ns[2]:.75},{ns[2]:1}],12,3)
        # Native middle-finger chain also carries the two smaller neighboring digits.
        ns=[prefix+'armmiddle'+str(i) for i in (1,2,3)];pts=[w.bone(n) for n in ns]
        axis=(p[4]-p[3]).cross(Vector((0,1,0))).normalized()
        for digit,offset,scale in [('ring',.018,.92),('little',.034,.78)]:
            pp=[pts[0]+axis*offset+(q-pts[0])*scale for q in pts];pp.append(pp[-1]+(pp[-1]-pp[-2])*.6)
            w.path(side+' '+digit,pp,[.010,.010,.008,.005],6,[{ns[0]:1},{ns[1]:1},{ns[2]:1},{ns[2]:1}],10,2)
    w.loft('Crimson waist sash',[((0,0,z),rx,ry) for z,rx,ry in [(.975,.183,.124),(1.005,.182,.127),(1.045,.185,.131)]],9,pelvis,32,subdiv=2,ripple=.018)
    w.path('Cross collar binding',[(.086,-.083,1.546),(.028,-.138,1.433),(-.078,-.145,1.31),(-.15,-.119,1.22)],[.012,.012,.012,.009],15,chest,10,3)
    w.path('Sash hanging end',[(-.13,-.117,1.005),(-.16,-.14,.92),(-.17,-.15,.80)],[.025,.027,.02],9,pelvis,12,3)
    if age>=3:
        w.loft('Light leather vest',[((0,0,z),rx,ry) for z,rx,ry in [(1.08,.185,.133),(1.19,.215,.146),(1.32,.238,.155),(1.44,.243,.145),(1.48,.225,.124)]],8,[{'metarig_spine1':.5,'metarig_spine2':.5},{'metarig_spine2':.5,chest:.5},{chest:1},{chest:1},{chest:1}],32,subdiv=2,ripple=.012)
        for z,rx,ry in [(1.10,.19,.138),(1.2,.219,.152),(1.32,.243,.160)]:
            w.loft('Vest stitched welt '+str(z),[((0,0,z),rx,ry),((0,0,z+.009),rx,ry)],15,chest,32)
    if age==4:
        for row,z in enumerate((1.16,1.245,1.33,1.415)):
            for column in range(9):
                a=math.pi*(1.16+column*.085);rx=.22 if row==0 else .246;ry=.153 if row==0 else .163
                x=rx*math.cos(a);y=ry*math.sin(a)
                w.oval('Lacquer lamella %s %s'%(row,column),(x,y,z),(.024,.008,.049),8,chest,10,5)
                w.oval('Lamellar tie %s %s'%(row,column),(x,y-.008,z+.025),(.005,.003,.005),15,chest,8,4)
        w.loft('Elite headband edge',[((0,.012,1.86),.112,.102),((0,.012,1.869),.113,.103)],9,head,40)

def buffalo(w):
    # Long low head, broad shoulders, moderate barrel and articulated cloven legs.
    w.loft('Trunk',[((0,y,z),rx,rz) for y,z,rx,rz in [(1.20,1.24,.13,.23),(1.06,1.25,.35,.39),(.8,1.27,.43,.43),(.4,1.25,.47,.47),(.0,1.26,.48,.45),(-.35,1.27,.45,.44),(-.62,1.24,.36,.38),(-.77,1.21,.24,.29)]],0,[{'root_m':1},{'root_m':1},{'root_m':.7,'spine1_m':.3},{'spine1_m':1},{'spine1_m':.4,'chest_m':.6},{'chest_m':1},{'chest_m':1},{'chest_m':.5,'neck_m':.5}],32,'y',3)
    w.loft('Neck and forehead',[((0,y,z),rx,rz) for y,z,rx,rz in [(-.56,1.21,.32,.34),(-.8,1.20,.29,.32),(-1.04,1.21,.245,.30),(-1.23,1.20,.25,.26),(-1.4,1.105,.20,.22),(-1.58,.99,.19,.17),(-1.76,.94,.205,.115),(-1.84,.94,.16,.08)]],0,[{'chest_m':1},{'neck_m':1},{'neck1_m':1},{'head_m':1},{'head_m':1},{'head_m':1},{'head_m':1},{'head_m':1}],32,'y',3)
    w.loft('Throat dewlap',[((0,y,z),rx,rz) for y,z,rx,rz in [(-.58,1.03,.21,.25),(-.85,.96,.15,.22),(-1.10,.98,.13,.16),(-1.36,.96,.12,.10)]],0,[{'chest_m':1},{'neck_m':1},{'neck1_m':1},{'head_m':1}],24,'y',2)
    main=['Trunk','Neck and forehead','Throat dewlap']
    for side in ('l','r'):
        for front in (True,False):
            ns=([n+side for n in ('frontrump_','fronthip_','frontknee_','frontankle_','fronttoes_')] if front else [n+side for n in ('backhip_','backknee_','backankle_','backtoes3_')])
            pts=[w.bone(n) for n in ns];name=('Foreleg ' if front else 'Hindleg ')+side
            rs=[.18,.14,.09,.06,.066] if front else [.24,.14,.078,.068]
            w.path(name,pts,rs,0,[{n:1} for n in ns],24,4);main.append(name)
    w.weld_hide(main,10000)
    for side,sign in [('l',1),('r',-1)]:
        for front in (True,False):
            bone=('fronttoes_' if front else 'backtoes3_')+side;p=w.bone(bone)
            for split in (-1,1):
                w.loft(('Front' if front else 'Back')+' cloven hoof '+side+str(split),[((p.x+split*.034,p.y-.06,.015),.031,.09),((p.x+split*.034,p.y-.055,.06),.037,.105),((p.x+split*.030,p.y-.036,.115),.03,.075)],2,bone,16,subdiv=2)
        # Broad flattened horn bases sweep outwards then back, ending in fine tips.
        pts=[(sign*x,y,z) for x,y,z in [(.19,-1.16,1.43),(.30,-1.13,1.45),(.46,-1.04,1.47),(.63,-.90,1.50),(.77,-.70,1.58),(.83,-.49,1.69),(.79,-.32,1.80),(.70,-.25,1.86)]]
        w.loft('Swept horn '+side,[(p,r,r*.72) for p,r in zip(pts,[.105,.10,.085,.067,.049,.032,.017,.0015])],1,'head_m',20,'path',3)
        w.loft('Leaf ear '+side,[((sign*.23,-1.18,1.34),.04,.035),((sign*.34,-1.16,1.32),.075,.037),((sign*.49,-1.10,1.30),.065,.024),((sign*.55,-1.07,1.30),.003,.003)],0,'ear_'+side,20,'path',3)
        w.oval('Eye socket '+side,(sign*.219,-1.36,1.22),(.034,.036,.031),0,'head_m',20,9)
        w.oval('Dark alert eye '+side,(sign*.242,-1.38,1.225),(.015,.021,.017),3,'head_m',20,9)
        w.oval('Eye highlight '+side,(sign*.251,-1.386,1.232),(.0035,.004,.004),14,'head_m',10,5)
        w.oval('Nostril '+side,(sign*.12,-1.826,.964),(.039,.012,.022),3,'head_m',20,8)
        w.path('Muzzle crease '+side,[(sign*.03,-1.838,.90),(sign*.13,-1.814,.899),(sign*.18,-1.76,.91)],[.005,.006,.004],2,'head_m',8,3)
    ns=['tail'+str(i)+'_m' for i in range(5)];pts=[w.bone(n) for n in ns]
    w.path('Flexible tail',pts,[.041,.033,.025,.019,.014],0,[{n:1} for n in ns],16,4)
    w.oval('Tail brush',pts[-1],(.04,.055,.095),7,ns[-1],20,10)

def javelin(w,age,projectile=False):
    # Native throwing tip=-Z; projectile tip=-Y. Origins are not interchangeable
    # with the longer held-state donor (+Z).
    w.loft('Bamboo shaft',[((0,0,z),r,r) for z,r in [(.12,.013),(.25,.016),(1.58,.015),(1.685,.009)]],12,None,16,subdiv=2)
    w.loft('Forged leaf point',[((0,0,z),rx,ry) for z,rx,ry in [(-.12,.0008,.0008),(-.025,.037,.009),(.055,.045,.011),(.12,.024,.01),(.20,.014,.009)]],10,None,8,subdiv=2)
    w.loft('Iron socket',[((0,0,.16),.019,.019),((0,0,.27),.019,.019)],10,None,16)
    w.loft('Cord grip',[((0,0,.52),.021,.021),((0,0,.69),.021,.021)],8,None,16,subdiv=4,ripple=.045)
    if age>=3:w.loft('Collar ring',[((0,0,.24),.024,.024),((0,0,.27),.024,.024)],11,None,16)
    for o in w.parts:
        for v in o.data.vertices:
            z=v.co.z
            if projectile:v.co=Vector((v.co.x,(z+.12)/1.805*1.709-.3535,-v.co.y))
            else:
                # Native shaft has a small authored lean; keep its socket origin.
                v.co.x+=max(0,z)*.037;v.co.y+=max(0,z)*.027
