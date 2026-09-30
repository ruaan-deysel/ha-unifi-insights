var e=[`gateway`,`switch`,`access_point`,`client`,`other`],t=`unifi_insights/topology/sources`,n=`unifi_insights/topology/subscribe`,r=`entry_unloaded`,i=`site_unavailable`,a=`devices_unavailable`,o=`legacy_uplink_missing`,s=`parents_unresolved`,c=`clients_truncated`,l=`entry_not_found`,u=`entry_not_loaded`,d=`site_not_selected`,f=class extends Error{received;constructor(e){super(`Unsupported topology schema_version ${String(e)}`),this.name=`IncompatibleSchemaError`,this.received=e}},p=e=>typeof e==`object`&&!!e&&!Array.isArray(e);function m(e){if(!p(e))throw TypeError(`Topology snapshot is not an object`);if(typeof e.schema_version!=`number`)throw TypeError(`Topology snapshot field schema_version is not a number`);if(e.schema_version!==1)throw new f(e.schema_version);for(let t of[`nodes`,`edges`,`issues`,`unresolved`])if(!Array.isArray(e[t]))throw TypeError(`Topology snapshot field ${t} is not a list`);for(let t of[`entry_id`,`site_id`,`site_name`,`revision`,`status`])if(typeof e[t]!=`string`)throw TypeError(`Topology snapshot field ${t} is not a string`);return e}var h=`unifi-insights-topology-card`,g=`unifi-insights-topology-card-editor`,_=`custom:${h}`,v=[`graph`,`list`],y=[`collapsed`,`expanded`,`hidden`],b=[`comfortable`,`compact`],ee=[`vertical`,`horizontal`];function x(e,t,n){if(e!==void 0&&!(typeof e==`string`&&t.includes(e)))throw Error(`${n} must be one of: ${t.join(`, `)}`)}function te(t){if(typeof t!=`object`||!t||Array.isArray(t))throw Error(`Card configuration must be an object`);let n=t;if(typeof n.type!=`string`)throw Error(`type is required`);for(let e of[`entry_id`,`site_id`,`title`]){let t=n[e];if(t!==void 0&&(typeof t!=`string`||t===``))throw Error(`${e} must be a non-empty string`)}if(n.entry_id===void 0!=(n.site_id===void 0))throw Error(`entry_id and site_id must be set together`);x(n.view,v,`view`),x(n.clients,y,`clients`),x(n.density,b,`density`),x(n.orientation,ee,`orientation`);for(let e of[`show_site_selector`,`show_labels`])if(n[e]!==void 0&&typeof n[e]!=`boolean`)throw Error(`${e} must be true or false`);if(n.kinds!==void 0&&(!Array.isArray(n.kinds)||n.kinds.length===0||!n.kinds.every(t=>e.includes(t))))throw Error(`kinds must be a non-empty list of: ${e.join(`, `)}`);let r=n.max_clients;if(r!==void 0&&(typeof r!=`number`||!Number.isInteger(r)||r<1||r>500))throw Error(`max_clients must be a whole number from 1 to 500`);return n}function ne(t){return{entry_id:t.entry_id,site_id:t.site_id,title:t.title,view:t.view??`graph`,show_site_selector:t.show_site_selector??!1,clients:t.clients??`collapsed`,kinds:t.kinds?[...t.kinds]:[...e],density:t.density,orientation:t.orientation??`vertical`,show_labels:t.show_labels??!0,max_clients:t.max_clients??500}}function S(e){return e.flatMap(e=>e.sites.map(t=>({binding:{entry_id:e.entry_id,site_id:t.id},label:`${e.title} — ${t.name}`})))}function re(e,t){if(e.entry_id!==void 0&&e.site_id!==void 0)return{entry_id:e.entry_id,site_id:e.site_id};let n=S(t??[]);return n.length===1?n[0].binding:void 0}function ie(e,t){return e?.entry_id===t?.entry_id&&e?.site_id===t?.site_id}var ae=globalThis,oe=ae.ShadowRoot&&(ae.ShadyCSS===void 0||ae.ShadyCSS.nativeShadow)&&`adoptedStyleSheets`in Document.prototype&&`replace`in CSSStyleSheet.prototype,se=Symbol(),ce=/* @__PURE__ */ new WeakMap,le=class{constructor(e,t,n){if(this._$cssResult$=!0,n!==se)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,t=this.t;if(oe&&e===void 0){let n=t!==void 0&&t.length===1;n&&(e=ce.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),n&&ce.set(t,e))}return e}toString(){return this.cssText}},ue=e=>new le(typeof e==`string`?e:e+``,void 0,se),C=(e,...t)=>new le(e.length===1?e[0]:t.reduce((t,n,r)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if(typeof e==`number`)return e;throw Error(`Value passed to 'css' function must be a 'css' function result: `+e+`. Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.`)})(n)+e[r+1],e[0]),e,se),de=(e,t)=>{if(oe)e.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let n of t){let t=document.createElement(`style`),r=ae.litNonce;r!==void 0&&t.setAttribute(`nonce`,r),t.textContent=n.cssText,e.appendChild(t)}},fe=oe?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t=``;for(let n of e.cssRules)t+=n.cssText;return ue(t)})(e):e,{is:pe,defineProperty:me,getOwnPropertyDescriptor:he,getOwnPropertyNames:ge,getOwnPropertySymbols:_e,getPrototypeOf:ve}=Object,ye=globalThis,be=ye.trustedTypes,xe=be?be.emptyScript:``,Se=ye.reactiveElementPolyfillSupport,Ce=(e,t)=>e,we={toAttribute(e,t){switch(t){case Boolean:e=e?xe:null;break;case Object:case Array:e=e==null?e:JSON.stringify(e)}return e},fromAttribute(e,t){let n=e;switch(t){case Boolean:n=e!==null;break;case Number:n=e===null?null:Number(e);break;case Object:case Array:try{n=JSON.parse(e)}catch{n=null}}return n}},Te=(e,t)=>!pe(e,t),Ee={attribute:!0,type:String,converter:we,reflect:!1,useDefault:!1,hasChanged:Te};Symbol.metadata??=Symbol(`metadata`),ye.litPropertyMetadata??=/* @__PURE__ */ new WeakMap;var De=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=Ee){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let n=Symbol(),r=this.getPropertyDescriptor(e,n,t);r!==void 0&&me(this.prototype,e,r)}}static getPropertyDescriptor(e,t,n){let{get:r,set:i}=he(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:r,set(t){let a=r?.call(this);i?.call(this,t),this.requestUpdate(e,a,n)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??Ee}static _$Ei(){if(this.hasOwnProperty(Ce(`elementProperties`)))return;let e=ve(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(Ce(`finalized`)))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(Ce(`properties`))){let e=this.properties,t=[...ge(e),..._e(e)];for(let n of t)this.createProperty(n,e[n])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[e,n]of t)this.elementProperties.set(e,n)}this._$Eh=/* @__PURE__ */ new Map;for(let[e,t]of this.elementProperties){let n=this._$Eu(e,t);n!==void 0&&this._$Eh.set(n,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let n=new Set(e.flat(1/0).reverse());for(let e of n)t.unshift(fe(e))}else e!==void 0&&t.push(fe(e));return t}static _$Eu(e,t){let n=t.attribute;return!1===n?void 0:typeof n==`string`?n:typeof e==`string`?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=/* @__PURE__ */ new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=/* @__PURE__ */ new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=/* @__PURE__ */ new Map,t=this.constructor.elementProperties;for(let n of t.keys())this.hasOwnProperty(n)&&(e.set(n,this[n]),delete this[n]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return de(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,n){this._$AK(e,n)}_$ET(e,t){let n=this.constructor.elementProperties.get(e),r=this.constructor._$Eu(e,n);if(r!==void 0&&!0===n.reflect){let i=(n.converter?.toAttribute===void 0?we:n.converter).toAttribute(t,n.type);this._$Em=e,i==null?this.removeAttribute(r):this.setAttribute(r,i),this._$Em=null}}_$AK(e,t){let n=this.constructor,r=n._$Eh.get(e);if(r!==void 0&&this._$Em!==r){let e=n.getPropertyOptions(r),i=typeof e.converter==`function`?{fromAttribute:e.converter}:e.converter?.fromAttribute===void 0?we:e.converter;this._$Em=r;let a=i.fromAttribute(t,e.type);this[r]=a??this._$Ej?.get(r)??a,this._$Em=null}}requestUpdate(e,t,n,r=!1,i){if(e!==void 0){let a=this.constructor;if(!1===r&&(i=this[e]),n??=a.getPropertyOptions(e),!((n.hasChanged??Te)(i,t)||n.useDefault&&n.reflect&&i===this._$Ej?.get(e)&&!this.hasAttribute(a._$Eu(e,n))))return;this.C(e,t,n)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:n,reflect:r,wrapped:i},a){n&&!(this._$Ej??=/* @__PURE__ */ new Map).has(e)&&(this._$Ej.set(e,a??t??this[e]),!0!==i||a!==void 0)||(this._$AL.has(e)||(this.hasUpdated||n||(t=void 0),this._$AL.set(e,t)),!0===r&&this._$Em!==e&&(this._$Eq??=/* @__PURE__ */ new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}let e=this.constructor.elementProperties;if(e.size>0)for(let[t,n]of e){let{wrapped:e}=n,r=this[t];!0!==e||this._$AL.has(t)||r===void 0||this.C(t,void 0,n,r)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=/* @__PURE__ */ new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};De.elementStyles=[],De.shadowRootOptions={mode:`open`},De[Ce(`elementProperties`)]=/* @__PURE__ */ new Map,De[Ce(`finalized`)]=/* @__PURE__ */ new Map,Se?.({ReactiveElement:De}),(ye.reactiveElementVersions??=[]).push(`2.1.2`);var Oe=globalThis,ke=e=>e,Ae=Oe.trustedTypes,je=Ae?Ae.createPolicy(`lit-html`,{createHTML:e=>e}):void 0,Me=`$lit$`,w=`lit$${Math.random().toFixed(9).slice(2)}$`,Ne=`?`+w,Pe=`<${Ne}>`,T=document,Fe=()=>T.createComment(``),Ie=e=>e===null||typeof e!=`object`&&typeof e!=`function`,Le=Array.isArray,Re=e=>Le(e)||typeof e?.[Symbol.iterator]==`function`,ze=`[ 	
\f\r]`,Be=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Ve=/-->/g,He=/>/g,E=RegExp(`>|${ze}(?:([^\\s"'>=/]+)(${ze}*=${ze}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,`g`),Ue=/'/g,We=/"/g,Ge=/^(?:script|style|textarea|title)$/i,Ke=e=>(t,...n)=>({_$litType$:e,strings:t,values:n}),D=Ke(1),qe=Ke(2),O=Symbol.for(`lit-noChange`),k=Symbol.for(`lit-nothing`),Je=/* @__PURE__ */ new WeakMap,A=T.createTreeWalker(T,129);function Ye(e,t){if(!Le(e)||!e.hasOwnProperty(`raw`))throw Error(`invalid template strings array`);return je===void 0?t:je.createHTML(t)}var Xe=(e,t)=>{let n=e.length-1,r=[],i,a=t===2?`<svg>`:t===3?`<math>`:``,o=Be;for(let t=0;t<n;t++){let n=e[t],s,c,l=-1,u=0;for(;u<n.length&&(o.lastIndex=u,c=o.exec(n),c!==null);)u=o.lastIndex,o===Be?c[1]===`!--`?o=Ve:c[1]===void 0?c[2]===void 0?c[3]!==void 0&&(o=E):(Ge.test(c[2])&&(i=RegExp(`</`+c[2],`g`)),o=E):o=He:o===E?c[0]===`>`?(o=i??Be,l=-1):c[1]===void 0?l=-2:(l=o.lastIndex-c[2].length,s=c[1],o=c[3]===void 0?E:c[3]===`"`?We:Ue):o===We||o===Ue?o=E:o===Ve||o===He?o=Be:(o=E,i=void 0);let d=o===E&&e[t+1].startsWith(`/>`)?` `:``;a+=o===Be?n+Pe:l>=0?(r.push(s),n.slice(0,l)+Me+n.slice(l)+w+d):n+w+(l===-2?t:d)}return[Ye(e,a+(e[n]||`<?>`)+(t===2?`</svg>`:t===3?`</math>`:``)),r]},Ze=class e{constructor({strings:t,_$litType$:n},r){let i;this.parts=[];let a=0,o=0,s=t.length-1,c=this.parts,[l,u]=Xe(t,n);if(this.el=e.createElement(l,r),A.currentNode=this.el.content,n===2||n===3){let e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;(i=A.nextNode())!==null&&c.length<s;){if(i.nodeType===1){if(i.hasAttributes())for(let e of i.getAttributeNames())if(e.endsWith(Me)){let t=u[o++],n=i.getAttribute(e).split(w),r=/([.?@])?(.*)/.exec(t);c.push({type:1,index:a,name:r[2],strings:n,ctor:r[1]===`.`?tt:r[1]===`?`?nt:r[1]===`@`?rt:et}),i.removeAttribute(e)}else e.startsWith(w)&&(c.push({type:6,index:a}),i.removeAttribute(e));if(Ge.test(i.tagName)){let e=i.textContent.split(w),t=e.length-1;if(t>0){i.textContent=Ae?Ae.emptyScript:``;for(let n=0;n<t;n++)i.append(e[n],Fe()),A.nextNode(),c.push({type:2,index:++a});i.append(e[t],Fe())}}}else if(i.nodeType===8){if(i.data===Ne)c.push({type:2,index:a});else{let e=-1;for(;(e=i.data.indexOf(w,e+1))!==-1;)c.push({type:7,index:a}),e+=w.length-1}}a++}}static createElement(e,t){let n=T.createElement(`template`);return n.innerHTML=e,n}};function j(e,t,n=e,r){if(t===O)return t;let i=r===void 0?n._$Cl:n._$Co?.[r],a=Ie(t)?void 0:t._$litDirective$;return i?.constructor!==a&&(i?._$AO?.(!1),a===void 0?i=void 0:(i=new a(e),i._$AT(e,n,r)),r===void 0?n._$Cl=i:(n._$Co??=[])[r]=i),i!==void 0&&(t=j(e,i._$AS(e,t.values),i,r)),t}var Qe=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:n}=this._$AD,r=(e?.creationScope??T).importNode(t,!0);A.currentNode=r;let i=A.nextNode(),a=0,o=0,s=n[0];for(;s!==void 0;){if(a===s.index){let t;s.type===2?t=new $e(i,i.nextSibling,this,e):s.type===1?t=new s.ctor(i,s.name,s.strings,this,e):s.type===6&&(t=new it(i,this,e)),this._$AV.push(t),s=n[++o]}a!==s?.index&&(i=A.nextNode(),a++)}return A.currentNode=T,r}p(e){let t=0;for(let n of this._$AV)n!==void 0&&(n.strings===void 0?n._$AI(e[t]):(n._$AI(e,n,t),t+=n.strings.length-2)),t++}},$e=class e{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,n,r){this.type=2,this._$AH=k,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=n,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=j(this,e,t),Ie(e)?e===k||e==null||e===``?(this._$AH!==k&&this._$AR(),this._$AH=k):e!==this._$AH&&e!==O&&this._(e):e._$litType$===void 0?e.nodeType===void 0?Re(e)?this.k(e):this._(e):this.T(e):this.$(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==k&&Ie(this._$AH)?this._$AA.nextSibling.data=e:this.T(T.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:n}=e,r=typeof n==`number`?this._$AC(e):(n.el===void 0&&(n.el=Ze.createElement(Ye(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===r)this._$AH.p(t);else{let e=new Qe(r,this),n=e.u(this.options);e.p(t),this.T(n),this._$AH=e}}_$AC(e){let t=Je.get(e.strings);return t===void 0&&Je.set(e.strings,t=new Ze(e)),t}k(t){Le(this._$AH)||(this._$AH=[],this._$AR());let n=this._$AH,r,i=0;for(let a of t)i===n.length?n.push(r=new e(this.O(Fe()),this.O(Fe()),this,this.options)):r=n[i],r._$AI(a),i++;i<n.length&&(this._$AR(r&&r._$AB.nextSibling,i),n.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let t=ke(e).nextSibling;ke(e).remove(),e=t}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},et=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,n,r,i){this.type=1,this._$AH=k,this._$AN=void 0,this.element=e,this.name=t,this._$AM=r,this.options=i,n.length>2||n[0]!==``||n[1]!==``?(this._$AH=Array(n.length-1).fill(/* @__PURE__ */ new String),this.strings=n):this._$AH=k}_$AI(e,t=this,n,r){let i=this.strings,a=!1;if(i===void 0)e=j(this,e,t,0),a=!Ie(e)||e!==this._$AH&&e!==O,a&&(this._$AH=e);else{let r=e,o,s;for(e=i[0],o=0;o<i.length-1;o++)s=j(this,r[n+o],t,o),s===O&&(s=this._$AH[o]),a||=!Ie(s)||s!==this._$AH[o],s===k?e=k:e!==k&&(e+=(s??``)+i[o+1]),this._$AH[o]=s}a&&!r&&this.j(e)}j(e){e===k?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??``)}},tt=class extends et{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===k?void 0:e}},nt=class extends et{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==k)}},rt=class extends et{constructor(e,t,n,r,i){super(e,t,n,r,i),this.type=5}_$AI(e,t=this){if((e=j(this,e,t,0)??k)===O)return;let n=this._$AH,r=e===k&&n!==k||e.capture!==n.capture||e.once!==n.once||e.passive!==n.passive,i=e!==k&&(n===k||r);r&&this.element.removeEventListener(this.name,this,n),i&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH==`function`?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},it=class{constructor(e,t,n){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=n}get _$AU(){return this._$AM._$AU}_$AI(e){j(this,e)}},at={M:Me,P:w,A:Ne,C:1,L:Xe,R:Qe,D:Re,V:j,I:$e,H:et,N:nt,U:rt,B:tt,F:it},ot=Oe.litHtmlPolyfillSupport;ot?.(Ze,$e),(Oe.litHtmlVersions??=[]).push(`3.3.3`);var st=(e,t,n)=>{let r=n?.renderBefore??t,i=r._$litPart$;if(i===void 0){let e=n?.renderBefore??null;r._$litPart$=i=new $e(t.insertBefore(Fe(),e),e,void 0,n??{})}return i._$AI(e),i},ct=globalThis,M=class extends De{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=st(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return O}};M._$litElement$=!0,M.finalized=!0,ct.litElementHydrateSupport?.({LitElement:M});var lt=ct.litElementPolyfillSupport;lt?.({LitElement:M}),(ct.litElementVersions??=[]).push(`4.2.2`);function ut(e){return typeof e==`object`&&!!e&&typeof e.code==`string`}function dt(e){return ut(e)?{code:e.code,message:typeof e.message==`string`?e.message:``}:{code:`unknown_error`,message:String(e)}}function N(e,t,n){e.dispatchEvent(new CustomEvent(t,{detail:n,bubbles:!0,composed:!0}))}function ft(e){history.pushState(null,``,e),N(window,`location-changed`,{replace:!1})}var pt={"card.name":`UniFi Insights Topology`,"card.description":`Interactive network topology of a UniFi site, from UniFi Insights.`,"state.loading":`Loading network topology…`,"state.no_sources":`No UniFi Insights integration is loaded.`,"state.unconfigured":`Choose a site to show.`,"state.empty":`No devices reported for {site}.`,"state.incompatible":`Card and integration versions don't match. Refresh the browser (clear cache) after updating.`,"state.stale":`Stale`,"state.reconnecting":`Reconnecting…`,"state.online":`Online`,"state.offline":`Offline`,"state.unknown":`Unknown`,"issue.site_unavailable":`Site data temporarily unavailable; will recover automatically.`,"issue.devices_unavailable":`Device data unavailable; showing last known layout.`,"issue.legacy_uplink_missing":`Uplink details unavailable; device links may be missing.`,"issue.parents_unresolved":`{count} nodes couldn't be placed under a parent.`,"issue.clients_truncated":`Showing {included} of {total} clients (limit {max}).`,"issue.entry_unloaded":`Integration is reloading.`,"issue.unknown":`Topology problem: {code}.`,"error.entry_not_found":`The configured site no longer exists or is disabled.`,"error.site_not_selected":`The configured site no longer exists or is disabled.`,"error.entry_not_loaded":`Integration isn't loaded (retrying).`,"error.unknown":`Could not load the topology ({code}).`,"action.integration":`Integration`,"action.edit":`Edit card`,"view.graph":`Graph`,"view.list":`List`,"toolbar.view":`View`,"toolbar.filters":`Show`,"toolbar.zoom":`Zoom`,"toolbar.options":`Options`,"toolbar.site":`Site`,"zoom.in":`Zoom in`,"zoom.out":`Zoom out`,"zoom.fit":`Fit to view`,"zoom.hint":`Use Ctrl + scroll to zoom`,"kind.gateway":`Gateway`,"kind.switch":`Switch`,"kind.access_point":`Access point`,"kind.client":`Client`,"kind.other":`Other`,"medium.wired":`Wired`,"medium.wireless":`Wireless`,"medium.unknown":`Unknown`,"group.clients":`{count} clients`,"group.client_one":`1 client`,"group.unconnected":`Unconnected clients`,"group.root":`Clients`,"group.summary":`{wireless} wireless, {offline} offline`,"graph.label":`{site} topology, {devices} devices, {clients} clients`,"graph.roledescription":`network topology`,"node.label":`{kind} {name}, {state}`,"node.clients":`{count} clients`,"node.client_one":`1 client`,"node.uplink":`uplink port {port}`,"node.uplink_speed":`uplink port {port} at {speed}`,"list.label":`{site} devices and clients`,"list.search":`Search`,"list.no_matches":`No matches`,"detail.close":`Close`,"detail.kind":`Type`,"detail.model":`Model`,"detail.state":`State`,"detail.parent":`Connected to`,"detail.port":`Port`,"detail.speed":`Speed`,"detail.medium":`Link`,"detail.poe":`PoE`,"detail.clients":`Clients`,"detail.clients_value":`{total} ({wired} wired, {wireless} wireless)`,"detail.connection":`Connection`,"detail.vlan":`VLAN`,"detail.network":`Network`,"detail.via_hidden":`Via hidden`,"detail.open_device":`Open device`,"detail.search_members":`Search clients`,"announce.updated":`Topology updated.`,"announce.offline":`{count} devices offline.`,"editor.site":`Site`,"editor.site_unavailable":`{site} (unavailable)`,"editor.title":`Title`,"editor.view":`Default view`,"editor.clients":`Clients`,"editor.kinds":`Show node types`,"editor.density":`Density`,"editor.orientation":`Orientation`,"editor.show_site_selector":`Show site selector`,"editor.show_labels":`Show labels`,"editor.max_clients":`Maximum clients`,"clients.collapsed":`Grouped`,"clients.expanded":`Expanded`,"clients.hidden":`Hidden`,"density.auto":`Automatic`,"density.comfortable":`Comfortable`,"density.compact":`Compact`,"orientation.vertical":`Top to bottom`,"orientation.horizontal":`Left to right`},mt={en:pt};function ht(e){let t=(e??`en`).toLowerCase(),n=mt[t]??mt[t.split(`-`)[0]??`en`]??{};return(e,t)=>{let r=n[e]??pt[e];if(t)for(let[e,n]of Object.entries(t))r=r.replaceAll(`{${e}}`,String(n));return r}}var gt=`group:unconnected`,_t=`group:root`,vt=e=>`group:${e}`,yt={gateway:0,switch:1,access_point:2,other:3,client:4},bt=(e,t)=>e.name.localeCompare(t.name)||e.id.localeCompare(t.id),xt=(e,t)=>yt[e.kind]-yt[t.kind]||bt(e,t);function St(e,t){let n=e.toggledGroups.has(t);return e.clients===`expanded`?!n:n}var Ct=()=>({total:0,wired:0,wireless:0,offline:0});function wt(e,t){e.total++,t.connection===`wired`&&e.wired++,t.connection===`wireless`&&e.wireless++,t.state===`offline`&&e.offline++}function Tt(e,t,n){let r=/* @__PURE__ */ new Set;for(let i of e){let e=/* @__PURE__ */ new Set,a=i.id;for(;a!==void 0&&!r.has(a);){e.add(a);let r=t.get(a);if(r!==void 0&&e.has(r)){t.delete(a),n.delete(a);break}a=r}for(let t of e)r.add(t)}}function Et(e,t){let n=new Map(e.nodes.map(e=>[e.id,e])),r=/* @__PURE__ */ new Map,i=/* @__PURE__ */ new Map;for(let t of e.edges){let e=n.get(t.source),a=n.get(t.target);e&&a&&e.id!==a.id&&a.kind!==`client`&&!r.has(e.id)&&(r.set(e.id,a.id),i.set(e.id,t))}Tt(e.nodes,r,i);let a=e.nodes.filter(e=>e.kind!==`client`).sort(xt),o=e.nodes.filter(e=>e.kind===`client`).sort(bt),s=/* @__PURE__ */ new Map;for(let e of o){let t=r.get(e.id);if(t===void 0)continue;let n=s.get(t);n||s.set(t,n=Ct()),wt(n,e)}let c=/* @__PURE__ */ new Map,l=/* @__PURE__ */ new Map,u=/* @__PURE__ */ new Map,d=/* @__PURE__ */ new Map,f=[],p=e=>t.kinds.has(e.kind),m=e=>{let t=[],i=r.get(e);for(;i!==void 0;){let e=n.get(i);if(p(e))return{id:i,skipped:t};t.push(e.kind),i=r.get(i)}return{id:void 0,skipped:t}},h=(e,t,n,r)=>{if(t===void 0){f.push(e);return}u.set(e,t),d.set(e,{childId:e,parentId:t,edge:n,viaHidden:[...new Set(r)]});let i=l.get(t);i?i.push(e):l.set(t,[e])};for(let e of a){if(!p(e))continue;c.set(e.id,{type:`device`,id:e.id,node:e});let t=m(e.id);h(e.id,t.id,i.get(e.id),t.skipped)}if(t.clients!==`hidden`&&t.kinds.has(`client`)){let e=/* @__PURE__ */ new Map;for(let t of o){let i=r.get(t.id),a,o=[],s;if(i===void 0)s=gt;else{let e=n.get(i);if(p(e))a=i;else{let t=m(i);a=t.id,o=[e.kind,...t.skipped]}s=a===void 0?_t:vt(a)}let c=e.get(s);c||e.set(s,c={parent:a,members:[],skipped:/* @__PURE__ */ new Set}),c.members.push(t);for(let e of o)c.skipped.add(e)}let a=[...e].sort(([e],[t])=>Number(e===gt)-Number(t===gt));for(let[e,n]of a){let r=Ct();for(let e of n.members)wt(r,e);let a=St(t,e);if(c.set(e,{type:`group`,id:e,members:n.members,counts:r,expanded:a}),h(e,n.parent,void 0,n.skipped),a)for(let t of n.members)c.set(t.id,{type:`client`,id:t.id,node:t}),h(t.id,e,i.get(t.id),[])}}return{snapshot:e,roots:f,visuals:c,children:l,parentOf:u,links:d,nodes:n,realParent:r,edges:i,clientCounts:s,stats:{devices:a.length,clients:o.length,offlineDevices:a.filter(e=>e.state===`offline`).length}}}function Dt(){let e,t,n;return(r,i)=>n&&r===e&&i===t?n:(e=r,t=i,n=Et(r,i),n)}function Ot(e,t){let n=e.parentOf.get(t);return n===void 0?e.roots:e.children.get(n)??[]}function kt(e,t){for(let n of e.visuals.values())if(n.type===`group`&&n.members.some(e=>e.id===t))return n}var At={gateway:`kind.gateway`,switch:`kind.switch`,access_point:`kind.access_point`,client:`kind.client`,other:`kind.other`},P={online:`state.online`,offline:`state.offline`,unknown:`state.unknown`},jt={graph:`view.graph`,list:`view.list`},Mt={wired:`medium.wired`,wireless:`medium.wireless`,unknown:`medium.unknown`};function Nt(e,t){let n=[...e];return n.length>t?`${n.slice(0,t-1).join(``)}…`:e}var Pt=e=>Number.isInteger(e)?String(e):e.toFixed(1);function Ft(e){return e>=1e3?`${Pt(e/1e3)}G`:`${e}M`}function It(e){return e>=1e3?`${Pt(e/1e3)} gigabit`:`${e} megabit`}function Lt(e){if(!e)return``;let t=[];return e.parent_port!==void 0&&t.push(`p${e.parent_port}`),e.speed_mbps&&t.push(Ft(e.speed_mbps)),e.poe_power_w!==void 0&&t.push(`PoE`),t.join(` · `)}function Rt(e,t){return e.type===`group`?e.id===`group:unconnected`?t(`group.unconnected`):e.id===`group:root`?t(`group.root`):e.counts.total===1?t(`group.client_one`):t(`group.clients`,{count:e.counts.total}):e.node.name}function zt(e){return e.type===`group`?e.counts.offline===e.counts.total?`offline`:`online`:e.node.state}function Bt(e,t,n){if(t.type===`group`)return`${Rt(t,n)}: ${n(`group.summary`,{wireless:t.counts.wireless,offline:t.counts.offline})}`;let r=t.node,i=[n(`node.label`,{kind:n(At[r.kind]),name:r.name,state:n(P[r.state]).toLocaleLowerCase()})],a=e.clientCounts.get(r.id)?.total??0;a>0&&i.push(a===1?n(`node.client_one`):n(`node.clients`,{count:a}));let o=e.edges.get(r.id);return o?.parent_port===void 0?r.connection&&i.push(n(Mt[r.connection]).toLocaleLowerCase()):i.push(o.speed_mbps?n(`node.uplink_speed`,{port:o.parent_port,speed:It(o.speed_mbps)}):n(`node.uplink`,{port:o.parent_port})),i.join(`, `)}var Vt=`current`,Ht=``,Ut={collapsed:`clients.collapsed`,expanded:`clients.expanded`,hidden:`clients.hidden`},Wt={auto:`density.auto`,comfortable:`density.comfortable`,compact:`density.compact`},Gt={vertical:`orientation.vertical`,horizontal:`orientation.horizontal`},Kt={site:`editor.site`,title:`editor.title`,view:`editor.view`,clients:`editor.clients`,kinds:`editor.kinds`,density:`editor.density`,orientation:`editor.orientation`,show_site_selector:`editor.show_site_selector`,show_labels:`editor.show_labels`,max_clients:`editor.max_clients`};function qt(e,t,n){return e.map(e=>({value:e,label:n(t[e])}))}var Jt=(e,t)=>typeof e==`string`&&t.includes(e);function Yt(e,t){let{entry_id:n,site_id:r}=e;if(n===void 0||r===void 0)return Ht;let i=t.findIndex(e=>ie(e.binding,{entry_id:n,site_id:r}));return i>=0?String(i):Vt}function Xt(t,n,r){let i=n.map((e,t)=>({value:String(t),label:e.label}));return Yt(t,n)===`current`&&i.push({value:Vt,label:r(`editor.site_unavailable`,{site:t.site_id??``})}),[{name:`site`,selector:{select:{mode:`dropdown`,options:i}}},{name:`title`,selector:{text:{}}},{name:``,type:`grid`,schema:[{name:`view`,selector:{select:{mode:`dropdown`,options:qt(v,jt,r)}}},{name:`clients`,selector:{select:{mode:`dropdown`,options:qt(y,Ut,r)}}},{name:`density`,selector:{select:{mode:`dropdown`,options:qt([`auto`,...b],Wt,r)}}},{name:`orientation`,selector:{select:{mode:`dropdown`,options:qt(ee,Gt,r)}}}]},{name:`kinds`,selector:{select:{multiple:!0,mode:`list`,options:qt(e,At,r)}}},{name:`show_site_selector`,selector:{boolean:{}}},{name:`show_labels`,selector:{boolean:{}}},{name:`max_clients`,selector:{number:{min:1,max:500,mode:`box`}}}]}function Zt(t,n){return{site:Yt(t,n),title:t.title??``,view:t.view??`graph`,clients:t.clients??`collapsed`,density:t.density??`auto`,orientation:t.orientation??`vertical`,kinds:t.kinds?[...t.kinds]:[...e],show_site_selector:t.show_site_selector??!1,show_labels:t.show_labels??!0,max_clients:t.max_clients??500}}function Qt(t,n,r){let i={...n},a=t.site??Ht;if(a===Ht)delete i.entry_id,delete i.site_id;else if(a!==`current`){let e=r[Number(a)];e&&(i.entry_id=e.binding.entry_id,i.site_id=e.binding.site_id)}t.title?i.title=t.title:delete i.title,Jt(t.view,v)&&(i.view=t.view),Jt(t.clients,y)&&(i.clients=t.clients),Jt(t.orientation,ee)&&(i.orientation=t.orientation),Jt(t.density,b)?i.density=t.density:t.density===`auto`&&delete i.density;let o=(t.kinds??[]).filter(t=>Jt(t,e));o.length===e.length?delete i.kinds:o.length>0&&(i.kinds=e.filter(e=>o.includes(e))),typeof t.show_site_selector==`boolean`&&(i.show_site_selector=t.show_site_selector),typeof t.show_labels==`boolean`&&(i.show_labels=t.show_labels);let s=t.max_clients;return s===500?delete i.max_clients:typeof s==`number`&&Number.isInteger(s)&&s>=1&&s<=500&&(i.max_clients=s),i}async function $t(e=customElements,t=window.loadCardHelpers){e.get(`ha-form`)||await((await t?.())?.createCardElement({type:`entities`,entities:[]})?.constructor)?.getConfigElement?.()}var en=class extends M{static properties={hass:{attribute:!1},config:{state:!0},sources:{state:!0},formReady:{state:!0}};sourcesRequested=!1;constructor(){super(),this.formReady=!1}setConfig(e){this.config={...e}}connectedCallback(){super.connectedCallback(),$t().catch(()=>void 0).then(()=>{this.formReady=!0})}willUpdate(){this.hass&&!this.sourcesRequested&&(this.sourcesRequested=!0,this.hass.callWS({type:t}).then(e=>{this.sources=e},()=>{this.sources=[]}))}render(){let{hass:e,config:t}=this;if(!e||!t)return k;let n=ht(e.locale?.language??e.language);if(!this.formReady)return D`<p>${n(`state.loading`)}</p>`;let r=S(this.sources??[]);return D`<ha-form
            .hass=${e}
            .data=${Zt(t,r)}
            .schema=${Xt(t,r,n)}
            .computeLabel=${e=>{let t=Kt[e.name];return t?n(t):``}}
            @value-changed=${this.onValueChanged}
        ></ha-form>`}onValueChanged=e=>{e.stopPropagation();let t=this.config;if(!t)return;let n=e.detail.value,r=Qt(n,t,S(this.sources??[]));this.config=r,N(this,`config-changed`,{config:r})}},tn=`unifi-insights-site-health-card`,nn=`unifi-insights-site-health-card-editor`,rn=`unifi-insights-internet-activity-card`,an=`unifi-insights-internet-activity-card-editor`,on=`unifi-insights-performance-card`,sn=`unifi-insights-performance-card-editor`,cn=`unifi-insights-protect-status-card`,ln=`unifi-insights-protect-status-card-editor`,un=`unifi-insights-timeline-card`,dn=`unifi-insights-timeline-card-editor`,fn=class extends M{static properties={hass:{attribute:!1},config:{state:!0},snapshot:{state:!0},sources:{state:!0},loading:{state:!0},error:{state:!0}};unsubscribe;bindingKey;syncGeneration=0;failedBindingKey;retryAfterMs=0;retryTimer;constructor(){super(),this.config={type:``},this.snapshot=void 0,this.sources=[],this.loading=!1,this.error=void 0}get includeSiteInSubscribeMessage(){return!0}connectedCallback(){super.connectedCallback(),this.sync()}disconnectedCallback(){super.disconnectedCallback(),this.syncGeneration+=1,this.retryTimer&&=(clearTimeout(this.retryTimer),void 0),this.unsubscribe?.(),this.unsubscribe=void 0}willUpdate(e){let t=e.has(`hass`),n=e.has(`config`),r=e.get(`hass`),i=t&&r?.connection!==this.hass?.connection;(n||i)&&this.sync()}setConfig(e){if(!e||typeof e.type!=`string`)throw Error(`Invalid card config`);this.config={...e}}getCardSize(){return 4}getGridOptions(){return{columns:6,rows:4,min_columns:3,min_rows:3}}getBinding(){if(this.config.entry_id&&this.config.site_id)return{entry_id:this.config.entry_id,site_id:this.config.site_id};if(this.sourceCommand!==`unifi_insights/topology/sources`){if(this.config.entry_id&&this.config.site_id)return{entry_id:this.config.entry_id,site_id:this.config.site_id};let e=this.sources.flatMap(e=>e.sites.map(t=>({entry_id:e.entry_id,site_id:t.id})));return e.length===1?e[0]:void 0}return re({entry_id:this.config.entry_id,site_id:this.config.site_id,title:this.config.title,view:`graph`,show_site_selector:!1,clients:`collapsed`,kinds:[`gateway`,`switch`,`access_point`,`client`,`other`],density:void 0,orientation:`vertical`,show_labels:!0,max_clients:500},this.sources)}async sync(){let e=++this.syncGeneration;if(!this.hass)return;this.loading=!0;try{if(this.sources=await this.hass.callWS({type:this.sourceCommand}),e!==this.syncGeneration||!this.isConnected){this.loading=!1;return}this.error=void 0}catch(t){if(e!==this.syncGeneration||!this.isConnected){this.loading=!1;return}this.error=dt(t),this.loading=!1;return}let t=this.getBinding(),n=t?`${t.entry_id}:${t.site_id}`:void 0;if(n===this.bindingKey&&this.unsubscribe){this.loading=!1;return}if(this.bindingKey=n,n!==this.failedBindingKey&&(this.failedBindingKey=void 0,this.retryAfterMs=0),this.snapshot=void 0,await this.unsubscribe?.(),this.unsubscribe=void 0,!t){this.loading=!1;return}if(n!==void 0&&n===this.failedBindingKey&&Date.now()<this.retryAfterMs){this.loading=!1;return}let r={type:this.subscribeCommand,entry_id:t.entry_id};this.includeSiteInSubscribeMessage&&(r.site_id=t.site_id);try{let t=await this.hass.connection.subscribeMessage(t=>{if(e===this.syncGeneration&&this.isConnected){if((Array.isArray(t.issues)?t.issues:[]).some(e=>e?.code===`entry_unloaded`)){this.unsubscribe?.().catch(()=>void 0),this.unsubscribe=void 0,this.bindingKey=void 0,this.retryTimer&&clearTimeout(this.retryTimer),this.retryTimer=setTimeout(()=>{e===this.syncGeneration&&this.isConnected&&this.sync()},1e3);return}this.failedBindingKey=void 0,this.retryAfterMs=0,this.error=void 0,this.snapshot=t,this.loading=!1}},r,{resubscribe:!1});if(e!==this.syncGeneration||!this.isConnected){await t(),this.loading=!1;return}this.unsubscribe=t}catch(t){if(e!==this.syncGeneration||!this.isConnected){this.loading=!1;return}this.failedBindingKey=n,this.retryAfterMs=Date.now()+5e3,this.error=dt(t),this.loading=!1,this.retryTimer=setTimeout(()=>{e===this.syncGeneration&&this.isConnected&&this.sync()},5e3)}}localize(e){return ht(this.hass?.locale?.language??this.hass?.language??`en`)(e)}openMoreInfo(e){N(this,`hass-more-info`,{entityId:e})}openDevice(e){ft(`/config/devices/device/${e}`)}render(){return D`
            <ha-card>
                <div class="header">${this.config.title??this.localize(`card.name`)}</div>
                ${this.loading?D`<div class="state">${this.localize(`state.loading`)}</div>`:k}
                ${this.error?D`<div class="state error">${this.error.code}</div>`:k}
                ${!this.loading&&!this.error?this.renderContent():k}
            </ha-card>
        `}static styles=C`
        ha-card {
            padding: 12px;
        }

        .header {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .state {
            color: var(--secondary-text-color);
            font-size: 0.9rem;
        }

        .error {
            color: var(--error-color);
        }

        .row {
            display: flex;
            justify-content: space-between;
            gap: 8px;
            margin-top: 6px;
            font-size: 0.9rem;
        }

        .chip {
            border-radius: 999px;
            padding: 2px 8px;
            background: var(--state-icon-color);
            color: var(--card-background-color);
            font-size: 0.75rem;
        }

        .list {
            display: grid;
            gap: 6px;
            margin-top: 8px;
        }

        button.link {
            border: 0;
            background: transparent;
            color: var(--primary-color);
            cursor: pointer;
            padding: 0;
            text-align: left;
            font: inherit;
        }
    `},pn=class extends fn{get cardType(){return`custom:${tn}`}get sourceCommand(){return t}get subscribeCommand(){return`unifi_insights/site_health/subscribe`}renderContent(){let e=this.snapshot;if(!e)return D`<div class="state">${this.localize(`state.unconfigured`)}</div>`;let t=e.health??{},n=e.gateway??{},r=e.clients??{};return D`
            <div class="row"><span>Health</span><span class="chip">${String(t.level??`unknown`)}</span></div>
            <div class="row"><span>Internet</span><span>${String(n.internet??`unknown`)}</span></div>
            <div class="row"><span>Clients</span><span>${String(r.total??0)}</span></div>
        `}},mn=class extends fn{get cardType(){return`custom:${rn}`}get sourceCommand(){return t}get subscribeCommand(){return`unifi_insights/internet_activity/subscribe`}renderContent(){let e=this.snapshot;if(!e)return D`<div class="state">No data</div>`;let t=e.windows??{},n=t[`1d`]??t[`1h`]??{},r=Number(n.download_bytes??0),i=Number(n.upload_bytes??0),a=r+i;return D`
            <div class="row"><span>Download</span><span>${Math.round(r/1e6)} MB</span></div>
            <div class="row"><span>Upload</span><span>${Math.round(i/1e6)} MB</span></div>
            <div class="row"><span>Total</span><span>${Math.round(a/1e6)} MB</span></div>
        `}},hn=class extends fn{get cardType(){return`custom:${on}`}get sourceCommand(){return t}get subscribeCommand(){return`unifi_insights/performance/subscribe`}renderContent(){let e=this.snapshot;if(!e)return D`<div class="state">No devices</div>`;let t=Array.isArray(e.devices)?e.devices:[];return D`
            <div class="row"><span>Devices</span><span>${t.length}</span></div>
            <div class="list">
                ${t.slice(0,5).map(e=>{let t=String(e.name??`Device`),n=e.cpu_pct;return D`<div class="row"><span>${t}</span><span>${n==null?`--`:`${Math.round(Number(n))}%`}</span></div>`})}
            </div>
        `}},gn=class extends fn{get cardType(){return`custom:${cn}`}get sourceCommand(){return`unifi_insights/protect/sources`}get subscribeCommand(){return`unifi_insights/protect/subscribe`}get includeSiteInSubscribeMessage(){return!1}getBinding(){let e=this.config.entry_id;if(e)return{entry_id:e,site_id:this.config.site_id??`*`};let t=this.sources[0];if(t)return{entry_id:t.entry_id,site_id:this.config.site_id??`*`}}renderContent(){let e=this.snapshot;if(!e)return D`<div class="state">No Protect data</div>`;let t=Array.isArray(e.devices)?e.devices:[],n=t.filter(e=>e.connected===!1).length;return D`
            <div class="row"><span>Devices</span><span>${t.length}</span></div>
            <div class="row"><span>Offline</span><span>${n}</span></div>
            <div class="list">
                ${t.slice(0,6).map(e=>{let t=typeof e.camera_entity_id==`string`?e.camera_entity_id:void 0,n=`${String(e.name??`Protect device`)} · ${String(e.kind??`device`)}`;return D`
                        <div class="row">
                            ${t?D`<button class="link" @click=${()=>this.openMoreInfo(t)}>${n}</button>`:D`<span>${n}</span>`}
                            <span>${e.connected===!1?`offline`:`online`}</span>
                        </div>
                    `})}
            </div>
        `}},_n=class extends fn{get cardType(){return`custom:${un}`}get sourceCommand(){return t}get subscribeCommand(){return`unifi_insights/timeline/subscribe`}renderContent(){let e=this.snapshot;if(!e)return D`<div class="state">No events</div>`;let t=Array.isArray(e.items)?e.items:[];return D`
            <div class="row"><span>Events</span><span>${t.length}</span></div>
            <div class="list">
                ${t.slice(0,6).map(e=>{let t=e.source??{};return D`<div class="row"><span>${String(t.name??`Source`)}</span><span>${String(e.kind??`event`)}</span></div>`})}
            </div>
        `}},vn=class extends M{static properties={hass:{attribute:!1},config:{state:!0}};cardType;sourceCommand;options;constructor(e,t){super(),this.cardType=e,this.sourceCommand=t,this.config={type:`custom:${e}`},this.options=[]}setConfig(e){this.config={...e}}connectedCallback(){super.connectedCallback(),$t(),this.loadOptions()}async loadOptions(){if(this.hass)try{let e=await this.hass.callWS({type:this.sourceCommand}),t=this.sourceCommand===`unifi_insights/protect/sources`?e.map(e=>({entryId:e.entry_id,siteId:`*`,label:e.title})):S(e).map(e=>({entryId:e.binding.entry_id,siteId:e.binding.site_id,label:e.label}));this.options=t,this.requestUpdate()}catch{this.options=[],this.requestUpdate()}}applySite(e){let t={...this.config,type:this.config.type||`custom:${this.cardType}`};if(!e)delete t.entry_id,delete t.site_id;else{let n=Number.parseInt(e,10),r=this.options[n];r&&(t.entry_id=r.entryId,t.site_id=r.siteId)}this.config=t,N(this,`config-changed`,{config:t})}applyTitle(e){let t={...this.config};e.trim()?t.title=e.trim():delete t.title,this.config=t,N(this,`config-changed`,{config:t})}render(){let e=this.config.entry_id&&this.config.site_id?String(this.options.findIndex(e=>e.entryId===this.config.entry_id&&e.siteId===this.config.site_id)):``;return D`
            <div class="editor">
                <label>Site</label>
                <select @change=${e=>this.applySite(e.target.value)}>
                    <option value="">Auto</option>
                    ${this.options.map((t,n)=>{let r=String(n);return D`<option value=${r} ?selected=${r===e}>${t.label}</option>`})}
                </select>
                <label>Title</label>
                <input
                    .value=${this.config.title??``}
                    @input=${e=>this.applyTitle(e.target.value)}
                />
            </div>
        `}static styles=C`
        .editor {
            display: grid;
            gap: 8px;
        }

        label {
            font-size: 0.85rem;
            color: var(--secondary-text-color);
        }

        select,
        input {
            min-height: 36px;
            border: 1px solid var(--divider-color);
            border-radius: 8px;
            padding: 4px 8px;
            background: var(--card-background-color);
            color: var(--primary-text-color);
        }
    `},yn=class extends vn{constructor(){super(tn,t)}},bn=class extends vn{constructor(){super(rn,t)}},xn=class extends vn{constructor(){super(on,t)}},Sn=class extends vn{constructor(){super(cn,`unifi_insights/protect/sources`)}},Cn=class extends vn{constructor(){super(un,t)}};function F(e,t){customElements.get(e)||customElements.define(e,t)}var wn=class{last=-1/0;pending;timer;emit;intervalMs;constructor(e,t=5e3){this.emit=e,this.intervalMs=t}announce(e){let t=this.last+this.intervalMs-Date.now();if(t<=0&&this.timer===void 0){this.last=Date.now(),this.emit(e);return}this.pending=e,this.timer??=setTimeout(()=>{this.timer=void 0;let e=this.pending;this.pending=void 0,e!==void 0&&(this.last=Date.now(),this.emit(e))},Math.max(t,0))}dispose(){this.timer!==void 0&&clearTimeout(this.timer),this.timer=void 0,this.pending=void 0}},Tn={[i]:{key:`issue.site_unavailable`},[a]:{key:`issue.devices_unavailable`,action:`integration`},[o]:{key:`issue.legacy_uplink_missing`},[s]:{key:`issue.parents_unresolved`},[c]:{key:`issue.clients_truncated`},[r]:{key:`issue.entry_unloaded`}},En={[l]:{key:`error.entry_not_found`,action:`edit`},[d]:{key:`error.site_not_selected`,action:`edit`},[u]:{key:`error.entry_not_loaded`,action:`integration`}};function Dn(e,t,n){let r=Tn[e.code];if(!r)return{code:e.code,severity:e.severity,key:`issue.unknown`,vars:{code:e.code}};let i={code:e.code,severity:e.severity,key:r.key};return e.code===`parents_unresolved`&&(i.vars={count:t.unresolved.length}),e.code===`clients_truncated`&&t.truncation&&(i.vars={included:t.truncation.clients_included,total:t.truncation.clients_total,max:n}),r.action&&(i.action=r.action),i}function On(e){let t=En[e.code];if(!t)return{code:e.code,severity:`error`,key:`error.unknown`,vars:{code:e.code}};let n={code:e.code,severity:`error`,key:t.key};return t.action&&(n.action=t.action),n}function kn(e){if(e.incompatible)return{phase:`incompatible`,stale:!1,notices:[]};if(e.error)return{phase:`error`,render:e.lastGood,stale:e.lastGood!==void 0,notices:[On(e.error)]};if(e.disconnected){let t=e.snapshot,n=t&&t.nodes.length>0?t:e.lastGood;if(n)return{phase:`reloading`,render:n,stale:!0,notices:[]}}if(e.sources!==void 0&&e.sources.length===0&&e.snapshot===void 0)return{phase:`no_sources`,stale:!1,notices:[]};if(e.binding===void 0)return{phase:e.sources===void 0?`loading`:`unconfigured`,stale:!1,notices:[]};let t=e.snapshot;if(t===void 0)return{phase:`loading`,stale:!1,notices:[]};let n=t.issues.map(n=>Dn(n,t,e.maxClients));if(t.status===`unavailable`){let i=t.issues.some(e=>e.code===r),a=t.nodes.length>0?t:e.lastGood;return{phase:i?`reloading`:`unavailable`,render:a,stale:a!==void 0,notices:n}}return t.nodes.length===0?{phase:`empty`,stale:!1,notices:n}:{phase:t.status===`partial`?`partial`:`ok`,render:t,stale:!1,notices:n}}var An=/* @__PURE__ */ new Set([u,`unknown_command`]),jn=2e3,Mn=6e4;function Nn(e,t=Math.random){let n=Math.min(jn*2**e,Mn);return Math.round(n*(.8+.4*t()))}var Pn=class{generation=0;connection;key;keyId;unsubscribe;retryTimer;attempt=0;lastRevision;isLive=!1;handlers;random;constructor(e,t=Math.random){this.handlers=e,this.random=t}get live(){return this.isLive}update(e,t){let n=t?JSON.stringify([t.entry_id,t.site_id,t.max_clients]):void 0;(e!==this.connection||n!==this.keyId)&&(this.stop(),this.connection=e,this.key=t,this.keyId=n,e&&(e.addEventListener(`ready`,this.onReady),e.addEventListener(`disconnected`,this.onDisconnected)),e&&t&&this.open())}stop(){this.generation++,this.clearRetry(),this.attempt=0,this.release(),this.connection?.removeEventListener(`ready`,this.onReady),this.connection?.removeEventListener(`disconnected`,this.onDisconnected),this.connection=void 0,this.key=void 0,this.keyId=void 0}clearRetry(){this.retryTimer!==void 0&&clearTimeout(this.retryTimer),this.retryTimer=void 0}drop(){this.generation++,this.clearRetry(),this.unsubscribe=void 0,this.isLive=!1,this.lastRevision=void 0}onDisconnected=()=>{this.drop(),this.handlers.onDisconnected()};onReady=()=>{this.drop(),this.attempt=0,this.key&&this.open(),this.handlers.onReconnected()};release(){let e=this.unsubscribe;this.unsubscribe=void 0,this.isLive=!1,this.lastRevision=void 0,e&&e().catch(()=>void 0)}open(){let e=++this.generation,{connection:t,key:r}=this;t&&r&&t.subscribeMessage(t=>{e===this.generation&&this.receive(t)},{type:n,entry_id:r.entry_id,site_id:r.site_id,max_clients:r.max_clients},{resubscribe:!1}).then(t=>{e===this.generation?this.unsubscribe=t:t().catch(()=>void 0)},t=>{if(e!==this.generation)return;let n=dt(t);this.handlers.onError(n),An.has(n.code)&&this.scheduleRetry()})}receive(e){let t;try{t=m(e)}catch(e){e instanceof f?this.handlers.onIncompatible():this.handlers.onError({code:`invalid_payload`,message:String(e)});return}let n=t.issues.some(e=>e.code===r);n||(this.isLive=!0,this.attempt=0),(t.revision===``||t.revision!==this.lastRevision)&&(this.lastRevision=t.revision,this.handlers.onSnapshot(t),n&&(this.generation++,this.release(),this.scheduleRetry()))}scheduleRetry(){let e=this.generation,t=Nn(this.attempt++,this.random);this.retryTimer=setTimeout(()=>{this.retryTimer=void 0,e===this.generation&&this.open()},t)}},Fn=`M4.93,4.93C3.12,6.74 2,9.24 2,12C2,14.76 3.12,17.26 4.93,19.07L6.34,17.66C4.89,16.22 4,14.22 4,12C4,9.79 4.89,7.78 6.34,6.34L4.93,4.93M19.07,4.93L17.66,6.34C19.11,7.78 20,9.79 20,12C20,14.22 19.11,16.22 17.66,17.66L19.07,19.07C20.88,17.26 22,14.76 22,12C22,9.24 20.88,6.74 19.07,4.93M7.76,7.76C6.67,8.85 6,10.35 6,12C6,13.65 6.67,15.15 7.76,16.24L9.17,14.83C8.45,14.11 8,13.11 8,12C8,10.89 8.45,9.89 9.17,9.17L7.76,7.76M16.24,7.76L14.83,9.17C15.55,9.89 16,10.89 16,12C16,13.11 15.55,14.11 14.83,14.83L16.24,16.24C17.33,15.15 18,13.65 18,12C18,10.35 17.33,8.85 16.24,7.76M12,10A2,2 0 0,0 10,12A2,2 0 0,0 12,14A2,2 0 0,0 14,12A2,2 0 0,0 12,10Z`,In=`M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z`,Ln=`M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z`,Rn=`M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z`,zn=`M3 6H21V4H3C1.9 4 1 4.9 1 6V18C1 19.1 1.9 20 3 20H7V18H3V6M13 12H9V13.78C8.39 14.33 8 15.11 8 16C8 16.89 8.39 17.67 9 18.22V20H13V18.22C13.61 17.67 14 16.88 14 16S13.61 14.33 13 13.78V12M11 17.5C10.17 17.5 9.5 16.83 9.5 16S10.17 14.5 11 14.5 12.5 15.17 12.5 16 11.83 17.5 11 17.5M22 8H16C15.5 8 15 8.5 15 9V19C15 19.5 15.5 20 16 20H22C22.5 20 23 19.5 23 19V9C23 8.5 22.5 8 22 8M21 18H17V10H21V18Z`,Bn=`M17 4H20C21.1 4 22 4.9 22 6V8H20V6H17V4M4 8V6H7V4H4C2.9 4 2 4.9 2 6V8H4M20 16V18H17V20H20C21.1 20 22 19.1 22 18V16H20M7 18H4V16H2V18C2 19.1 2.9 20 4 20H7V18M16 10V14H8V10H16M18 8H6V16H18V8Z`,Vn=`M4,1C2.89,1 2,1.89 2,3V7C2,8.11 2.89,9 4,9H1V11H13V9H10C11.11,9 12,8.11 12,7V3C12,1.89 11.11,1 10,1H4M4,3H10V7H4V3M3,13V18L3,20H10V18H5V13H3M14,13C12.89,13 12,13.89 12,15V19C12,20.11 12.89,21 14,21H11V23H23V21H20C21.11,21 22,20.11 22,19V15C22,13.89 21.11,13 20,13H14M14,15H20V19H14V15Z`,Hn=`M15.5,14H14.71L14.43,13.73C15.41,12.59 16,11.11 16,9.5A6.5,6.5 0 0,0 9.5,3A6.5,6.5 0 0,0 3,9.5A6.5,6.5 0 0,0 9.5,16C11.11,16 12.59,15.41 13.73,14.43L14,14.71V15.5L19,20.5L20.5,19L15.5,14M9.5,14C7,14 5,12 5,9.5C5,7 7,5 9.5,5C12,5 14,7 14,9.5C14,12 12,14 9.5,14M7,9H12V10H7V9Z`,Un=`M15.5,14L20.5,19L19,20.5L14,15.5V14.71L13.73,14.43C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.43,13.73L14.71,14H15.5M9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14M12,10H10V12H9V10H7V9H9V7H10V9H12V10Z`,Wn=`M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z`,Gn=`M5 9C3.9 9 3 9.9 3 11V15C3 16.11 3.9 17 5 17H11V19H10C9.45 19 9 19.45 9 20H2V22H9C9 22.55 9.45 23 10 23H14C14.55 23 15 22.55 15 22H22V20H15C15 19.45 14.55 19 14 19H13V17H19C20.11 17 21 16.11 21 15V11C21 9.9 20.11 9 19 9H5M6 12H8V14H6V12M9.5 12H11.5V14H9.5V12M13 12H15V14H13V12Z`,Kn=`M13,18H14A1,1 0 0,1 15,19H22V21H15A1,1 0 0,1 14,22H10A1,1 0 0,1 9,21H2V19H9A1,1 0 0,1 10,18H11V16H8A1,1 0 0,1 7,15V3A1,1 0 0,1 8,2H16A1,1 0 0,1 17,3V15A1,1 0 0,1 16,16H13V18M13,6H14V4H13V6M9,4V6H11V4H9M9,8V10H11V8H9M9,12V14H11V12H9Z`,qn=`M12,21L15.6,16.2C14.6,15.45 13.35,15 12,15C10.65,15 9.4,15.45 8.4,16.2L12,21M12,3C7.95,3 4.21,4.34 1.2,6.6L3,9C5.5,7.12 8.62,6 12,6C15.38,6 18.5,7.12 21,9L22.8,6.6C19.79,4.34 16.05,3 12,3M12,9C9.3,9 6.81,9.89 4.8,11.4L6.6,13.8C8.1,12.67 9.97,12 12,12C14.03,12 15.9,12.67 17.4,13.8L19.2,11.4C17.19,9.89 14.7,9 12,9Z`,Jn=zn;function Yn(e){switch(e.kind){case`gateway`:return Gn;case`switch`:return Kn;case`access_point`:return Fn;case`client`:return e.connection===`wireless`?qn:Vn;default:return zn}}function Xn(e){return D`<svg
        class="icon"
        viewBox="0 0 24 24"
        aria-hidden="true"
        focusable="false"
    >
        <path d=${e}></path>
    </svg>`}var Zn=C`
    :host {
        --uit-online: var(--success-color, #43a047);
        --uit-offline: var(--error-color, #db4437);
        --uit-warning: var(--warning-color, #ffa600);
        --uit-unknown: var(--disabled-text-color, #bdbdbd);
        --uit-focus: var(--primary-color, #03a9f4);
        --uit-line: var(--divider-color, rgba(0, 0, 0, 0.12));
        color: var(--primary-text-color);
        font-family: var(
            --ha-font-family-body,
            var(--paper-font-body1_-_font-family, sans-serif)
        );
    }
    @media (forced-colors: active) {
        :host {
            --uit-online: CanvasText;
            --uit-offline: CanvasText;
            --uit-warning: CanvasText;
            --uit-unknown: GrayText;
            --uit-focus: Highlight;
        }
    }
`,Qn=C`
    button {
        font: inherit;
        color: var(--primary-text-color);
        background: none;
        border: 1px solid var(--uit-line);
        border-radius: 18px;
        min-height: 44px;
        min-width: 44px;
        padding: 0 14px;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    button[aria-pressed="true"] {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: var(--text-primary-color, #fff);
    }
    input,
    select {
        font: inherit;
        color: var(--primary-text-color);
        background: var(--card-background-color);
        border: 1px solid var(--uit-line);
        border-radius: 8px;
        min-height: 44px;
        padding: 0 12px;
        box-sizing: border-box;
    }
    :focus-visible {
        outline: 2px solid var(--uit-focus);
        outline-offset: 2px;
    }
    .icon {
        width: 20px;
        height: 20px;
        fill: currentColor;
        flex: none;
    }
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
        white-space: nowrap;
    }
    @media (prefers-reduced-motion: reduce) {
        * {
            transition: none !important;
            animation: none !important;
        }
    }
`;F(`uit-detail-panel`,class extends M{static properties={model:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},narrow:{type:Boolean,reflect:!0},memberQuery:{state:!0}};constructor(){super(),this.narrow=!1,this.memberQuery=``}willUpdate(e){e.has(`selectedId`)&&(this.memberQuery=``)}render(){let{model:e,selectedId:t,localize:n}=this;if(!e||!t||!n)return k;let r=e.visuals.get(t);if(r?.type===`group`)return this.shell(Rt(r,n),this.groupBody(r,n));let i=e.nodes.get(t);if(!i)return k;let a=i.kind===`client`?this.clientBody(e,i,n):this.deviceBody(e,i,n);return this.shell(i.name,a)}shell(e,t){let n=this.localize;return D`<section class="panel" role="region" aria-label=${e}>
            <header>
                <h3 title=${e}>${e}</h3>
                <button
                    class="close"
                    aria-label=${n(`detail.close`)}
                    title=${n(`detail.close`)}
                    @click=${()=>N(this,`uit-close`)}
                >
                    ${Xn(Rn)}
                </button>
            </header>
            ${t}
        </section>`}rows(e){return D`<dl>
            ${e.filter(e=>e[1]!==void 0&&e[1]!==``).map(([e,t])=>D`<div class="row">
                        <dt>${this.localize(e)}</dt>
                        <dd>${t}</dd>
                    </div>`)}
        </dl>`}uplinkRows(e,t,n,r){let i=e.realParent.get(t),a=e.edges.get(t),o;return a?.parent_port!==void 0&&(o=a.child_port===void 0?String(a.parent_port):`${a.parent_port} → ${a.child_port}`),[[`detail.parent`,i===void 0?void 0:e.nodes.get(i)?.name],[`detail.port`,o],[`detail.speed`,a?.speed_mbps?Ft(a.speed_mbps):void 0],[`detail.medium`,r&&a?n(Mt[a.medium]):void 0],[`detail.poe`,a?.poe_power_w===void 0?void 0:`${a.poe_power_w.toFixed(1)} W`]]}deviceBody(e,t,n){let r=e.clientCounts.get(t.id),i=e.links.get(t.id)?.viaHidden??[];return D`${this.rows([[`detail.kind`,n(At[t.kind])],[`detail.model`,t.model],[`detail.state`,n(P[t.state])],...this.uplinkRows(e,t.id,n,!0),[`detail.clients`,r?n(`detail.clients_value`,{total:r.total,wired:r.wired,wireless:r.wireless}):void 0],[`detail.via_hidden`,i.length>0?i.map(e=>n(At[e])).join(`, `):void 0]])}
        ${t.ha_device_id?D`<button
                  class="action"
                  @click=${()=>ft(`/config/devices/device/${encodeURIComponent(t.ha_device_id)}`)}
              >
                  ${Xn(Wn)}${n(`detail.open_device`)}
              </button>`:k}`}clientBody(e,t,n){return this.rows([[`detail.state`,n(P[t.state])],[`detail.connection`,t.connection?n(Mt[t.connection]):void 0],[`detail.vlan`,t.vlan_id===void 0?void 0:String(t.vlan_id)],[`detail.network`,t.network_name],...this.uplinkRows(e,t.id,n,!1)])}groupBody(e,t){let n=this.memberQuery.trim().toLowerCase(),r=n?e.members.filter(e=>e.name.toLowerCase().includes(n)):e.members,i=e.counts;return D`${this.rows([[`detail.clients`,t(`detail.clients_value`,{total:i.total,wired:i.wired,wireless:i.wireless})]])}
            <input
                type="search"
                .value=${this.memberQuery}
                placeholder=${t(`detail.search_members`)}
                aria-label=${t(`detail.search_members`)}
                @input=${e=>{this.memberQuery=e.target.value}}
            />
            <ul class="members">
                ${r.map(e=>D`<li>
                            <button
                                class="member ${e.state}"
                                @click=${()=>N(this,`uit-select`,{id:e.id})}
                            >
                                ${Xn(Yn(e))}<span
                                    class="name"
                                    title=${e.name}
                                    >${e.name}</span
                                >
                                ${e.state===`online`?k:D`<span class="state-text"
                                          >${t(P[e.state])}</span
                                      >`}
                            </button>
                        </li>`)}
            </ul>`}static styles=[Zn,Qn,C`
            :host {
                position: absolute;
                top: 8px;
                right: 8px;
                bottom: 8px;
                width: min(320px, 45%);
                display: flex;
                flex-direction: column;
                z-index: 2;
                pointer-events: none;
            }
            :host([narrow]) {
                top: auto;
                left: 0;
                right: 0;
                bottom: 0;
                width: auto;
                max-height: 60%;
            }
            .panel {
                pointer-events: auto;
                box-sizing: border-box;
                flex: 1 1 auto;
                min-height: 0;
                overflow: auto;
                padding: 4px 16px 16px;
                background: var(--card-background-color);
                border: 1px solid var(--uit-line);
                border-radius: var(--ha-card-border-radius, 12px);
                box-shadow: var(--ha-card-box-shadow, none);
            }
            header {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            h3 {
                flex: 1;
                min-width: 0;
                margin: 0;
                font-size: 1.1em;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            button.close {
                border: none;
                padding: 0;
            }
            dl {
                margin: 8px 0;
            }
            .row {
                display: flex;
                gap: 12px;
                padding: 4px 0;
            }
            dt {
                color: var(--secondary-text-color);
                min-width: 7em;
            }
            dd {
                margin: 0;
                overflow-wrap: anywhere;
            }
            input {
                width: 100%;
            }
            .members {
                list-style: none;
                margin: 8px 0 0;
                padding: 0;
            }
            .member {
                width: 100%;
                border: none;
                border-radius: 8px;
                justify-content: flex-start;
            }
            .member .name {
                flex: 1;
                min-width: 0;
                text-align: start;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .member.offline .name {
                opacity: 0.55;
            }
            .state-text {
                color: var(--uit-offline);
                font-weight: 600;
            }
            .action {
                margin-top: 8px;
            }
        `]});var $n={svg:`http://www.w3.org/2000/svg`,xhtml:`http://www.w3.org/1999/xhtml`,xlink:`http://www.w3.org/1999/xlink`,xml:`http://www.w3.org/XML/1998/namespace`,xmlns:`http://www.w3.org/2000/xmlns/`};function er(e){var t=e+=``,n=t.indexOf(`:`);return n>=0&&(t=e.slice(0,n))!==`xmlns`&&(e=e.slice(n+1)),$n.hasOwnProperty(t)?{space:$n[t],local:e}:e}function tr(e){return function(){var t=this.ownerDocument,n=this.namespaceURI;return n===`http://www.w3.org/1999/xhtml`&&t.documentElement.namespaceURI===`http://www.w3.org/1999/xhtml`?t.createElement(e):t.createElementNS(n,e)}}function nr(e){return function(){return this.ownerDocument.createElementNS(e.space,e.local)}}function rr(e){var t=er(e);return(t.local?nr:tr)(t)}function ir(){}function ar(e){return e==null?ir:function(){return this.querySelector(e)}}function or(e){typeof e!=`function`&&(e=ar(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=Array(o),c,l,u=0;u<o;++u)(c=a[u])&&(l=e.call(c,c.__data__,u,a))&&(`__data__`in c&&(l.__data__=c.__data__),s[u]=l);return new I(r,this._parents)}function sr(e){return e==null?[]:Array.isArray(e)?e:Array.from(e)}function cr(){return[]}function lr(e){return e==null?cr:function(){return this.querySelectorAll(e)}}function ur(e){return function(){return sr(e.apply(this,arguments))}}function dr(e){e=typeof e==`function`?ur(e):lr(e);for(var t=this._groups,n=t.length,r=[],i=[],a=0;a<n;++a)for(var o=t[a],s=o.length,c,l=0;l<s;++l)(c=o[l])&&(r.push(e.call(c,c.__data__,l,o)),i.push(c));return new I(r,i)}function fr(e){return function(){return this.matches(e)}}function pr(e){return function(t){return t.matches(e)}}var mr=Array.prototype.find;function hr(e){return function(){return mr.call(this.children,e)}}function gr(){return this.firstElementChild}function _r(e){return this.select(e==null?gr:hr(typeof e==`function`?e:pr(e)))}var vr=Array.prototype.filter;function yr(){return Array.from(this.children)}function br(e){return function(){return vr.call(this.children,e)}}function xr(e){return this.selectAll(e==null?yr:br(typeof e==`function`?e:pr(e)))}function Sr(e){typeof e!=`function`&&(e=fr(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=[],c,l=0;l<o;++l)(c=a[l])&&e.call(c,c.__data__,l,a)&&s.push(c);return new I(r,this._parents)}function Cr(e){return Array(e.length)}function wr(){return new I(this._enter||this._groups.map(Cr),this._parents)}function Tr(e,t){this.ownerDocument=e.ownerDocument,this.namespaceURI=e.namespaceURI,this._next=null,this._parent=e,this.__data__=t}Tr.prototype={constructor:Tr,appendChild:function(e){return this._parent.insertBefore(e,this._next)},insertBefore:function(e,t){return this._parent.insertBefore(e,t)},querySelector:function(e){return this._parent.querySelector(e)},querySelectorAll:function(e){return this._parent.querySelectorAll(e)}};function Er(e){return function(){return e}}function Dr(e,t,n,r,i,a){for(var o=0,s,c=t.length,l=a.length;o<l;++o)(s=t[o])?(s.__data__=a[o],r[o]=s):n[o]=new Tr(e,a[o]);for(;o<c;++o)(s=t[o])&&(i[o]=s)}function Or(e,t,n,r,i,a,o){var s,c,l=/* @__PURE__ */ new Map,u=t.length,d=a.length,f=Array(u),p;for(s=0;s<u;++s)(c=t[s])&&(f[s]=p=o.call(c,c.__data__,s,t)+``,l.has(p)?i[s]=c:l.set(p,c));for(s=0;s<d;++s)p=o.call(e,a[s],s,a)+``,(c=l.get(p))?(r[s]=c,c.__data__=a[s],l.delete(p)):n[s]=new Tr(e,a[s]);for(s=0;s<u;++s)(c=t[s])&&l.get(f[s])===c&&(i[s]=c)}function kr(e){return e.__data__}function Ar(e,t){if(!arguments.length)return Array.from(this,kr);var n=t?Or:Dr,r=this._parents,i=this._groups;typeof e!=`function`&&(e=Er(e));for(var a=i.length,o=Array(a),s=Array(a),c=Array(a),l=0;l<a;++l){var u=r[l],d=i[l],f=d.length,p=jr(e.call(u,u&&u.__data__,l,r)),m=p.length,h=s[l]=Array(m),g=o[l]=Array(m);n(u,d,h,g,c[l]=Array(f),p,t);for(var _=0,v=0,y,b;_<m;++_)if(y=h[_]){for(_>=v&&(v=_+1);!(b=g[v])&&++v<m;);y._next=b||null}}return o=new I(o,r),o._enter=s,o._exit=c,o}function jr(e){return typeof e==`object`&&`length`in e?e:Array.from(e)}function Mr(){return new I(this._exit||this._groups.map(Cr),this._parents)}function Nr(e,t,n){var r=this.enter(),i=this,a=this.exit();return typeof e==`function`?(r=e(r),r&&=r.selection()):r=r.append(e+``),t!=null&&(i=t(i),i&&=i.selection()),n==null?a.remove():n(a),r&&i?r.merge(i).order():i}function Pr(e){for(var t=e.selection?e.selection():e,n=this._groups,r=t._groups,i=n.length,a=r.length,o=Math.min(i,a),s=Array(i),c=0;c<o;++c)for(var l=n[c],u=r[c],d=l.length,f=s[c]=Array(d),p,m=0;m<d;++m)(p=l[m]||u[m])&&(f[m]=p);for(;c<i;++c)s[c]=n[c];return new I(s,this._parents)}function Fr(){for(var e=this._groups,t=-1,n=e.length;++t<n;)for(var r=e[t],i=r.length-1,a=r[i],o;--i>=0;)(o=r[i])&&(a&&o.compareDocumentPosition(a)^4&&a.parentNode.insertBefore(o,a),a=o);return this}function Ir(e){e||=Lr;function t(t,n){return t&&n?e(t.__data__,n.__data__):!t-!n}for(var n=this._groups,r=n.length,i=Array(r),a=0;a<r;++a){for(var o=n[a],s=o.length,c=i[a]=Array(s),l,u=0;u<s;++u)(l=o[u])&&(c[u]=l);c.sort(t)}return new I(i,this._parents).order()}function Lr(e,t){return e<t?-1:e>t?1:e>=t?0:NaN}function Rr(){var e=arguments[0];return arguments[0]=this,e.apply(null,arguments),this}function zr(){return Array.from(this)}function Br(){for(var e=this._groups,t=0,n=e.length;t<n;++t)for(var r=e[t],i=0,a=r.length;i<a;++i){var o=r[i];if(o)return o}return null}function Vr(){let e=0;for(let t of this)++e;return e}function Hr(){return!this.node()}function Ur(e){for(var t=this._groups,n=0,r=t.length;n<r;++n)for(var i=t[n],a=0,o=i.length,s;a<o;++a)(s=i[a])&&e.call(s,s.__data__,a,i);return this}function Wr(e){return function(){this.removeAttribute(e)}}function Gr(e){return function(){this.removeAttributeNS(e.space,e.local)}}function Kr(e,t){return function(){this.setAttribute(e,t)}}function qr(e,t){return function(){this.setAttributeNS(e.space,e.local,t)}}function Jr(e,t){return function(){var n=t.apply(this,arguments);n==null?this.removeAttribute(e):this.setAttribute(e,n)}}function Yr(e,t){return function(){var n=t.apply(this,arguments);n==null?this.removeAttributeNS(e.space,e.local):this.setAttributeNS(e.space,e.local,n)}}function Xr(e,t){var n=er(e);if(arguments.length<2){var r=this.node();return n.local?r.getAttributeNS(n.space,n.local):r.getAttribute(n)}return this.each((t==null?n.local?Gr:Wr:typeof t==`function`?n.local?Yr:Jr:n.local?qr:Kr)(n,t))}function Zr(e){return e.ownerDocument&&e.ownerDocument.defaultView||e.document&&e||e.defaultView}function Qr(e){return function(){this.style.removeProperty(e)}}function $r(e,t,n){return function(){this.style.setProperty(e,t,n)}}function ei(e,t,n){return function(){var r=t.apply(this,arguments);r==null?this.style.removeProperty(e):this.style.setProperty(e,r,n)}}function ti(e,t,n){return arguments.length>1?this.each((t==null?Qr:typeof t==`function`?ei:$r)(e,t,n??``)):ni(this.node(),e)}function ni(e,t){return e.style.getPropertyValue(t)||Zr(e).getComputedStyle(e,null).getPropertyValue(t)}function ri(e){return function(){delete this[e]}}function ii(e,t){return function(){this[e]=t}}function ai(e,t){return function(){var n=t.apply(this,arguments);n==null?delete this[e]:this[e]=n}}function oi(e,t){return arguments.length>1?this.each((t==null?ri:typeof t==`function`?ai:ii)(e,t)):this.node()[e]}function si(e){return e.trim().split(/^|\s+/)}function ci(e){return e.classList||new li(e)}function li(e){this._node=e,this._names=si(e.getAttribute(`class`)||``)}li.prototype={add:function(e){this._names.indexOf(e)<0&&(this._names.push(e),this._node.setAttribute(`class`,this._names.join(` `)))},remove:function(e){var t=this._names.indexOf(e);t>=0&&(this._names.splice(t,1),this._node.setAttribute(`class`,this._names.join(` `)))},contains:function(e){return this._names.indexOf(e)>=0}};function ui(e,t){for(var n=ci(e),r=-1,i=t.length;++r<i;)n.add(t[r])}function di(e,t){for(var n=ci(e),r=-1,i=t.length;++r<i;)n.remove(t[r])}function fi(e){return function(){ui(this,e)}}function pi(e){return function(){di(this,e)}}function mi(e,t){return function(){(t.apply(this,arguments)?ui:di)(this,e)}}function hi(e,t){var n=si(e+``);if(arguments.length<2){for(var r=ci(this.node()),i=-1,a=n.length;++i<a;)if(!r.contains(n[i]))return!1;return!0}return this.each((typeof t==`function`?mi:t?fi:pi)(n,t))}function gi(){this.textContent=``}function _i(e){return function(){this.textContent=e}}function vi(e){return function(){var t=e.apply(this,arguments);this.textContent=t??``}}function yi(e){return arguments.length?this.each(e==null?gi:(typeof e==`function`?vi:_i)(e)):this.node().textContent}function bi(){this.innerHTML=``}function xi(e){return function(){this.innerHTML=e}}function Si(e){return function(){var t=e.apply(this,arguments);this.innerHTML=t??``}}function Ci(e){return arguments.length?this.each(e==null?bi:(typeof e==`function`?Si:xi)(e)):this.node().innerHTML}function wi(){this.nextSibling&&this.parentNode.appendChild(this)}function Ti(){return this.each(wi)}function Ei(){this.previousSibling&&this.parentNode.insertBefore(this,this.parentNode.firstChild)}function Di(){return this.each(Ei)}function Oi(e){var t=typeof e==`function`?e:rr(e);return this.select(function(){return this.appendChild(t.apply(this,arguments))})}function ki(){return null}function Ai(e,t){var n=typeof e==`function`?e:rr(e),r=t==null?ki:typeof t==`function`?t:ar(t);return this.select(function(){return this.insertBefore(n.apply(this,arguments),r.apply(this,arguments)||null)})}function ji(){var e=this.parentNode;e&&e.removeChild(this)}function Mi(){return this.each(ji)}function Ni(){var e=this.cloneNode(!1),t=this.parentNode;return t?t.insertBefore(e,this.nextSibling):e}function Pi(){var e=this.cloneNode(!0),t=this.parentNode;return t?t.insertBefore(e,this.nextSibling):e}function Fi(e){return this.select(e?Pi:Ni)}function Ii(e){return arguments.length?this.property(`__data__`,e):this.node().__data__}function Li(e){return function(t){e.call(this,t,this.__data__)}}function Ri(e){return e.trim().split(/^|\s+/).map(function(e){var t=``,n=e.indexOf(`.`);return n>=0&&(t=e.slice(n+1),e=e.slice(0,n)),{type:e,name:t}})}function zi(e){return function(){var t=this.__on;if(t){for(var n=0,r=-1,i=t.length,a;n<i;++n)a=t[n],(!e.type||a.type===e.type)&&a.name===e.name?this.removeEventListener(a.type,a.listener,a.options):t[++r]=a;++r?t.length=r:delete this.__on}}}function Bi(e,t,n){return function(){var r=this.__on,i,a=Li(t);if(r){for(var o=0,s=r.length;o<s;++o)if((i=r[o]).type===e.type&&i.name===e.name){this.removeEventListener(i.type,i.listener,i.options),this.addEventListener(i.type,i.listener=a,i.options=n),i.value=t;return}}this.addEventListener(e.type,a,n),i={type:e.type,name:e.name,value:t,listener:a,options:n},r?r.push(i):this.__on=[i]}}function Vi(e,t,n){var r=Ri(e+``),i,a=r.length,o;if(arguments.length<2){var s=this.node().__on;if(s){for(var c=0,l=s.length,u;c<l;++c)for(i=0,u=s[c];i<a;++i)if((o=r[i]).type===u.type&&o.name===u.name)return u.value}return}for(s=t?Bi:zi,i=0;i<a;++i)this.each(s(r[i],t,n));return this}function Hi(e,t,n){var r=Zr(e),i=r.CustomEvent;typeof i==`function`?i=new i(t,n):(i=r.document.createEvent(`Event`),n?(i.initEvent(t,n.bubbles,n.cancelable),i.detail=n.detail):i.initEvent(t,!1,!1)),e.dispatchEvent(i)}function Ui(e,t){return function(){return Hi(this,e,t)}}function Wi(e,t){return function(){return Hi(this,e,t.apply(this,arguments))}}function Gi(e,t){return this.each((typeof t==`function`?Wi:Ui)(e,t))}function*Ki(){for(var e=this._groups,t=0,n=e.length;t<n;++t)for(var r=e[t],i=0,a=r.length,o;i<a;++i)(o=r[i])&&(yield o)}var qi=[null];function I(e,t){this._groups=e,this._parents=t}function Ji(){return new I([[document.documentElement]],qi)}function Yi(){return this}I.prototype=Ji.prototype={constructor:I,select:or,selectAll:dr,selectChild:_r,selectChildren:xr,filter:Sr,data:Ar,enter:wr,exit:Mr,join:Nr,merge:Pr,selection:Yi,order:Fr,sort:Ir,call:Rr,nodes:zr,node:Br,size:Vr,empty:Hr,each:Ur,attr:Xr,style:ti,property:oi,classed:hi,text:yi,html:Ci,raise:Ti,lower:Di,append:Oi,insert:Ai,remove:Mi,clone:Fi,datum:Ii,on:Vi,dispatch:Gi,[Symbol.iterator]:Ki};function L(e){return typeof e==`string`?new I([[document.querySelector(e)]],[document.documentElement]):new I([[e]],qi)}function Xi(e){let t;for(;t=e.sourceEvent;)e=t;return e}function R(e,t){if(e=Xi(e),t===void 0&&(t=e.currentTarget),t){var n=t.ownerSVGElement||t;if(n.createSVGPoint){var r=n.createSVGPoint();return r.x=e.clientX,r.y=e.clientY,r=r.matrixTransform(t.getScreenCTM().inverse()),[r.x,r.y]}if(t.getBoundingClientRect){var i=t.getBoundingClientRect();return[e.clientX-i.left-t.clientLeft,e.clientY-i.top-t.clientTop]}}return[e.pageX,e.pageY]}var Zi={value:()=>{}};function Qi(){for(var e=0,t=arguments.length,n={},r;e<t;++e){if(!(r=arguments[e]+``)||r in n||/[\s.]/.test(r))throw Error(`illegal type: `+r);n[r]=[]}return new $i(n)}function $i(e){this._=e}function ea(e,t){return e.trim().split(/^|\s+/).map(function(e){var n=``,r=e.indexOf(`.`);if(r>=0&&(n=e.slice(r+1),e=e.slice(0,r)),e&&!t.hasOwnProperty(e))throw Error(`unknown type: `+e);return{type:e,name:n}})}$i.prototype=Qi.prototype={constructor:$i,on:function(e,t){var n=this._,r=ea(e+``,n),i,a=-1,o=r.length;if(arguments.length<2){for(;++a<o;)if((i=(e=r[a]).type)&&(i=ta(n[i],e.name)))return i;return}if(t!=null&&typeof t!=`function`)throw Error(`invalid callback: `+t);for(;++a<o;)if(i=(e=r[a]).type)n[i]=na(n[i],e.name,t);else if(t==null)for(i in n)n[i]=na(n[i],e.name,null);return this},copy:function(){var e={},t=this._;for(var n in t)e[n]=t[n].slice();return new $i(e)},call:function(e,t){if((i=arguments.length-2)>0)for(var n=Array(i),r=0,i,a;r<i;++r)n[r]=arguments[r+2];if(!this._.hasOwnProperty(e))throw Error(`unknown type: `+e);for(a=this._[e],r=0,i=a.length;r<i;++r)a[r].value.apply(t,n)},apply:function(e,t,n){if(!this._.hasOwnProperty(e))throw Error(`unknown type: `+e);for(var r=this._[e],i=0,a=r.length;i<a;++i)r[i].value.apply(t,n)}};function ta(e,t){for(var n=0,r=e.length,i;n<r;++n)if((i=e[n]).name===t)return i.value}function na(e,t,n){for(var r=0,i=e.length;r<i;++r)if(e[r].name===t){e[r]=Zi,e=e.slice(0,r).concat(e.slice(r+1));break}return n!=null&&e.push({name:t,value:n}),e}var z=0,ra=0,ia=0,aa=1e3,oa,sa,ca=0,B=0,la=0,ua=typeof performance==`object`&&performance.now?performance:Date,da=typeof window==`object`&&window.requestAnimationFrame?window.requestAnimationFrame.bind(window):function(e){setTimeout(e,17)};function fa(){return B||=(da(pa),ua.now()+la)}function pa(){B=0}function ma(){this._call=this._time=this._next=null}ma.prototype=ha.prototype={constructor:ma,restart:function(e,t,n){if(typeof e!=`function`)throw TypeError(`callback is not a function`);n=(n==null?fa():+n)+(t==null?0:+t),!this._next&&sa!==this&&(sa?sa._next=this:oa=this,sa=this),this._call=e,this._time=n,ba()},stop:function(){this._call&&(this._call=null,this._time=1/0,ba())}};function ha(e,t,n){var r=new ma;return r.restart(e,t,n),r}function ga(){fa(),++z;for(var e=oa,t;e;)(t=B-e._time)>=0&&e._call.call(void 0,t),e=e._next;--z}function _a(){B=(ca=ua.now())+la,z=ra=0;try{ga()}finally{z=0,ya(),B=0}}function va(){var e=ua.now(),t=e-ca;t>aa&&(la-=t,ca=e)}function ya(){for(var e,t=oa,n,r=1/0;t;)t._call?(r>t._time&&(r=t._time),e=t,t=t._next):(n=t._next,t._next=null,t=e?e._next=n:oa=n);sa=e,ba(r)}function ba(e){z||(ra&&=clearTimeout(ra),e-B>24?(e<1/0&&(ra=setTimeout(_a,e-ua.now()-la)),ia&&=clearInterval(ia)):(ia||=(ca=ua.now(),setInterval(va,aa)),z=1,da(_a)))}function xa(e,t,n){var r=new ma;return t=t==null?0:+t,r.restart(n=>{r.stop(),e(n+t)},t,n),r}var Sa=Qi(`start`,`end`,`cancel`,`interrupt`),Ca=[];function wa(e,t,n,r,i,a){var o=e.__transition;if(!o)e.__transition={};else if(n in o)return;Ea(e,n,{name:t,index:r,group:i,on:Sa,tween:Ca,time:a.time,delay:a.delay,duration:a.duration,ease:a.ease,timer:null,state:0})}function Ta(e,t){var n=H(e,t);if(n.state>0)throw Error(`too late; already scheduled`);return n}function V(e,t){var n=H(e,t);if(n.state>3)throw Error(`too late; already running`);return n}function H(e,t){var n=e.__transition;if(!n||!(n=n[t]))throw Error(`transition not found`);return n}function Ea(e,t,n){var r=e.__transition,i;r[t]=n,n.timer=ha(a,0,n.time);function a(e){n.state=1,n.timer.restart(o,n.delay,n.time),n.delay<=e&&o(e-n.delay)}function o(a){var l,u,d,f;if(n.state!==1)return c();for(l in r)if(f=r[l],f.name===n.name){if(f.state===3)return xa(o);f.state===4?(f.state=6,f.timer.stop(),f.on.call(`interrupt`,e,e.__data__,f.index,f.group),delete r[l]):+l<t&&(f.state=6,f.timer.stop(),f.on.call(`cancel`,e,e.__data__,f.index,f.group),delete r[l])}if(xa(function(){n.state===3&&(n.state=4,n.timer.restart(s,n.delay,n.time),s(a))}),n.state=2,n.on.call(`start`,e,e.__data__,n.index,n.group),n.state===2){for(n.state=3,i=Array(d=n.tween.length),l=0,u=-1;l<d;++l)(f=n.tween[l].value.call(e,e.__data__,n.index,n.group))&&(i[++u]=f);i.length=u+1}}function s(t){for(var r=t<n.duration?n.ease.call(null,t/n.duration):(n.timer.restart(c),n.state=5,1),a=-1,o=i.length;++a<o;)i[a].call(e,r);n.state===5&&(n.on.call(`end`,e,e.__data__,n.index,n.group),c())}function c(){for(var i in n.state=6,n.timer.stop(),delete r[t],r)return;delete e.__transition}}function Da(e,t){var n=e.__transition,r,i,a=!0,o;if(n){for(o in t=t==null?null:t+``,n){if((r=n[o]).name!==t){a=!1;continue}i=r.state>2&&r.state<5,r.state=6,r.timer.stop(),r.on.call(i?`interrupt`:`cancel`,e,e.__data__,r.index,r.group),delete n[o]}a&&delete e.__transition}}function Oa(e){return this.each(function(){Da(this,e)})}function ka(e,t,n){e.prototype=t.prototype=n,n.constructor=e}function Aa(e,t){var n=Object.create(e.prototype);for(var r in t)n[r]=t[r];return n}function ja(){}var Ma=.7,Na=1/Ma,U=`\\s*([+-]?\\d+)\\s*`,Pa=`\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)\\s*`,W=`\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)%\\s*`,Fa=/^#([0-9a-f]{3,8})$/,Ia=RegExp(`^rgb\\(${U},${U},${U}\\)$`),La=RegExp(`^rgb\\(${W},${W},${W}\\)$`),Ra=RegExp(`^rgba\\(${U},${U},${U},${Pa}\\)$`),za=RegExp(`^rgba\\(${W},${W},${W},${Pa}\\)$`),Ba=RegExp(`^hsl\\(${Pa},${W},${W}\\)$`),Va=RegExp(`^hsla\\(${Pa},${W},${W},${Pa}\\)$`),Ha={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074};ka(ja,qa,{copy(e){return Object.assign(new this.constructor,this,e)},displayable(){return this.rgb().displayable()},hex:Ua,formatHex:Ua,formatHex8:Wa,formatHsl:Ga,formatRgb:Ka,toString:Ka});function Ua(){return this.rgb().formatHex()}function Wa(){return this.rgb().formatHex8()}function Ga(){return ro(this).formatHsl()}function Ka(){return this.rgb().formatRgb()}function qa(e){var t,n;return e=(e+``).trim().toLowerCase(),(t=Fa.exec(e))?(n=t[1].length,t=parseInt(t[1],16),n===6?Ja(t):n===3?new G(t>>8&15|t>>4&240,t>>4&15|t&240,(t&15)<<4|t&15,1):n===8?Ya(t>>24&255,t>>16&255,t>>8&255,(t&255)/255):n===4?Ya(t>>12&15|t>>8&240,t>>8&15|t>>4&240,t>>4&15|t&240,((t&15)<<4|t&15)/255):null):(t=Ia.exec(e))?new G(t[1],t[2],t[3],1):(t=La.exec(e))?new G(t[1]*255/100,t[2]*255/100,t[3]*255/100,1):(t=Ra.exec(e))?Ya(t[1],t[2],t[3],t[4]):(t=za.exec(e))?Ya(t[1]*255/100,t[2]*255/100,t[3]*255/100,t[4]):(t=Ba.exec(e))?no(t[1],t[2]/100,t[3]/100,1):(t=Va.exec(e))?no(t[1],t[2]/100,t[3]/100,t[4]):Ha.hasOwnProperty(e)?Ja(Ha[e]):e===`transparent`?new G(NaN,NaN,NaN,0):null}function Ja(e){return new G(e>>16&255,e>>8&255,e&255,1)}function Ya(e,t,n,r){return r<=0&&(e=t=n=NaN),new G(e,t,n,r)}function Xa(e){return e instanceof ja||(e=qa(e)),e?(e=e.rgb(),new G(e.r,e.g,e.b,e.opacity)):new G}function Za(e,t,n,r){return arguments.length===1?Xa(e):new G(e,t,n,r??1)}function G(e,t,n,r){this.r=+e,this.g=+t,this.b=+n,this.opacity=+r}ka(G,Za,Aa(ja,{brighter(e){return e=e==null?Na:Na**+e,new G(this.r*e,this.g*e,this.b*e,this.opacity)},darker(e){return e=e==null?Ma:Ma**+e,new G(this.r*e,this.g*e,this.b*e,this.opacity)},rgb(){return this},clamp(){return new G(K(this.r),K(this.g),K(this.b),to(this.opacity))},displayable(){return-.5<=this.r&&this.r<255.5&&-.5<=this.g&&this.g<255.5&&-.5<=this.b&&this.b<255.5&&0<=this.opacity&&this.opacity<=1},hex:Qa,formatHex:Qa,formatHex8:$a,formatRgb:eo,toString:eo}));function Qa(){return`#${q(this.r)}${q(this.g)}${q(this.b)}`}function $a(){return`#${q(this.r)}${q(this.g)}${q(this.b)}${q((isNaN(this.opacity)?1:this.opacity)*255)}`}function eo(){let e=to(this.opacity);return`${e===1?`rgb(`:`rgba(`}${K(this.r)}, ${K(this.g)}, ${K(this.b)}${e===1?`)`:`, ${e})`}`}function to(e){return isNaN(e)?1:Math.max(0,Math.min(1,e))}function K(e){return Math.max(0,Math.min(255,Math.round(e)||0))}function q(e){return e=K(e),(e<16?`0`:``)+e.toString(16)}function no(e,t,n,r){return r<=0?e=t=n=NaN:n<=0||n>=1?e=t=NaN:t<=0&&(e=NaN),new J(e,t,n,r)}function ro(e){if(e instanceof J)return new J(e.h,e.s,e.l,e.opacity);if(e instanceof ja||(e=qa(e)),!e)return new J;if(e instanceof J)return e;e=e.rgb();var t=e.r/255,n=e.g/255,r=e.b/255,i=Math.min(t,n,r),a=Math.max(t,n,r),o=NaN,s=a-i,c=(a+i)/2;return s?(o=t===a?(n-r)/s+(n<r)*6:n===a?(r-t)/s+2:(t-n)/s+4,s/=c<.5?a+i:2-a-i,o*=60):s=c>0&&c<1?0:o,new J(o,s,c,e.opacity)}function io(e,t,n,r){return arguments.length===1?ro(e):new J(e,t,n,r??1)}function J(e,t,n,r){this.h=+e,this.s=+t,this.l=+n,this.opacity=+r}ka(J,io,Aa(ja,{brighter(e){return e=e==null?Na:Na**+e,new J(this.h,this.s,this.l*e,this.opacity)},darker(e){return e=e==null?Ma:Ma**+e,new J(this.h,this.s,this.l*e,this.opacity)},rgb(){var e=this.h%360+(this.h<0)*360,t=isNaN(e)||isNaN(this.s)?0:this.s,n=this.l,r=n+(n<.5?n:1-n)*t,i=2*n-r;return new G(so(e>=240?e-240:e+120,i,r),so(e,i,r),so(e<120?e+240:e-120,i,r),this.opacity)},clamp(){return new J(ao(this.h),oo(this.s),oo(this.l),to(this.opacity))},displayable(){return(0<=this.s&&this.s<=1||isNaN(this.s))&&0<=this.l&&this.l<=1&&0<=this.opacity&&this.opacity<=1},formatHsl(){let e=to(this.opacity);return`${e===1?`hsl(`:`hsla(`}${ao(this.h)}, ${oo(this.s)*100}%, ${oo(this.l)*100}%${e===1?`)`:`, ${e})`}`}}));function ao(e){return e=(e||0)%360,e<0?e+360:e}function oo(e){return Math.max(0,Math.min(1,e||0))}function so(e,t,n){return(e<60?t+(n-t)*e/60:e<180?n:e<240?t+(n-t)*(240-e)/60:t)*255}var co=e=>()=>e;function lo(e,t){return function(n){return e+n*t}}function uo(e,t,n){return e**=+n,t=t**+n-e,n=1/n,function(r){return(e+r*t)**+n}}function fo(e){return(e=+e)==1?po:function(t,n){return n-t?uo(t,n,e):co(isNaN(t)?n:t)}}function po(e,t){var n=t-e;return n?lo(e,n):co(isNaN(e)?t:e)}var mo=(function e(t){var n=fo(t);function r(e,t){var r=n((e=Za(e)).r,(t=Za(t)).r),i=n(e.g,t.g),a=n(e.b,t.b),o=po(e.opacity,t.opacity);return function(t){return e.r=r(t),e.g=i(t),e.b=a(t),e.opacity=o(t),e+``}}return r.gamma=e,r})(1);function Y(e,t){return e=+e,t=+t,function(n){return e*(1-n)+t*n}}var ho=/[-+]?(?:\d+\.?\d*|\.?\d+)(?:[eE][-+]?\d+)?/g,go=new RegExp(ho.source,`g`);function _o(e){return function(){return e}}function vo(e){return function(t){return e(t)+``}}function yo(e,t){var n=ho.lastIndex=go.lastIndex=0,r,i,a,o=-1,s=[],c=[];for(e+=``,t+=``;(r=ho.exec(e))&&(i=go.exec(t));)(a=i.index)>n&&(a=t.slice(n,a),s[o]?s[o]+=a:s[++o]=a),(r=r[0])===(i=i[0])?s[o]?s[o]+=i:s[++o]=i:(s[++o]=null,c.push({i:o,x:Y(r,i)})),n=go.lastIndex;return n<t.length&&(a=t.slice(n),s[o]?s[o]+=a:s[++o]=a),s.length<2?c[0]?vo(c[0].x):_o(t):(t=c.length,function(e){for(var n=0,r;n<t;++n)s[(r=c[n]).i]=r.x(e);return s.join(``)})}var bo=180/Math.PI,xo={translateX:0,translateY:0,rotate:0,skewX:0,scaleX:1,scaleY:1};function So(e,t,n,r,i,a){var o,s,c;return(o=Math.sqrt(e*e+t*t))&&(e/=o,t/=o),(c=e*n+t*r)&&(n-=e*c,r-=t*c),(s=Math.sqrt(n*n+r*r))&&(n/=s,r/=s,c/=s),e*r<t*n&&(e=-e,t=-t,c=-c,o=-o),{translateX:i,translateY:a,rotate:Math.atan2(t,e)*bo,skewX:Math.atan(c)*bo,scaleX:o,scaleY:s}}var Co;function wo(e){let t=new(typeof DOMMatrix==`function`?DOMMatrix:WebKitCSSMatrix)(e+``);return t.isIdentity?xo:So(t.a,t.b,t.c,t.d,t.e,t.f)}function To(e){return e==null||(Co||=document.createElementNS(`http://www.w3.org/2000/svg`,`g`),Co.setAttribute(`transform`,e),!(e=Co.transform.baseVal.consolidate()))?xo:(e=e.matrix,So(e.a,e.b,e.c,e.d,e.e,e.f))}function Eo(e,t,n,r){function i(e){return e.length?e.pop()+` `:``}function a(e,r,i,a,o,s){if(e!==i||r!==a){var c=o.push(`translate(`,null,t,null,n);s.push({i:c-4,x:Y(e,i)},{i:c-2,x:Y(r,a)})}else(i||a)&&o.push(`translate(`+i+t+a+n)}function o(e,t,n,a){e===t?t&&n.push(i(n)+`rotate(`+t+r):(e-t>180?t+=360:t-e>180&&(e+=360),a.push({i:n.push(i(n)+`rotate(`,null,r)-2,x:Y(e,t)}))}function s(e,t,n,a){e===t?t&&n.push(i(n)+`skewX(`+t+r):a.push({i:n.push(i(n)+`skewX(`,null,r)-2,x:Y(e,t)})}function c(e,t,n,r,a,o){if(e!==n||t!==r){var s=a.push(i(a)+`scale(`,null,`,`,null,`)`);o.push({i:s-4,x:Y(e,n)},{i:s-2,x:Y(t,r)})}else(n!==1||r!==1)&&a.push(i(a)+`scale(`+n+`,`+r+`)`)}return function(t,n){var r=[],i=[];return t=e(t),n=e(n),a(t.translateX,t.translateY,n.translateX,n.translateY,r,i),o(t.rotate,n.rotate,r,i),s(t.skewX,n.skewX,r,i),c(t.scaleX,t.scaleY,n.scaleX,n.scaleY,r,i),t=n=null,function(e){for(var t=-1,n=i.length,a;++t<n;)r[(a=i[t]).i]=a.x(e);return r.join(``)}}}var Do=Eo(wo,`px, `,`px)`,`deg)`),Oo=Eo(To,`, `,`)`,`)`),ko=1e-12;function Ao(e){return((e=Math.exp(e))+1/e)/2}function jo(e){return((e=Math.exp(e))-1/e)/2}function Mo(e){return((e=Math.exp(2*e))-1)/(e+1)}var No=(function e(t,n,r){function i(e,i){var a=e[0],o=e[1],s=e[2],c=i[0],l=i[1],u=i[2],d=c-a,f=l-o,p=d*d+f*f,m,h;if(p<ko)h=Math.log(u/s)/t,m=function(e){return[a+e*d,o+e*f,s*Math.exp(t*e*h)]};else{var g=Math.sqrt(p),_=(u*u-s*s+r*p)/(2*s*n*g),v=(u*u-s*s-r*p)/(2*u*n*g),y=Math.log(Math.sqrt(_*_+1)-_);h=(Math.log(Math.sqrt(v*v+1)-v)-y)/t,m=function(e){var r=e*h,i=Ao(y),c=s/(n*g)*(i*Mo(t*r+y)-jo(y));return[a+c*d,o+c*f,s*i/Ao(t*r+y)]}}return m.duration=h*1e3*t/Math.SQRT2,m}return i.rho=function(t){var n=Math.max(.001,+t),r=n*n;return e(n,r,r*r)},i})(Math.SQRT2,2,4);function Po(e,t){var n,r;return function(){var i=V(this,e),a=i.tween;if(a!==n){r=n=a;for(var o=0,s=r.length;o<s;++o)if(r[o].name===t){r=r.slice(),r.splice(o,1);break}}i.tween=r}}function Fo(e,t,n){var r,i;if(typeof n!=`function`)throw Error();return function(){var a=V(this,e),o=a.tween;if(o!==r){i=(r=o).slice();for(var s={name:t,value:n},c=0,l=i.length;c<l;++c)if(i[c].name===t){i[c]=s;break}c===l&&i.push(s)}a.tween=i}}function Io(e,t){var n=this._id;if(e+=``,arguments.length<2){for(var r=H(this.node(),n).tween,i=0,a=r.length,o;i<a;++i)if((o=r[i]).name===e)return o.value;return null}return this.each((t==null?Po:Fo)(n,e,t))}function Lo(e,t,n){var r=e._id;return e.each(function(){var e=V(this,r);(e.value||={})[t]=n.apply(this,arguments)}),function(e){return H(e,r).value[t]}}function Ro(e,t){var n;return(typeof t==`number`?Y:t instanceof qa?mo:(n=qa(t))?(t=n,mo):yo)(e,t)}function zo(e){return function(){this.removeAttribute(e)}}function Bo(e){return function(){this.removeAttributeNS(e.space,e.local)}}function Vo(e,t,n){var r,i=n+``,a;return function(){var o=this.getAttribute(e);return o===i?null:o===r?a:a=t(r=o,n)}}function Ho(e,t,n){var r,i=n+``,a;return function(){var o=this.getAttributeNS(e.space,e.local);return o===i?null:o===r?a:a=t(r=o,n)}}function Uo(e,t,n){var r,i,a;return function(){var o,s=n(this),c;return s==null?void this.removeAttribute(e):(o=this.getAttribute(e),c=s+``,o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s)))}}function Wo(e,t,n){var r,i,a;return function(){var o,s=n(this),c;return s==null?void this.removeAttributeNS(e.space,e.local):(o=this.getAttributeNS(e.space,e.local),c=s+``,o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s)))}}function Go(e,t){var n=er(e),r=n===`transform`?Oo:Ro;return this.attrTween(e,typeof t==`function`?(n.local?Wo:Uo)(n,r,Lo(this,`attr.`+e,t)):t==null?(n.local?Bo:zo)(n):(n.local?Ho:Vo)(n,r,t))}function Ko(e,t){return function(n){this.setAttribute(e,t.call(this,n))}}function qo(e,t){return function(n){this.setAttributeNS(e.space,e.local,t.call(this,n))}}function Jo(e,t){var n,r;function i(){var i=t.apply(this,arguments);return i!==r&&(n=(r=i)&&qo(e,i)),n}return i._value=t,i}function Yo(e,t){var n,r;function i(){var i=t.apply(this,arguments);return i!==r&&(n=(r=i)&&Ko(e,i)),n}return i._value=t,i}function Xo(e,t){var n=`attr.`+e;if(arguments.length<2)return(n=this.tween(n))&&n._value;if(t==null)return this.tween(n,null);if(typeof t!=`function`)throw Error();var r=er(e);return this.tween(n,(r.local?Jo:Yo)(r,t))}function Zo(e,t){return function(){Ta(this,e).delay=+t.apply(this,arguments)}}function Qo(e,t){return t=+t,function(){Ta(this,e).delay=t}}function $o(e){var t=this._id;return arguments.length?this.each((typeof e==`function`?Zo:Qo)(t,e)):H(this.node(),t).delay}function es(e,t){return function(){V(this,e).duration=+t.apply(this,arguments)}}function ts(e,t){return t=+t,function(){V(this,e).duration=t}}function ns(e){var t=this._id;return arguments.length?this.each((typeof e==`function`?es:ts)(t,e)):H(this.node(),t).duration}function rs(e,t){if(typeof t!=`function`)throw Error();return function(){V(this,e).ease=t}}function is(e){var t=this._id;return arguments.length?this.each(rs(t,e)):H(this.node(),t).ease}function as(e,t){return function(){var n=t.apply(this,arguments);if(typeof n!=`function`)throw Error();V(this,e).ease=n}}function os(e){if(typeof e!=`function`)throw Error();return this.each(as(this._id,e))}function ss(e){typeof e!=`function`&&(e=fr(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=[],c,l=0;l<o;++l)(c=a[l])&&e.call(c,c.__data__,l,a)&&s.push(c);return new X(r,this._parents,this._name,this._id)}function cs(e){if(e._id!==this._id)throw Error();for(var t=this._groups,n=e._groups,r=t.length,i=n.length,a=Math.min(r,i),o=Array(r),s=0;s<a;++s)for(var c=t[s],l=n[s],u=c.length,d=o[s]=Array(u),f,p=0;p<u;++p)(f=c[p]||l[p])&&(d[p]=f);for(;s<r;++s)o[s]=t[s];return new X(o,this._parents,this._name,this._id)}function ls(e){return(e+``).trim().split(/^|\s+/).every(function(e){var t=e.indexOf(`.`);return t>=0&&(e=e.slice(0,t)),!e||e===`start`})}function us(e,t,n){var r,i,a=ls(t)?Ta:V;return function(){var o=a(this,e),s=o.on;s!==r&&(i=(r=s).copy()).on(t,n),o.on=i}}function ds(e,t){var n=this._id;return arguments.length<2?H(this.node(),n).on.on(e):this.each(us(n,e,t))}function fs(e){return function(){var t=this.parentNode;for(var n in this.__transition)if(+n!==e)return;t&&t.removeChild(this)}}function ps(){return this.on(`end.remove`,fs(this._id))}function ms(e){var t=this._name,n=this._id;typeof e!=`function`&&(e=ar(e));for(var r=this._groups,i=r.length,a=Array(i),o=0;o<i;++o)for(var s=r[o],c=s.length,l=a[o]=Array(c),u,d,f=0;f<c;++f)(u=s[f])&&(d=e.call(u,u.__data__,f,s))&&(`__data__`in u&&(d.__data__=u.__data__),l[f]=d,wa(l[f],t,n,f,l,H(u,n)));return new X(a,this._parents,t,n)}function hs(e){var t=this._name,n=this._id;typeof e!=`function`&&(e=lr(e));for(var r=this._groups,i=r.length,a=[],o=[],s=0;s<i;++s)for(var c=r[s],l=c.length,u,d=0;d<l;++d)if(u=c[d]){for(var f=e.call(u,u.__data__,d,c),p,m=H(u,n),h=0,g=f.length;h<g;++h)(p=f[h])&&wa(p,t,n,h,f,m);a.push(f),o.push(u)}return new X(a,o,t,n)}var gs=Ji.prototype.constructor;function _s(){return new gs(this._groups,this._parents)}function vs(e,t){var n,r,i;return function(){var a=ni(this,e),o=(this.style.removeProperty(e),ni(this,e));return a===o?null:a===n&&o===r?i:i=t(n=a,r=o)}}function ys(e){return function(){this.style.removeProperty(e)}}function bs(e,t,n){var r,i=n+``,a;return function(){var o=ni(this,e);return o===i?null:o===r?a:a=t(r=o,n)}}function xs(e,t,n){var r,i,a;return function(){var o=ni(this,e),s=n(this),c=s+``;return s??(c=s=(this.style.removeProperty(e),ni(this,e))),o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s))}}function Ss(e,t){var n,r,i,a=`style.`+t,o=`end.`+a,s;return function(){var c=V(this,e),l=c.on,u=c.value[a]==null?s||=ys(t):void 0;(l!==n||i!==u)&&(r=(n=l).copy()).on(o,i=u),c.on=r}}function Cs(e,t,n){var r=(e+=``)==`transform`?Do:Ro;return t==null?this.styleTween(e,vs(e,r)).on(`end.style.`+e,ys(e)):typeof t==`function`?this.styleTween(e,xs(e,r,Lo(this,`style.`+e,t))).each(Ss(this._id,e)):this.styleTween(e,bs(e,r,t),n).on(`end.style.`+e,null)}function ws(e,t,n){return function(r){this.style.setProperty(e,t.call(this,r),n)}}function Ts(e,t,n){var r,i;function a(){var a=t.apply(this,arguments);return a!==i&&(r=(i=a)&&ws(e,a,n)),r}return a._value=t,a}function Es(e,t,n){var r=`style.`+(e+=``);if(arguments.length<2)return(r=this.tween(r))&&r._value;if(t==null)return this.tween(r,null);if(typeof t!=`function`)throw Error();return this.tween(r,Ts(e,t,n??``))}function Ds(e){return function(){this.textContent=e}}function Os(e){return function(){var t=e(this);this.textContent=t??``}}function ks(e){return this.tween(`text`,typeof e==`function`?Os(Lo(this,`text`,e)):Ds(e==null?``:e+``))}function As(e){return function(t){this.textContent=e.call(this,t)}}function js(e){var t,n;function r(){var r=e.apply(this,arguments);return r!==n&&(t=(n=r)&&As(r)),t}return r._value=e,r}function Ms(e){var t=`text`;if(arguments.length<1)return(t=this.tween(t))&&t._value;if(e==null)return this.tween(t,null);if(typeof e!=`function`)throw Error();return this.tween(t,js(e))}function Ns(){for(var e=this._name,t=this._id,n=Is(),r=this._groups,i=r.length,a=0;a<i;++a)for(var o=r[a],s=o.length,c,l=0;l<s;++l)if(c=o[l]){var u=H(c,t);wa(c,e,n,l,o,{time:u.time+u.delay+u.duration,delay:0,duration:u.duration,ease:u.ease})}return new X(r,this._parents,e,n)}function Ps(){var e,t,n=this,r=n._id,i=n.size();return new Promise(function(a,o){var s={value:o},c={value:function(){--i===0&&a()}};n.each(function(){var n=V(this,r),i=n.on;i!==e&&(t=(e=i).copy(),t._.cancel.push(s),t._.interrupt.push(s),t._.end.push(c)),n.on=t}),i===0&&a()})}var Fs=0;function X(e,t,n,r){this._groups=e,this._parents=t,this._name=n,this._id=r}function Is(){return++Fs}var Z=Ji.prototype;X.prototype={constructor:X,select:ms,selectAll:hs,selectChild:Z.selectChild,selectChildren:Z.selectChildren,filter:ss,merge:cs,selection:_s,transition:Ns,call:Z.call,nodes:Z.nodes,node:Z.node,size:Z.size,empty:Z.empty,each:Z.each,on:ds,attr:Go,attrTween:Xo,style:Cs,styleTween:Es,text:ks,textTween:Ms,remove:ps,tween:Io,delay:$o,duration:ns,ease:is,easeVarying:os,end:Ps,[Symbol.iterator]:Z[Symbol.iterator]};function Ls(e){return((e*=2)<=1?e*e*e:(e-=2)*e*e+2)/2}var Rs={time:null,delay:0,duration:250,ease:Ls};function zs(e,t){for(var n;!(n=e.__transition)||!(n=n[t]);)if(!(e=e.parentNode))throw Error(`transition ${t} not found`);return n}function Bs(e){var t,n;e instanceof X?(t=e._id,e=e._name):(t=Is(),(n=Rs).time=fa(),e=e==null?null:e+``);for(var r=this._groups,i=r.length,a=0;a<i;++a)for(var o=r[a],s=o.length,c,l=0;l<s;++l)(c=o[l])&&wa(c,e,t,l,o,n||zs(c,t));return new X(r,this._parents,e,t)}Ji.prototype.interrupt=Oa,Ji.prototype.transition=Bs;var Vs={capture:!0,passive:!1};function Hs(e){e.preventDefault(),e.stopImmediatePropagation()}function Us(e){var t=e.document.documentElement,n=L(e).on(`dragstart.drag`,Hs,Vs);`onselectstart`in t?n.on(`selectstart.drag`,Hs,Vs):(t.__noselect=t.style.MozUserSelect,t.style.MozUserSelect=`none`)}function Ws(e,t){var n=e.document.documentElement,r=L(e).on(`dragstart.drag`,null);t&&(r.on(`click.drag`,Hs,Vs),setTimeout(function(){r.on(`click.drag`,null)},0)),`onselectstart`in n?r.on(`selectstart.drag`,null):(n.style.MozUserSelect=n.__noselect,delete n.__noselect)}var Gs=e=>()=>e;function Ks(e,{sourceEvent:t,target:n,transform:r,dispatch:i}){Object.defineProperties(this,{type:{value:e,enumerable:!0,configurable:!0},sourceEvent:{value:t,enumerable:!0,configurable:!0},target:{value:n,enumerable:!0,configurable:!0},transform:{value:r,enumerable:!0,configurable:!0},_:{value:i}})}function Q(e,t,n){this.k=e,this.x=t,this.y=n}Q.prototype={constructor:Q,scale:function(e){return e===1?this:new Q(this.k*e,this.x,this.y)},translate:function(e,t){return e===0&t===0?this:new Q(this.k,this.x+this.k*e,this.y+this.k*t)},apply:function(e){return[e[0]*this.k+this.x,e[1]*this.k+this.y]},applyX:function(e){return e*this.k+this.x},applyY:function(e){return e*this.k+this.y},invert:function(e){return[(e[0]-this.x)/this.k,(e[1]-this.y)/this.k]},invertX:function(e){return(e-this.x)/this.k},invertY:function(e){return(e-this.y)/this.k},rescaleX:function(e){return e.copy().domain(e.range().map(this.invertX,this).map(e.invert,e))},rescaleY:function(e){return e.copy().domain(e.range().map(this.invertY,this).map(e.invert,e))},toString:function(){return`translate(`+this.x+`,`+this.y+`) scale(`+this.k+`)`}};var qs=new Q(1,0,0);Js.prototype=Q.prototype;function Js(e){for(;!e.__zoom;)if(!(e=e.parentNode))return qs;return e.__zoom}function Ys(e){e.stopImmediatePropagation()}function Xs(e){e.preventDefault(),e.stopImmediatePropagation()}function Zs(e){return(!e.ctrlKey||e.type===`wheel`)&&!e.button}function Qs(){var e=this;return e instanceof SVGElement?(e=e.ownerSVGElement||e,e.hasAttribute(`viewBox`)?(e=e.viewBox.baseVal,[[e.x,e.y],[e.x+e.width,e.y+e.height]]):[[0,0],[e.width.baseVal.value,e.height.baseVal.value]]):[[0,0],[e.clientWidth,e.clientHeight]]}function $s(){return this.__zoom||qs}function ec(e){return-e.deltaY*(e.deltaMode===1?.05:e.deltaMode?1:.002)*(e.ctrlKey?10:1)}function tc(){return navigator.maxTouchPoints||`ontouchstart`in this}function nc(e,t,n){var r=e.invertX(t[0][0])-n[0][0],i=e.invertX(t[1][0])-n[1][0],a=e.invertY(t[0][1])-n[0][1],o=e.invertY(t[1][1])-n[1][1];return e.translate(i>r?(r+i)/2:Math.min(0,r)||Math.max(0,i),o>a?(a+o)/2:Math.min(0,a)||Math.max(0,o))}function rc(){var e=Zs,t=Qs,n=nc,r=ec,i=tc,a=[0,1/0],o=[[-1/0,-1/0],[1/0,1/0]],s=250,c=No,l=Qi(`start`,`zoom`,`end`),u,d,f,p=500,m=150,h=0,g=10;function _(e){e.property(`__zoom`,$s).on(`wheel.zoom`,ne,{passive:!1}).on(`mousedown.zoom`,S).on(`dblclick.zoom`,re).filter(i).on(`touchstart.zoom`,ie).on(`touchmove.zoom`,ae).on(`touchend.zoom touchcancel.zoom`,oe).style(`-webkit-tap-highlight-color`,`rgba(0,0,0,0)`)}_.transform=function(e,t,n,r){var i=e.selection?e.selection():e;i.property(`__zoom`,$s),e===i?i.interrupt().each(function(){x(this,arguments).event(r).start().zoom(null,typeof t==`function`?t.apply(this,arguments):t).end()}):ee(e,t,n,r)},_.scaleBy=function(e,t,n,r){_.scaleTo(e,function(){return this.__zoom.k*(typeof t==`function`?t.apply(this,arguments):t)},n,r)},_.scaleTo=function(e,r,i,a){_.transform(e,function(){var e=t.apply(this,arguments),a=this.__zoom,s=i==null?b(e):typeof i==`function`?i.apply(this,arguments):i,c=a.invert(s),l=typeof r==`function`?r.apply(this,arguments):r;return n(y(v(a,l),s,c),e,o)},i,a)},_.translateBy=function(e,r,i,a){_.transform(e,function(){return n(this.__zoom.translate(typeof r==`function`?r.apply(this,arguments):r,typeof i==`function`?i.apply(this,arguments):i),t.apply(this,arguments),o)},null,a)},_.translateTo=function(e,r,i,a,s){_.transform(e,function(){var e=t.apply(this,arguments),s=this.__zoom,c=a==null?b(e):typeof a==`function`?a.apply(this,arguments):a;return n(qs.translate(c[0],c[1]).scale(s.k).translate(typeof r==`function`?-r.apply(this,arguments):-r,typeof i==`function`?-i.apply(this,arguments):-i),e,o)},a,s)};function v(e,t){return t=Math.max(a[0],Math.min(a[1],t)),t===e.k?e:new Q(t,e.x,e.y)}function y(e,t,n){var r=t[0]-n[0]*e.k,i=t[1]-n[1]*e.k;return r===e.x&&i===e.y?e:new Q(e.k,r,i)}function b(e){return[(+e[0][0]+ +e[1][0])/2,(+e[0][1]+ +e[1][1])/2]}function ee(e,n,r,i){e.on(`start.zoom`,function(){x(this,arguments).event(i).start()}).on(`interrupt.zoom end.zoom`,function(){x(this,arguments).event(i).end()}).tween(`zoom`,function(){var e=this,a=arguments,o=x(e,a).event(i),s=t.apply(e,a),l=r==null?b(s):typeof r==`function`?r.apply(e,a):r,u=Math.max(s[1][0]-s[0][0],s[1][1]-s[0][1]),d=e.__zoom,f=typeof n==`function`?n.apply(e,a):n,p=c(d.invert(l).concat(u/d.k),f.invert(l).concat(u/f.k));return function(e){if(e===1)e=f;else{var t=p(e),n=u/t[2];e=new Q(n,l[0]-t[0]*n,l[1]-t[1]*n)}o.zoom(null,e)}})}function x(e,t,n){return!n&&e.__zooming||new te(e,t)}function te(e,n){this.that=e,this.args=n,this.active=0,this.sourceEvent=null,this.extent=t.apply(e,n),this.taps=0}te.prototype={event:function(e){return e&&(this.sourceEvent=e),this},start:function(){return++this.active===1&&(this.that.__zooming=this,this.emit(`start`)),this},zoom:function(e,t){return this.mouse&&e!==`mouse`&&(this.mouse[1]=t.invert(this.mouse[0])),this.touch0&&e!==`touch`&&(this.touch0[1]=t.invert(this.touch0[0])),this.touch1&&e!==`touch`&&(this.touch1[1]=t.invert(this.touch1[0])),this.that.__zoom=t,this.emit(`zoom`),this},end:function(){return--this.active===0&&(delete this.that.__zooming,this.emit(`end`)),this},emit:function(e){var t=L(this.that).datum();l.call(e,this.that,new Ks(e,{sourceEvent:this.sourceEvent,target:_,type:e,transform:this.that.__zoom,dispatch:l}),t)}};function ne(t,...i){if(!e.apply(this,arguments))return;var s=x(this,i).event(t),c=this.__zoom,l=Math.max(a[0],Math.min(a[1],c.k*2**r.apply(this,arguments))),u=R(t);if(s.wheel)(s.mouse[0][0]!==u[0]||s.mouse[0][1]!==u[1])&&(s.mouse[1]=c.invert(s.mouse[0]=u)),clearTimeout(s.wheel);else if(c.k===l)return;else s.mouse=[u,c.invert(u)],Da(this),s.start();Xs(t),s.wheel=setTimeout(d,m),s.zoom(`mouse`,n(y(v(c,l),s.mouse[0],s.mouse[1]),s.extent,o));function d(){s.wheel=null,s.end()}}function S(t,...r){if(f||!e.apply(this,arguments))return;var i=t.currentTarget,a=x(this,r,!0).event(t),s=L(t.view).on(`mousemove.zoom`,d,!0).on(`mouseup.zoom`,p,!0),c=R(t,i),l=t.clientX,u=t.clientY;Us(t.view),Ys(t),a.mouse=[c,this.__zoom.invert(c)],Da(this),a.start();function d(e){if(Xs(e),!a.moved){var t=e.clientX-l,r=e.clientY-u;a.moved=t*t+r*r>h}a.event(e).zoom(`mouse`,n(y(a.that.__zoom,a.mouse[0]=R(e,i),a.mouse[1]),a.extent,o))}function p(e){s.on(`mousemove.zoom mouseup.zoom`,null),Ws(e.view,a.moved),Xs(e),a.event(e).end()}}function re(r,...i){if(e.apply(this,arguments)){var a=this.__zoom,c=R(r.changedTouches?r.changedTouches[0]:r,this),l=a.invert(c),u=a.k*(r.shiftKey?.5:2),d=n(y(v(a,u),c,l),t.apply(this,i),o);Xs(r),s>0?L(this).transition().duration(s).call(ee,d,c,r):L(this).call(_.transform,d,c,r)}}function ie(t,...n){if(e.apply(this,arguments)){var r=t.touches,i=r.length,a=x(this,n,t.changedTouches.length===i).event(t),o,s,c,l;for(Ys(t),s=0;s<i;++s)c=r[s],l=R(c,this),l=[l,this.__zoom.invert(l),c.identifier],a.touch0?!a.touch1&&a.touch0[2]!==l[2]&&(a.touch1=l,a.taps=0):(a.touch0=l,o=!0,a.taps=1+!!u);u&&=clearTimeout(u),o&&(a.taps<2&&(d=l[0],u=setTimeout(function(){u=null},p)),Da(this),a.start())}}function ae(e,...t){if(this.__zooming){var r=x(this,t).event(e),i=e.changedTouches,a=i.length,s,c,l,u;for(Xs(e),s=0;s<a;++s)c=i[s],l=R(c,this),r.touch0&&r.touch0[2]===c.identifier?r.touch0[0]=l:r.touch1&&r.touch1[2]===c.identifier&&(r.touch1[0]=l);if(c=r.that.__zoom,r.touch1){var d=r.touch0[0],f=r.touch0[1],p=r.touch1[0],m=r.touch1[1],h=(h=p[0]-d[0])*h+(h=p[1]-d[1])*h,g=(g=m[0]-f[0])*g+(g=m[1]-f[1])*g;c=v(c,Math.sqrt(h/g)),l=[(d[0]+p[0])/2,(d[1]+p[1])/2],u=[(f[0]+m[0])/2,(f[1]+m[1])/2]}else if(r.touch0)l=r.touch0[0],u=r.touch0[1];else return;r.zoom(`touch`,n(y(c,l,u),r.extent,o))}}function oe(e,...t){if(this.__zooming){var n=x(this,t).event(e),r=e.changedTouches,i=r.length,a,o;for(Ys(e),f&&clearTimeout(f),f=setTimeout(function(){f=null},p),a=0;a<i;++a)o=r[a],n.touch0&&n.touch0[2]===o.identifier?delete n.touch0:n.touch1&&n.touch1[2]===o.identifier&&delete n.touch1;if(n.touch1&&!n.touch0&&(n.touch0=n.touch1,delete n.touch1),n.touch0)n.touch0[1]=this.__zoom.invert(n.touch0[0]);else if(n.end(),n.taps===2&&(o=R(o,this),Math.hypot(d[0]-o[0],d[1]-o[1])<g)){var s=L(this).on(`dblclick.zoom`);s&&s.apply(this,arguments)}}}return _.wheelDelta=function(e){return arguments.length?(r=typeof e==`function`?e:Gs(+e),_):r},_.filter=function(t){return arguments.length?(e=typeof t==`function`?t:Gs(!!t),_):e},_.touchable=function(e){return arguments.length?(i=typeof e==`function`?e:Gs(!!e),_):i},_.extent=function(e){return arguments.length?(t=typeof e==`function`?e:Gs([[+e[0][0],+e[0][1]],[+e[1][0],+e[1][1]]]),_):t},_.scaleExtent=function(e){return arguments.length?(a[0]=+e[0],a[1]=+e[1],_):[a[0],a[1]]},_.translateExtent=function(e){return arguments.length?(o[0][0]=+e[0][0],o[1][0]=+e[1][0],o[0][1]=+e[0][1],o[1][1]=+e[1][1],_):[[o[0][0],o[0][1]],[o[1][0],o[1][1]]]},_.constrain=function(e){return arguments.length?(n=e,_):n},_.duration=function(e){return arguments.length?(s=+e,_):s},_.interpolate=function(e){return arguments.length?(c=e,_):c},_.on=function(){var e=l.on.apply(l,arguments);return e===l?_:e},_.clickDistance=function(e){return arguments.length?(h=(e=+e)*e,_):Math.sqrt(h)},_.tapDistance=function(e){return arguments.length?(g=+e,_):g},_}var ic={ATTRIBUTE:1,CHILD:2,PROPERTY:3,BOOLEAN_ATTRIBUTE:4,EVENT:5,ELEMENT:6},ac=e=>(...t)=>({_$litDirective$:e,values:t}),oc=class{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,n){this._$Ct=e,this._$AM=t,this._$Ci=n}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}},{I:sc}=at,cc=e=>e,lc=()=>document.createComment(``),uc=(e,t,n)=>{let r=e._$AA.parentNode,i=t===void 0?e._$AB:t._$AA;if(n===void 0)n=new sc(r.insertBefore(lc(),i),r.insertBefore(lc(),i),e,e.options);else{let t=n._$AB.nextSibling,a=n._$AM,o=a!==e;if(o){let t;n._$AQ?.(e),n._$AM=e,n._$AP!==void 0&&(t=e._$AU)!==a._$AU&&n._$AP(t)}if(t!==i||o){let e=n._$AA;for(;e!==t;){let t=cc(e).nextSibling;cc(r).insertBefore(e,i),e=t}}}return n},$=(e,t,n=e)=>(e._$AI(t,n),e),dc={},fc=(e,t=dc)=>e._$AH=t,pc=e=>e._$AH,mc=e=>{e._$AR(),e._$AA.remove()},hc=(e,t,n)=>{let r=/* @__PURE__ */ new Map;for(let i=t;i<=n;i++)r.set(e[i],i);return r},gc=ac(class extends oc{constructor(e){if(super(e),e.type!==ic.CHILD)throw Error(`repeat() can only be used in text expressions`)}dt(e,t,n){let r;n===void 0?n=t:t!==void 0&&(r=t);let i=[],a=[],o=0;for(let t of e)i[o]=r?r(t,o):o,a[o]=n(t,o),o++;return{values:a,keys:i}}render(e,t,n){return this.dt(e,t,n).values}update(e,[t,n,r]){let i=pc(e),{values:a,keys:o}=this.dt(t,n,r);if(!Array.isArray(i))return this.ut=o,a;let s=this.ut??=[],c=[],l,u,d=0,f=i.length-1,p=0,m=a.length-1;for(;d<=f&&p<=m;)if(i[d]===null)d++;else if(i[f]===null)f--;else if(s[d]===o[p])c[p]=$(i[d],a[p]),d++,p++;else if(s[f]===o[m])c[m]=$(i[f],a[m]),f--,m--;else if(s[d]===o[m])c[m]=$(i[d],a[m]),uc(e,c[m+1],i[d]),d++,m--;else if(s[f]===o[p])c[p]=$(i[f],a[p]),uc(e,i[d],i[f]),f--,p++;else if(l===void 0&&(l=hc(o,p,m),u=hc(s,d,f)),l.has(s[d])){if(l.has(s[f])){let t=u.get(o[p]),n=t===void 0?null:i[t];if(n===null){let t=uc(e,i[d]);$(t,a[p]),c[p]=t}else c[p]=$(n,a[p]),uc(e,i[d],n),i[t]=null;p++}else mc(i[f]),f--}else mc(i[d]),d++;for(;p<=m;){let t=uc(e,c[m+1]);$(t,a[p]),c[p++]=t}for(;d<=f;){let e=i[d++];e!==null&&mc(e)}return this.ut=o,fc(e,c),O}});function _c(e){var t=0,n=e.children,r=n&&n.length;if(!r)t=1;else for(;--r>=0;)t+=n[r].value;e.value=t}function vc(){return this.eachAfter(_c)}function yc(e,t){let n=-1;for(let r of this)e.call(t,r,++n,this);return this}function bc(e,t){for(var n=this,r=[n],i,a,o=-1;n=r.pop();)if(e.call(t,n,++o,this),i=n.children)for(a=i.length-1;a>=0;--a)r.push(i[a]);return this}function xc(e,t){for(var n=this,r=[n],i=[],a,o,s,c=-1;n=r.pop();)if(i.push(n),a=n.children)for(o=0,s=a.length;o<s;++o)r.push(a[o]);for(;n=i.pop();)e.call(t,n,++c,this);return this}function Sc(e,t){let n=-1;for(let r of this)if(e.call(t,r,++n,this))return r}function Cc(e){return this.eachAfter(function(t){for(var n=+e(t.data)||0,r=t.children,i=r&&r.length;--i>=0;)n+=r[i].value;t.value=n})}function wc(e){return this.eachBefore(function(t){t.children&&t.children.sort(e)})}function Tc(e){for(var t=this,n=Ec(t,e),r=[t];t!==n;)t=t.parent,r.push(t);for(var i=r.length;e!==n;)r.splice(i,0,e),e=e.parent;return r}function Ec(e,t){if(e===t)return e;var n=e.ancestors(),r=t.ancestors(),i=null;for(e=n.pop(),t=r.pop();e===t;)i=e,e=n.pop(),t=r.pop();return i}function Dc(){for(var e=this,t=[e];e=e.parent;)t.push(e);return t}function Oc(){return Array.from(this)}function kc(){var e=[];return this.eachBefore(function(t){t.children||e.push(t)}),e}function Ac(){var e=this,t=[];return e.each(function(n){n!==e&&t.push({source:n.parent,target:n})}),t}function*jc(){var e=this,t,n=[e],r,i,a;do for(t=n.reverse(),n=[];e=t.pop();)if(yield e,r=e.children)for(i=0,a=r.length;i<a;++i)n.push(r[i]);while(n.length)}function Mc(e,t){e instanceof Map?(e=[void 0,e],t===void 0&&(t=Fc)):t===void 0&&(t=Pc);for(var n=new Rc(e),r,i=[n],a,o,s,c;r=i.pop();)if((o=t(r.data))&&(c=(o=Array.from(o)).length))for(r.children=o,s=c-1;s>=0;--s)i.push(a=o[s]=new Rc(o[s])),a.parent=r,a.depth=r.depth+1;return n.eachBefore(Lc)}function Nc(){return Mc(this).eachBefore(Ic)}function Pc(e){return e.children}function Fc(e){return Array.isArray(e)?e[1]:null}function Ic(e){e.data.value!==void 0&&(e.value=e.data.value),e.data=e.data.data}function Lc(e){var t=0;do e.height=t;while((e=e.parent)&&e.height<++t)}function Rc(e){this.data=e,this.depth=this.height=0,this.parent=null}Rc.prototype=Mc.prototype={constructor:Rc,count:vc,each:yc,eachAfter:xc,eachBefore:bc,find:Sc,sum:Cc,sort:wc,path:Tc,ancestors:Dc,descendants:Oc,leaves:kc,links:Ac,copy:Nc,[Symbol.iterator]:jc};function zc(e,t){return e.parent===t.parent?1:2}function Bc(e){var t=e.children;return t?t[0]:e.t}function Vc(e){var t=e.children;return t?t[t.length-1]:e.t}function Hc(e,t,n){var r=n/(t.i-e.i);t.c-=r,t.s+=n,e.c+=r,t.z+=n,t.m+=n}function Uc(e){for(var t=0,n=0,r=e.children,i=r.length,a;--i>=0;)a=r[i],a.z+=t,a.m+=t,t+=a.s+(n+=a.c)}function Wc(e,t,n){return e.a.parent===t.parent?e.a:n}function Gc(e,t){this._=e,this.parent=null,this.children=null,this.A=null,this.a=this,this.z=0,this.m=0,this.c=0,this.s=0,this.t=null,this.i=t}Gc.prototype=Object.create(Rc.prototype);function Kc(e){for(var t=new Gc(e,0),n,r=[t],i,a,o,s;n=r.pop();)if(a=n._.children)for(n.children=Array(s=a.length),o=s-1;o>=0;--o)r.push(i=n.children[o]=new Gc(a[o],o)),i.parent=n;return(t.parent=new Gc(null,0)).children=[t],t}function qc(){var e=zc,t=1,n=1,r=null;function i(i){var s=Kc(i);if(s.eachAfter(a),s.parent.m=-s.z,s.eachBefore(o),r)i.eachBefore(c);else{var l=i,u=i,d=i;i.eachBefore(function(e){e.x<l.x&&(l=e),e.x>u.x&&(u=e),e.depth>d.depth&&(d=e)});var f=l===u?1:e(l,u)/2,p=f-l.x,m=t/(u.x+f+p),h=n/(d.depth||1);i.eachBefore(function(e){e.x=(e.x+p)*m,e.y=e.depth*h})}return i}function a(t){var n=t.children,r=t.parent.children,i=t.i?r[t.i-1]:null;if(n){Uc(t);var a=(n[0].z+n[n.length-1].z)/2;i?(t.z=i.z+e(t._,i._),t.m=t.z-a):t.z=a}else i&&(t.z=i.z+e(t._,i._));t.parent.A=s(t,i,t.parent.A||r[0])}function o(e){e._.x=e.z+e.parent.m,e.m+=e.parent.m}function s(t,n,r){if(n){for(var i=t,a=t,o=n,s=i.parent.children[0],c=i.m,l=a.m,u=o.m,d=s.m,f;o=Vc(o),i=Bc(i),o&&i;)s=Bc(s),a=Vc(a),a.a=t,f=o.z+u-i.z-c+e(o._,i._),f>0&&(Hc(Wc(o,t,r),t,f),c+=f,l+=f),u+=o.m,c+=i.m,d+=s.m,l+=a.m;o&&!Vc(a)&&(a.t=o,a.m+=u-l),i&&!Bc(s)&&(s.t=i,s.m+=c-d,r=t)}return r}function c(e){e.x*=t,e.y=e.depth*n}return i.separation=function(t){return arguments.length?(e=t,i):e},i.size=function(e){return arguments.length?(r=!1,t=+e[0],n=+e[1],i):r?null:[t,n]},i.nodeSize=function(e){return arguments.length?(r=!0,t=+e[0],n=+e[1],i):r?[t,n]:null},i}var Jc={comfortable:{breadth:132,depth:150},compact:{breadth:92,depth:112}},Yc=`\0root`;function Xc(e,t,n){let r=/* @__PURE__ */ new Map;if(e.roots.length===0)return{positions:r,bounds:{minX:0,minY:0,maxX:0,maxY:0}};let{breadth:i,depth:a}=Jc[t],o=Mc(Yc,t=>t===Yc?e.roots:e.children.get(t)),s=qc().nodeSize([i,a]).separation((e,t)=>e.parent===t.parent?1:1.25)(o),c={minX:1/0,minY:1/0,maxX:-1/0,maxY:-1/0};for(let e of s.descendants()){if(e.data===Yc)continue;let t=e.x,i=(e.depth-1)*a,o=n===`vertical`?{x:t,y:i}:{x:i,y:t};r.set(e.data,o),c.minX=Math.min(c.minX,o.x),c.minY=Math.min(c.minY,o.y),c.maxX=Math.max(c.maxX,o.x),c.maxY=Math.max(c.maxY,o.y)}return{positions:r,bounds:c}}function Zc(e,t,n,r=48){let i=Math.max(e.maxX-e.minX,1),a=Math.max(e.maxY-e.minY,1),o=Math.min(1.5,Math.max(.2,Math.min((t-2*r)/i,(n-2*r)/a))),s=(e.minX+e.maxX)/2,c=(e.minY+e.maxY)/2;return{k:o,x:t/2-s*o,y:n/2-c*o}}function Qc(e,t,n,r,i=120){let a=/* @__PURE__ */ new Set;for(let[o,s]of e.positions){let e=s.x*t.k+t.x,c=s.y*t.k+t.y;e>=-i&&e<=n+i&&c>=-i&&c<=r+i&&a.add(o)}return a}function $c(e,t,n,r){let i=r===`vertical`,a={parent:i?`ArrowUp`:`ArrowLeft`,child:i?`ArrowDown`:`ArrowRight`,previous:i?`ArrowLeft`:`ArrowUp`,next:i?`ArrowRight`:`ArrowDown`};if(!Object.values(a).includes(n))return;if(t===void 0||!e.visuals.has(t))return e.roots[0];let o=Ot(e,t),s=o.indexOf(t);switch(n){case a.parent:return e.parentOf.get(t)??t;case a.child:return e.children.get(t)?.[0]??t;case a.previous:return o[s-1]??t;default:return o[s+1]??t}}var el={comfortable:22,compact:16},tl=250,nl=22;function rl(e,t){if(e.type===`wheel`){let n=e;return t&&!n.ctrlKey&&!n.metaKey?`hint`:`zoom`}let n=e;return n.ctrlKey||(n.button??0)!==0?`ignore`:`zoom`}F(`uit-graph-view`,class extends M{static properties={model:{attribute:!1},density:{attribute:!1},orientation:{attribute:!1},showLabels:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},siteName:{attribute:!1},ctrlZoom:{attribute:!1},reducedMotion:{attribute:!1},focusId:{state:!0},hintVisible:{state:!0}};layout;entering=/* @__PURE__ */ new Set;exiting=/* @__PURE__ */ new Map;lastVisuals=/* @__PURE__ */ new Map;exitTimer;hintTimer;transform={x:0,y:0,k:1};width=0;height=0;fitted=!1;zoomBehavior;resizeObserver;constructor(){super(),this.density=`comfortable`,this.orientation=`vertical`,this.showLabels=!0,this.siteName=``,this.ctrlZoom=!0,this.reducedMotion=!1,this.hintVisible=!1}connectedCallback(){super.connectedCallback(),this.resizeObserver=new ResizeObserver(e=>{let t=e[0]?.contentRect;t&&this.setViewportSize(t.width,t.height)}),this.resizeObserver.observe(this)}disconnectedCallback(){super.disconnectedCallback(),this.resizeObserver?.disconnect(),this.exitTimer!==void 0&&clearTimeout(this.exitTimer),this.hintTimer!==void 0&&clearTimeout(this.hintTimer),this.exitTimer=void 0,this.hintTimer=void 0}setViewportSize(e,t){this.width=e,this.height=t,this.fitted?this.needsCulling&&this.requestUpdate():this.tryInitialFit()}get needsCulling(){return(this.layout?.positions.size??0)>300}get svgEl(){return this.renderRoot.querySelector(`svg.canvas`)}willUpdate(e){if(this.model&&(e.has(`model`)||e.has(`density`)||e.has(`orientation`))){let e=Xc(this.model,this.density,this.orientation),t=this.layout;this.entering=new Set(t?[...e.positions.keys()].filter(e=>!t.positions.has(e)):[]);for(let t of e.positions.keys())this.exiting.delete(t);if(t&&!this.reducedMotion){for(let[n,r]of t.positions){let t=this.lastVisuals.get(n);!e.positions.has(n)&&t&&this.exiting.set(n,{point:r,visual:t})}this.scheduleExitCleanup()}this.layout=e,this.lastVisuals=new Map(this.model.visuals),(this.focusId===void 0||!this.model.visuals.has(this.focusId))&&(this.focusId=this.model.roots[0])}}firstUpdated(){let e=this.svgEl;e&&(this.zoomBehavior=rc().scaleExtent([.2,4]).extent(()=>[[0,0],[Math.max(this.width,1),Math.max(this.height,1)]]).filter(e=>{let t=rl(e,this.ctrlZoom);return t===`hint`&&this.flashHint(),t===`zoom`}).on(`zoom`,e=>this.onZoom(e.transform)).on(`end`,()=>{this.needsCulling&&this.requestUpdate()}),L(e).call(this.zoomBehavior).on(`dblclick.zoom`,null),this.tryInitialFit())}updated(){this.tryInitialFit()}tryInitialFit(){this.fitted||!this.layout||!this.zoomBehavior||this.width<=0||this.height<=0||(this.fitted=!0,this.fit(!1))}onZoom(e){this.transform={x:e.x,y:e.y,k:e.k},this.renderRoot.querySelector(`g.viewport`)?.setAttribute(`transform`,this.transformAttr())}transformAttr(){let{x:e,y:t,k:n}=this.transform;return`translate(${e},${t}) scale(${n})`}fit(e=!0){let t=this.svgEl;if(!this.layout||!this.zoomBehavior||!t)return;let n=Zc(this.layout.bounds,this.width,this.height),r=qs.translate(n.x,n.y).scale(n.k);e&&!this.reducedMotion?this.zoomBehavior.transform(L(t).transition().duration(300),r):this.zoomBehavior.transform(L(t),r)}zoomBy(e){let t=this.svgEl;this.zoomBehavior&&t&&(this.reducedMotion?this.zoomBehavior.scaleBy(L(t),e):this.zoomBehavior.scaleBy(L(t).transition().duration(200),e))}async focusNode(e){this.focusId=e,await this.updateComplete;let t=this.layout?.positions.get(e),n=this.svgEl;if(t&&n&&this.zoomBehavior&&this.width>0){let e=t.x*this.transform.k+this.transform.x,r=t.y*this.transform.k+this.transform.y;(e<40||e>this.width-40||r<40||r>this.height-40)&&(this.zoomBehavior.translateTo(L(n),t.x,t.y),await this.updateComplete)}for(let t of this.renderRoot.querySelectorAll(`g.nodes g.node`))t.getAttribute(`data-id`)===e&&t.focus()}flashHint(){this.hintVisible=!0,this.hintTimer!==void 0&&clearTimeout(this.hintTimer),this.hintTimer=setTimeout(()=>{this.hintVisible=!1},1500)}scheduleExitCleanup(){this.exiting.size!==0&&this.exitTimer===void 0&&(this.exitTimer=setTimeout(()=>{this.exitTimer=void 0,this.exiting.clear(),this.requestUpdate()},tl))}highlightedPath(){let e=/* @__PURE__ */ new Set,t=this.model;if(!t||this.selectedId===void 0)return e;let n=t.visuals.has(this.selectedId)?this.selectedId:kt(t,this.selectedId)?.id;for(;n!==void 0;)e.add(n),n=t.parentOf.get(n);return e}onKeydown(e){let t=this.model;if(!t)return;let n=$c(t,this.focusId,e.key,this.orientation);if(n!==void 0){e.preventDefault(),this.focusNode(n);return}(e.key===`Enter`||e.key===` `)&&this.focusId!==void 0?(e.preventDefault(),N(this,`uit-activate`,{id:this.focusId})):e.key===`+`||e.key===`=`?(e.preventDefault(),this.zoomBy(1.25)):e.key===`-`?(e.preventDefault(),this.zoomBy(.8)):e.key===`0`&&(e.preventDefault(),this.fit())}render(){let{model:e,layout:t,localize:n}=this;if(!e||!t||!n)return k;let r=el[this.density],i=[...t.positions.keys()],a=[...e.links.values()];if(this.needsCulling&&this.width>0){let e=Qc(t,this.transform,this.width,this.height);this.focusId!==void 0&&e.add(this.focusId),this.selectedId!==void 0&&e.add(this.selectedId),i=i.filter(t=>e.has(t)),a=a.filter(t=>e.has(t.childId)||e.has(t.parentId))}let o=this.highlightedPath();return D`
            <svg
                class="canvas ${this.reducedMotion?`still`:``}"
                role="application"
                aria-roledescription=${n(`graph.roledescription`)}
                aria-label=${n(`graph.label`,{site:this.siteName,devices:e.stats.devices,clients:e.stats.clients})}
                @keydown=${this.onKeydown}
            >
                <g class="viewport" transform=${this.transformAttr()}>
                    <g class="links">
                        ${gc(a,e=>e.childId,e=>this.renderLink(e,t,o))}
                    </g>
                    <g class="nodes">
                        ${gc(i,e=>e,n=>this.renderNode(e,e.visuals.get(n),t.positions.get(n),r,o,!0))}
                    </g>
                    <g class="exits" aria-hidden="true">
                        ${gc([...this.exiting],([e])=>e,([,t])=>this.renderGhost(e,t,r))}
                    </g>
                </g>
            </svg>
            <div class="hint" aria-hidden="true" ?hidden=${!this.hintVisible}>
                ${n(`zoom.hint`)}
            </div>
        `}renderLink(e,t,n){let r=t.positions.get(e.parentId),i=t.positions.get(e.childId);if(!r||!i)return k;let a=this.orientation===`vertical`?(r.y+i.y)/2:(r.x+i.x)/2,o=this.orientation===`vertical`?`M${r.x},${r.y} C${r.x},${a} ${i.x},${a} ${i.x},${i.y}`:`M${r.x},${r.y} C${a},${r.y} ${a},${i.y} ${i.x},${i.y}`,s=this.showLabels?Lt(e.edge):``;return qe`<path class=${[`link`,e.edge?.medium??`unknown`,e.viaHidden.length>0?`via-hidden`:``,n.has(e.childId)?`on-path`:``].join(` `)} d=${o}></path>${s?qe`<text class="link-label" x=${(r.x+i.x)/2} y=${(r.y+i.y)/2}>${s}</text>`:k}`}renderNode(e,t,n,r,i,a){let o=this.localize,s=t.id,c=zt(t),l=Rt(t,o),u=t.type===`group`?`group`:t.node.kind,d=[`node`,t.type,u,c,s===this.selectedId?`selected`:``,i.has(s)?`on-path`:``,this.entering.has(s)?`enter`:``],f=t.type===`group`?Jn:Yn(t.node),p=r+16;return qe`<g
      class=${d.join(` `)}
      data-id=${s}
      role=${a?`button`:k}
      tabindex=${a?s===this.focusId?0:-1:k}
      aria-label=${a?Bt(e,t,o):k}
      aria-expanded=${a&&t.type===`group`?String(t.expanded):k}
      style=${`transform: translate(${n.x}px, ${n.y}px)`}
      @click=${a?()=>N(this,`uit-activate`,{id:s}):k}
      @focus=${a?()=>{this.focusId=s}:k}
    >
      <title>${l}</title>
      <circle class="hit" r=${Math.max(r,22)}></circle>
      <circle class="ring" r=${r+5}></circle>
      <circle class="disc" r=${r}></circle>
      <svg class="glyph" x=${-r*.6} y=${-r*.6} width=${r*1.2} height=${r*1.2} viewBox="0 0 24 24" aria-hidden="true">
        <path d=${f}></path>
      </svg>
      <circle class="status" cx=${r*.72} cy=${-r*.72} r=${Math.max(4,r*.24)}></circle>
      ${t.type===`group`?qe`<text class="badge" x=${r*.95} y=${r+2}>${t.counts.total}</text>`:k}
      ${this.showLabels?qe`<text class="label" y=${p}>${Nt(l,nl)}</text>`:k}
      ${c===`offline`?qe`<text class="state-text" y=${this.showLabels?p+14:p}>${o(P.offline)}</text>`:k}
    </g>`}renderGhost(e,t,n){return this.renderNode(e,t.visual,t.point,n,/* @__PURE__ */ new Set,!1)}static styles=[Zn,C`
            :host {
                display: block;
                position: relative;
                flex: 1;
                min-width: 0;
                min-height: 0;
            }
            svg.canvas {
                display: block;
                width: 100%;
                height: 100%;
                touch-action: none;
                user-select: none;
            }
            .node {
                cursor: pointer;
                outline: none;
                transition: transform 250ms ease;
            }
            .still .node {
                transition: none;
            }
            .node.enter {
                animation: uit-fade-in 250ms ease;
            }
            .exits .node {
                animation: uit-fade-out 250ms ease forwards;
                pointer-events: none;
            }
            .still .node.enter,
            .still .exits .node {
                animation: none;
            }
            @keyframes uit-fade-in {
                from {
                    opacity: 0;
                }
            }
            @keyframes uit-fade-out {
                to {
                    opacity: 0;
                }
            }
            .hit {
                fill: transparent;
            }
            .ring {
                fill: none;
                stroke: none;
            }
            .node:focus-visible .ring {
                stroke: var(--uit-focus);
                stroke-width: 2;
            }
            .disc {
                fill: var(--card-background-color, #fff);
                stroke: var(--uit-line);
                stroke-width: 2;
            }
            .selected .disc,
            .on-path .disc {
                stroke: var(--uit-focus);
            }
            .selected .disc {
                stroke-width: 3;
            }
            .glyph path {
                fill: var(--primary-text-color);
            }
            .offline .disc,
            .offline .glyph {
                opacity: 0.55;
            }
            .status {
                fill: var(--uit-online);
                stroke: var(--card-background-color, #fff);
                stroke-width: 2;
            }
            .offline .status {
                fill: var(--uit-offline);
            }
            .unknown .status {
                fill: var(--uit-unknown);
            }
            text {
                font-size: 12px;
                fill: var(--primary-text-color);
                text-anchor: middle;
                dominant-baseline: hanging;
            }
            .badge {
                font-weight: 600;
                text-anchor: start;
            }
            .state-text {
                fill: var(--uit-offline);
                font-weight: 600;
            }
            .link {
                fill: none;
                stroke: var(--secondary-text-color);
                stroke-opacity: 0.6;
                stroke-width: 1.5;
            }
            .link.wireless {
                stroke-dasharray: 2 4;
            }
            .link.via-hidden {
                stroke-dasharray: 8 4;
            }
            .link.on-path {
                stroke: var(--uit-focus);
                stroke-opacity: 1;
                stroke-width: 2.5;
            }
            .link-label {
                font-size: 10px;
                fill: var(--secondary-text-color);
                paint-order: stroke;
                stroke: var(--card-background-color, #fff);
                stroke-width: 3;
            }
            .hint {
                position: absolute;
                left: 50%;
                bottom: 12px;
                transform: translateX(-50%);
                padding: 6px 12px;
                border-radius: 16px;
                background: var(--primary-text-color);
                color: var(--card-background-color, #fff);
                font-size: 12px;
                pointer-events: none;
            }
            .hint[hidden] {
                display: none;
            }
            @media (prefers-reduced-motion: reduce) {
                .node {
                    transition: none;
                }
                .node.enter,
                .exits .node {
                    animation: none;
                }
            }
        `]});function il(e,t){return e.type===`group`?e.members.some(e=>e.name.toLowerCase().includes(t)):e.node.name.toLowerCase().includes(t)}function al(e,t,n){let r=n.trim().toLowerCase(),i;if(r){i=/* @__PURE__ */ new Set;for(let[t,n]of e.visuals)if(il(n,r))for(let n=t;n!==void 0&&!i.has(n);n=e.parentOf.get(n))i.add(n)}let a=[],o=(n,s,c)=>{let l=i?n.filter(e=>i.has(e)):n;l.forEach((n,i)=>{let u=e.visuals.get(n),d=e.children.get(n)??[],f=u.type===`group`,p=f||d.length>0,m=f?u.expanded:r!==``||!t.has(n);a.push({id:n,visual:u,level:s,posinset:i+1,setsize:l.length,hasChildren:p,expanded:p&&m,parentId:c}),m&&d.length>0&&o(d,s+1,n)})};return o(e.roots,1,void 0),a}F(`uit-list-view`,class extends M{static properties={model:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},siteName:{attribute:!1},query:{state:!0},collapsed:{state:!0},focusId:{state:!0}};rows=[];typeahead=``;typeaheadTimer;constructor(){super(),this.siteName=``,this.query=``,this.collapsed=/* @__PURE__ */ new Set}willUpdate(){this.model&&(this.rows=al(this.model,this.collapsed,this.query),this.rows.some(e=>e.id===this.focusId)||(this.focusId=this.rows[0]?.id))}render(){let{model:e,localize:t}=this;return!e||!t?k:D`
            <div class="search">
                <input
                    type="search"
                    .value=${this.query}
                    placeholder=${t(`list.search`)}
                    aria-label=${t(`list.search`)}
                    @input=${e=>{this.query=e.target.value}}
                />
            </div>
            ${this.rows.length===0?D`<p class="empty">${t(`list.no_matches`)}</p>`:D`<div
                      class="tree"
                      role="tree"
                      aria-label=${t(`list.label`,{site:this.siteName})}
                      @keydown=${this.onKeydown}
                  >
                      ${gc(this.rows,e=>e.id,n=>this.renderRow(e,n,t))}
                  </div>`}
        `}renderRow(e,t,n){let r=t.visual,i=Rt(r,n),a=zt(r);return D`<div
            class="row ${a} ${t.id===this.selectedId?`selected`:``}"
            role="treeitem"
            data-id=${t.id}
            aria-level=${t.level}
            aria-setsize=${t.setsize}
            aria-posinset=${t.posinset}
            aria-selected=${String(t.id===this.selectedId)}
            aria-expanded=${t.hasChildren?String(t.expanded):k}
            aria-label=${Bt(e,r,n)}
            tabindex=${t.id===this.focusId?0:-1}
            style=${`--level: ${t.level}`}
            @click=${()=>N(this,`uit-activate`,{id:t.id})}
            @focus=${()=>{this.focusId=t.id}}
        >
            <span
                class="chevron"
                aria-hidden="true"
                @click=${e=>{e.stopPropagation(),t.hasChildren&&this.toggle(t)}}
                >${t.hasChildren?Xn(t.expanded?In:Ln):k}</span
            >
            ${Xn(r.type===`group`?Jn:Yn(r.node))}
            <span class="name" title=${i}>${i}</span>
            ${r.type===`group`?D`<span class="count">${r.counts.total}</span>`:D`<span class="dot" aria-hidden="true"></span>${a===`online`?k:D`<span class="state-text"
                                >${n(P[a])}</span
                            >`}`}
        </div>`}toggle(e){if(e.visual.type===`group`){N(this,`uit-toggle-group`,{id:e.id});return}let t=new Set(this.collapsed);t.has(e.id)?t.delete(e.id):t.add(e.id),this.collapsed=t}onKeydown(e){let t=this.rows,n=t.findIndex(e=>e.id===this.focusId),r=t[n];if(!r)return;let i;switch(e.key){case`ArrowDown`:i=t[n+1]?.id;break;case`ArrowUp`:i=t[n-1]?.id;break;case`Home`:i=t[0]?.id;break;case`End`:i=t.at(-1)?.id;break;case`ArrowRight`:r.hasChildren&&!r.expanded?this.toggle(r):r.expanded&&(i=t[n+1]?.id);break;case`ArrowLeft`:r.expanded?this.toggle(r):i=r.parentId;break;case`Enter`:case` `:N(this,`uit-activate`,{id:r.id});break;default:e.key.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&(e.preventDefault(),this.typeAhead(e.key,n));return}e.preventDefault(),i!==void 0&&this.focusRow(i)}typeAhead(e,t){this.typeahead+=e.toLowerCase(),this.typeaheadTimer!==void 0&&clearTimeout(this.typeaheadTimer),this.typeaheadTimer=setTimeout(()=>{this.typeahead=``},500);let n=this.rows;for(let e=1;e<=n.length;e++){let r=n[(t+e)%n.length];if(Rt(r.visual,this.localize).toLowerCase().startsWith(this.typeahead)){this.focusRow(r.id);return}}}async focusRow(e){this.focusId=e,await this.updateComplete;let t=this.renderRoot.querySelectorAll(`[role="treeitem"]`);for(let n of t)n.getAttribute(`data-id`)===e&&n.focus()}static styles=[Zn,Qn,C`
            :host {
                display: flex;
                flex-direction: column;
                flex: 1;
                min-height: 0;
                min-width: 0;
            }
            .search {
                padding: 8px 12px;
            }
            .search input {
                width: 100%;
            }
            .tree {
                overflow: auto;
                flex: 1;
                padding: 0 4px 8px;
            }
            .row {
                display: flex;
                align-items: center;
                gap: 8px;
                min-height: 44px;
                padding-inline-start: calc((var(--level) - 1) * 20px + 4px);
                padding-inline-end: 12px;
                border-radius: 8px;
                cursor: pointer;
            }
            .row.selected {
                background: color-mix(
                    in srgb,
                    var(--uit-focus) 16%,
                    transparent
                );
            }
            .row.offline .icon,
            .row.offline .name {
                opacity: 0.55;
            }
            .chevron {
                width: 24px;
                display: inline-flex;
            }
            .name {
                flex: 1;
                min-width: 0;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: var(--uit-online);
                flex: none;
            }
            .offline .dot {
                background: var(--uit-offline);
            }
            .unknown .dot {
                background: var(--uit-unknown);
            }
            .state-text {
                color: var(--uit-offline);
                font-weight: 600;
                font-size: 0.85em;
            }
            .count {
                color: var(--secondary-text-color);
            }
            .empty {
                padding: 16px;
                color: var(--secondary-text-color);
            }
        `]});var ol=600,sl=`/config/integrations/integration/unifi_insights`,cl={integration:`action.integration`,edit:`action.edit`},ll={loading:{key:`state.loading`},no_sources:{key:`state.no_sources`,action:`integration`},unconfigured:{key:`state.unconfigured`,action:`edit`},empty:{key:`state.empty`},incompatible:{key:`state.incompatible`},reloading:{key:`state.reconnecting`}},ul=e=>e?.nodes.filter(e=>e.kind!==`client`&&e.state===`offline`).length??0;F(h,class extends M{static properties={hass:{attribute:!1},layout:{attribute:!1},config:{state:!0},sources:{state:!0},snapshot:{state:!0},lastGood:{state:!0},error:{state:!0},incompatible:{state:!0},disconnected:{state:!0},ui:{state:!0},view:{state:!0},selectedId:{state:!0},siteOverride:{state:!0},narrow:{state:!0},reducedMotion:{state:!0},announcement:{state:!0}};subscription=new Pn({onSnapshot:e=>this.applySnapshot(e),onError:e=>{this.error=e},onIncompatible:()=>{this.incompatible=!0},onDisconnected:()=>{this.disconnected=!0},onReconnected:()=>{this.hass&&this.loadSources(this.hass)}});buildModel=Dt();announcer=new wn(e=>{this.announcement=e});sourcesFor;sourcesPending=!1;sourcesRetry;sourcesAttempt=0;sourcesError;boundKey;cardState={phase:`loading`,stale:!1,notices:[]};model;resizeObserver;motionQuery;localizeLang;localizeFn;constructor(){super(),this.incompatible=!1,this.disconnected=!1,this.ui={kinds:new Set(e),clients:`collapsed`,toggledGroups:/* @__PURE__ */ new Set},this.view=`graph`,this.narrow=!1,this.reducedMotion=!1,this.announcement=``}setConfig(e){let t=ne(te(e));this.config=t,this.view=t.view,this.ui={kinds:new Set(t.kinds),clients:t.clients,toggledGroups:/* @__PURE__ */ new Set},this.siteOverride=void 0}getCardSize(){return 8}getGridOptions(){return{columns:12,rows:8,min_columns:6,min_rows:4}}static getConfigElement(){return document.createElement(g)}static async getStubConfig(e){try{let n=S(await e.callWS({type:t}))[0];if(n)return{type:_,...n.binding}}catch{}return{type:_}}connectedCallback(){super.connectedCallback(),this.resizeObserver=new ResizeObserver(e=>{let t=e[0]?.contentRect.width??0;this.narrow=t>0&&t<ol}),this.resizeObserver.observe(this),this.motionQuery=window.matchMedia(`(prefers-reduced-motion: reduce)`),this.motionQuery.addEventListener(`change`,this.onMotionChange),this.onMotionChange(),this.sync()}disconnectedCallback(){super.disconnectedCallback(),this.subscription.stop(),this.announcer.dispose(),this.resizeObserver?.disconnect(),this.resizeObserver=void 0,this.motionQuery?.removeEventListener(`change`,this.onMotionChange),this.sourcesFor=void 0,this.clearSourcesRetry()}shouldUpdate(e){if(e.size!==1||!e.has(`hass`))return!0;let t=e.get(`hass`),n=this.hass;return!t||!n||t.connection!==n.connection||(t.locale?.language??t.language)!==(n.locale?.language??n.language)}willUpdate(e){(e.has(`hass`)||e.has(`config`)||e.has(`sources`)||e.has(`siteOverride`))&&this.sync();let t=this.config;if(!t)return;this.cardState=kn({sources:this.sources,binding:this.binding,snapshot:this.snapshot,lastGood:this.lastGood,error:this.error,incompatible:this.incompatible,disconnected:this.disconnected,maxClients:t.max_clients}),this.model=this.cardState.render?this.buildModel(this.cardState.render,this.ui):void 0;let n=this.selectedId;n!==void 0&&!(this.model?.visuals.has(n)||this.model?.nodes.has(n))&&(this.selectedId=void 0)}get binding(){return this.config?this.siteOverride??re(this.config,this.sources):void 0}get localize(){let e=this.hass?.locale?.language??this.hass?.language??`en`;return(e!==this.localizeLang||!this.localizeFn)&&(this.localizeLang=e,this.localizeFn=ht(e)),this.localizeFn}get graphView(){return this.renderRoot.querySelector(`uit-graph-view`)}sync(){let{hass:e,config:t}=this;if(!this.isConnected||!e||!t)return;this.sourcesFor!==e.connection&&(this.sourcesFor=e.connection,this.disconnected=!1,this.clearSourcesRetry(),this.sourcesAttempt=0,this.loadSources(e));let n=this.binding,r=n?`${n.entry_id}\u0000${n.site_id}`:void 0;r!==this.boundKey&&(this.boundKey=r,this.snapshot=void 0,this.lastGood=void 0,this.error=void 0,this.sourcesError=void 0,this.incompatible=!1,this.selectedId=void 0),this.subscription.update(e.connection,n?{...n,max_clients:t.max_clients}:void 0)}async loadSources(e){if(this.sourcesPending)return;this.sourcesPending=!0,this.clearSourcesRetry();let n=e.connection;try{let r=await e.callWS({type:t});if(this.sourcesFor!==n)return;this.sources=r,this.sourcesError&&this.error===this.sourcesError&&(this.error=void 0),this.sourcesError=void 0,r.length>0?this.sourcesAttempt=0:this.scheduleSourcesRetry()}catch(e){if(this.sourcesFor!==n)return;let t=this.sourcesError;this.sourcesError=dt(e),(!this.error||this.error===t)&&(this.error=this.sourcesError),this.scheduleSourcesRetry()}finally{this.sourcesPending=!1,this.isConnected&&this.sourcesFor!==void 0&&this.sourcesFor!==n&&this.hass&&this.loadSources(this.hass)}}scheduleSourcesRetry(){this.isConnected&&(this.sourcesRetry=setTimeout(()=>{this.sourcesRetry=void 0,this.hass&&this.loadSources(this.hass)},Nn(this.sourcesAttempt++)))}clearSourcesRetry(){this.sourcesRetry!==void 0&&clearTimeout(this.sourcesRetry),this.sourcesRetry=void 0}applySnapshot(e){let t=this.snapshot;this.snapshot=e,this.error=void 0,this.incompatible=!1,this.disconnected=!1,e.status!==`unavailable`&&e.nodes.length>0&&(this.lastGood=e),this.hass&&this.sources!==void 0&&!this.sources.some(t=>t.entry_id===e.entry_id)&&this.loadSources(this.hass);let n=this.localize,r=n(`announce.updated`),i=e.issues[0],a=ul(e);if(e.status===`unavailable`&&i){let t=Dn(i,e,this.config?.max_clients??0);r=n(t.key,t.vars)}else a>0&&a!==ul(t)&&(r=n(`announce.offline`,{count:a}));this.announcer.announce(r)}onMotionChange=()=>{this.reducedMotion=this.motionQuery?.matches??!1};onActivate=e=>{let t=e.detail.id;this.model?.visuals.get(t)?.type===`group`&&this.toggleGroup(t),this.selectedId=t};onSelect=e=>{let t=e.detail.id,n=this.model;if(n&&!n.visuals.has(t)){let e=kt(n,t);e&&!e.expanded&&this.toggleGroup(e.id)}this.selectedId=t};onToggleGroup=e=>{this.toggleGroup(e.detail.id)};onClose=()=>{this.selectedId=void 0};onKeydown=e=>{e.key===`Escape`&&this.selectedId!==void 0&&(e.stopPropagation(),this.selectedId=void 0)};toggleGroup(e){let t=new Set(this.ui.toggledGroups);t.has(e)?t.delete(e):t.add(e),this.ui={...this.ui,toggledGroups:t}}toggleKind(e){let t=new Set(this.ui.kinds);if(t.has(e)){if(t.size===1)return;t.delete(e)}else t.add(e);this.ui={...this.ui,kinds:t}}runAction(e){ft(e===`integration`?sl:`${location.pathname}?edit=1`)}render(){let e=this.config;if(!e)return k;let t=this.localize,n=this.cardState,r=this.model,i=e.title??n.render?.site_name??this.snapshot?.site_name??t(`card.name`);return D`<ha-card>
            <div
                class="card ${this.narrow?`narrow`:``}"
                @keydown=${this.onKeydown}
                @uit-activate=${this.onActivate}
                @uit-select=${this.onSelect}
                @uit-toggle-group=${this.onToggleGroup}
                @uit-close=${this.onClose}
            >
                <header>
                    <h2 class="title" title=${i}>${i}</h2>
                    ${this.renderSiteSelector(e,t)}
                </header>
                ${r?this.renderToolbar(t):k}
                ${r?this.renderNotices(n.notices,t):k}
                <div class="body">
                    ${r?this.renderContent(r,n,e,t):this.renderMessage(n,t)}
                </div>
                <div class="sr-only" role="status" aria-live="polite">
                    ${this.announcement}
                </div>
            </div>
        </ha-card>`}renderSiteSelector(e,t){let n=S(this.sources??[]);if(!e.show_site_selector||n.length<2)return k;let r=this.binding;return D`<label class="site">
            <span class="sr-only">${t(`toolbar.site`)}</span>
            <select
                @change=${e=>{let t=n[Number(e.target.value)];t&&(this.siteOverride=t.binding)}}
            >
                ${n.map((e,t)=>D`<option
                            value=${t}
                            ?selected=${ie(e.binding,r)}
                        >
                            ${e.label}
                        </option>`)}
            </select>
        </label>`}renderToolbar(t){let n=D`
            <div
                class="group"
                role="group"
                aria-label=${t(`toolbar.view`)}
            >
                ${v.map(e=>D`<button
                            aria-pressed=${String(this.view===e)}
                            @click=${()=>{this.view=e}}
                        >
                            ${t(jt[e])}
                        </button>`)}
            </div>
            <div
                class="group"
                role="group"
                aria-label=${t(`toolbar.filters`)}
            >
                ${e.map(e=>D`<button
                            aria-pressed=${String(this.ui.kinds.has(e))}
                            @click=${()=>this.toggleKind(e)}
                        >
                            ${t(At[e])}
                        </button>`)}
            </div>
            ${this.view===`graph`?D`<div
                      class="group"
                      role="group"
                      aria-label=${t(`toolbar.zoom`)}
                  >
                      ${this.iconButton(Un,t(`zoom.in`),()=>this.graphView?.zoomBy(1.25))}
                      ${this.iconButton(Hn,t(`zoom.out`),()=>this.graphView?.zoomBy(.8))}
                      ${this.iconButton(Bn,t(`zoom.fit`),()=>this.graphView?.fit())}
                  </div>`:k}
        `;return this.narrow?D`<details class="toolbar">
                  <summary>${t(`toolbar.options`)}</summary>
                  <div class="controls">${n}</div>
              </details>`:D`<div class="toolbar">
                  <div class="controls">${n}</div>
              </div>`}iconButton(e,t,n){return D`<button
            class="icon-button"
            aria-label=${t}
            title=${t}
            @click=${n}
        >
            ${Xn(e)}
        </button>`}actionButton(e,t){return D`<button
            class="action"
            @click=${()=>this.runAction(e)}
        >
            ${t(cl[e])}
        </button>`}renderNotices(e,t){return e.length===0?k:D`<ul class="notices">
            ${e.map(e=>D`<li class=${e.severity}>
                        <span>${t(e.key,e.vars)}</span>${e.action?this.actionButton(e.action,t):k}
                    </li>`)}
        </ul>`}renderMessage(e,t){let n=ll[e.phase],r={site:this.snapshot?.site_name??``},i=[];return n&&i.push({...n,vars:r}),i.push(...e.notices),D`<div class="message ${e.phase}">
            ${e.phase===`loading`?D`<svg
                      class="skeleton"
                      viewBox="0 0 120 60"
                      aria-hidden="true"
                  >
                      <path d="M60 18 L30 37 M60 18 L90 37"></path>
                      <circle cx="60" cy="10" r="8"></circle>
                      <circle cx="30" cy="45" r="8"></circle>
                      <circle cx="90" cy="45" r="8"></circle>
                  </svg>`:k}
            ${i.map(e=>D`<p>${t(e.key,e.vars)}</p>
                        ${e.action?this.actionButton(e.action,t):k}`)}
        </div>`}renderContent(e,t,n,r){let i=n.density??(this.narrow?`compact`:`comfortable`),a=t.render?.site_name??``,o=t.phase===`reloading`?`${r(`state.stale`)} · ${r(`state.reconnecting`)}`:r(`state.stale`);return D`<div class="content ${t.stale?`stale`:``}">
            ${t.stale?D`<span class="badge stale">${o}</span>`:k}
            ${this.view===`graph`?D`<uit-graph-view
                      .model=${e}
                      .density=${i}
                      .orientation=${n.orientation}
                      .showLabels=${n.show_labels}
                      .selectedId=${this.selectedId}
                      .localize=${r}
                      .siteName=${a}
                      .ctrlZoom=${this.layout!==`panel`}
                      .reducedMotion=${this.reducedMotion}
                  ></uit-graph-view>`:D`<uit-list-view
                      .model=${e}
                      .selectedId=${this.selectedId}
                      .localize=${r}
                      .siteName=${a}
                  ></uit-list-view>`}
            <uit-detail-panel
                .model=${e}
                .selectedId=${this.selectedId}
                .localize=${r}
                ?narrow=${this.narrow}
            ></uit-detail-panel>
        </div>`}static styles=[Zn,Qn,C`
            :host {
                display: block;
                height: 100%;
            }
            ha-card {
                height: 100%;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                container-type: inline-size;
            }
            .card {
                position: relative;
                display: flex;
                flex-direction: column;
                flex: 1;
                min-height: 0;
            }
            header {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 16px 4px;
            }
            .title {
                flex: 1;
                min-width: 0;
                margin: 0;
                font-size: var(--ha-card-header-font-size, 1.25rem);
                font-weight: normal;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .toolbar {
                padding: 4px 12px;
            }
            details.toolbar > summary {
                min-height: 44px;
                display: flex;
                align-items: center;
                cursor: pointer;
                padding: 0 4px;
            }
            .controls {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 8px 16px;
            }
            .group {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            }
            .icon-button {
                padding: 0;
                border-radius: 50%;
            }
            .notices {
                list-style: none;
                margin: 4px 12px;
                padding: 0;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .notices li {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 6px 10px;
                border-radius: 8px;
                border-inline-start: 4px solid var(--uit-warning);
                background: color-mix(
                    in srgb,
                    var(--uit-warning) 12%,
                    transparent
                );
            }
            .notices li.info {
                border-color: var(--uit-focus);
                background: color-mix(
                    in srgb,
                    var(--uit-focus) 10%,
                    transparent
                );
            }
            .notices li.error {
                border-color: var(--uit-offline);
                background: color-mix(
                    in srgb,
                    var(--uit-offline) 12%,
                    transparent
                );
            }
            .notices li span {
                flex: 1;
            }
            .body {
                position: relative;
                display: flex;
                flex: 1 1 280px;
                min-height: 0;
            }
            .content {
                position: relative;
                display: flex;
                flex: 1;
                min-width: 0;
                min-height: 0;
            }
            .content.stale uit-graph-view,
            .content.stale uit-list-view {
                opacity: 0.55;
                filter: grayscale(1);
            }
            .badge.stale {
                position: absolute;
                top: 8px;
                left: 12px;
                z-index: 1;
                padding: 2px 10px;
                border-radius: 12px;
                background: var(--card-background-color);
                border: 1px solid var(--uit-line);
                font-size: 0.85em;
            }
            .message {
                margin: auto;
                padding: 24px;
                text-align: center;
                color: var(--secondary-text-color);
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
            }
            .message p {
                margin: 0;
            }
            .skeleton {
                width: 120px;
                fill: var(--uit-line);
                stroke: var(--uit-line);
                stroke-width: 2;
                animation: uit-pulse 1.5s ease-in-out infinite;
            }
            @keyframes uit-pulse {
                50% {
                    opacity: 0.4;
                }
            }
            @container (width < 600px) {
                header {
                    padding: 8px 12px 0;
                }
                .body {
                    flex-basis: 240px;
                }
            }
        `]}),F(g,en),F(tn,pn),F(nn,yn),F(rn,mn),F(an,bn),F(on,hn),F(sn,xn),F(cn,gn),F(ln,Sn),F(un,_n),F(dn,Cn);var dl=ht(`en`);window.customCards??=[],window.customCards.some(e=>e.type===`unifi-insights-topology-card`)||window.customCards.push({type:h,name:dl(`card.name`),description:dl(`card.description`),preview:!0,documentationURL:`https://github.com/ruaan-deysel/ha-unifi-insights#network-topology-card`});var fl=[{type:tn,name:`UniFi Insights Site Health`,description:``},{type:rn,name:`UniFi Insights Internet Activity`,description:``},{type:on,name:`UniFi Insights Device Performance`,description:``},{type:cn,name:`UniFi Insights Protect Status`,description:``},{type:un,name:`UniFi Insights Event Timeline`,description:``}];for(let e of fl)window.customCards.some(t=>t.type===e.type)||window.customCards.push({type:e.type,name:e.name,description:e.description,preview:!0});