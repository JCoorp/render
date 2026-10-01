# -*- coding: utf-8 -*-
import bpy, math, os, sys, random
from mathutils import Vector

def arg(flag, default):
    if "--" in sys.argv:
        a=sys.argv[sys.argv.index("--")+1:]
        if flag in a and a.index(flag)+1<len(a): return a[a.index(flag)+1]
    return default

OUT=os.path.abspath(arg("--output", os.path.join(os.getcwd(),"output")))
os.makedirs(OUT, exist_ok=True)

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

def inp(node, names, value):
    if isinstance(names,str): names=[names]
    for n in names:
        if node.inputs.get(n):
            node.inputs[n].default_value=value; return

def principled(name, color, metal=0, rough=.5, emit=None, estr=0):
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
    w=bpy.data.worlds.new('Mundo_HDRI_Procedural') if not bpy.data.worlds else bpy.data.worlds[0]
    sc.world=w; w.use_nodes=True
    nt=w.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputWorld'); out.location=(600,0)
    bg=nt.nodes.new('ShaderNodeBackground'); bg.location=(360,0); bg.inputs['Strength'].default_value=.55
    # Fondo panoramico de alto contraste tipo HDRI usando nodos de mundo.
    tex=nt.nodes.new('ShaderNodeTexCoord'); tex.location=(-650,0)
    sep=nt.nodes.new('ShaderNodeSeparateXYZ'); sep.location=(-430,0)
    ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.location=(-180,0)
    ramp.color_ramp.elements[0].position=.20; ramp.color_ramp.elements[0].color=(.06,.11,.03,1)
    ramp.color_ramp.elements[1].position=.70; ramp.color_ramp.elements[1].color=(.18,.48,1.0,1)
    sun=nt.nodes.new('ShaderNodeTexGradient'); sun.gradient_type='RADIAL'; sun.location=(-180,-180)
    nt.links.new(tex.outputs['Generated'],sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'],ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'],bg.inputs['Color']); nt.links.new(bg.outputs['Background'],out.inputs['Surface'])
    return w

def box(name, loc, dims, mat, bevel=.04):
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
    sc['ACTIVIDAD']='Practica docente: materiales, Mix Shader y ambiente HDRI'
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

def maze():
    clear(); sc=bpy.context.scene; sc.name='Laberinto_HDRI'; engine(sc); setup_world(sc)
    sc['ACTIVIDAD']='Propuesta de laberinto con ambiente HDRI, como se solicita aprox. en el minuto 33'
    wall=mixmat('Muros_MixShader',(.025,.10,.28,1),(.08,.58,1,1),.26,0,.76,.58,.18)
    floor=principled('Piso',(.04,.05,.06,1),.15,.38); edge=principled('Marco',(.015,.015,.02,1),.8,.18)
    ent=principled('Entrada',(.05,.8,.16,1),0,.25,(.05,.8,.16,1),4); sal=principled('Salida',(1,.10,.02,1),0,.25,(1,.06,.01,1),4); white=principled('Texto',(1,1,1,1),0,.4)
    w,h=9,7; cell=2.15; th=.18; wh=2.45; tx=w*cell; ty=h*cell
    box('Piso',(0,0,-.10),(tx+2.2,ty+2.2,.2),floor,.06)
    D=maze_data(w,h)
    for y in range(h):
        for x in range(w):
            cx=(x-(w-1)/2)*cell; cy=(y-(h-1)/2)*cell; z=wh/2; d=D[(x,y)]
            if d['N']: box(f'N{x}_{y}',(cx,cy+cell/2,z),(cell+th,th,wh),wall)
            if d['W']: box(f'W{x}_{y}',(cx-cell/2,cy,z),(th,cell+th,wh),wall)
            if y==0 and d['S']: box(f'S{x}_{y}',(cx,cy-cell/2,z),(cell+th,th,wh),wall)
            if x==w-1 and d['E']: box(f'E{x}_{y}',(cx+cell/2,cy,z),(th,cell+th,wh),wall)
    entrance=(-tx/2-1.15,-(h-1)/2*cell,.55); exitp=(tx/2+1.15,(h-1)/2*cell,.55)
    for nm,p,m in [('ENTRADA',entrance,ent),('SALIDA',exitp,sal)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=.42,location=p); bpy.context.object.name=nm; bpy.context.object.data.materials.append(m)
    text_obj('LABERINTO HDRI',(0,-ty/2-1.55,.03),white,.62)
    area((-7,-6,12),(0,0,0),1500,8,(1,.82,.67)); area((8,6,10),(0,0,1),1000,7,(.55,.72,1)); sun()
    c=camera(sc,(18,-22,20),(0,0,.9),48)
    path=os.path.join(OUT,'02_Laberinto_HDRI.blend'); save(path)
    render(sc,c,(18,-22,20),(0,0,.9),'05_laberinto_diagonal.png',48)
    render(sc,c,(0,-1,30),(0,0,0),'06_laberinto_superior.png',52)
    render(sc,c,(-16,-14,7),(0,-1,1),'07_laberinto_entrada.png',52)
    render(sc,c,(16,14,8),(0,1,1),'08_laberinto_salida.png',52)
    save(path)

practice(); maze()
print("LISTO", sorted(os.listdir(OUT)))
