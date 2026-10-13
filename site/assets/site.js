// shared across every page: the theme skin switcher, remembered per visitor.
(function(){
  "use strict";
  var root = document.documentElement, skins = document.getElementById("skins");
  var SKINS = ["violet", "slate", "nordic"];
  function apply(t){
    if(SKINS.indexOf(t) < 0) t = "violet";
    if(t === "violet") root.removeAttribute("data-skin"); else root.setAttribute("data-skin", t);
    if(skins){ var b = skins.querySelectorAll(".sw");
      for(var i=0;i<b.length;i++) b[i].classList.toggle("on", b[i].getAttribute("data-skin") === t); }
    // tells the page, so anything drawn per theme (like a build's still image) can follow
    document.dispatchEvent(new CustomEvent("skin", {detail: t}));
  }
  var saved = "violet"; try{ var s = localStorage.getItem("skin"); if(s) saved = s; }catch(e){}
  apply(saved);
  if(skins) skins.addEventListener("click", function(e){
    var b = e.target.closest(".sw"); if(!b) return;
    var t = b.getAttribute("data-skin"); apply(t);
    try{ localStorage.setItem("skin", t); }catch(e){}
  });
  // a theme picked in another page of this site, including the page around a live preview,
  // arrives as a storage event
  window.addEventListener("storage", function(e){ if(e.key === "skin") apply(e.newValue || "violet"); });
})();
