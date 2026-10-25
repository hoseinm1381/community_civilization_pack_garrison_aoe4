"""Compose already-rendered reference/custom panels; never edits source media."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont


def main():
 ap=argparse.ArgumentParser();ap.add_argument('capture_folder',type=Path);args=ap.parse_args()
 folder=args.capture_folder.resolve();root=Path(__file__).resolve().parents[3]
 if not folder.is_relative_to((root/'output/release_075/comparators').resolve()):raise ValueError('Not comparator-owned output')
 capture=json.loads((folder/'capture.json').read_text());views=('iso','gameplay','front')
 panels=('reference','custom') if 'custom_source' in capture else ('reference',)
 font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',22)
 sheet=Image.new('RGB',(1100*len(panels),910*len(views)+110),(242,242,238));draw=ImageDraw.Draw(sheet)
 for y,view in enumerate(views):
  for x,panel in enumerate(panels):
   path=folder/panel/(view+'.png')
   with Image.open(path) as image:
    if image.size!=(1100,850):raise ValueError('Unexpected panel dimensions')
    sheet.paste(image.convert('RGB'),(x*1100,y*910+50))
   label=(capture['reference']+' | partial official static reference') if panel=='reference' else 'Custom candidate | authoring source'
   draw.text((x*1100+20,y*910+12),label+' | '+view,font=font,fill=(20,20,20))
 bottom=910*len(views)
 draw.text((20,bottom+10),'Matched camera/light convention and apparent size; physical scale normalized independently.',font=font,fill=(20,20,20))
 draw.text((20,bottom+40),'Official panel excludes ambiguous debris/outskirts. Layered preview materials; not native appearance proof.',font=font,fill=(20,20,20))
 target=folder/'comparison-sheet.png'
 if target.exists():raise FileExistsError('Preserve previous comparison sheet')
 sheet.save(target);print(target)


if __name__=='__main__':main()
