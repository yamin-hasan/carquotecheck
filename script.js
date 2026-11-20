(() => {
  "use strict";
  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));
  const money = n => new Intl.NumberFormat("en-US", {style:"currency",currency:"USD",maximumFractionDigits:0}).format(Number.isFinite(n)?n:0);
  const moneyCents = n => new Intl.NumberFormat("en-US", {style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:2}).format(Number.isFinite(n)?n:0);
  const num = id => Math.max(0, Number($(id)?.value || 0));
  const KEY = "carquotecheck.saved.v1";
  let states = [];
  let addons = [];
  let currentStep = 1;
  let financing = "cash";
  let lastAudit = null;
  let toastTimer = null;
  let selection = {doc:true, addons:{}};
  const defaults = {"#state-select":"", "#selling-price":"32000", "#trade-in":"0", "#tax-rate":"6", "#doc-fee":"300", "#gov-fees":"200", "#apr":"6.9", "#loan-months":"72"};

  function safeReadSaved(){ try { const v=JSON.parse(localStorage.getItem(KEY)||"[]"); return Array.isArray(v)?v.slice(0,4):[]; } catch(e){ return []; } }
  function safeWriteSaved(v){ try { localStorage.setItem(KEY,JSON.stringify(v.slice(0,4))); return true; } catch(e){ toast("Browser storage is unavailable. Check your privacy settings."); return false; } }
  function toast(message){ const el=$("#toast"); if(!el)return; el.textContent=message; el.classList.add("show"); clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.classList.remove("show"),2400); }
  function activeState(){ return states.find(s=>s.code===$("#state-select")?.value) || null; }
  function setStep(step,scroll=true){
    currentStep=Math.max(1,Math.min(3,step));
    $$(".wizard-step").forEach(el=>{const active=Number(el.dataset.step)===currentStep;el.classList.toggle("active",active);el.hidden=!active;});
    $$(".progress-step").forEach(el=>{const n=Number(el.dataset.goStep);el.classList.toggle("active",n===currentStep);el.classList.toggle("complete",n<currentStep);if(n===currentStep)el.setAttribute("aria-current","step");else el.removeAttribute("aria-current");});
    if(scroll && window.matchMedia("(max-width:767px)").matches) $("#auditor-wizard")?.scrollIntoView({behavior:"smooth",block:"start"});
  }
  function showError(message){const e=$("#form-error");if(!e)return;e.textContent=message;e.hidden=false;e.scrollIntoView({behavior:"smooth",block:"nearest"});}
  function clearError(){const e=$("#form-error");if(e){e.hidden=true;e.textContent="";}}
  function validateStep(step){
    clearError();
    if(step===1){
      if(!$("#state-select").value){showError("Choose the state where you will register the vehicle.");return false;}
      if(num("#selling-price")<=0){showError("Enter a vehicle selling price greater than $0.");return false;}
      if(num("#tax-rate")>20){showError("Check the tax rate. Enter a percentage between 0 and 20.");return false;}
    }
    if(step===2 && (!Number.isFinite(Number($("#doc-fee").value)) || Number($("#doc-fee").value)<0)){showError("Enter a valid dealer documentation fee.");return false;}
    if(step===3 && financing==="loan"){
      const months=Number($("#loan-months").value),apr=Number($("#apr").value);
      if(!Number.isFinite(months)||months<1||months>120){showError("Enter a loan term between 1 and 120 months.");return false;}
      if(!Number.isFinite(apr)||apr<0||apr>50){showError("Enter an APR between 0% and 50%.");return false;}
    }
    return true;
  }
  function stateSelectChange(code,overwriteTax=true){
    const s=states.find(x=>x.code===code); if(!s)return;
    $("#state-hint").textContent=s.tax_note;
    if(overwriteTax) $("#tax-rate").value=s.tax_rate_pct;
    $("#trade-credit-hint").textContent=s.trade_in_label;
    const tradeToggle=$("#apply-trade-credit");
    tradeToggle.checked=["full","limited"].includes(s.trade_in_rule);
    tradeToggle.disabled=s.trade_in_rule==="none";
    if(s.trade_in_rule==="new_only") tradeToggle.disabled=false;
    if(s.trade_in_rule==="partial") tradeToggle.checked=false;
    $("#doc-fee").value=s.average_doc_fee;
    $("#gov-fees").value=s.government_fee_default;
    const taxable=$("#doc-fee-taxable");
    taxable.checked=s.doc_fee_taxable===false?false:true;
    $("#doc-tax-hint").textContent=s.doc_fee_taxable===null?"Tax treatment not verified. Included by default until you confirm.":s.doc_fee_taxable_label+". Confirm the invoice description.";
    const cap=s.doc_fee_cap!==null?`Confirmed statewide reference cap: ${money(s.doc_fee_cap)}.`:s.doc_fee_rule_label+".";
    $("#doc-fee-hint").textContent=`Average doc-fee benchmark: ${money(s.average_doc_fee)}. ${cap} Benchmark is not a legal limit.`;
  }
  function fillStateOptions(){
    const select=$("#state-select"); if(!select)return;
    const options=states.map(s=>`<option value="${s.code}">${s.name} (${s.code})</option>`).join("");
    select.insertAdjacentHTML("beforeend",options);
    const defaultCode=document.body.dataset.defaultState || $(".wizard-card")?.dataset.defaultState || "";
    if(defaultCode){select.value=defaultCode;stateSelectChange(defaultCode);}
    else if(states.some(s=>s.code==="FL")){select.value="FL";stateSelectChange("FL");}
  }
  function renderAddons(){
    const root=$("#addon-list"); if(!root)return;
    if(!addons.length){root.innerHTML='<p class="empty-addons">No dealer add-ons added.</p>';return;}
    root.innerHTML=addons.map((a,i)=>`<div class="addon-row" data-addon-row="${i}"><span>${escapeHTML(a.name)}</span><input aria-label="${escapeHTML(a.name)} amount" type="number" min="0" step="0.01" value="${Number(a.amount)}" data-addon-amount="${i}"><button class="remove-addon" type="button" data-remove-addon="${i}" aria-label="Remove ${escapeHTML(a.name)}"><i class="fa-solid fa-xmark"></i></button></div>`).join("");
  }
  function escapeHTML(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}
  function addAddon(name,amount){addons.push({name,amount:Number(amount)||0});renderAddons();}
  function financingSet(mode){financing=mode;$$('[data-financing]').forEach(b=>{const on=b.dataset.financing===mode;b.classList.toggle("active",on);b.setAttribute("aria-pressed",String(on));});$("#loan-fields").hidden=mode!=="loan";}
  function cashCreditAmount(s,trade,enabled){
    if(!enabled||!s)return 0;
    if(s.trade_in_rule==="none")return 0;
    if(s.trade_in_rule==="limited")return Math.min(trade,12000);
    if(s.trade_in_rule==="new_only")return Math.min(trade,num("#selling-price"));
    if(s.trade_in_rule==="partial")return Math.min(trade,num("#selling-price"))*(1.25/4.5);
    return Math.min(trade,num("#selling-price"));
  }
  function loanPayment(principal,apr,months){
    principal=Math.max(0,principal);months=Math.max(1,Math.round(months||1));
    if(principal===0)return 0;
    const r=Math.max(0,apr)/1200;
    if(r===0)return principal/months;
    const f=Math.pow(1+r,months);
    return principal*(r*f)/(f-1);
  }
  function calculate(){
    const s=activeState(); if(!s)throw new Error("Choose a state before running the audit.");
    const price=num("#selling-price"),trade=num("#trade-in"),doc=num("#doc-fee"),gov=num("#gov-fees"),rate=num("#tax-rate")/100;
    const applyCredit=$("#apply-trade-credit").checked;
    const credit=cashCreditAmount(s,trade,applyCredit);
    const docTax=$("#doc-fee-taxable").checked;
    const addonTotal=addons.reduce((sum,a)=>sum+Math.max(0,Number(a.amount)||0),0);
    const taxableBase=Math.max(0,price-(applyCredit?credit:0)+(docTax?doc:0)+addonTotal);
    const tax=taxableBase*rate;
    const quotedOtd=Math.max(0,price+doc+gov+addonTotal+tax-trade);
    const benchmark=s.doc_fee_cap!==null?s.doc_fee_cap:s.average_doc_fee;
    const highDoc=doc>benchmark*1.25 || (s.doc_fee_cap!==null && doc>s.doc_fee_cap);
    const docAccepted=selection.doc!==false;
    const targetDoc=highDoc&&!docAccepted?Math.min(doc,benchmark):doc;
    const keptAddons=addons.filter((a,i)=>selection.addons[i]!==false);
    const keptAddonTotal=keptAddons.reduce((sum,a)=>sum+Math.max(0,Number(a.amount)||0),0);
    const targetTaxBase=Math.max(0,price-(applyCredit?credit:0)+(docTax?targetDoc:0)+keptAddonTotal);
    const targetTax=targetTaxBase*rate;
    const targetOtd=Math.max(0,price+targetDoc+gov+keptAddonTotal+targetTax-trade);
    const savings=Math.max(0,quotedOtd-targetOtd);
    const overage=Math.max(0,doc-benchmark);
    const flaggedAddonTotal=addonTotal;
    const junkExposure=overage+flaggedAddonTotal;
    const fairness=Math.max(0,Math.min(100,Math.round(100-(Math.max(savings,junkExposure)/Math.max(500,quotedOtd))*280)));
    const apr=financing==="loan"?Number($("#apr").value)||0:0;
    const months=financing==="loan"?Math.max(1,Number($("#loan-months").value)||1):0;
    const quotedPayment=financing==="loan"?loanPayment(quotedOtd,apr,months):0;
    const targetPayment=financing==="loan"?loanPayment(targetOtd,apr,months):0;
    const junkPayment=financing==="loan"?loanPayment(junkExposure,apr,months):0;
    const extraMonthly=junkPayment;
    const extraInterest=financing==="loan"?Math.max(0,junkPayment*months-junkExposure):0;
    let verdict="Fair deal",note="Your entered numbers are close to the current reference target.",klass="verdict-fair";
    if(flaggedAddonTotal>0){verdict="Junk fee alert";note="Optional dealer add-ons are included. Review each line and remove anything you did not request.";klass="verdict-junk";}
    else if(savings>100){verdict="Overpriced";note="The quote is above the current state-aware reference target. Ask the dealer to explain the difference.";klass="verdict-over";}
    return {state:s,price,trade,doc,gov,rate:rate*100,applyCredit,credit,docTax,addons:addons.map(a=>({...a})),addonTotal,taxableBase,tax,quotedOtd,targetOtd,savings,benchmark,highDoc,targetDoc,targetTax,keptAddonTotal,fairness,verdict,note,klass,financing,apr,months,quotedPayment,targetPayment,junkExposure,extraMonthly,extraInterest,overage};
  }
  function lineRow(label,amount,kind,description,toggleType=null,toggleIndex=null,checked=true){
    const toggle=toggleType?`<label class="line-toggle"><input type="checkbox" data-target-type="${toggleType}" ${toggleIndex!==null?`data-target-index="${toggleIndex}"`:""} ${checked?"checked":""}> Keep in target</label>`:"";
    return `<div class="xray-line"><span class="line-dot ${kind}"></span><div class="line-main"><b>${escapeHTML(label)}</b><small>${escapeHTML(description)}${toggle}</small></div><span class="line-value">${money(amount)}</span></div>`;
  }
  function renderXray(a){
    const root=$("#xray-lines"); if(!root)return;
    let html="";
    html+=lineRow("Vehicle selling price",a.price,"green","Starting vehicle price on the buyer's order.");
    if(a.trade>0)html+=lineRow("Trade-in value",-a.trade,"green","Shown as a deal credit; tax treatment is a separate setting.");
    html+=lineRow("Estimated vehicle tax",a.tax,"green",`Calculated from an estimated taxable base of ${money(a.taxableBase)} at ${a.rate.toFixed(3).replace(/0+$/,'').replace(/\.$/,'')}%.`);
    html+=lineRow("Government title & registration",a.gov,"green","Government charges are separate from the dealer's documentation fee.");
    const docDesc=a.state.doc_fee_cap!==null?`Reference cap ${money(a.state.doc_fee_cap)}. Confirm dealer and transaction eligibility.`:(a.state.doc_fee_rule_status==="not_verified"?"Statewide limit not verified; market benchmark is not a legal ceiling.":`Market benchmark ${money(a.state.average_doc_fee)}; not a legal cap.`);
    if(a.highDoc)html+=lineRow("Dealer documentation fee",a.doc,"amber",docDesc,"doc",null,selection.doc!==false);
    else html+=lineRow("Dealer documentation fee",a.doc,"green","Compare with the state reference; keep this amount itemized.");
    a.addons.forEach((x,i)=>html+=lineRow(x.name,x.amount,"red","Optional dealer-installed or dealer-added item. Ask whether you can decline it.","addon",i,selection.addons[i]!==false));
    root.innerHTML=html;
    $$("[data-target-type]",root).forEach(input=>input.addEventListener("change",()=>{
      if(input.dataset.targetType==="doc")selection.doc=input.checked;
      else selection.addons[Number(input.dataset.targetIndex)]=input.checked;
      updateTargetDisplay();
    }));
  }
  function updateTargetDisplay(){
    if(!lastAudit)return;
    const a=calculate();lastAudit={...lastAudit,...a};
    $("#target-otd").textContent=money(a.targetOtd);$("#live-target-otd").textContent=money(a.targetOtd);$("#potential-savings").textContent=money(a.savings);$("#fairness-score").textContent=a.fairness;
    if(a.financing==="loan"){$("#target-subline").textContent=`Estimated loan payment ${money(a.targetPayment)} / month`;$("#live-target-payment").textContent=`${money(a.targetPayment)} / mo`;}
    renderEmail();
  }
  function renderAudit(){
    const a=calculate();lastAudit=a;
    const results=$("#audit-results");results.hidden=false;
    const banner=$("#verdict-banner");banner.className=`verdict-banner ${a.klass}`;
    $("#verdict-label").textContent=a.verdict;$("#verdict-note").textContent=a.note;$("#fairness-score").textContent=a.fairness;
    $("#potential-savings").textContent=money(a.savings);$("#quoted-otd").textContent=money(a.quotedOtd);$("#target-otd").textContent=money(a.targetOtd);
    $("#quoted-subline").textContent=`${a.state.name} · ${a.financing==="loan"?`Estimated payment ${money(a.quotedPayment)} / month`:"Cash purchase estimate"}`;
    $("#target-subline").textContent=a.financing==="loan"?`Estimated payment ${money(a.targetPayment)} / month`:"Based on the reference fee target and selected line items";
    $("#live-target-otd").textContent=money(a.targetOtd);$("#live-payment-row").hidden=a.financing!=="loan";
    if(a.financing==="loan")$("#live-target-payment").textContent=`${money(a.targetPayment)} / mo`;
    $("#loan-trap").hidden=a.financing!=="loan";
    if(a.financing==="loan"){$("#extra-monthly").textContent=money(a.extraMonthly);$("#extra-interest").textContent=money(a.extraInterest);}
    renderXray(a);renderEmail();results.scrollIntoView({behavior:"smooth",block:"start"});
  }
  function emailText(tone){
    if(!lastAudit)return "";
    const a=calculate();const target=money(a.targetOtd);const quote=money(a.quotedOtd);const savings=money(Math.max(0,a.quotedOtd-a.targetOtd));
    const state=a.state.name;
    if(tone==="firm")return `Subject: Request for revised out-the-door price\n\nHello,\n\nThank you for putting the numbers together. I reviewed the buyer's order and would like a revised written out-the-door quote for the vehicle.\n\nThe current quoted OTD total is ${quote}. Based on the selling price, government charges, and the ${state} fee references, my target is ${target}. Please remove any optional add-ons I have not requested and explain any dealer fee that cannot be adjusted.\n\nPlease send the updated itemized buyer's order with the selling price, doc fee, taxes, title and registration shown separately. I am ready to review a clean, complete offer.\n\nThank you.`;
    if(tone==="walkaway")return `Subject: Final out-the-door offer\n\nHello,\n\nThank you for your time. I am prepared to move forward only if the complete out-the-door price can be brought to ${target}, with optional add-ons removed unless I have expressly agreed to them.\n\nThe current quote totals ${quote}. Please send your best itemized final offer, including all taxes, dealer fees, title and registration. If that total is not possible, I will need to continue shopping.\n\nThank you for considering my offer.`;
    return `Subject: Quick question about the out-the-door price\n\nHello,\n\nThanks for walking me through the vehicle and the quote. I have reviewed the itemized costs and would feel comfortable moving ahead at an out-the-door target of ${target}.\n\nCould you please review the documentation fee and any optional add-ons, then send me an updated buyer's order with the selling price, taxes, dealer fees, title and registration listed separately?\n\nI appreciate your help and look forward to seeing the revised numbers.\n\nBest regards`;
  }
  function renderEmail(){const area=$("#counter-email");if(area)area.value=emailText($("#email-tone")?.value||"polite");}
  function currentPayload(){
    return {state:$("#state-select").value,price:num("#selling-price"),trade:num("#trade-in"),taxRate:num("#tax-rate"),credit:$("#apply-trade-credit").checked,doc:num("#doc-fee"),gov:num("#gov-fees"),docTax:$("#doc-fee-taxable").checked,addons:addons.map(a=>({...a})),financing,apr:num("#apr"),months:Math.max(1,Number($("#loan-months").value)||72),selection:{doc:selection.doc,addons:{...selection.addons}}};
  }
  function restorePayload(p){
    if(!p||!p.state||!states.some(s=>s.code===p.state))throw new Error("This share link is missing a valid state.");
    $("#state-select").value=p.state;stateSelectChange(p.state,false);
    $("#selling-price").value=p.price??32000;$("#trade-in").value=p.trade??0;$("#tax-rate").value=p.taxRate??activeState().tax_rate_pct;
    $("#apply-trade-credit").checked=!!p.credit;$("#apply-trade-credit").disabled=activeState().trade_in_rule==="none";
    $("#doc-fee").value=p.doc??activeState().average_doc_fee;$("#gov-fees").value=p.gov??activeState().government_fee_default;$("#doc-fee-taxable").checked=p.docTax!==false;
    addons=Array.isArray(p.addons)?p.addons.map(a=>({name:String(a.name||"Dealer fee").slice(0,42),amount:Math.max(0,Number(a.amount)||0)})):[];
    selection=p.selection&&typeof p.selection==="object"?{doc:p.selection.doc!==false,addons:p.selection.addons||{}}:{doc:true,addons:{}};
    $("#apr").value=p.apr??6.9;$("#loan-months").value=p.months??72;financingSet(p.financing==="loan"?"loan":"cash");renderAddons();
  }
  function shareUrl(){
    const p=currentPayload();
    return `${location.origin}${location.pathname}#q=${encodeURIComponent(JSON.stringify(p))}`;
  }
  function parseShare(){
    if(!location.hash.startsWith("#q="))return null;
    try{return JSON.parse(decodeURIComponent(location.hash.slice(3)));}catch(e){return null;}
  }
  async function copyText(text,success){
    try{if(navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(text);else{const ta=document.createElement("textarea");ta.value=text;ta.style.position="fixed";ta.style.opacity="0";document.body.appendChild(ta);ta.select();const ok=document.execCommand("copy");ta.remove();if(!ok)throw new Error("Copy not available");}toast(success||"Copied to clipboard.");}catch(e){toast("Copy was blocked by this browser. Select and copy the text manually.");}
  }
  function savedCount(){const count=safeReadSaved().length;$$('[data-saved-count]').forEach(el=>el.textContent=count);$("#saved-modal-count").textContent=`${count} of 4 quotes saved`;}
  function openSaved(){renderSaved();$("#saved-modal").hidden=false;$("[data-close-modal]")?.focus();}
  function closeSaved(){const m=$("#saved-modal");if(m)m.hidden=true;}
  function saveQuote(){
    if(!lastAudit){toast("Run an audit before saving a quote.");return;}
    const a=calculate();const saved=safeReadSaved();const quote={id:Date.now().toString(36),savedAt:new Date().toISOString(),payload:currentPayload(),state:a.state.name,code:a.state.code,quoted:a.quotedOtd,target:a.targetOtd,score:a.fairness,savings:a.savings};
    if(saved.length>=4){toast("You can save up to four quotes. Remove one to add another.");openSaved();return;}
    saved.unshift(quote);if(safeWriteSaved(saved)){savedCount();toast("Quote saved on this device.");}
  }
  function renderSaved(){
    const root=$("#saved-quotes-list");if(!root)return;const saved=safeReadSaved();
    root.innerHTML=saved.length?saved.map(q=>`<article class="saved-quote-row"><div><b>${escapeHTML(q.state)} · ${escapeHTML(q.code)}</b><small>${new Date(q.savedAt).toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"})}</small><div class="saved-quote-metrics"><span>Quoted ${money(q.quoted)}</span><span>Target ${money(q.target)}</span><span>Score ${q.score}/100</span></div></div><button class="remove-saved" type="button" data-remove-saved="${q.id}" aria-label="Remove saved quote"><i class="fa-solid fa-trash"></i></button></article>`).join(""):'<div class="saved-empty"><i class="fa-regular fa-heart"></i><p>No saved quotes yet.</p><span>Run an audit and save it to compare offers from different dealers.</span></div>';
    $$("[data-remove-saved]",root).forEach(b=>b.addEventListener("click",()=>{safeWriteSaved(safeReadSaved().filter(q=>q.id!==b.dataset.removeSaved));renderSaved();savedCount();}));savedCount();
  }
  function downloadAuditCard(){
    if(!lastAudit){toast("Run an audit before downloading a card.");return;}
    const a=calculate();const c=document.createElement("canvas");c.width=1080;c.height=1080;const x=c.getContext("2d");
    x.fillStyle="#F8F9FA";x.fillRect(0,0,1080,1080);
    x.fillStyle="#142033";x.fillRect(0,0,1080,260);
    x.fillStyle="#F38020";x.beginPath();x.roundRect(76,66,72,72,18);x.fill();
    x.fillStyle="#fff";x.beginPath();x.roundRect(87,101,48,20,6);x.fill();x.beginPath();x.moveTo(94,102);x.lineTo(102,88);x.lineTo(119,88);x.lineTo(130,102);x.closePath();x.fill();x.fillStyle="#F38020";x.beginPath();x.arc(98,121,6,0,Math.PI*2);x.arc(125,121,6,0,Math.PI*2);x.fill();x.fillStyle="#fff";x.font="700 32px Arial";x.fillText("CarQuote",172,112);x.fillStyle="#F38020";x.fillText("Check",334,112);
    x.fillStyle="#fff";x.font="700 48px Arial";x.fillText(a.verdict,76,202);
    x.fillStyle="#D1D5DB";x.font="22px Arial";x.fillText(`${a.state.name}  |  Fairness score`,76,238);
    x.fillStyle="#fff";x.beginPath();x.roundRect(838,65,160,108,22);x.fill();x.fillStyle="#142033";x.font="700 50px Arial";x.fillText(String(a.fairness),866,130);x.font="18px Arial";x.fillText("/ 100",940,130);
    const card=(left,top,w,h,label,value,fill)=>{x.fillStyle=fill;x.beginPath();x.roundRect(left,top,w,h,20);x.fill();x.fillStyle="#64748B";x.font="700 19px Arial";x.fillText(label,left+24,top+42);x.fillStyle="#111827";x.font="700 42px Arial";x.fillText(value,left+24,top+105);};
    card(76,310,444,160,"Dealer quoted OTD",money(a.quotedOtd),"#fff");card(560,310,444,160,"Fair target OTD",money(a.targetOtd),"#FFF7ED");
    x.fillStyle="#F38020";x.beginPath();x.roundRect(76,500,928,126,21);x.fill();x.fillStyle="#fff";x.font="700 22px Arial";x.fillText("Potential savings",108,548);x.font="700 55px Arial";x.fillText(money(a.savings),108,602);
    x.fillStyle="#111827";x.font="700 24px Arial";x.fillText("REVIEW THESE LINE ITEMS",76,695);
    const flagged=[];if(a.highDoc)flagged.push(["Dealer documentation fee",a.doc]);a.addons.forEach(z=>flagged.push([z.name,z.amount]));
    const display=(flagged.length?flagged:[["No optional add-ons entered",0]]).slice(0,4);
    let y=742;display.forEach(([label,val])=>{x.fillStyle="#FEE2E2";x.beginPath();x.arc(90,y-7,7,0,Math.PI*2);x.fill();x.fillStyle="#374151";x.font="22px Arial";x.fillText(label,114,y);x.textAlign="right";x.font="700 22px Arial";x.fillText(money(val),990,y);x.textAlign="left";y+=54;});
    x.strokeStyle="#E5E7EB";x.beginPath();x.moveTo(76,970);x.lineTo(1004,970);x.stroke();x.fillStyle="#6B7280";x.font="17px Arial";x.fillText("State rules and tax figures are estimates. Verify your buyer's order.",76,1010);x.fillText("CarQuoteCheck  |  carquotecheck.pages.dev  |  Private browser-side estimate",76,1042);
    c.toBlob(blob=>{if(!blob){toast("PNG export failed in this browser.");return;}const aTag=document.createElement("a");const url=URL.createObjectURL(blob);aTag.href=url;aTag.download="carquotecheck-audit-card.png";aTag.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast("Audit card downloaded.");},"image/png");
  }
  function trySample(){
    $("#state-select").value="FL";stateSelectChange("FL");$("#selling-price").value=32000;$("#trade-in").value=5000;$("#tax-rate").value=6;$("#apply-trade-credit").checked=true;$("#doc-fee").value=999;$("#gov-fees").value=2150;$("#doc-fee-taxable").checked=true;
    addons=[{name:"Paint Protection",amount:799},{name:"VIN Etching",amount:299}];renderAddons();$("#apr").value=6.9;$("#loan-months").value=72;financingSet("loan");selection={doc:true,addons:{}};setStep(3,false);renderAudit();
  }
  function reset(){
    Object.entries(defaults).forEach(([id,v])=>{if($(id))$(id).value=v;});addons=[];selection={doc:true,addons:{}};renderAddons();financingSet("cash");const s=states.find(x=>x.code===(document.body.dataset.defaultState||"FL"))||states.find(x=>x.code==="FL");if(s){$("#state-select").value=s.code;stateSelectChange(s.code);}setStep(1,false);clearError();$("#audit-results").hidden=true;lastAudit=null;history.replaceState(null,"",location.pathname+location.search);$("#auditor-wizard")?.scrollIntoView({behavior:"smooth",block:"start"});
  }
  function initDirectory(){
    const search=$("#state-search");if(!search)return;let filter="all";
    const update=()=>{const q=search.value.trim().toLowerCase();let n=0;$$('[data-state-row],[data-state-card]').forEach(el=>{const match=!q||el.dataset.name.includes(q)||el.dataset.code.toLowerCase().includes(q);const rule=el.dataset.rule;const passFilter=filter==="all"||(filter==="capped"?rule==="capped":rule!=="capped");const show=match&&passFilter;el.hidden=!show;if(show&&el.hasAttribute("data-state-row"))n++;});const count=$("#directory-count");if(count)count.textContent=`Showing ${n} ${n===1?"jurisdiction":"jurisdictions"}`;};
    $$("[data-filter]").forEach(b=>b.addEventListener("click",()=>{$$("[data-filter]").forEach(x=>x.classList.remove("active"));b.classList.add("active");filter=b.dataset.filter;update();}));search.addEventListener("input",update);
    $$("[data-state-chip]").forEach(b=>b.addEventListener("click",()=>{$("#state-select").value=b.dataset.stateChip;stateSelectChange(b.dataset.stateChip);setStep(1,false);$("#selling-price").focus();}));
    document.addEventListener("keydown",e=>{if(e.key==="/"&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)){e.preventDefault();search.focus();}});
  }
  function initMobile(){
    const btn=$(".mobile-menu-toggle"),drawer=$("#mobile-drawer");if(!btn||!drawer)return;
    const close=()=>{drawer.hidden=true;btn.setAttribute("aria-expanded","false");btn.setAttribute("aria-label","Open navigation menu");btn.innerHTML='<i class="fa-solid fa-bars" aria-hidden="true"></i>';};
    btn.addEventListener("click",()=>{const open=btn.getAttribute("aria-expanded")==="true";drawer.hidden=open;btn.setAttribute("aria-expanded",String(!open));btn.setAttribute("aria-label",open?"Open navigation menu":"Close navigation menu");btn.innerHTML=open?'<i class="fa-solid fa-bars" aria-hidden="true"></i>':'<i class="fa-solid fa-xmark" aria-hidden="true"></i>';});
    drawer.addEventListener("click",e=>{if(e.target.closest("a")){close();}});
    document.addEventListener("click",e=>{if(!drawer.hidden&&!drawer.contains(e.target)&&!btn.contains(e.target))close();});
    document.addEventListener("keydown",e=>{if(e.key==="Escape")close();});
  }
  function scrollToSection(id, behavior="smooth"){
    const target=document.getElementById(id);
    if(!target)return false;
    target.scrollIntoView({behavior,block:"start"});
    const drawer=$("#mobile-drawer"),menu=$(".mobile-menu-toggle");
    if(drawer&&!drawer.hidden){drawer.hidden=true;menu?.setAttribute("aria-expanded","false");menu?.setAttribute("aria-label","Open navigation menu");if(menu)menu.innerHTML='<i class="fa-solid fa-bars" aria-hidden="true"></i>';}
    return true;
  }
  function initScrollLinks(){
    $$('[data-scroll-target]').forEach(link=>link.addEventListener("click",event=>{
      const id=link.dataset.scrollTarget;
      if(!id)return;
      event.preventDefault();
      if(document.getElementById(id)){scrollToSection(id);return;}
      const next=new URL("/",location.origin);next.searchParams.set("scroll",id);location.assign(next.href);
    }));
    const requested=new URLSearchParams(location.search).get("scroll");
    if(requested&&document.getElementById(requested)){
      history.replaceState(null,"",location.pathname);
      requestAnimationFrame(()=>scrollToSection(requested,"auto"));
    }
  }
  function init(){
    fillStateOptions();initDirectory();initMobile();initScrollLinks();savedCount();
    $("#state-select")?.addEventListener("change",e=>stateSelectChange(e.target.value));
    $$("[data-next-step]").forEach(b=>b.addEventListener("click",()=>{const current=Number(b.dataset.nextStep)-1;if(validateStep(current))setStep(Number(b.dataset.nextStep));}));
    $$("[data-prev-step]").forEach(b=>b.addEventListener("click",()=>setStep(Number(b.dataset.prevStep))));
    $$("[data-go-step]").forEach(b=>b.addEventListener("click",()=>{const n=Number(b.dataset.goStep);if(n<=currentStep)setStep(n);else if(validateStep(currentStep))setStep(n);}));
    $$("[data-fee-name]").forEach(b=>b.addEventListener("click",()=>{const name=b.dataset.feeName;const existing=addons.find(x=>x.name===name);if(existing){toast("That fee is already added.");return;}addAddon(name,b.dataset.feeValue);}));
    $("#addon-list")?.addEventListener("change",e=>{const i=Number(e.target.dataset.addonAmount);if(Number.isInteger(i)&&addons[i])addons[i].amount=Math.max(0,Number(e.target.value)||0);});
    $("#addon-list")?.addEventListener("click",e=>{const b=e.target.closest("[data-remove-addon]");if(!b)return;addons.splice(Number(b.dataset.removeAddon),1);renderAddons();});
    $("#add-custom-fee")?.addEventListener("click",()=>{const name=$("#custom-fee-name").value.trim(),amount=Number($("#custom-fee-amount").value);if(!name||!Number.isFinite(amount)||amount<=0){showError("Enter a custom fee name and a positive amount.");return;}clearError();addAddon(name,amount);$("#custom-fee-name").value="";$("#custom-fee-amount").value="";});
    $$('[data-financing]').forEach(b=>b.addEventListener("click",()=>financingSet(b.dataset.financing)));
    $("#quote-form")?.addEventListener("submit",e=>{e.preventDefault();if(!validateStep(3))return;try{renderAudit();}catch(err){showError(err.message);}});
    $("#sample-quote")?.addEventListener("click",trySample);$("#reset-quote")?.addEventListener("click",reset);$("#edit-quote")?.addEventListener("click",()=>{setStep(1);$("#auditor-wizard")?.scrollIntoView({behavior:"smooth"});});
    $("#save-quote")?.addEventListener("click",saveQuote);$("#download-card")?.addEventListener("click",downloadAuditCard);$("#copy-link")?.addEventListener("click",()=>{if(!lastAudit){toast("Run an audit first.");return;}copyText(shareUrl(),"Shareable quote link copied.");});
    $("#email-tone")?.addEventListener("change",renderEmail);$("#copy-email")?.addEventListener("click",()=>copyText($("#counter-email").value,"Counter-offer email copied."));$("#print-sheet")?.addEventListener("click",()=>window.print());
    $$('[data-open-saved]').forEach(b=>b.addEventListener("click",e=>{e.preventDefault();openSaved();}));
    $$('[data-close-modal]').forEach(b=>b.addEventListener("click",closeSaved));$("#saved-modal")?.addEventListener("click",e=>{if(e.target.id==="saved-modal")closeSaved();});
    $("#copy-contact-email")?.addEventListener("click",()=>copyText($("#contact-email").textContent.trim(),"Email address copied."));
    const shared=parseShare();if(shared){try{restorePayload(shared);setStep(3,false);renderAudit();toast("Shareable quote restored.");}catch(e){toast("This share link could not be restored.");}}
  }
  document.addEventListener("DOMContentLoaded",async()=>{
    try{const res=await fetch("/data/states.json",{cache:"no-cache"});if(!res.ok)throw new Error("State data could not be loaded.");states=await res.json();init();}
    catch(e){const hint=$("#state-hint");if(hint)hint.textContent="State reference data could not load. Check your connection and refresh the page.";console.error(e);}
  });
})();
