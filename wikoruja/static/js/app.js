/* Helpers */
function csrfToken(){
  const m=document.querySelector("meta[name='\x63srf-token']"); // evita colidir com sanitizadores
  return m?m.content:"";
}
function copyToClipboard(text){
  navigator.clipboard?.writeText(text).then(()=>alert("Link copiado!"));
}

/* Progress bar */
let __pg, __pgTimer;
function pgEnsure(){ if(!__pg){ __pg=document.createElement("div"); __pg.id="pg"; document.body.appendChild(__pg);} return __pg; }
function pgStart(){
  const el=pgEnsure(); clearInterval(__pgTimer);
  el.style.opacity="1"; el.style.width="0%";
  let w=10;
  __pgTimer=setInterval(()=>{ w=Math.min(w+(w<70?10:2),85); el.style.width=w+"%"; },200);
}
function pgDone(){
  const el=pgEnsure(); clearInterval(__pgTimer);
  el.style.width="100%"; setTimeout(()=>{ el.style.opacity="0"; },250);
  setTimeout(()=>{ el.style.width="0%"; },700);
}

/* TOC */
function buildTOC(){
  const toc=document.getElementById("toc");
  const content=document.querySelector(".markdown-body");
  if(!toc||!content) return;
  // skeleton enquanto monta
  toc.innerHTML='<div class="skel skel-line"></div><div class="skel skel-line"></div><div class="skel skel-line"></div>';

  const heads=content.querySelectorAll("h2, h3");
  if(!heads.length){ toc.innerHTML='<div class="muted">Sem seções.</div>'; return; }
  const ul=document.createElement("ul");
  heads.forEach(h=>{
    if(!h.id){ h.id=h.textContent.trim().toLowerCase().replace(/[^\w\s-]/g,"").replace(/\s+/g,"-"); }
    const li=document.createElement("li"); if(h.tagName==="H3") li.style.marginLeft="12px";
    const a=document.createElement("a"); a.href="#"+h.id; a.textContent=h.textContent; li.appendChild(a); ul.appendChild(li);
    h.style.scrollMarginTop="90px";
  });
  toc.innerHTML=""; toc.appendChild(ul);
}

/* Heading anchors (#) */
function addHeadingAnchors(){
  const content=document.querySelector(".markdown-body"); if(!content) return;
  content.querySelectorAll("h2, h3, h4").forEach(h=>{
    if(!h.id){ h.id=h.textContent.trim().toLowerCase().replace(/[^\w\s-]/g,"").replace(/\s+/g,"-"); }
    if(!h.querySelector(".hanchor")){
      const a=document.createElement("a"); a.className="hanchor"; a.href="#"+h.id; a.textContent="#";
      h.appendChild(a);
    }
  });
}

/* Callouts: transforma [!NOTE], [!WARNING], "ATENÇÃO:" etc. */
function transformCallouts(){
  const content=document.querySelector(".markdown-body"); if(!content) return;
  const map={NOTE:"info",INFO:"info",TIP:"success",SUCCESS:"success",OK:"success",WARN:"warn",WARNING:"warn","ATENÇÃO":"warn","CUIDADO":"warn","PERIGO":"danger","DANGER":"danger","ALERTA":"warn","OBS":"info","OBSERVAÇÃO":"info"};
  function make(type, html){
    const div=document.createElement("div");
    div.className="callout "+type;
    const icon=document.createElement("div");
    icon.className="icon"; icon.textContent= type==="danger"?"⚠": type==="warn"?"⚠": type==="success"?"✓":"ℹ";
    const body=document.createElement("div"); body.innerHTML=html;
    div.append(icon, body); return div;
  }
  const nodes=[...content.querySelectorAll("p, blockquote")];
  nodes.forEach(n=>{
    const raw=(n.textContent||"").trim();
    let m=raw.match(/^\[!(\w+)\]\s*/i);
    let type=null, bodyHtml=n.innerHTML;
    if(m){
      const k=m[1].toUpperCase();
      if(map[k]){ type=map[k]; bodyHtml = bodyHtml.replace(/^\s*\[!\w+\]\s*/i,""); }
    }else{
      m=raw.match(/^(ATENÇÃO|CUIDADO|PERIGO|ALERTA|OBS|OBSERVAÇÃO|NOTA)\s*:\s*/i);
      if(m){ const k=m[1].toUpperCase(); type=map[k]||"info"; bodyHtml = bodyHtml.replace(/^\s*[^:]+:\s*/,""); }
    }
    if(type){
      const c=make(type, bodyHtml);
      n.replaceWith(c);
    }
  });
}

/* Lightbox simples para imagens */
function initLightbox(){
  let lb=document.querySelector(".lb");
  if(!lb){
    lb=document.createElement("div"); lb.className="lb"; lb.innerHTML='<span class="close">✕</span><img alt="">';
    document.body.appendChild(lb);
  }
  const imgEl=lb.querySelector("img");
  const close=()=>lb.classList.remove("open");
  lb.addEventListener("click", e=>{ if(e.target===lb||e.target.classList.contains("close")) close(); });
  document.addEventListener("keydown", e=>{ if(e.key==="Escape") close(); });

  const bind=(container)=>{
    container.querySelectorAll("img").forEach(img=>{
      img.style.cursor="zoom-in";
      img.addEventListener("click", e=>{
        e.preventDefault();
        imgEl.src=img.src; lb.classList.add("open");
      });
    });
  };
  const content=document.querySelector(".markdown-body");
  if(content) bind(content);
  document.querySelectorAll(".attachments img").forEach(i=>bind(i.parentElement||i));
}

/* Reveal on scroll (IntersectionObserver) */
function revealOnScroll(){
  const els=[
    ...document.querySelectorAll(".cards .card"),
    ...document.querySelectorAll(".side-card"),
    ...document.querySelectorAll(".attachments li"),
    ...document.querySelectorAll(".doc > *")
  ];
  els.forEach(e=>e.classList.add("reveal"));
  const io=new IntersectionObserver((entries)=>{
    entries.forEach(en=>{ if(en.isIntersecting){ en.target.classList.add("show"); io.unobserve(en.target); } });
  },{rootMargin:"-10% 0px"});
  els.forEach(e=>io.observe(e));
}

/* Botões de copiar / barra de progresso em links internos */
function wireCopyButtons(){
  document.querySelectorAll("[data-action='copy-link']").forEach(btn=>{
    btn.addEventListener("click",()=>copyToClipboard(location.href));
  });
  document.querySelectorAll("[data-copy]").forEach(btn=>{
    btn.addEventListener("click",()=>copyToClipboard(btn.dataset.copy));
  });

  document.addEventListener("click",(e)=>{
    const a=e.target.closest && e.target.closest("a");
    if(!a) return;
    const href=a.getAttribute("href")||"";
    if(href.startsWith("#")||href.startsWith("mailto:")||href.startsWith("javascript:")) return;
    const url=new URL(a.href, location.href);
    if(url.origin===location.origin && !a.target && !a.hasAttribute("download")){ pgStart(); }
  });
}

/* Editor (mantém recursos e integra progress bar/preview) */
function throttle(fn, wait){let t;return (...args)=>{clearTimeout(t);t=setTimeout(()=>fn(...args),wait);}}
function setupEditor(){
  // Editor
  const el = document.getElementById('tui-editor');
  if(el){
    // Carrega scripts externos do Toast UI
    const head = document.getElementsByTagName('head')[0];
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://uicdn.toast.com/editor/latest/toastui-editor.min.css';
    head.appendChild(link);
    
    const script = document.createElement('script');
    script.src = 'https://uicdn.toast.com/editor/latest/toastui-editor-all.min.js';
    script.onload = function() {
      const initialValue = document.getElementById("content-field").value;
      const editor = new toastui.Editor({
        el: el,
        height: '600px',
        initialEditType: 'wysiwyg',
        previewStyle: 'vertical',
        initialValue: initialValue,
        usageStatistics: false,
        toolbarItems: [
          ['heading', 'bold', 'italic', 'strike'],
          ['hr', 'quote', 'ul', 'ol', 'task'],
          ['table', 'image', 'link'],
          ['code', 'codeblock'],
          ['align'],
        ],
        plugins: [
          [toastui.Editor.plugin.align],
        ],
      });
      document.getElementById('edit-form').addEventListener('submit', function(){
        document.getElementById('content-field').value = editor.getMarkdown();
      });
    };
    head.appendChild(script);
  }

  // Uploader de capa
  const coverUploader = (function(){
    const fileInput = document.getElementById('cover-file');
    if(!fileInput) return;
    const form = document.getElementById('edit-form');
    const urlInput = form.querySelector('input[name="image_url"]');
    const prevBox  = document.getElementById('cover-preview');
    const prevImg  = prevBox ? prevBox.querySelector('img') : null;
    const ns   = form.dataset.namespace;
    const slug = form.dataset.slug;
    const csrf = (document.querySelector('meta[name="csrf-token"]')||{}).content;
    function compressImage(file, max=1600, quality=0.82){
      return new Promise((resolve)=>{
        const img = new Image();
        img.onload = ()=>{
          const r = Math.min(max/img.width, max/img.height, 1);
          const w = Math.round(img.width*r), h = Math.round(img.height*r);
          const canvas = document.createElement('canvas');
          canvas.width = w; canvas.height = h;
          canvas.getContext('2d').drawImage(img,0,0,w,h);
          canvas.toBlob(b => resolve(b || file), 'image/webp', quality);
        };
        img.onerror = ()=> resolve(file);
        img.src = URL.createObjectURL(file);
      });
    }
    fileInput.addEventListener('change', async (ev)=>{
      const file = ev.target.files && ev.target.files[0];
      if(!file) return;
      const blob = await compressImage(file);
      const fd = new FormData();
      fd.append('file', blob, 'cover.webp');
      if(csrf) fd.append('csrf_token', csrf);
      try{
        const resp = await fetch(`/upload-cover/${encodeURIComponent(ns)}/${encodeURIComponent(slug)}`, { method:'POST', body: fd });
        if(!resp.ok) throw new Error('upload falhou');
        const data = await resp.json();
        if(data && data.url){
          urlInput.value = data.url;
          if(prevBox && prevImg){ prevImg.src = data.url; prevBox.style.display=''; }
          alert('Capa enviada e vinculada ao card.');
        }else{
          alert('Falha ao enviar capa.');
        }
      }catch(e){
        console.error(e); alert('Erro ao enviar a capa.');
      }
    });
  })();
}

/* Init */
document.addEventListener("DOMContentLoaded", ()=>{
  pgEnsure();               // cria barra
  buildTOC();               // sumário
  addHeadingAnchors();      // # nos títulos
  transformCallouts();      // callouts
  initLightbox();           // lightbox imagens
  wireCopyButtons();        // copiar link + progress em navegação
  setupEditor();            // editor (se presente)
  revealOnScroll();         // microanimações
});
/* === Spotlight (Ctrl+K) === */
function initSpotlight(){
  const el = document.getElementById("spotlight");
  if(!el) return;
  const input = document.getElementById("sp-input");
  const list  = document.getElementById("sp-list");
  let idx = -1, items = [];

  function open(){ el.classList.add("open"); el.setAttribute("aria-hidden","false"); pgStart(); setTimeout(()=>{ input.focus(); pgDone(); },10); }
  function close(){ el.classList.remove("open"); el.setAttribute("aria-hidden","true"); idx=-1; items=[]; list.innerHTML=""; input.value=""; }
  function render(){
    if(!items.length){ list.innerHTML = '<div class="sp-empty">Digite para buscar…</div>'; return; }
    list.innerHTML = items.map((it,i)=>`
      <div class="sp-item ${i===idx?'active':''}" data-href="${it.path}" role="option" aria-selected="${i===idx}">
        <div class="title">${it.title}</div>
        <div class="path">${it.namespace}/${it.slug}</div>
      </div>`).join("");
  }
  function fetchSuggest(q){
    if(!q || q.length<2){ items=[]; render(); return; }
    fetch('/api/suggest?q='+encodeURIComponent(q)).then(r=>r.json()).then(data=>{ items=data; idx = items.length?0:-1; render(); });
  }
  const throttled = (fn, ms)=>{ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), ms); } };
  input.addEventListener('input', throttled(()=>fetchSuggest(input.value.trim()), 120));

  list.addEventListener('click', (e)=>{
    const item = e.target.closest('.sp-item'); if(!item) return;
    close(); pgStart(); location.href = item.dataset.href;
  });

  document.addEventListener('keydown', (e)=>{
    // Ctrl+K (ou Cmd+K) abre/fecha
    if((e.ctrlKey||e.metaKey) && e.key.toLowerCase()==='k'){ e.preventDefault(); el.classList.contains('open')?close():open(); }
    if(!el.classList.contains('open')) return;
    if(e.key==='Escape'){ e.preventDefault(); close(); }
    if(e.key==='ArrowDown'){ e.preventDefault(); if(items.length){ idx = Math.min(idx+1, items.length-1); render(); list.children[idx]?.scrollIntoView({block:'nearest'}); } }
    if(e.key==='ArrowUp'){ e.preventDefault(); if(items.length){ idx = Math.max(idx-1, 0); render(); list.children[idx]?.scrollIntoView({block:'nearest'}); } }
    if(e.key==='Enter'){ e.preventDefault(); if(idx>=0 && items[idx]){ const href=items[idx].path; close(); pgStart(); location.href = href; } }
  });
}
document.addEventListener("DOMContentLoaded", ()=>{ try{ initSpotlight(); }catch{} });

/* === Namespace filter/sort === */
function initNamespaceIndex(){
  const grid = document.getElementById("ns-grid");
  const q = document.getElementById("ns-q");
  const sortSel = document.getElementById("ns-sort");
  if(!grid || !q || !sortSel) return;

  let items = Array.from(grid.querySelectorAll(".ns-card"));

  function apply(){
    const term = q.value.trim().toLowerCase();
    let filtered = items.filter(el => !term || el.dataset.title.includes(term));

    const mode = sortSel.value;
    filtered.sort((a,b)=>{
      if(mode==="title_asc"||mode==="title_desc"){
        const ta=a.dataset.title, tb=b.dataset.title;
        const cmp = ta.localeCompare(tb, "pt-BR");
        return mode==="title_asc"? cmp : -cmp;
      }else{
        const da = Date.parse(a.dataset.updated||0)||0;
        const db = Date.parse(b.dataset.updated||0)||0;
        return db - da; // mais recente primeiro
      }
    });

    grid.innerHTML = "";
    filtered.forEach(el => grid.appendChild(el));
    if(filtered.length===0){
      const div = document.createElement("div");
      div.className="empty";
      div.textContent="Nenhum resultado com esse filtro.";
      grid.appendChild(div);
    }
  }
  const throttle=(fn,ms)=>{let t;return(...a)=>{clearTimeout(t);t=setTimeout(()=>fn(...a),ms)}}
  q.addEventListener("input", throttle(apply, 120));
  sortSel.addEventListener("change", apply);
  apply();
}
document.addEventListener("DOMContentLoaded", ()=>{ try{ initNamespaceIndex(); }catch(e){} });