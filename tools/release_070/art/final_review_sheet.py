"""Arrange existing Blender screenshots without changing the depicted art."""
from pathlib import Path
from PIL import Image,ImageDraw
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/final-previews')
for suffix in ('material-iso','material-iso_back','solid-iso-distance'):
    canvas=Image.new('RGB',(1600,1640),'#222426');draw=ImageDraw.Draw(canvas)
    for i,name in enumerate(('garden','foundry','wonder','university')):
        p=OUT/(name+'-'+suffix+'.png');im=Image.open(p).convert('RGB');im.thumbnail((800,780))
        x=(i%2)*800+(800-im.width)//2;y=(i//2)*820+35
        canvas.paste(im,(x,y));draw.text(((i%2)*800+20,(i//2)*820+12),name.upper()+' | Blender source review',fill='white')
    canvas.save(OUT/('four-'+suffix+'.png'))
