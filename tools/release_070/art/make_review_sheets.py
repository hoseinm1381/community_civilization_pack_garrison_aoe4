"""Arrange unaltered Blender viewport captures into labeled review sheets."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art')
FONT=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',30)
SMALL=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',22)
ASSETS=[('garden','Imperial Garden: lotus court + animal service yard','iso'),('foundry','Trung Foundaries: open casting court + workshops','iso'),('wonder','Wonder: Kinh Thien-inspired palace','iso'),('university','University: retained stock building + scholarly court','iso')]
sheet=Image.new('RGB',(1800,1560),(35,37,39));draw=ImageDraw.Draw(sheet)
draw.text((28,16),'0.7.0 BLOCKOUT REVIEW - forms and layout, before detailed art',font=FONT,fill=(240,235,224))
for i,(key,title,direction) in enumerate(ASSETS):
    im=Image.open(OUT/f'{key}-{direction}-review.png').convert('RGB')
    im=im.crop((130,160,1270,1000));im.thumbnail((870,640),Image.Resampling.LANCZOS)
    x=20+(i%2)*900;y=78+(i//2)*735
    draw.text((x+10,y),title,font=SMALL,fill=(234,222,196));sheet.paste(im,(x+(870-im.width)//2,y+40))
draw.text((30,1510),'Neutral preview colours; no final ornament, textures, LODs or native-game proof.',font=SMALL,fill=(196,196,196))
sheet.save(OUT/'four-blockouts-review.png')
for key,title,_ in ASSETS:
    canvas=Image.new('RGB',(1800,1140),(35,37,39));d=ImageDraw.Draw(canvas);d.text((20,10),title+' - six-side inspection',font=FONT,fill='white')
    for i,side in enumerate(('front','rear','left','right','top','bottom')):
        im=Image.open(OUT/f'{key}-{side}-review.png').convert('RGB');im=im.crop((130,160,1270,1000));im.thumbnail((580,490))
        x=(i%3)*600+10;y=(i//3)*540+60;d.text((x,y),side.upper(),font=SMALL,fill='white');canvas.paste(im,(x,y+30))
    canvas.save(OUT/f'{key}-six-side-sheet.png')
print(OUT/'four-blockouts-review.png')
