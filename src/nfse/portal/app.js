'use strict';
const menus=[
 {id:'dashboard',label:'Visão geral',group:'PRINCIPAL',icon:'▦',permission:'dashboard'},
 {id:'companies',label:'Empresas',group:'OPERAÇÃO FISCAL',icon:'▤',permission:'companies'},
 {id:'certificates',label:'Certificados digitais',group:'OPERAÇÃO FISCAL',icon:'◇',permission:'certificates'},
 {id:'sync',label:'Sincronizar ADN',group:'OPERAÇÃO FISCAL',icon:'⇄',permission:'sync'},
 {id:'documents',label:'Documentos e eventos',group:'OPERAÇÃO FISCAL',icon:'▧',permission:'documents'},
 {id:'reports',label:'Relatórios fiscais',group:'OPERAÇÃO FISCAL',icon:'▣',permission:'reports'},
 {id:'users',label:'Usuários',group:'ADMINISTRAÇÃO',icon:'♙',permission:'users'},
 {id:'settings',label:'Configurações',group:'ADMINISTRAÇÃO',icon:'⚙',permission:'settings'},
 {id:'audit',label:'Auditoria',group:'ADMINISTRAÇÃO',icon:'◷',permission:'audit'},
 {id:'profile',label:'Minha conta',group:'CONTA',icon:'◉'}
];
const app=Vue.createApp({
 render:NFSeRender,
 data:()=>({ready:false,busy:false,user:null,permissions:[],csrf:'',version:'',configured:true,
   error:'',notice:'',page:'dashboard',menuOpen:false,login:{name:'',email:'',password:''},
   dashboard:{companies:0,invoices:0,events:0,sync_runs:0,latest:[]},companies:[],certificates:[],
   runs:[],documents:[],audit:[],users:[],settings:{adn_url:''},showCompany:false,
   companyForm:{name:'',identifier:''},certificate:{label:'',pfx_base64:'',password:''},
   link:{company_id:'',certificate_id:''},syncForm:{company_id:'',certificate_id:''},
   filter:{company_id:'',document_type:''},direct:{nsu:0,lote:true,access_key:'',save:false},directResult:null,report:{company_id:'',kind:'mensal',inicio:'',fim:''},
   reportResult:null,userForm:{name:'',email:'',password:'',role:'leitor'}}),
 computed:{
   initials(){return (this.user?.name||'C').split(' ').filter(Boolean).slice(0,2).map(p=>p[0].toUpperCase()).join('');},
   menuGroups(){const allowed=menus.filter(x=>!x.permission||this.permissions.includes(x.permission));const groups=[...new Set(allowed.map(x=>x.group))];return groups.map(title=>({title,items:allowed.filter(x=>x.group===title)}));},
   pageLabel(){return menus.find(x=>x.id===this.page)?.label||'Visão geral';},
   pageSubtitle(){return ({dashboard:'Acompanhe documentos, eventos e operações recentes.',companies:'Gestão de contribuintes e autorizações.',certificates:'Guarde e gerencie certificados de forma protegida.',sync:'Distribuição sequencial de documentos a partir do ADN.',documents:'Consulte NFS-e, eventos e XMLs preservados.',reports:'Fechamento fiscal por emissão, competência, retenções e cancelamento.',users:'Gerencie contas e permissões da equipe.',settings:'Conexão com serviços oficiais da NFS-e.',audit:'Rastreabilidade das operações administrativas.',profile:'Informações de acesso e segurança.'})[this.page];},
   metrics(){return [{key:'companies',label:'Empresas',icon:'▤',desc:'Contribuintes cadastrados'},
     {key:'invoices',label:'NFS-e',icon:'▧',desc:'Documentos armazenados'},
     {key:'events',label:'Eventos',icon:'◷',desc:'Eventos distribuídos'},
     {key:'sync_runs',label:'Sincronizações',icon:'⇄',desc:'Execuções registradas'}]}
 },
 methods:{
  currency(c){return ((Number(c)||0)/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});},
  datetime(v){if(!v)return '—';try{return new Date(v).toLocaleString('pt-BR')}catch{return v}},
  async api(path,data){const opts={method:data===undefined?'GET':'POST',credentials:'same-origin',cache:'no-store',headers:{}};
   if(data!==undefined){opts.headers['Content-Type']='application/json';opts.headers['X-CSRF-Token']=this.csrf;opts.body=JSON.stringify(data)}
   const response=await fetch('/api/v1/'+path,opts);let out;
   try{out=await response.json()}catch{throw Error('Resposta inválida do servidor.');}
   if(!response.ok){if(response.status===401&&path!=='auth/login'){this.user=null;this.permissions=[];}throw Error(out.error||'A operação não pôde ser concluída.');}
   return out.data;
  },
  async act(action){if(this.busy)return;this.busy=true;this.error='';this.notice='';try{await action()}catch(e){this.error=String(e.message||e)}finally{this.busy=false}},
  async init(){try{const status=await this.api('status');this.configured=status.configured;this.version=status.version;
    try{const me=await this.api('auth/me');this.user=me.user;this.csrf=me.csrf;this.permissions=me.permissions}catch{}
    this.page=(location.hash||'#/dashboard').replace('#/','');if(!menus.some(x=>x.id===this.page))this.page='dashboard';
    const today=new Date();const first=new Date(today.getFullYear(),today.getMonth(),1);
    const iso=d=>[d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');
    this.report.inicio=iso(first);this.report.fim=iso(today);
    if(this.user)await this.load(this.page);
    window.addEventListener('hashchange',()=>{const name=location.hash.replace('#/','');if(menus.some(x=>x.id===name))this.go(name,false)});
    window.addEventListener('keydown',(event)=>{if(event.key==='Escape'){this.menuOpen=false;this.showCompany=false;}});
   }catch(e){this.error=e.message}finally{this.ready=true}},
  go(page,hash=true){const selected=menus.find(x=>x.id===page);if(!selected||selected.permission&&!this.permissions.includes(selected.permission))return;
   this.page=page;this.menuOpen=false;this.error='';this.notice='';this.reportResult=null;
   if(hash)history.replaceState(null,'','#/'+page);this.load(page);},
  async submitAuth(){await this.act(async()=>{if(!this.configured){await this.api('setup',this.login);this.configured=true;this.notice='Administrador criado. Entre com a conta.';this.login.password='';return;}
     const r=await this.api('auth/login',{email:this.login.email,password:this.login.password});this.user=r.user;this.permissions=r.permissions;this.csrf=r.csrf;
     this.login.password='';this.page='dashboard';history.replaceState(null,'','#/dashboard');await this.load('dashboard')})},
  async logout(){await this.act(async()=>{await this.api('auth/logout',{});this.user=null;this.csrf='';this.permissions=[];this.dashboard={};})},
  async load(page){if(!this.user)return;try{if(['dashboard'].includes(page))this.dashboard=await this.api('dashboard');
    if(['companies','certificates','sync','documents','reports'].includes(page)){this.companies=await this.api('companies');if(!this.filter.company_id)this.filter.company_id=this.companies[0]?.id||'';if(!this.report.company_id)this.report.company_id=this.companies[0]?.id||'';if(!this.syncForm.company_id)this.syncForm.company_id=this.companies[0]?.id||'';if(!this.link.company_id)this.link.company_id=this.companies[0]?.id||'';}
    if(['certificates','sync'].includes(page)){if(this.permissions.includes('certificates'))this.certificates=await this.api('certificates');}
    if(page==='sync')this.runs=await this.api('sync');
    if(page==='documents')await this.loadDocuments();
    if(page==='settings')this.settings=await this.api('settings');
    if(page==='users')this.users=await this.api('users');
    if(page==='audit')this.audit=await this.api('audit');
   }catch(e){this.error=e.message}},
  async addCompany(){await this.act(async()=>{await this.api('companies',this.companyForm);this.companyForm={name:'',identifier:''};this.showCompany=false;this.notice='Empresa cadastrada.';this.companies=await this.api('companies');})},
  readCertificate(event){const file=event.target.files?.[0];if(!file){this.certificate.pfx_base64='';return}if(file.size>2*1024*1024){this.error='O arquivo não pode exceder 2 MB.';return}
   const reader=new FileReader();reader.onload=()=>{this.certificate.pfx_base64=String(reader.result).split(',')[1]||'';};reader.readAsDataURL(file);},
  async uploadCertificate(){await this.act(async()=>{if(!this.certificate.pfx_base64)throw Error('Selecione um PFX/P12 válido.');
    await this.api('certificates',this.certificate);this.certificate={label:'',pfx_base64:'',password:''};this.certificates=await this.api('certificates');this.notice='Certificado A1 importado.';})},
  async linkCertificate(){await this.act(async()=>{await this.api('companies/'+this.link.company_id+'/certificates',{certificate_id:this.link.certificate_id});this.notice='Vínculo autorizado.'})},
  async startSync(){await this.act(async()=>{const result=await this.api('sync',this.syncForm);this.notice='Sincronização iniciada. Execução #'+result.run_id;this.runs=await this.api('sync');})},
  async directQuery(kind){await this.act(async()=>{
    const base={company_id:this.syncForm.company_id,certificate_id:this.syncForm.certificate_id,save:this.direct.save};
    const request=kind==='nsu'?{...base,nsu:this.direct.nsu,lote:this.direct.lote}:{...base,access_key:this.direct.access_key};
    const endpoint=kind==='nsu'?'adn/by-nsu':'adn/events';
    this.directResult=await this.api(endpoint,request);
    this.notice='Consulta concluída.';
  })},
  async loadDocuments(){if(!this.filter.company_id)return;try{this.documents=await this.api('documents?company_id='+this.filter.company_id+'&document_type='+encodeURIComponent(this.filter.document_type))}catch(e){this.error=e.message}},
  reportPath(format){const q=new URLSearchParams({company_id:this.report.company_id,inicio:this.report.inicio,fim:this.report.fim,formato:format});return '/api/v1/reports/'+this.report.kind+'?'+q.toString()},
  async previewReport(){await this.act(async()=>{const response=await fetch(this.reportPath('json'),{credentials:'same-origin',cache:'no-store'});const out=await response.json();if(!response.ok)throw Error(out.error||'Falha no relatório.');this.reportResult=out.data;})},
  async download(format){await this.act(async()=>{const r=await fetch(this.reportPath(format),{credentials:'same-origin',cache:'no-store'});if(!r.ok){const x=await r.json();throw Error(x.error||'Falha ao exportar.');}const blob=await r.blob();const a=document.createElement('a');const url=URL.createObjectURL(blob);a.href=url;a.download='codisplan-nfse-'+this.report.kind+'-'+this.report.inicio+'-'+this.report.fim+'.'+format;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);})},
  async saveSettings(){await this.act(async()=>{await this.api('settings',this.settings);this.notice='Configuração salva.';})},
  async createUser(){await this.act(async()=>{await this.api('users',this.userForm);this.users=await this.api('users');this.userForm={name:'',email:'',password:'',role:'leitor'};this.notice='Usuário cadastrado.';})}
 },
 mounted(){this.init()}
});
app.mount('#app');
