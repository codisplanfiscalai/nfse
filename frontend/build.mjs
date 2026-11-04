import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url));
const out=path.join(dir,'../src/nfse/portal');
// Same offline build pattern: precompiled Vue render, CSP without unsafe-eval.
const decode=s=>s.replace(/&(#x[0-9a-f]+|#\d+|amp|lt|gt|quot|apos|nbsp);/gi, (_,k)=>k[0]==='#'?String.fromCodePoint(k[1].toLowerCase()==='x'?parseInt(k.slice(2),16):parseInt(k.slice(1),10)):({amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",nbsp:'\u00a0'})[k.toLowerCase()]);
const sandbox={console,document:{createElement(){return {textContent:'',get innerHTML(){return this.textContent;},set innerHTML(v){this.textContent=decode(v);this.children=[{getAttribute(){return decode(v.slice(10,-2))}}]}}}}};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(dir,'vendor/vue.js'),'utf8'),sandbox);
const errors=[];
const template=fs.readFileSync(path.join(dir,'templates/app.html'),'utf8').replace(/\r\n?/g,'\n');
const render=sandbox.Vue.compile(template,{hoistStatic:false,onError:e=>errors.push(String(e))});
if(errors.length)throw Error(errors.join('\n'));
const result='/* Vue 3 - template compilado offline */\nvar _Vue=Vue; var NFSeRender='+render.toString()+';\n';
if(process.argv.includes('--check')){
 if(fs.readFileSync(path.join(out,'render.js'),'utf8')!==result)throw Error('Compile a interface: node frontend/build.mjs');
}else {fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'render.js'),result);}
console.log('Vue compilado offline, template validado.');
