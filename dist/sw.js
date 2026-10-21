
const CACHE='hulaween-poster-v5';const SHELL=['./','./index.html','./nonmusic.html','./hulaween-guide.html','./hulaween-activities.html'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith('hulaween-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('message',e=>{if(e.data==='CACHE_STATUS')e.waitUntil(caches.open(CACHE).then(c=>c.match('./index.html')).then(r=>e.source.postMessage({type:'CACHE_STATUS',ready:!!r}))) });
self.addEventListener('fetch',e=>{if(e.request.method!=='GET'||new URL(e.request.url).origin!==self.location.origin)return;if(e.request.mode==='navigate')e.respondWith((async()=>{const c=await caches.open(CACHE);try{const r=await Promise.race([fetch(e.request),new Promise((_,reject)=>setTimeout(()=>reject(Error()),5000))]);if(r.ok)c.put(e.request,r.clone());return r}catch{return await c.match(e.request)||await c.match('./index.html')||Response.error()}})());});
