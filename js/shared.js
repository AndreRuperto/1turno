// --- Formatting ---
function fmt(n){return n.toFixed(2).replace('.',',')}
function fmtN(n){return n.toLocaleString('pt-BR')}
function fmtR(n){return 'R$ '+n.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})}
function escH(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}

// --- Sortable tables ---
function makeSortable(table){
  var tbody=table.querySelector('tbody');
  if(!tbody)return;
  table.querySelectorAll('thead th.sort').forEach(function(th){
    th.addEventListener('click',function(){
      var asc=th.getAttribute('aria-sort')!=='ascending';
      table.querySelectorAll('thead th').forEach(function(t){t.removeAttribute('aria-sort')});
      th.setAttribute('aria-sort',asc?'ascending':'descending');
      var ci=Array.from(th.parentNode.children).indexOf(th);
      var isNum=th.classList.contains('n');
      var rows=Array.from(tbody.querySelectorAll('tr'));
      rows.sort(function(a,b){
        var ac=a.cells[ci],bc=b.cells[ci];
        var av=ac?(ac.dataset.sort!==undefined?ac.dataset.sort:ac.textContent.trim()):'';
        var bv=bc?(bc.dataset.sort!==undefined?bc.dataset.sort:bc.textContent.trim()):'';
        if(isNum){av=parseFloat(String(av).replace(',','.'))||0;bv=parseFloat(String(bv).replace(',','.'))||0;}
        var r=av>bv?1:av<bv?-1:0;
        return asc?r:-r;
      });
      rows.forEach(function(r){tbody.appendChild(r)});
    });
  });
}

// --- Nav scroll arrows ---
!function(){
  var c=document.querySelector('.nav-links'),l=document.querySelector('.nav-arr-l'),r=document.querySelector('.nav-arr-r');
  if(!c||!l||!r)return;
  function u(){var s=c.scrollLeft,m=c.scrollWidth-c.clientWidth;l.hidden=s<2;r.hidden=m-s<2}
  l.onclick=function(){c.scrollBy({left:-150,behavior:'smooth'})};
  r.onclick=function(){c.scrollBy({left:150,behavior:'smooth'})};
  c.addEventListener('scroll',u,{passive:true});
  new ResizeObserver(u).observe(c);
  u();
}()

// --- Theme toggle ---
!function(){
  var btn=document.querySelector('.theme-toggle'),root=document.documentElement;
  if(!btn)return;
  function isDark(){var t=root.getAttribute('data-theme');if(t)return t==='dark';return matchMedia('(prefers-color-scheme:dark)').matches}
  function update(){btn.textContent=isDark()?'☀':'☾';btn.setAttribute('aria-label',isDark()?'Mudar para tema claro':'Mudar para tema escuro')}
  var saved=localStorage.getItem('theme');
  if(saved)root.setAttribute('data-theme',saved);
  update();
  btn.onclick=function(){var next=isDark()?'light':'dark';root.setAttribute('data-theme',next);localStorage.setItem('theme',next);update()};
}()

// --- Nav section highlighting ---
// Highlights the active section in the navbar based on scroll position.
// Uses a[href^="#"] to naturally exclude external links like "2º turno →" or "← 1º turno".
!function(){
  var navLinks={};
  document.querySelectorAll('.nav-links a[href^="#"]').forEach(function(a){navLinks[a.getAttribute('href').slice(1)]=a});
  if(!Object.keys(navLinks).length)return;
  if('IntersectionObserver' in window){
    var navIO=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;
      Object.keys(navLinks).forEach(function(k){navLinks[k].classList.remove('on')});
      var a=navLinks[e.target.id];if(a){a.classList.add('on');var n=a.parentNode;n.scrollLeft=a.offsetLeft-n.offsetLeft-n.clientWidth/2+a.offsetWidth/2}
    })},{rootMargin:'-30% 0px -60% 0px'});
    document.querySelectorAll('section[id]').forEach(function(s){navIO.observe(s)});
  }
}()
