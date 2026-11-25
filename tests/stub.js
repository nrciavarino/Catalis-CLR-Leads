(() => {
  // ---- in-memory Firestore stub ----
  const store = new Map();            // path -> data
  const listeners = [];               // {kind:'col'|'doc', path, q, cb}
  const clone = o => JSON.parse(JSON.stringify(o));
  const parentOf = p => p.split('/').slice(0,-1).join('/');
  const isChild = (colPath, p) => parentOf(p) === colPath;
  function colDocs(colPath, q){
    let docs = [...store.entries()].filter(([p]) => isChild(colPath,p)).map(([p,d]) => ({id:p.split('/').pop(), data:()=>clone(d), exists:true}));
    if(q && q.orderBy){ const [f,dir] = q.orderBy; docs.sort((a,b)=> (a.data()[f]>b.data()[f]?1:-1)*(dir==='desc'?-1:1)); }
    if(q && q.limit) docs = docs.slice(0,q.limit);
    return docs;
  }
  const notify = () => listeners.forEach(l => {
    if(l.kind==='col'){ const docs = colDocs(l.path,l.q); l.cb({docs, forEach:fn=>docs.forEach(fn), size:docs.length}); }
    else { const d = store.get(l.path); l.cb({exists:d!==undefined, id:l.path.split('/').pop(), data:()=>clone(d||{})}); }
  });
  let n = 0;
  function docRef(path){
    return {
      path, id: path.split('/').pop(),
      collection: name => colRef(path+'/'+name),
      async set(data, opts){ const cur = store.get(path); store.set(path, opts&&opts.merge&&cur ? Object.assign({},cur,clone(data)) : clone(data)); notify(); },
      async delete(){ store.delete(path); notify(); },
      async get(){ const d = store.get(path); return {exists:d!==undefined, id:this.id, data:()=>clone(d||{})}; },
      onSnapshot(cb){ const l={kind:'doc',path,cb}; listeners.push(l); setTimeout(()=>{ const d=store.get(path); cb({exists:d!==undefined,id:l.path.split('/').pop(),data:()=>clone(d||{})}); },0); return ()=>{ const i=listeners.indexOf(l); if(i>=0) listeners.splice(i,1); }; },
    };
  }
  function colRef(path, q={}){
    return {
      doc: id => docRef(path+'/'+(id||('auto'+(++n)))),
      async add(data){ const id='auto'+(++n); store.set(path+'/'+id, clone(data)); notify(); return docRef(path+'/'+id); },
      orderBy: (f,dir)=> colRef(path, Object.assign({},q,{orderBy:[f,dir]})),
      limit: k => colRef(path, Object.assign({},q,{limit:k})),
      where: ()=> colRef(path,q),
      async get(){ const docs = colDocs(path,q); return {docs, forEach:fn=>docs.forEach(fn), size:docs.length, empty:!docs.length}; },
      onSnapshot(cb, err){ const l={kind:'col',path,q,cb}; listeners.push(l); setTimeout(()=>{ const docs=colDocs(path,q); cb({docs,forEach:fn=>docs.forEach(fn),size:docs.length}); },0); return ()=>{ const i=listeners.indexOf(l); if(i>=0) listeners.splice(i,1); }; },
    };
  }
  const db = {
    collection: p => colRef(p),
    collectionGroup: () => colRef('__none__'),
    async runTransaction(fn){
      const tx = { get: ref => ref.get(), set: (ref,data,opts) => ref.set(data,opts) };
      return fn(tx);
    },
  };
  window.__store = store;
  window.firebase = {
    apps: [], initializeApp(){ this.apps.push({delete: async()=>{ window.firebase.apps=[]; }}); },
    firestore: () => db,
    auth: () => ({ signInAnonymously: async()=>({}) }),
  };
  window.firebase.firestore.FieldValue = {serverTimestamp:()=>Date.now()};
  window.QrScanner = class { static hasCamera(){ return Promise.resolve(false); } static WORKER_PATH=''; };
  window.QRCode = class { constructor(){} };
  window.Papa = { unparse: rows => { const cols=[...new Set(rows.flatMap(r=>Object.keys(r)))]; const q=v=>'"'+String(v).replace(/"/g,'""')+'"'; return [cols.map(q).join(','), ...rows.map(r=>cols.map(c=>q(r[c]==null?'':r[c])).join(','))].join('\n'); }, parse: ()=>({data:[]}) };
  window.ZXing = {};
  // seed
  localStorage.setItem('compassleads.firebaseConfig', JSON.stringify({apiKey:'x',projectId:'test'}));
  localStorage.setItem('compassleads.workerName','Nic');
  localStorage.setItem('compassleads.apiKey','sk-test');
  localStorage.setItem('compassleads.activeEventId','ev1');
  store.set('events/ev1', {name:'Test Conf 2026', createdAt: 2000});
  store.set('events/ev0', {name:'Old Conf', createdAt: 1000, qualFields:[{id:'qold',label:'Budget cycle open?',type:'yesno',options:[],required:false,archived:false}]});
})();
