#!/usr/bin/env python3
"""Render compact, linked schedule posters with festival-day overnight timing."""
import json, math, re
from datetime import datetime
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parent
W,H=1684,1190
STAGES=['The Meadow','The Hallows','The Amphitheatre','Spirit Lake','DEF Off Limits']
DAY_COLORS=['#59a9cc','#9365b4','#ff795c','#2abd86']
WHITE=colors.white

def read(name,default):
 p=ROOT/'data'/name
 return json.loads(p.read_text()) if p.exists() else default

def setup_fonts():
 pdfmetrics.registerFont(TTFont('Condensed',str(ROOT/'references'/'gravity.ttf') if (ROOT/'references'/'gravity.ttf').exists() else '/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf'))
 pdfmetrics.registerFont(TTFont('Body','/System/Library/Fonts/Supplemental/Arial.ttf'))
 pdfmetrics.registerFont(TTFont('BodyBold','/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
 try:
  for name,file in [('Title','marvin'),('Gravity','gravity')]:
   dest=ROOT/'references'/f'{file}.ttf'
   if not dest.exists():
    from fontTools.ttLib import TTFont as Font
    font=Font(ROOT/'references'/f'{file}.woff2');font.flavor=None
    dest=ROOT/'tmp'/f'{file}.ttf';dest.parent.mkdir(exist_ok=True);font.save(dest)
   pdfmetrics.registerFont(TTFont(name,str(dest)))
 except Exception:
  pass

def txt(c,x,y,text,size=14,font='Condensed',center=False,color=WHITE):
 c.setFillColor(color);c.setFont(font,size)
 (c.drawCentredString if center else c.drawString)(x,y,clean(text))

def clean(s):
 return str(s or '').replace('’',"'").replace('—','-').replace('–','-').replace('¥ØU$UK€ ¥UK1MAT$U','YOUSUKE YUKIMATSU')

def wrap(text,width,size,font='Condensed'):
 lines=[];line=''
 for word in clean(text).split():
  candidate=(line+' '+word).strip()
  if line and pdfmetrics.stringWidth(candidate,font,size)>width:
   lines.append(line);line=word
  else:line=candidate
 if line:lines.append(line)
 return lines

def timevalue(t):
 h,m=map(int,t[:5].split(':'));return h+m/60+(24 if h<8 else 0)

def clock(t):
 if not t:return 'TBA'
 return datetime.strptime(t[:5],'%H:%M').strftime('%-I:%M%p')

def lane(s):
 stage=s.get('stage') or s.get('location') or 'Location TBA'
 if 'silent disco' in stage.lower():
  m=re.search(r'(Blue|Red|Green) headphone channel',s.get('notes',''),re.I)
  return 'Wooksville / '+(m[1].upper() if m else 'SILENT')
 return stage

def header(c,day,subtitle,number,total,nonmusic=False):
 color=DAY_COLORS[max(0,min(3,int(day[-2:])-22))] if day else '#9b6abb'
 ref=ROOT/'references'/('official-'+(datetime.strptime(day,'%Y-%m-%d').strftime('%A').lower() if day and day[-2:]!='21' else 'thursday')+'.png')
 c.setFillColor(colors.black);c.rect(0,0,W,H,fill=1,stroke=0)
 if ref.exists():
  c.drawImage(str(ref),0,0,width=W,height=H,mask='auto')
  c.setFillColor(colors.black);c.rect(85,42,W-170,H-242,fill=1,stroke=0)
  c.rect(330,H-205,W-660,205,fill=1,stroke=0)
  c.rect(0,0,W,H-185,fill=1,stroke=0)
 logo=ROOT/'references'/'logo.png'
 if logo.exists():c.drawImage(str(logo),W/2-150,H-81,width=300,height=57,preserveAspectRatio=True,anchor='c',mask='auto')
 title=datetime.strptime(day,'%Y-%m-%d').strftime('%a %m/%d/%y').upper() if day else 'ANNOUNCED / TIME TBA'
 if nonmusic:title='BEYOND THE MUSIC'+(' / '+datetime.strptime(day,'%Y-%m-%d').strftime('%a %m/%d').upper() if day else '')
 titlefont='Title' if 'Title' in pdfmetrics.getRegisteredFontNames() else 'Condensed'
 txt(c,W/2,H-140,title,55 if not nonmusic else 43,titlefont,True,colors.HexColor(color))
 txt(c,W/2,H-171,subtitle,14,'BodyBold',True)
 meta=read('metadata.json',{});stamp=meta.get('lastVerified') or meta.get('last_verified') or 'October 21, 2026'
 txt(c,90,26,'UNOFFICIAL FAN GUIDE / TIMES EASTERN / AFTER-MIDNIGHT SETS STAY WITH THE LABELED DAY / END TBA BOXES MARK STARTS ONLY',10,'BodyBold')
 txt(c,W-90,26,f'{number}/{total}',11,center=False)
 txt(c,90,10,'CHECKED '+str(stamp)+' / CAMPGROUND PLANS MAY CHANGE. TAP A SET FOR ITS SOURCE.',9,'Body')
 c.linkURL('https://hulaween.com/schedule/',(90,5,950,36),relative=0)
 return color

def block(c,s,x,y,width,height,color,point=False):
 c.setStrokeColor(WHITE);c.setLineWidth(1.2)
 c.setFillColor(colors.HexColor(color));c.roundRect(x,y,width,height,9,stroke=1,fill=1)
 title=(s.get('artist') or s.get('title') or s.get('name') or 'TBA').upper()
 if title.startswith('BIG GRAMATIK'):title='BIG GRAMATIK\nBIG GIGANTIC B2B GRAMATIK'
 size=19 if width>110 else 15
 if height<35:size=min(size,14)
 for _ in range(24):
  lines=[]
  for part in title.split('\n'):lines.extend(wrap(part,width-12,size))
  if len(lines)*size*.98+min(13.5,height*.27)+8<=height and max([pdfmetrics.stringWidth(line,'Condensed',size) for line in lines] or [0])<=width-12:break
  size-=.7
 size=max(5.5,size)
 lines=[]
 for part in title.split('\n'):lines.extend(wrap(part,width-12,size))
 times=clock(s.get('start'))+(' - '+clock(s.get('end')) if s.get('end') else ' / END TBA')
 timefont=min(13.5,max(8.2,width/11))
 if height<35:timefont=min(timefont,height*.27)
 while pdfmetrics.stringWidth(times,'Condensed',timefont)>width-8:timefont-=.3
 leading=size*1.0;desc=wrap(s.get('description',''),width-24,14,'Body') if s.get('kind')=='activity' else []
 available_lines=max(0,int((height-len(lines)*leading-timefont-12)/17))
 if len(desc)>available_lines:desc=[]
 totalh=len(lines)*leading+timefont+4+len(desc)*17
 timebase=y+(height-totalh)/2+len(desc)*17+3
 base=timebase+timefont+4+(len(lines)-1)*leading
 for line in lines:txt(c,x+width/2,base,line,size,center=True);base-=leading
 txt(c,x+width/2,timebase,times,timefont,center=True)
 base=timebase-18
 for line in desc:
  txt(c,x+width/2,base,line,14,'Body',True);base-=17
 if s.get('sourceUrl'):c.linkURL(s['sourceUrl'],(x,y,x+width,y+height),relative=0)

def schedule(c,day,entries,n,total,nonmusic=False):
 subtitle='OFFICIAL STAGES + CAMPGROUND SETS / LATEST SETS AT THE TOP' if not nonmusic else 'WORKSHOPS, GATHERINGS & EXPERIENCES / MUSIC LISTED IN THE MAIN GUIDE'
 color=header(c,day,subtitle,n,total,nonmusic)
 lanes=sorted({lane(s) for s in entries},key=lambda x:(STAGES.index(x) if x in STAGES else 10, x.replace('/ BLUE','/ 1 BLUE').replace('/ RED','/ 2 RED').replace('/ GREEN','/ 3 GREEN')))
 earliest=math.floor(min(timevalue(s['start']) for s in entries))
 latest=math.ceil(max(timevalue(s['end']) if s.get('end') else timevalue(s['start'])+.5 for s in entries))
 if latest<=earliest:latest=earliest+1
 x0=110;right=W-90;bottom=80;top=H-245;cw=(right-x0)/len(lanes);scale=(top-bottom)/(latest-earliest)
 # Hours ascend vertically, matching the official Hulaween posters.
 for hour in range(earliest,latest+1):
  y=bottom+(hour-earliest)*scale
  c.setStrokeColor(colors.HexColor('#28343a'));c.setLineWidth(.6);c.line(x0,y,right,y)
  label=f'{hour%12 or 12}'+('AM' if hour%24<12 else 'PM')
  # Right-align the time labels outside the plot.
  c.setFillColor(colors.black);c.rect(20,y-8,x0-24,22,fill=1,stroke=0)
  c.setFillColor(WHITE);c.setFont('Condensed',15);c.drawRightString(x0-12,y-4,label)
 for i,name in enumerate(lanes):
  x=x0+i*cw
  c.setStrokeColor(WHITE);c.setLineWidth(1.4);c.line(x,bottom,x,top+9)
  head=clean(name).replace('Wooksville - ','WOOKSVILLE / ').upper()
  headsize=17
  for _ in range(15):
   lines=wrap(head,cw-12,headsize)
   if max([pdfmetrics.stringWidth(t,'Condensed',headsize) for t in lines] or [0])<=cw-12:break
   headsize-=.5
  for j,line in enumerate(lines):txt(c,x+cw/2,top+40+(len(lines)-1)*8-j*headsize,line,headsize,center=True)
 c.line(right,bottom,right,top+9);c.line(x0,bottom,right,bottom)
 for s in entries:
  start=timevalue(s['start']);end=timevalue(s['end']) if s.get('end') else None
  x=x0+lanes.index(lane(s))*cw+5
  if end is None:
   # A compact start marker: its height does not encode a duration.
   y=bottom+(start-earliest)*scale
   height=min(145 if nonmusic else 43,scale*.75);y+=4
   c.setStrokeColor(WHITE);c.setDash(2,3);c.line(x,y+height/2,x+cw-10,y+height/2);c.setDash()
  else:
   y=bottom+(start-earliest)*scale+3;height=(end-start)*scale-6
  block(c,s,x,y,cw-10,max(23,height),color,end is None)
 c.showPage()

def untimed(c,entries,n,total,nonmusic=False):
 color=header(c,None,'UNTIMED EXPERIENCES / NO DAY OR OPENING TIME HAS BEEN INFERRED' if nonmusic else 'ANNOUNCED PERFORMERS / NO DAY OR SET TIME HAS BEEN INFERRED',n,total,nonmusic)
 cols=2 if nonmusic else 3;gap=24;margin=110;cw=(W-margin*2-gap*(cols-1))/cols
 for i,s in enumerate(entries):
  col=i%cols;row=i//cols;x=margin+col*(cw+gap);y=H-300-row*(250 if nonmusic else 145)
  c.setFillColor(colors.HexColor(color));c.setStrokeColor(WHITE);c.roundRect(x,y-(218 if nonmusic else 105),cw,231 if nonmusic else 118,10,fill=1,stroke=1)
  lines=wrap(s.get('artist') or s.get('title') or s.get('name') or 'TBA',cw-30,29)
  for j,line in enumerate(lines):txt(c,x+15,y-18-j*30,line.upper(),29)
  txt(c,x+15,y-78,clean(s.get('stage') or s.get('location','Location TBA')),16)
  if nonmusic:
   for j,line in enumerate(wrap(s.get('description','')+' '+s.get('notes',''),cw-30,15,'Body')):
    txt(c,x+15,y-110-j*19,line,15,'Body')
  if s.get('sourceUrl'):c.linkURL(s['sourceUrl'],(x,y-(218 if nonmusic else 105),x+cw,y+13),relative=0)
 if not nonmusic:txt(c,110,92,'DESCRIPTIONS & SONG LINKS: DOWNLOAD DETAILS.PDF FROM THE LIVE GUIDE.',18)
 c.linkURL('https://ustice.github.io/hulaween-2026/details.pdf',(110,80,W-100,115),relative=0)
 c.showPage()

def build(rows,path,nonmusic=False):
 dated={d:[s for s in rows if s.get('day')==d and s.get('start')] for d in sorted({s['day'] for s in rows if s.get('day') and s.get('start')})}
 tba=[s for s in rows if not s.get('day') or not s.get('start')]
 chunk_size=6 if nonmusic else 15
 chunks=[tba[i:i+chunk_size] for i in range(0,len(tba),chunk_size)]
 total=len(dated)+len(chunks)
 c=canvas.Canvas(str(path),pagesize=(W,H));c.setTitle('Hulaween 2026 - '+('Beyond the Music' if nonmusic else 'Schedule Posters'));c.setAuthor('Independent fan guide')
 n=0
 for day,entries in dated.items():
  n+=1;c.bookmarkPage(day);c.addOutlineEntry(day,day);schedule(c,day,entries,n,total,nonmusic)
 for entries in chunks:
  n+=1;untimed(c,entries,n,total,nonmusic)
 if not total:
  header(c,None,'PROGRAMMING DETAILS HAVE NOT BEEN ANNOUNCED',1,1,True)
  txt(c,W/2,H/2,'CHECK THE LIVE GUIDE FOR NEW ANNOUNCEMENTS',30,center=True);c.showPage()
 c.save();return max(total,1)

def main():
 setup_fonts();(ROOT/'dist').mkdir(exist_ok=True)
 sets=read('main.json',[])+read('camps.json',[])+read('house-music.json',[])
 pages=build(sets,ROOT/'dist'/'guide.pdf')
 nonmusic=read('nonmusic.json',[])
 if isinstance(nonmusic,dict):nonmusic=nonmusic.get('events',nonmusic.get('activities',[]))
 nmpages=build(nonmusic,ROOT/'dist'/'nonmusic.pdf',True)
 print(json.dumps({'musicPages':pages,'musicSets':len(sets),'nonmusicPages':nmpages,'nonmusicEvents':len(nonmusic)}))
if __name__=='__main__':main()
