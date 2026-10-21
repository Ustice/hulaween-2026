#!/usr/bin/env python3
"""Build self-contained poster-style music and activity schedules."""
import base64
import html
import json
import math
import re
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def read(name,default):
 p=ROOT/'data'/name
 return json.loads(p.read_text()) if p.exists() else default

def e(x):return html.escape(str(x or ''),quote=True)
def minute(t):
 h,m=map(int,t[:5].split(':'));return (h+24 if h<8 else h)*60+m

def clock(m):
 m=int(m)%1440;h=m//60
 return str(h%12 or 12)+(f':{m%60:02d}' if m%60 else '')+('AM' if h<12 else 'PM')

def lane(s):
 match=re.search(r'(Blue|Red|Green) headphone channel',s.get('notes',''),re.I)
 return s.get('stage','Location TBA')+((' / '+match[1].title()+' channel') if match else '')

def details(s,a):
 out='<p class="detail-location">'+e(s.get('stage'))+'</p>'
 desc=s.get('description') or a.get('description')
 if desc:out+='<p>'+e(desc)+'</p>'
 if s.get('notes'):out+='<p class="notes">'+e(s['notes'])+'</p>'
 for song in a.get('songs',[]):
  match=re.fullmatch(r'https://open\.spotify\.com/track/([A-Za-z0-9]{22})(?:\?.*)?',song.get('url',''))
  if match:out+='<div class="song"><a href="spotify:track:'+match[1]+'">♫ '+e(song['title'])+'</a><a class="web" href="'+e(song['url'])+'">Web ↗</a></div>'
 links=[]
 for label,url in [('Set announcement',s.get('sourceUrl')),('Artist source',a.get('descriptionSource')),('Spotify artist',a.get('spotifyArtistUrl'))]:
  if url:links.append('<a href="'+e(url)+'">'+label+' ↗</a>')
 return out+'<div class="sources">'+' · '.join(links)+'</div>'

def render(sets,artists,activity=False):
 sections=[];all_days=sorted({s.get('day') for s in sets if s.get('day')})
 # Main festival day tabs remain stable even while activity announcements are sparse.
 all_days=sorted(set(all_days)|{'2026-10-22','2026-10-23','2026-10-24','2026-10-25'})
 tabs=[];palettes={'2026-10-21':'#ef9d4b','2026-10-22':'#59a9cc','2026-10-23':'#9365b4','2026-10-24':'#ff795c','2026-10-25':'#2abd86'}
 for day in all_days:
  dt=datetime.strptime(day,'%Y-%m-%d');entries=[s for s in sets if s.get('day')==day]
  timed=[s for s in entries if s.get('start')];untimed=[s for s in entries if not s.get('start')]
  tabs.append('<a href="#day-'+day+'" data-tab="'+day+'" style="--tab:'+palettes.get(day,'#59a9cc')+'">'+dt.strftime('%a %-d').upper()+'</a>')
  stages=list(dict.fromkeys(lane(s) for s in entries))
  official=['The Meadow','The Hallows','The Amphitheatre','Spirit Lake','DEF Off Limits']
  stages.sort(key=lambda v:(official.index(v) if v in official else 5,v if v not in official else ''))
  earliest=math.floor(min((minute(s['start']) for s in timed),default=12*60)/60)*60
  latest=math.ceil(max((minute(s.get('end') or s['start']) for s in timed),default=18*60)/60)*60
  if earliest==latest:latest+=60
  height=(latest-earliest)*1.7
  grid='';rail=''
  for m in range(latest,earliest-1,-60):
   y=(latest-m)*1.7+24
   grid+=f'<div class="hour-line" style="top:{y}px"></div>'
   rail+=f'<span class="hour" style="top:{y}px">{clock(m)}</span>'
  grid='<div class="time-rail">'+rail+'</div>'+grid
  for i,stage in enumerate(stages):
   grid+=f'<div class="lane" data-lane="{i}" style="left:calc(var(--time) + {i} * var(--lane));height:{height}px"></div>'
  for s in sorted(timed,key=lambda x:minute(x['start']),reverse=True):
   start=minute(s['start']);end=minute(s['end']) if s.get('end') else None
   if end is not None and end<start:end+=1440
   top=(latest-(end if end is not None else start))*1.7+24
   duration=max((end-start)*1.7,34) if end is not None else 42
   text=clock(start)+(('–'+clock(end)) if end is not None else ' · END TBA')
   # Untimed end markers are visibly distinct; their box height is a label, not a duration.
   classes='slot'+(' end-tba' if end is None else '')
   data=details(s,artists.get(s['artist'],{}))
   grid+=f'<details class="{classes}" data-lane="{stages.index(lane(s))}" style="left:calc(var(--time) + {stages.index(lane(s))} * var(--lane) + 4px);top:{top}px;height:{duration}px" data-id="{e(s["id"])}"><summary><b>{e(s["artist"])}</b><span>{e(text)}</span></summary><div class="detail"><h3>{e(s["artist"])}</h3><p class="detail-time">{e(text)} · {dt.strftime("%A")}</p>{data}<button class="save" data-id="{e(s["id"])}">☆ Save set</button><button class="close">Close ×</button></div></details>'
  heads='<div class="corner">TIME<br><span>↑ LATER</span></div>'+''.join('<div class="stage-head" data-lane="'+str(i)+'">'+e(stage).replace(' / ','<br>')+'</div>' for i,stage in enumerate(stages))
  controls='<div class="stage-controls js-only"><button type="button" class="prev-stage" aria-label="Previous stage or camp">‹</button><label>Stage / camp<select class="stage-picker" aria-label="Stage or camp">'+''.join('<option value="'+str(i)+'">'+e(stage)+'</option>' for i,stage in enumerate(stages))+'<option value="all">All stages overview</option></select></label><button type="button" class="next-stage" aria-label="Next stage or camp">›</button></div>'
  tbas=''.join('<details class="tba-set"><summary>'+e(s['artist'])+' <small>'+e(s.get('stage'))+' · TIME TBA</small></summary>'+details(s,artists.get(s['artist'],{}))+'</details>' for s in untimed)
  empty='<p class="empty">No timed '+('activities' if activity else 'sets')+' confirmed in the sources checked. Check the announcements below.</p>' if not timed else ''
  title=dt.strftime('%a').upper()+' '+dt.strftime('%m/%d/%y')
  sections.append(f'<section class="day" id="day-{day}" data-day="{day}" style="--day:{palettes.get(day,"#4da2cb")}"><h2>{title}</h2><p class="day-note">{"Activities + experiences" if activity else "Official stages + campground sets"} · {len(entries)} announced · Times Eastern</p>{empty}'+(controls+f'<div class="table-wrap" style="--columns:{len(stages)}"><div class="sticky-stage-heads"><div class="stage-heads">{heads}</div></div><div class="grid-scroll" tabindex="0" aria-label="{e(title)} stage schedule; scroll horizontally"><div class="poster-grid" style="--columns:{len(stages)}"><div class="timeline" style="height:{height+70}px">{grid}</div></div></div></div>' if timed else '')+(('<div class="tba"><h3>TIME TO BE ANNOUNCED</h3>'+tbas+'</div>') if tbas else '')+'</section>')
 unknown=[s for s in sets if not s.get('day')]
 if unknown:sections.append('<section class="tba standalone"><h2>DATE / TIME TBA</h2>'+''.join('<details class="tba-set"><summary>'+e(s['artist'])+'<small>'+e(s.get('stage'))+'</small></summary>'+details(s,artists.get(s['artist'],{}))+'</details>' for s in unknown)+'</section>')
 meta=read('metadata.json',{})
 art=''
 for stem in ['header-art','header-crop','foliage']:
  for folder in ['data','references']:
   for ext,mime in [('png','image/png'),('jpg','image/jpeg'),('webp','image/webp')]:
    path=ROOT/folder/(stem+'.'+ext)
    if path.exists():art='data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
 def asset(name):
  p=ROOT/'references'/name
  mime='font/woff2' if name.endswith('woff2') else 'image/png'
  return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode() if p.exists() else ''
 fonts=''.join('@font-face{font-family:'+family+';src:url('+asset(file)+') format("woff2");font-display:swap}' for family,file in [('Marvin','marvin.woff2'),('Gravity','gravity.woff2')])
 template=(ROOT/'template.html').read_text()
 template=template.replace('{{FONTS}}',fonts).replace('{{BAT}}',asset('bat.png')).replace('{{SKELETON}}',asset('skeleton.png')).replace('{{LOGO}}',asset('logo.png')).replace('{{HEADER_BG}}',asset('official-thursday.png'))
 changes=''.join('<li>'+e(x if isinstance(x,str) else x.get('text',''))+'</li>' for x in meta.get('changes',[]))
 replacements={'SECTIONS':''.join(sections),'TABS':''.join(tabs),'TYPE':'ACTIVITIES & EXPERIENCES' if activity else 'MUSIC SCHEDULE','OTHER':'index.html' if activity else 'nonmusic.html','OTHER_LABEL':'Music schedule' if activity else 'Activities schedule','PDF':'nonmusic.pdf' if activity else 'guide.pdf','DOWNLOAD':'hulaween-activities.html' if activity else 'hulaween-guide.html','VERIFIED':e(meta.get('lastVerified','Current source snapshot')),'ART':art,'CHANGES':changes,'COUNT':str(len(sets)),'NOTICE':'<p class="activity-notice">Updated from Hulaween’s newly released Spirit Lake programming posters, including House of the Lost, Oasis and Incendia, alongside confirmed campground activities. Unknown end times remain explicitly marked.</p>' if activity else '<p class="activity-notice">House of Lost and Incendia are now included from the <a href="https://www.instagram.com/hulaweenfl/p/Dew_G-5lLSx/">new official Spirit Lake posters</a>. No House of Lost slot is listed on the Sunday poster.</p>'}
 for key,value in replacements.items():template=template.replace('{{'+key+'}}',value)
 if activity:template=template.replace('SCROLL SIDEWAYS FOR ALL STAGES & CAMPS · LATEST SETS AT THE TOP ↑ · TAP A SET FOR DESCRIPTION & SONGS','SCROLL SIDEWAYS FOR ALL LOCATIONS · LATEST EVENTS AT THE TOP ↑ · TAP AN EVENT FOR DETAILS')
 return template

def main():
 artists={**read('artists-main.json',{}),**read('artists-camps.json',{})}
 for name,cat in read('spotify-catalog.json',{}).items():artists[name]={**artists.get(name,{}),**cat}
 dist=ROOT/'dist';dist.mkdir(exist_ok=True)
 music=render(read('main.json',[])+read('camps.json',[])+read('house-music.json',[]),artists)
 activities=render(read('nonmusic.json',[]),{},True)
 for name in ['index.html','hulaween-guide.html']:(dist/name).write_text(music)
 for name in ['nonmusic.html','hulaween-activities.html']:(dist/name).write_text(activities)
 (dist/'sw.js').write_text(SERVICE_WORKER)
 print('Built music and separate activity poster guides')

SERVICE_WORKER=r"""
const CACHE='hulaween-poster-v5';const SHELL=['./','./index.html','./nonmusic.html','./hulaween-guide.html','./hulaween-activities.html'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith('hulaween-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('message',e=>{if(e.data==='CACHE_STATUS')e.waitUntil(caches.open(CACHE).then(c=>c.match('./index.html')).then(r=>e.source.postMessage({type:'CACHE_STATUS',ready:!!r}))) });
self.addEventListener('fetch',e=>{if(e.request.method!=='GET'||new URL(e.request.url).origin!==self.location.origin)return;if(e.request.mode==='navigate')e.respondWith((async()=>{const c=await caches.open(CACHE);try{const r=await Promise.race([fetch(e.request),new Promise((_,reject)=>setTimeout(()=>reject(Error()),5000))]);if(r.ok)c.put(e.request,r.clone());return r}catch{return await c.match(e.request)||await c.match('./index.html')||Response.error()}})());});
"""
if __name__=='__main__':main()
