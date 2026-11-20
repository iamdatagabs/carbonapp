(() => {
  const apiBase=(window.CARBONAPP_API_BASE||"http://localhost:8080").replace(/\/$/,"");
  const form=document.querySelector("#record-form"),status=document.querySelector("#form-status"),records=document.querySelector("#records");
  const depthLabel={A:"0–10 cm",B:"10–20 cm",C:"20–40 cm",D:"40–60 cm",E:"60–80 cm",F:"80–100 cm",G:"100–130 cm",H:"130–160 cm",I:"160–200 cm"};
  async function request(path,options={}) {
    const response=await fetch(apiBase+path,{...options,headers:{"Content-Type":"application/json",...(options.headers||{})}});
    if(!response.ok) throw new Error("API "+response.status+": "+(await response.text()));
    return response.status===204?null:response.json();
  }
  function render(items) {
    if(!items.length){records.textContent="Nenhum registro cadastrado.";return;}
    records.replaceChildren(...items.slice().reverse().map(item=>{
      const card=document.createElement("article");card.className="record";
      const title=document.createElement("strong");title.textContent=item.projectCode+" · "+item.pointCode;
      const meta=document.createElement("small");meta.textContent="Camada "+item.depthCode+" ("+(depthLabel[item.depthCode]||"intervalo não reconhecido")+") · "+(item.createdAt?new Date(item.createdAt).toLocaleString("pt-BR"):"data indisponível");
      const note=document.createElement("p");note.textContent=item.notes||"Sem observações";note.className="muted";
      card.append(title,meta,note);return card;
    }));
  }
  async function refresh(){try{status.textContent="Sincronizando…";const data=await request("/api/v1/field-records");render(data);status.textContent="API conectada · "+data.length+" registro(s)";}catch(error){status.textContent=error.message;records.textContent="Não foi possível carregar. Verifique se o backend está ativo.";}}
  form.addEventListener("submit",async event=>{
    event.preventDefault();const payload=Object.fromEntries(new FormData(form).entries());status.textContent="Salvando…";
    try{await request("/api/v1/field-records",{method:"POST",body:JSON.stringify(payload)});form.elements.pointCode.value="";form.elements.notes.value="";status.textContent="Registro salvo no servidor.";await refresh();}
    catch(error){status.textContent=error.message;}
  });
  document.querySelector("#refresh").addEventListener("click",refresh);refresh();
})();
