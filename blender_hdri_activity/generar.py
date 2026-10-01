# -*- coding: utf-8 -*-
import bpy, math, os, sys, random, urllib.request
from mathutils import Vector

def arg(flag, default):
    if "--" in sys.argv:
        a=sys.argv[sys.argv.index("--")+1:]
        if flag in a and a.index(flag)+1<len(a): return a[a.index(flag)+1]
    return default

OUT=os.path.abspath(arg("--output", os.path.join(os.getcwd(),"output")))
os.makedirs(OUT, exist_ok=True)
HDRI=os.path.join(OUT,"stadium_01_1k.hdr")
HDRI_URL="https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/stadium_01_1k.hdr"

# ------------------------------------------------------------
# HDRI real en formato Radiance RGBE
# ------------------------------------------------------------
def rgbe(r,g,b):
    v=max(r,g,b)
    if v < 1e-32: return (0,0,0,0)
    m,e=math.frexp(v)
    s=(m*256.0)/v
    return (max(0,min(255,int(r*s))), max(0,min(255,int(g*s))), max(0,min(255,int(b*s))), max(0,min(255,e+128)))

def rle_channel(f,vals):
    i=0
    while i<len(vals):
        n=min(128,len(vals)-i)
        f.write(bytes([n])); f.write(bytes(vals[i:i+n])); i+=n

def make_hdri(path,w=512,h=256):
    sun_lon=math.radians(35); sun_lat=math.radians(26)
    with open(path,"wb") as f:
        f.write(b"#?RADIANCE\n")
        f.write(b"# HDRI sintetica para actividad Blender Mix Shader\n")
        f.write(b"FORMAT=32-bit_rle_rgbe\n\n")
        f.write(f"-Y {h} +X {w}\n".encode("ascii"))
        for y in range(h):
            lat=math.pi/2-(y+.5)/h*math.pi
            row=[]
            for x in range(w):
                lon=(x+.5)/w*2*math.pi-math.pi
                if lat>=0:
                    t=max(0,min(1,lat/(math.pi/2)))
                    r=(.74*(1-t)+.16*t)*1.65
                    g=(.84*(1-t)+.42*t)*1.65
                    b=(1.00*(1-t)+1.30*t)*1.65
                else:
                    t=max(0,min(1,-lat/(math.pi/2)))
                    wave=.07*(.5+.5*math.sin(lon*5))
                    r=.18+.13*t+wave
                    g=.32+.08*(1-t)+wave*.55
                    b=.10+.05*(1-t)
                ca=math.sin(lat)*math.sin(sun_lat)+math.cos(lat)*math.cos(sun_lat)*math.cos(lon-sun_lon)
                ang=math.acos(max(-1,min(1,ca)))
                if ang<math.radians(2.5):
                    k=1-ang/math.radians(2.5)
                    r+=32*k; g+=28*k; b+=20*k
                row.append(rgbe(r,g,b))
            f.write(bytes([2,2,(w>>8)&255,w&255]))
            for c in range(4): rle_channel(f,[p[c] for p in row])
    print("HDRI creada",path)

# ------------------------------------------------------------
# Helpers Blender
# ------------------------------------------------------------
def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def engine(sc):
    for e in ("BLENDER_EEVEE_NEXT","BLENDER_EEVEE"):
        try: sc.render.engine=e; break
        except: pass
    sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'
    try: sc.view_settings.look='AgX - Medium High Contrast'
    except:
        try: sc.view_settings.look='Medium High Contrast'
        except: pass

def inp(node,names,value):
    if isinstance(names,str): names=[names]
    for n in names:
        if node.inputs.get(n):
            node.inputs[n].default_value=value; return

def principled(name,color,metal=0,rough=.5,emit=None,estr=0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    o=nt.nodes.new('ShaderNodeOutputMaterial'); o.location=(320,0)
    p=nt.nodes.new('ShaderNodeBsdfPrincipled'); p.location=(0,0)
    inp(p,'Base Color',color); inp(p,'Metallic',metal); inp(p,'Roughness',rough)
    if emit:
        inp(p,['Emission Color','Emission'],emit); inp(p,'Emission Strength',estr)
    nt.links.new(p.outputs['BSDF'],o.inputs['Surface'])
    return m

def mixmat(name,a,b,fac=.3,ma=0,mb=.8,ra=.55,rb=.18):
    m=bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    o=nt.nodes.new('ShaderNodeOutputMaterial'); o.location=(520,0)
    mx=nt.nodes.new('ShaderNodeMixShader'); mx.location=(260,0); mx.name='MIX_SHADER_DEMO'; mx.label='MIX SHADER'
    mx.inputs[0].default_value=fac
    p1=nt.nodes.new('ShaderNodeBsdfPrincipled'); p1.location=(-80,110); p1.label='Shader A'
    p2=nt.nodes.new('ShaderNodeBsdfPrincipled'); p2.location=(-80,-120); p2.label='Shader B'
    inp(p1,'Base Color',a); inp(p1,'Metallic',ma); inp(p1,'Roughness',ra)
    inp(p2,'Base Color',b); inp(p2,'Metallic',mb); inp(p2,'Roughness',rb)
    nt.links.new(p1.outputs['BSDF'],mx.inputs[1]); nt.links.new(p2.outputs['BSDF'],mx.inputs[2]); nt.links.new(mx.outputs['Shader'],o.inputs['Surface'])
    return m

def setup_world(sc):
    w=bpy.data.worlds.new('Mundo_HDRI') if not bpy.data.worlds else bpy.data.worlds[0]
    sc.world=w; w.use_nodes=True
    nt=w.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputWorld'); out.location=(600,0)
    bg=nt.nodes.new('ShaderNodeBackground'); bg.location=(360,0); bg.inputs['Strength'].default_value=.58
    env=nt.nodes.new('ShaderNodeTexEnvironment'); env.location=(80,0); env.name='IMAGEN_HDRI'; env.label='IMAGEN HDRI'
    env.image=bpy.data.images.load(HDRI,check_existing=True)
    tc=nt.nodes.new('ShaderNodeTexCoord'); tc.location=(-180,0)
    nt.links.new(tc.outputs['Generated'],env.inputs['Vector'])
    nt.links.new(env.outputs['Color'],bg.inputs['Color']); nt.links.new(bg.outputs['Background'],out.inputs['Surface'])
    return w

def box(name,loc,dims,mat,bevel=.04):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        md=o.modifiers.new('Bevel','BEVEL'); md.width=bevel; md.segments=3
    o.data.materials.append(mat); return o

def look(o,t):
    o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()

def camera(sc,loc,t,lens=50):
    bpy.ops.object.camera_add(location=loc); c=bpy.context.object; c.data.lens=lens; sc.camera=c; look(c,t); return c

def area(loc,t,e=900,size=6,col=(1,1,1)):
    bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.data.energy=e; l.data.size=size; l.data.color=col; look(l,t)

def sun():
    bpy.ops.object.light_add(type='SUN',rotation=(math.radians(25),0,math.radians(35))); bpy.context.object.data.energy=1.2

def text_obj(body,loc,mat,size=.55):
    bpy.ops.object.text_add(location=loc); o=bpy.context.object; o.data.body=body; o.data.align_x='CENTER'; o.data.size=size; o.data.extrude=.025; o.data.bevel_depth=.01; o.data.materials.append(mat); return o

def render(sc,c,loc,t,name,lens=50):
    c.location=loc; c.data.lens=lens; look(c,t); sc.render.filepath=os.path.join(OUT,name); bpy.ops.render.render(write_still=True)

def save(path):
    try: bpy.ops.file.pack_all()
    except: pass
    bpy.ops.wm.save_as_mainfile(filepath=path)

def practice():
    clear(); sc=bpy.context.scene; sc.name='Practica_MixShader_HDRI'; engine(sc); setup_world(sc)
    sc['ACTIVIDAD']='Practica docente: materiales, Mix Shader e IMAGEN HDRI'
    floor=mixmat('Cobre_MixShader',(.32,.06,.015,1),(.9,.32,.025,1),.42,0,.95,.5,.13)
    blue=mixmat('Suzanne_MixShader',(.015,.04,.42,1),(.03,.25,1,1),.38,0,.88,.35,.10)
    green=principled('Verde',(.08,.74,.37,1),.08,.25)
    gold=mixmat('Cilindro_MixShader',(.26,.16,.01,1),(1,.48,.01,1),.52,0,.95,.5,.12)
    black=principled('Negro',(.005,.005,.008,1),.5,.2)
    white=principled('Texto',(1,1,1,1),0,.4)
    box('Plano_reflectivo',(0,0,.08),(10,8,.16),floor,.06)
    bpy.ops.mesh.primitive_monkey_add(location=(-1.35,0,1.45)); s=bpy.context.object; s.name='Suzanne_MixShader'; s.scale=(1.35,)*3; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in s.data.polygons: p.use_smooth=True
    md=s.modifiers.new('Subdivision','SUBSURF'); md.levels=2; md.render_levels=2; s.data.materials.append(blue)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.88,depth=1.7,location=(2.35,.35,.93)); bpy.context.object.data.materials.append(gold)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.88,depth=1.15,location=(2.35,.35,2.35)); bpy.context.object.data.materials.append(green)
    bpy.ops.mesh.primitive_torus_add(major_radius=.89,minor_radius=.085,major_segments=64,minor_segments=16,location=(2.35,.35,1.70)); bpy.context.object.data.materials.append(black)
    text_obj('MIX SHADER + HDRI',(0,-3.55,.18),white,.52)
    area((-4,-3,7),(0,0,1),950,5.5,(1,.82,.65)); area((4,2,5),(0,0,1.2),700,4,(.55,.72,1)); sun()
    c=camera(sc,(10,-12,8),(0,0,1.2),52)
    path=os.path.join(OUT,'01_Practica_MixShader_HDRI.blend'); save(path)
    render(sc,c,(10,-12,8),(0,0,1.2),'01_practica_frontal.png',52)
    render(sc,c,(-9,-10,6.5),(0,0,1.2),'02_practica_izquierda.png',55)
    render(sc,c,(8,8,7),(0,0,1.1),'03_practica_posterior.png',55)
    render(sc,c,(0,-1,13),(0,0,.6),'04_practica_superior.png',48)
    save(path)

def maze_data(w=9,h=7,seed=33):
    random.seed(seed); W={(x,y):{'N':1,'S':1,'E':1,'W':1} for y in range(h) for x in range(w)}
    vis={(0,0)}; st=[(0,0)]; ds=[('N',0,1,'S'),('S',0,-1,'N'),('E',1,0,'W'),('W',-1,0,'E')]
    while st:
        x,y=st[-1]; op=[]
        for d,dx,dy,rv in ds:
            nx,ny=x+dx,y+dy
            if 0<=nx<w and 0<=ny<h and (nx,ny) not in vis: op.append((d,dx,dy,rv,nx,ny))
        if not op: st.pop(); continue
        d,dx,dy,rv,nx,ny=random.choice(op); W[(x,y)][d]=0; W[(nx,ny)][rv]=0; vis.add((nx,ny)); st.append((nx,ny))
    W[(0,0)]['W']=0; W[(w-1,h-1)]['E']=0; return W


def material_concreto(name='Concreto_Rugoso'):
    m=bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); out.location=(620,0)
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled'); bs.location=(360,0)
    inp(bs,'Roughness',.82); inp(bs,'Metallic',0.0)
    tex=nt.nodes.new('ShaderNodeTexNoise'); tex.location=(-360,30)
    inp(tex,'Scale',5.0); inp(tex,'Detail',7.0); inp(tex,'Roughness',.78)
    ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.location=(-100,90)
    ramp.color_ramp.elements[0].color=(.075,.085,.095,1)
    ramp.color_ramp.elements[1].color=(.38,.42,.45,1)
    bump=nt.nodes.new('ShaderNodeBump'); bump.location=(110,-120)
    inp(bump,'Strength',.38); inp(bump,'Distance',.22)
    tc=nt.nodes.new('ShaderNodeTexCoord'); tc.location=(-600,30)
    nt.links.new(tc.outputs['Generated'],tex.inputs['Vector'])
    nt.links.new(tex.outputs['Fac'],ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    nt.links.new(tex.outputs['Fac'],bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    return m

def material_madera(name='Madera_Veteada'):
    m=bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); out.location=(640,0)
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled'); bs.location=(380,0)
    inp(bs,'Roughness',.42); inp(bs,'Metallic',0.0)
    wave=nt.nodes.new('ShaderNodeTexWave'); wave.location=(-330,40)
    wave.wave_type='BANDS'; wave.bands_direction='X'
    inp(wave,'Scale',3.7); inp(wave,'Distortion',7.0); inp(wave,'Detail',5.0); inp(wave,'Detail Scale',2.0)
    ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.location=(-80,70)
    ramp.color_ramp.elements[0].color=(.055,.012,.004,1)
    ramp.color_ramp.elements[1].color=(.48,.16,.035,1)
    bump=nt.nodes.new('ShaderNodeBump'); bump.location=(130,-120)
    inp(bump,'Strength',.24); inp(bump,'Distance',.10)
    tc=nt.nodes.new('ShaderNodeTexCoord'); tc.location=(-580,40)
    nt.links.new(tc.outputs['Generated'],wave.inputs['Vector'])
    nt.links.new(wave.outputs['Color'],ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    nt.links.new(wave.outputs['Fac'],bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    return m

def material_metal(name='Metal_Pulido'):
    return principled(name,(.055,.09,.16,1),.96,.16)

def material_ladrillo(name='Ladrillo'):
    m=bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); out.location=(640,0)
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled'); bs.location=(380,0)
    inp(bs,'Roughness',.72)
    brick=nt.nodes.new('ShaderNodeTexBrick'); brick.location=(-300,30)
    inp(brick,'Color1',(.34,.035,.012,1)); inp(brick,'Color2',(.62,.105,.025,1)); inp(brick,'Mortar',(.025,.025,.025,1))
    inp(brick,'Scale',7.0); inp(brick,'Mortar Size',.035)
    bump=nt.nodes.new('ShaderNodeBump'); bump.location=(130,-110)
    inp(bump,'Strength',.30); inp(bump,'Distance',.16)
    tc=nt.nodes.new('ShaderNodeTexCoord'); tc.location=(-560,30)
    nt.links.new(tc.outputs['Generated'],brick.inputs['Vector'])
    nt.links.new(brick.outputs['Color'],bs.inputs['Base Color'])
    nt.links.new(brick.outputs['Fac'],bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    return m

def material_marmol(name='Marmol'):
    m=bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); out.location=(640,0)
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled'); bs.location=(380,0)
    inp(bs,'Roughness',.24); inp(bs,'Metallic',.05)
    noise=nt.nodes.new('ShaderNodeTexNoise'); noise.location=(-350,20)
    inp(noise,'Scale',3.0); inp(noise,'Detail',9.0); inp(noise,'Roughness',.72); inp(noise,'Distortion',2.8)
    ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.location=(-80,80)
    ramp.color_ramp.elements[0].position=.33
    ramp.color_ramp.elements[0].color=(.018,.025,.04,1)
    ramp.color_ramp.elements[1].position=.62
    ramp.color_ramp.elements[1].color=(.92,.95,1.0,1)
    bump=nt.nodes.new('ShaderNodeBump'); bump.location=(130,-120)
    inp(bump,'Strength',.12); inp(bump,'Distance',.06)
    tc=nt.nodes.new('ShaderNodeTexCoord'); tc.location=(-590,20)
    nt.links.new(tc.outputs['Generated'],noise.inputs['Vector'])
    nt.links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    nt.links.new(noise.outputs['Fac'],bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    return m

def material_piso(name='Piso_Ceramico'):
    m=bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); out.location=(600,0)
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled'); bs.location=(350,0)
    inp(bs,'Roughness',.32); inp(bs,'Metallic',.08)
    chk=nt.nodes.new('ShaderNodeTexChecker'); chk.location=(-170,40)
    inp(chk,'Color1',(.025,.03,.038,1)); inp(chk,'Color2',(.12,.14,.16,1)); inp(chk,'Scale',18.0)
    tc=nt.nodes.new('ShaderNodeTexCoord'); tc.location=(-420,40)
    nt.links.new(tc.outputs['Generated'],chk.inputs['Vector'])
    nt.links.new(chk.outputs['Color'],bs.inputs['Base Color'])
    nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    return m

def maze():
    clear(); sc=bpy.context.scene; sc.name='Laberinto_HDRI_Materiales'; engine(sc); setup_world(sc)
    sc['ACTIVIDAD']='Laberinto con IMAGEN HDRI y diferentes tipos de materiales'
    sc['MATERIALES']='Concreto rugoso, madera veteada, metal pulido, ladrillo y marmol'

    concreto=material_concreto()
    madera=material_madera()
    metal=material_metal()
    ladrillo=material_ladrillo()
    marmol=material_marmol()
    materiales=[concreto,madera,metal,ladrillo,marmol]

    floor=material_piso()
    ent=principled('Entrada',(.05,.8,.16,1),0,.25,(.05,.8,.16,1),4)
    sal=principled('Salida',(1,.10,.02,1),0,.25,(1,.06,.01,1),4)
    white=principled('Texto',(1,1,1,1),0,.4)

    w,h=9,7; cell=2.15; th=.18; wh=2.45; tx=w*cell; ty=h*cell
    box('Piso_Ceramico',(0,0,-.10),(tx+2.2,ty+2.2,.2),floor,.06)
    D=maze_data(w,h)

    def pickmat(x,y,ori):
        oi={'N':0,'S':1,'E':2,'W':3}.get(ori,0)
        return materiales[(x*2+y*3+oi)%len(materiales)]

    def wallobj(prefix,x,y,ori,loc,dims):
        mat=pickmat(x,y,ori)
        safe=mat.name.replace(' ','_')
        return box(f'{prefix}{x}_{y}_{safe}',loc,dims,mat,.04)

    for y in range(h):
        for x in range(w):
            cx=(x-(w-1)/2)*cell; cy=(y-(h-1)/2)*cell; z=wh/2; d=D[(x,y)]
            if d['N']: wallobj('N',x,y,'N',(cx,cy+cell/2,z),(cell+th,th,wh))
            if d['W']: wallobj('W',x,y,'W',(cx-cell/2,cy,z),(th,cell+th,wh))
            if y==0 and d['S']: wallobj('S',x,y,'S',(cx,cy-cell/2,z),(cell+th,th,wh))
            if x==w-1 and d['E']: wallobj('E',x,y,'E',(cx+cell/2,cy,z),(th,cell+th,wh))

    entrance=(-tx/2-1.15,-(h-1)/2*cell,.55); exitp=(tx/2+1.15,(h-1)/2*cell,.55)
    for nm,p,m in [('ENTRADA',entrance,ent),('SALIDA',exitp,sal)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=.42,location=p)
        bpy.context.object.name=nm; bpy.context.object.data.materials.append(m)

    # Muestras visibles de materiales fuera del laberinto.
    labels=[('CONCRETO',concreto),('MADERA',madera),('METAL',metal),('LADRILLO',ladrillo),('MARMOL',marmol)]
    sx=-6.0
    for i,(label,mat) in enumerate(labels):
        x=sx+i*3.0
        box('Muestra_'+label,(x,-ty/2-2.15,.38),(1.45,.85,.75),mat,.08)
        t=text_obj(label,(x,-ty/2-2.72,.02),white,.28)
        t.rotation_euler=(0,0,0)

    text_obj('LABERINTO HDRI - MULTIMATERIAL',(0,-ty/2-3.55,.03),white,.54)
    area((-7,-6,12),(0,0,0),1650,8,(1,.82,.67))
    area((8,6,10),(0,0,1),1150,7,(.55,.72,1))
    sun()

    c=camera(sc,(18,-22,20),(0,-.6,.9),48)
    path=os.path.join(OUT,'02_Laberinto_HDRI.blend')
    save(path)
    render(sc,c,(18,-22,20),(0,-.6,.9),'05_laberinto_diagonal.png',48)
    render(sc,c,(0,-1,30),(0,0,0),'06_laberinto_superior.png',52)
    render(sc,c,(-16,-14,7),(0,-1,1),'07_laberinto_entrada.png',52)
    render(sc,c,(16,14,8),(0,1,1),'08_laberinto_salida.png',52)
    render(sc,c,(0,-20,6),(0,-ty/2-1.5,.5),'09_muestras_materiales.png',55)
    save(path)

try:
    print("Descargando HDRI fotografica CC0 de Poly Haven...")
    urllib.request.urlretrieve(HDRI_URL,HDRI)
    print("HDRI descargada",HDRI,os.path.getsize(HDRI),"bytes")
except Exception as e:
    print("No se pudo descargar HDRI fotografica; se usara HDRI sintetica:",e)
    make_hdri(HDRI)
practice(); maze()
print("LISTO", sorted(os.listdir(OUT)))
