import{$ as e,A as t,At as n,C as r,Ct as i,D as a,Dt as o,E as s,Et as c,F as l,Ft as u,G as d,I as f,It as p,J as m,L as h,Lt as g,M as _,Mt as v,N as y,Nt as b,O as x,Ot as S,P as C,Pt as ee,Q as te,St as ne,T as w,Tt as re,W as ie,X as ae,_t as oe,a as se,bt as ce,dt as le,et as ue,ft as de,gt as fe,ht as pe,i as me,it as he,j as T,jt as ge,k as _e,kt as ve,lt as E,mt as ye,pt as be,q as xe,r as Se,rt as Ce,tt as we,ut as Te,vt as Ee,w as De,wt as Oe,xt as ke,yt as Ae}from"./chunks/register-dashboard-card-C7zfXImU.js";import"./internet-activity-card.js";import"./performance-card.js";import"./protect-status-card.js";import"./site-health-card.js";import"./timeline-card.js";var je={"card.name":`UniFi Topology`,"card.description":`Interactive network topology of a UniFi site, from UniFi Insights.`,"header.summary":`{devices} devices · {clients} clients`,"state.loading":`Loading network topology…`,"state.no_sources":`No UniFi Insights integration is loaded.`,"state.unconfigured":`Choose a site to show.`,"state.empty":`No devices reported for {site}.`,"state.incompatible":`Card and integration versions don't match. Refresh the browser (clear cache) after updating.`,"state.stale":`Stale`,"state.reconnecting":`Reconnecting…`,"state.online":`Online`,"state.offline":`Offline`,"state.unknown":`Unknown`,"issue.site_unavailable":`Site data temporarily unavailable; will recover automatically.`,"issue.devices_unavailable":`Device data unavailable; showing last known layout.`,"issue.legacy_uplink_missing":`Uplink details unavailable; device links may be missing.`,"issue.parents_unresolved":`{count} nodes couldn't be placed under a parent.`,"issue.clients_truncated":`Showing {included} of {total} clients (limit {max}).`,"issue.entry_unloaded":`Integration is reloading.`,"issue.unknown":`Topology problem: {code}.`,"error.entry_not_found":`The configured site no longer exists or is disabled.`,"error.site_not_selected":`The configured site no longer exists or is disabled.`,"error.entry_not_loaded":`Integration isn't loaded (retrying).`,"error.unknown":`Could not load the topology ({code}).`,"action.integration":`Integration`,"action.edit":`Edit card`,"view.graph":`Graph`,"view.list":`List`,"toolbar.view":`View`,"toolbar.filters":`Show`,"toolbar.zoom":`Zoom`,"toolbar.options":`Options`,"toolbar.site":`Site`,"zoom.in":`Zoom in`,"zoom.out":`Zoom out`,"zoom.fit":`Fit to view`,"zoom.hint":`Use Ctrl + scroll to zoom`,"kind.gateway":`Gateway`,"kind.switch":`Switch`,"kind.access_point":`Access point`,"kind.client":`Client`,"kind.other":`Other`,"medium.wired":`Wired`,"medium.wireless":`Wireless`,"medium.unknown":`Unknown`,"group.clients":`{count} clients`,"group.client_one":`1 client`,"group.unconnected":`Unconnected clients`,"group.root":`Clients`,"group.summary":`{wireless} wireless, {offline} offline`,"graph.label":`{site} topology, {devices} devices, {clients} clients`,"graph.roledescription":`network topology`,"node.label":`{kind} {name}, {state}`,"node.clients":`{count} clients`,"node.client_one":`1 client`,"node.uplink":`uplink port {port}`,"node.uplink_speed":`uplink port {port} at {speed}`,"list.label":`{site} devices and clients`,"list.search":`Search`,"list.no_matches":`No matches`,"detail.close":`Close`,"detail.kind":`Type`,"detail.model":`Model`,"detail.state":`State`,"detail.parent":`Connected to`,"detail.port":`Port`,"detail.speed":`Speed`,"detail.medium":`Link`,"detail.poe":`PoE`,"detail.clients":`Clients`,"detail.clients_value":`{total} ({wired} wired, {wireless} wireless)`,"detail.connection":`Connection`,"detail.vlan":`VLAN`,"detail.network":`Network`,"detail.via_hidden":`Via hidden`,"detail.open_device":`Open device`,"detail.search_members":`Search clients`,"menu.label":`Actions`,"menu.copy_ip":`Copy IP address`,"menu.copy_mac":`Copy MAC address`,"menu.open_entity":`Open entity`,"menu.copied_ip":`IP address copied to the clipboard.`,"menu.copied_mac":`MAC address copied to the clipboard.`,"menu.copy_failed":`Couldn't copy. Select the value below to copy it by hand.`,"announce.updated":`Topology updated.`,"announce.offline":`{count} devices offline.`,"editor.site":`Site`,"editor.site_unavailable":`{site} (unavailable)`,"editor.title":`Title`,"editor.view":`Default view`,"editor.clients":`Clients`,"editor.kinds":`Show node types`,"editor.density":`Density`,"editor.orientation":`Orientation`,"editor.layout":`Layout`,"editor.show_site_selector":`Show site selector`,"editor.show_labels":`Show labels`,"editor.max_clients":`Maximum clients`,"clients.collapsed":`Grouped`,"clients.expanded":`Expanded`,"clients.hidden":`Hidden`,"density.auto":`Automatic`,"density.comfortable":`Comfortable`,"density.compact":`Compact`,"orientation.vertical":`Top to bottom`,"orientation.horizontal":`Left to right`,"layout.tree":`Tree`,"layout.tiered":`Tiered by role`},Me={en:je};function Ne(e){let t=(e??`en`).toLowerCase(),n=Me[t]??Me[t.split(`-`)[0]??`en`]??{};return(e,t)=>{let r=n[e]??je[e];if(t)for(let[e,n]of Object.entries(t))r=r.replaceAll(`{${e}}`,String(n));return r}}var Pe={status:`idle`},Fe=class{onChange;current=Pe;keyId;connection;generation=0;constructor(e){this.onChange=e}get state(){return this.current}select(e,t){let n=t&&x(e)&&!t.node_id.startsWith(`group:`)?JSON.stringify([t.entry_id,t.site_id,t.node_id]):void 0,r=e?.connection;if(n===this.keyId&&r===this.connection||(this.stop(),this.keyId=n,this.connection=r,!e||!t||n===void 0))return;let i=this.generation;this.current={status:`loading`};let a={type:ee,...t};this.fetch(e,a,i)}stop(){this.generation++,this.current=Pe,this.keyId=void 0,this.connection=void 0}async fetch(e,t,n){let r;try{r={status:`ready`,details:await e.callWS(t)}}catch{r=Pe}n===this.generation&&(this.current=r,this.onChange())}},Ie=e=>typeof e==`string`&&e!==``;function Le(e,t){if(!t||!e)return[];let n=[];return Ie(e.ip_address)&&n.push(`copy_ip`),Ie(e.mac_address)&&n.push(`copy_mac`),Ie(e.device_id)&&n.push(`open_device`),Ie(e.entity_id)&&n.push(`open_entity`),n}var Re=class{last=-1/0;pending;timer;emit;intervalMs;constructor(e,t=5e3){this.emit=e,this.intervalMs=t}announce(e){let t=this.last+this.intervalMs-Date.now();t<=0&&this.timer===void 0?(this.last=Date.now(),this.emit(e)):(this.pending=e,this.timer??=setTimeout(()=>{this.timer=void 0;let e=this.pending;this.pending=void 0,e!==void 0&&(this.last=Date.now(),this.emit(e))},Math.max(t,0)))}dispose(){this.timer!==void 0&&clearTimeout(this.timer),this.timer=void 0,this.pending=void 0}},ze={[ge]:{key:`issue.site_unavailable`},[o]:{key:`issue.devices_unavailable`,action:`integration`},[ve]:{key:`issue.legacy_uplink_missing`},[n]:{key:`issue.parents_unresolved`},[c]:{key:`issue.clients_truncated`},[S]:{key:`issue.entry_unloaded`}},Be={[i]:{key:`error.entry_not_found`,action:`edit`},[re]:{key:`error.site_not_selected`,action:`edit`},[Oe]:{key:`error.entry_not_loaded`,action:`integration`}};function Ve(e,t,n){let r=ze[e.code];if(!r)return{code:e.code,severity:e.severity,key:`issue.unknown`,vars:{code:e.code}};let i={code:e.code,severity:e.severity,key:r.key};return e.code===`parents_unresolved`&&(i.vars={count:t.unresolved.length}),e.code===`clients_truncated`&&t.truncation&&(i.vars={included:t.truncation.clients_included,total:t.truncation.clients_total,max:n}),r.action&&(i.action=r.action),i}function He(e){let t=Be[e.code];if(!t)return{code:e.code,severity:`error`,key:`error.unknown`,vars:{code:e.code}};let n={code:e.code,severity:`error`,key:t.key};return t.action&&(n.action=t.action),n}function Ue(e){if(e.incompatible)return{phase:`incompatible`,stale:!1,notices:[]};if(e.error)return{phase:`error`,render:e.lastGood,stale:e.lastGood!==void 0,notices:[He(e.error)]};if(e.disconnected){let t=e.snapshot,n=t&&t.nodes.length>0?t:e.lastGood;if(n)return{phase:`reloading`,render:n,stale:!0,notices:[]}}if(e.sources!==void 0&&e.sources.length===0&&e.snapshot===void 0)return{phase:`no_sources`,stale:!1,notices:[]};if(e.binding===void 0)return{phase:e.sources===void 0?`loading`:`unconfigured`,stale:!1,notices:[]};let t=e.snapshot;if(t===void 0)return{phase:`loading`,stale:!1,notices:[]};let n=t.issues.map(n=>Ve(n,t,e.maxClients));if(t.status===`unavailable`){let r=t.issues.some(e=>e.code===S),i=t.nodes.length>0?t:e.lastGood;return{phase:r?`reloading`:`unavailable`,render:i,stale:i!==void 0,notices:n}}return t.nodes.length===0?{phase:`empty`,stale:!1,notices:n}:{phase:t.status===`partial`?`partial`:`ok`,render:t,stale:!1,notices:n}}var We=new Set([Oe,`unknown_command`]),Ge=2e3,Ke=6e4;function qe(e,t=Math.random){let n=Math.min(Ge*2**e,Ke);return Math.round(n*(.8+.4*t()))}var Je=class{generation=0;connection;key;keyId;unsubscribe;retryTimer;attempt=0;lastRevision;isLive=!1;handlers;random;constructor(e,t=Math.random){this.handlers=e,this.random=t}get live(){return this.isLive}update(e,t){let n=t?JSON.stringify([t.entry_id,t.site_id,t.max_clients]):void 0;(e!==this.connection||n!==this.keyId)&&(this.stop(),this.connection=e,this.key=t,this.keyId=n,e&&(e.addEventListener(`ready`,this.onReady),e.addEventListener(`disconnected`,this.onDisconnected)),e&&t&&this.open())}stop(){this.generation++,this.clearRetry(),this.attempt=0,this.release(),this.connection?.removeEventListener(`ready`,this.onReady),this.connection?.removeEventListener(`disconnected`,this.onDisconnected),this.connection=void 0,this.key=void 0,this.keyId=void 0}clearRetry(){this.retryTimer!==void 0&&clearTimeout(this.retryTimer),this.retryTimer=void 0}drop(){this.generation++,this.clearRetry(),this.unsubscribe=void 0,this.isLive=!1,this.lastRevision=void 0}onDisconnected=()=>{this.drop(),this.handlers.onDisconnected()};onReady=()=>{this.drop(),this.attempt=0,this.key&&this.open(),this.handlers.onReconnected()};release(){let e=this.unsubscribe;this.unsubscribe=void 0,this.isLive=!1,this.lastRevision=void 0,e&&e().catch(()=>void 0)}open(){let e=++this.generation,{connection:n,key:r}=this;n&&r&&n.subscribeMessage(t=>{e===this.generation&&this.receive(t)},{type:p,entry_id:r.entry_id,site_id:r.site_id,max_clients:r.max_clients},{resubscribe:!1}).then(t=>{e===this.generation?this.unsubscribe=t:t().catch(()=>void 0)},n=>{if(e!==this.generation)return;let r=t(n);this.handlers.onError(r),We.has(r.code)&&this.scheduleRetry()})}receive(e){let t;try{t=g(e)}catch(e){e instanceof v?this.handlers.onIncompatible():this.handlers.onError({code:`invalid_payload`,message:String(e)});return}let n=t.issues.some(e=>e.code===S);n||(this.isLive=!0,this.attempt=0),(t.revision===``||t.revision!==this.lastRevision)&&(this.lastRevision=t.revision,this.handlers.onSnapshot(t),n&&(this.generation++,this.release(),this.scheduleRetry()))}scheduleRetry(){let e=this.generation,t=qe(this.attempt++,this.random);this.retryTimer=setTimeout(()=>{this.retryTimer=void 0,e===this.generation&&this.open()},t)}},Ye=`group:unconnected`,Xe=`group:root`,Ze=e=>`group:${e}`,Qe={gateway:0,switch:1,access_point:2,other:3,client:4},$e=(e,t)=>e.name.localeCompare(t.name)||e.id.localeCompare(t.id),et=(e,t)=>Qe[e.kind]-Qe[t.kind]||$e(e,t);function tt(e,t){let n=e.toggledGroups.has(t);return e.clients===`expanded`?!n:n}var nt=()=>({total:0,wired:0,wireless:0,offline:0});function rt(e,t){e.total++,t.connection===`wired`&&e.wired++,t.connection===`wireless`&&e.wireless++,t.state===`offline`&&e.offline++}function it(e,t,n){let r=new Set;for(let i of e){let e=new Set,a=i.id;for(;a!==void 0&&!r.has(a);){e.add(a);let r=t.get(a);if(r!==void 0&&e.has(r)){t.delete(a),n.delete(a);break}a=r}for(let t of e)r.add(t)}}function at(e,t){let n=new Map(e.nodes.map(e=>[e.id,e])),r=new Map,i=new Map;for(let t of e.edges){let e=n.get(t.source),a=n.get(t.target);e&&a&&e.id!==a.id&&a.kind!==`client`&&!r.has(e.id)&&(r.set(e.id,a.id),i.set(e.id,t))}it(e.nodes,r,i);let a=e.nodes.filter(e=>e.kind!==`client`).sort(et),o=e.nodes.filter(e=>e.kind===`client`).sort($e),s=new Map;for(let e of o){let t=r.get(e.id);if(t===void 0)continue;let n=s.get(t);n||s.set(t,n=nt()),rt(n,e)}let c=new Map,l=new Map,u=new Map,d=new Map,f=[],p=e=>t.kinds.has(e.kind),m=e=>{let t=[],i=r.get(e);for(;i!==void 0;){let e=n.get(i);if(p(e))return{id:i,skipped:t};t.push(e.kind),i=r.get(i)}return{id:void 0,skipped:t}},h=(e,t,n,r)=>{if(t===void 0){f.push(e);return}u.set(e,t),d.set(e,{childId:e,parentId:t,edge:n,viaHidden:[...new Set(r)]});let i=l.get(t);i?i.push(e):l.set(t,[e])};for(let e of a){if(!p(e))continue;c.set(e.id,{type:`device`,id:e.id,node:e});let t=m(e.id);h(e.id,t.id,i.get(e.id),t.skipped)}if(t.clients!==`hidden`&&t.kinds.has(`client`)){let e=new Map;for(let t of o){let i=r.get(t.id),a,o=[],s;if(i===void 0)s=Ye;else{let e=n.get(i);if(p(e))a=i;else{let t=m(i);a=t.id,o=[e.kind,...t.skipped]}s=a===void 0?Xe:Ze(a)}let c=e.get(s);c||e.set(s,c={parent:a,members:[],skipped:new Set}),c.members.push(t);for(let e of o)c.skipped.add(e)}let a=[...e].sort(([e],[t])=>Number(e===Ye)-Number(t===Ye));for(let[e,n]of a){let r=nt();for(let e of n.members)rt(r,e);let a=tt(t,e);if(c.set(e,{type:`group`,id:e,members:n.members,counts:r,expanded:a}),h(e,n.parent,void 0,n.skipped),a)for(let t of n.members)c.set(t.id,{type:`client`,id:t.id,node:t}),h(t.id,e,i.get(t.id),[])}}return{snapshot:e,roots:f,visuals:c,children:l,parentOf:u,links:d,nodes:n,realParent:r,edges:i,clientCounts:s,stats:{devices:a.length,clients:o.length,offlineDevices:a.filter(e=>e.state===`offline`).length}}}function ot(){let e,t,n;return(r,i)=>(n&&r===e&&i===t||(e=r,t=i,n=at(r,i)),n)}function st(e,t){let n=e.parentOf.get(t);return n===void 0?e.roots:e.children.get(n)??[]}function ct(e,t){for(let n of e.visuals.values())if(n.type===`group`&&n.members.some(e=>e.id===t))return n}var lt={gateway:`kind.gateway`,switch:`kind.switch`,access_point:`kind.access_point`,client:`kind.client`,other:`kind.other`},D={online:`state.online`,offline:`state.offline`,unknown:`state.unknown`},ut={graph:`view.graph`,list:`view.list`},dt={wired:`medium.wired`,wireless:`medium.wireless`,unknown:`medium.unknown`};function ft(e,t){let n=[...e];return n.length>t?`${n.slice(0,t-1).join(``)}…`:e}var pt=e=>Number.isInteger(e)?String(e):e.toFixed(1);function mt(e){return e>=1e3?`${pt(e/1e3)}G`:`${e}M`}function ht(e){return e>=1e3?`${pt(e/1e3)} gigabit`:`${e} megabit`}function gt(e){if(!e)return``;let t=[];return e.parent_port!==void 0&&t.push(`p${e.parent_port}`),e.speed_mbps&&t.push(mt(e.speed_mbps)),e.poe_power_w!==void 0&&t.push(`PoE`),t.join(` · `)}function O(e,t){return e.type===`group`?e.id===`group:unconnected`?t(`group.unconnected`):e.id===`group:root`?t(`group.root`):e.counts.total===1?t(`group.client_one`):t(`group.clients`,{count:e.counts.total}):e.node.name}function _t(e){return e.type===`group`?e.counts.offline===e.counts.total?`offline`:`online`:e.node.state}function vt(e,t,n){if(t.type===`group`)return`${O(t,n)}: ${n(`group.summary`,{wireless:t.counts.wireless,offline:t.counts.offline})}`;let r=t.node,i=[n(`node.label`,{kind:n(lt[r.kind]),name:r.name,state:n(D[r.state]).toLocaleLowerCase()})],a=e.clientCounts.get(r.id)?.total??0;a>0&&i.push(a===1?n(`node.client_one`):n(`node.clients`,{count:a}));let o=e.edges.get(r.id);return o?.parent_port===void 0?r.connection&&i.push(n(dt[r.connection]).toLocaleLowerCase()):i.push(o.speed_mbps?n(`node.uplink_speed`,{port:o.parent_port,speed:ht(o.speed_mbps)}):n(`node.uplink`,{port:o.parent_port})),i.join(`, `)}var yt={ATTRIBUTE:1,CHILD:2,PROPERTY:3,BOOLEAN_ATTRIBUTE:4,EVENT:5,ELEMENT:6},bt=e=>(...t)=>({_$litDirective$:e,values:t}),xt=class{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,n){this._$Ct=e,this._$AM=t,this._$Ci=n}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}},{I:St}=l,Ct=e=>e,wt=()=>document.createComment(``),Tt=(e,t,n)=>{let r=e._$AA.parentNode,i=t===void 0?e._$AB:t._$AA;if(n===void 0)n=new St(r.insertBefore(wt(),i),r.insertBefore(wt(),i),e,e.options);else{let t=n._$AB.nextSibling,a=n._$AM,o=a!==e;if(o){let t;n._$AQ?.(e),n._$AM=e,n._$AP!==void 0&&(t=e._$AU)!==a._$AU&&n._$AP(t)}if(t!==i||o){let e=n._$AA;for(;e!==t;){let t=Ct(e).nextSibling;Ct(r).insertBefore(e,i),e=t}}}return n},k=(e,t,n=e)=>(e._$AI(t,n),e),Et={},Dt=(e,t=Et)=>e._$AH=t,Ot=e=>e._$AH,kt=e=>{e._$AR(),e._$AA.remove()},At=bt(class extends xt{constructor(){super(...arguments),this.key=_}render(e,t){return this.key=e,t}update(e,[t,n]){return t!==this.key&&(Dt(e),this.key=t),n}});function jt(){let e=document.activeElement;for(;e?.shadowRoot?.activeElement;)e=e.shadowRoot.activeElement;return e instanceof HTMLElement?e:null}function Mt(e,t){let n=jt(),r=document.createElement(`textarea`);r.value=e,r.setAttribute(`readonly`,``),r.setAttribute(`aria-hidden`,`true`),r.style.cssText=`position:fixed;top:0;left:0;width:1px;height:1px;opacity:0;pointer-events:none`,t.append(r);try{return r.focus(),r.select(),typeof document.execCommand==`function`&&document.execCommand(`copy`)}catch{return!1}finally{r.remove(),n?.focus()}}async function Nt(e,t=document.body){if(navigator.clipboard?.writeText)try{return await navigator.clipboard.writeText(e),!0}catch{}return Mt(e,t)}var Pt=(e,t,n)=>{let r=new Map;for(let i=t;i<=n;i++)r.set(e[i],i);return r},Ft=bt(class extends xt{constructor(e){if(super(e),e.type!==yt.CHILD)throw Error(`repeat() can only be used in text expressions`)}dt(e,t,n){let r;n===void 0?n=t:t!==void 0&&(r=t);let i=[],a=[],o=0;for(let t of e)i[o]=r?r(t,o):o,a[o]=n(t,o),o++;return{values:a,keys:i}}render(e,t,n){return this.dt(e,t,n).values}update(e,[t,n,r]){let i=Ot(e),{values:a,keys:o}=this.dt(t,n,r);if(!Array.isArray(i))return this.ut=o,a;let s=this.ut??=[],c=[],l,u,d=0,f=i.length-1,p=0,m=a.length-1;for(;d<=f&&p<=m;)if(i[d]===null)d++;else if(i[f]===null)f--;else if(s[d]===o[p])c[p]=k(i[d],a[p]),d++,p++;else if(s[f]===o[m])c[m]=k(i[f],a[m]),f--,m--;else if(s[d]===o[m])c[m]=k(i[d],a[m]),Tt(e,c[m+1],i[d]),d++,m--;else if(s[f]===o[p])c[p]=k(i[f],a[p]),Tt(e,i[d],i[f]),f--,p++;else if(l===void 0&&(l=Pt(o,p,m),u=Pt(s,d,f)),l.has(s[d])){if(l.has(s[f])){let t=u.get(o[p]),n=t===void 0?null:i[t];if(n===null){let t=Tt(e,i[d]);k(t,a[p]),c[p]=t}else c[p]=k(n,a[p]),Tt(e,i[d],n),i[t]=null;p++}else kt(i[f]),f--}else kt(i[d]),d++;for(;p<=m;){let t=Tt(e,c[m+1]);k(t,a[p]),c[p++]=t}for(;d<=f;){let e=i[d++];e!==null&&kt(e)}return this.ut=o,Dt(e,c),y}}),It={copy_ip:`menu.copy_ip`,copy_mac:`menu.copy_mac`,open_device:`detail.open_device`,open_entity:`menu.open_entity`},Lt={copy_ip:m,copy_mac:m,open_device:Ce,open_entity:e},Rt=0;E(`uit-node-menu`,class extends T{static properties={actions:{attribute:!1},localize:{attribute:!1},open:{state:!0}};menuId=`uit-node-menu-${++Rt}`;listening=!1;tabClose;constructor(){super(),this.actions=[],this.open=!1}get trigger(){return this.renderRoot.querySelector(`button.trigger`)}get menu(){return this.renderRoot.querySelector(`[role="menu"]`)}get items(){return[...this.renderRoot.querySelectorAll(`[role="menuitem"]`)]}get focusedItem(){let e=this.renderRoot.activeElement;return e instanceof HTMLElement&&this.menu?.contains(e)?e:null}get hasContent(){return this.actions.length>0}connectedCallback(){super.connectedCallback(),this.listenOutside(this.open)}disconnectedCallback(){super.disconnectedCallback(),this.hide(!1),this.listenOutside(!1)}async show(e=`first`){if(!this.hasContent)return;clearTimeout(this.tabClose),this.open=!0,await this.updateComplete;let t=this.items,n=t[e===`first`?0:t.length-1];for(let e of t)e.tabIndex=e===n?0:-1;n?.focus()}hide(e=!0){clearTimeout(this.tabClose),this.tabClose=void 0,this.open&&(this.open=!1,e&&this.trigger?.focus())}willUpdate(){this.hasContent||(this.open=!1)}updated(e){e.has(`open`)&&this.listenOutside(this.open)}listenOutside(e){e!==this.listening&&(this.listening=e,e?document.addEventListener(`pointerdown`,this.onOutsidePress,!0):document.removeEventListener(`pointerdown`,this.onOutsidePress,!0))}onOutsidePress=e=>{e.composedPath().includes(this)||this.hide(!1)};onTriggerKeydown(e){e.key===`ArrowDown`||e.key===`ArrowUp`?(e.preventDefault(),this.show(e.key===`ArrowDown`?`first`:`last`)):e.key===`Escape`&&this.open&&(this.swallow(e),this.hide())}swallow(e){e.preventDefault(),e.stopPropagation()}onMenuKeydown(e){e.stopPropagation();let t=this.items,n=this.focusedItem?t.indexOf(this.focusedItem):-1,r;switch(e.key){case`ArrowDown`:r=(n+1)%t.length;break;case`ArrowUp`:r=n<=0?t.length-1:n-1;break;case`Home`:r=0;break;case`End`:r=t.length-1;break;case`Escape`:this.swallow(e),this.hide();return;case`Tab`:this.tabClose=setTimeout(()=>this.hide(!1),0);return;default:return}e.preventDefault();for(let e of t)e.tabIndex=e===t[r]?0:-1;t[r]?.focus()}choose(e){this.hide(),s(this,`uit-action`,{action:e})}render(){let{localize:e}=this;if(!e||!this.hasContent)return _;let t=e(`menu.label`);return C`<button
        class="trigger"
        type="button"
        aria-haspopup="menu"
        aria-expanded=${String(this.open)}
        aria-controls=${this.menuId}
        aria-label=${t}
        title=${t}
        @click=${e=>{e.stopPropagation(),this.open?this.hide():this.show()}}
        @keydown=${e=>this.onTriggerKeydown(e)}
      >
        ${w(ae)}<span>${t}</span>
      </button>
      ${this.open?C`<div
            id=${this.menuId}
            class="menu"
            role="menu"
            aria-label=${t}
            @click=${e=>e.stopPropagation()}
            @pointerdown=${e=>e.stopPropagation()}
            @contextmenu=${e=>e.stopPropagation()}
            @keydown=${e=>this.onMenuKeydown(e)}
          >
            ${Ft(this.actions,e=>e,t=>C`<button
                  type="button"
                  role="menuitem"
                  tabindex="-1"
                  data-action=${t}
                  @click=${()=>this.choose(t)}
                >
                  ${w(Lt[t])}<span
                    >${e(It[t])}</span
                  >
                </button>`)}
          </div>`:_}`}static styles=[se,Se,me]});var zt=class extends T{static properties={model:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},hass:{attribute:!1},menuRequest:{attribute:!1},details:{attribute:!1},narrow:{type:Boolean,reflect:!0},memberQuery:{state:!0},modal:{state:!0},copyStatus:{state:!0}};pressedBackdrop=!1;menuPending=!1;copyScope;copyGeneration=0;constructor(){super(),this.narrow=!1,this.memberQuery=``,this.modal=!1}disconnectedCallback(){super.disconnectedCallback(),this.closeMenu(),this.menuPending=!1,this.copyGeneration++,this.copyStatus=void 0,this.renderRoot.querySelector(`dialog`)?.close()}willUpdate(e){e.has(`selectedId`)&&(this.memberQuery=``);let t=JSON.stringify([this.model?.snapshot.entry_id,this.model?.snapshot.site_id,this.selectedId,x(this.hass)]);if(t!==this.copyScope&&(this.closeMenu(),this.menuPending=!1,this.copyScope=t,this.copyGeneration++,this.copyStatus=void 0),this.selectedId===void 0&&(this.modal=!1),e.has(`menuRequest`)){let e=this.menuRequest;this.menuPending=e!==void 0&&e.node_id===this.selectedId&&e.entry_id===this.model?.snapshot.entry_id&&e.site_id===this.model?.snapshot.site_id}}updated(e){if(!this.isConnected)return;let t=this.renderRoot.querySelector(`dialog`);if(t)t.open||t.showModal();else if(e.has(`selectedId`)||e.has(`narrow`)||e.has(`details`)){let e=this.renderRoot.querySelector(`.panel`);if(e&&e.scrollHeight>e.clientHeight+1){this.modal=!0;return}}this.openRequestedMenu()}closeMenu(){this.renderRoot.querySelector(`uit-node-menu`)?.hide(!1)}get menuOpen(){return this.renderRoot.querySelector(`uit-node-menu`)?.open===!0}openRequestedMenu(){this.menuPending&&this.details&&(this.menuPending=!1,this.renderRoot.querySelector(`uit-node-menu`)?.show())}close(){this.closeMenu(),this.menuPending=!1;let e=this.renderRoot.querySelector(`dialog`);e?e.close():s(this,`uit-close`)}render(){let{model:e,selectedId:t,localize:n}=this;if(!e||!t||!n)return _;let r=e.visuals.get(t);if(r?.type===`group`)return this.shell(O(r,n),this.groupBody(r,n));let i=e.nodes.get(t);if(!i)return _;let a=i.kind===`client`?this.clientBody(e,i,n):this.deviceBody(e,i,n);return this.shell(i.name,a)}shell(e,t){let n=this.panel(e,t);return this.modal?C`<dialog
      aria-labelledby="title"
      @close=${()=>{this.closeMenu(),this.menuPending=!1,s(this,`uit-close`)}}
      @cancel=${e=>{this.menuOpen&&(e.preventDefault(),this.renderRoot.querySelector(`uit-node-menu`)?.hide())}}
      @keydown=${e=>{e.key===`Escape`&&(e.preventDefault(),e.stopPropagation(),this.close())}}
      @pointerdown=${{capture:!0,handleEvent:e=>{this.pressedBackdrop=e.target===e.currentTarget}}}
      @click=${e=>{e.target===e.currentTarget&&this.pressedBackdrop&&this.close()}}
    >
      ${n}
    </dialog>`:n}panel(e,t){let n=this.localize;return C`<section
      class="panel"
      role=${this.modal?_:`region`}
      aria-label=${this.modal?_:e}
      @keydown=${e=>{e.key===`Escape`&&this.menuOpen&&(e.preventDefault(),e.stopPropagation(),this.renderRoot.querySelector(`uit-node-menu`)?.hide())}}
    >
      <header>
        <h3 id="title" title=${e}>${e}</h3>
        <button
          class="close"
          aria-label=${n(`detail.close`)}
          title=${n(`detail.close`)}
          @click=${()=>this.close()}
        >
          ${w(xe)}
        </button>
      </header>
      ${t}${this.statusRegion(n)}
    </section>`}menu(e,t){let n=Le(this.details,x(this.hass));return n.length===0?_:C`${At(e.id,C`<uit-node-menu
        .actions=${n}
        .localize=${t}
        @uit-action=${e=>this.runAction(e.detail.action)}
      ></uit-node-menu>`)}`}statusRegion(e){let t=this.copyStatus?.value===void 0||x(this.hass)?this.copyStatus:void 0;return C`<div
      class="status ${t?`has-message`:``}"
      role="status"
      aria-live="polite"
    >
      ${t?C`<span>${e(t.key,t.vars)}</span
            >${t.value===void 0?_:C`<code class="manual">${t.value}</code>`}`:_}
    </div>`}runAction(e){if(!x(this.hass))return;let t=this.details;switch(e){case`copy_ip`:this.copy(t?.ip_address,`menu.copied_ip`);break;case`copy_mac`:this.copy(t?.mac_address,`menu.copied_mac`);break;case`open_device`:{let e=t?.device_id;e&&this.openDevice(e);break}case`open_entity`:t?.entity_id&&(this.renderRoot.querySelector(`dialog`)?.close(),a(this,t.entity_id))}}async copy(e,t){if(!e)return;this.copyStatus=void 0;let n=this.copyGeneration,r=await Nt(e,this.renderRoot.querySelector(`dialog`)??this.renderRoot);if(n===this.copyGeneration&&(this.copyStatus=r?{key:t}:{key:`menu.copy_failed`,value:e},!r)){if(await this.updateComplete,n!==this.copyGeneration)return;let e=this.renderRoot.querySelector(`.manual`);if(e){let t=document.createRange();t.selectNodeContents(e);let n=window.getSelection();n?.removeAllRanges(),n?.addRange(t)}}}openDevice(e){this.renderRoot.querySelector(`dialog`)?.close(),_e(`/config/devices/device/${encodeURIComponent(e)}`)}rows(e){let t=e.filter(e=>e[1]!==void 0&&e[1]!==``);return C`<dl>
      ${t.map(([e,t])=>C`<div class="row">
            <dt>${this.localize(e)}</dt>
            <dd>${t}</dd>
          </div>`)}
    </dl>`}uplinkRows(e,t,n,r){let i=e.realParent.get(t),a=e.edges.get(t),o;return a?.parent_port!==void 0&&(o=a.child_port===void 0?String(a.parent_port):`${a.parent_port} → ${a.child_port}`),[[`detail.parent`,i===void 0?void 0:e.nodes.get(i)?.name],[`detail.port`,o],[`detail.speed`,a?.speed_mbps?mt(a.speed_mbps):void 0],[`detail.medium`,r&&a?n(dt[a.medium]):void 0],[`detail.poe`,a?.poe_power_w===void 0?void 0:`${a.poe_power_w.toFixed(1)} W`]]}deviceBody(e,t,n){let r=e.clientCounts.get(t.id),i=e.links.get(t.id)?.viaHidden??[];return C`${this.menu(t,n)}${this.rows([[`detail.kind`,n(lt[t.kind])],[`detail.model`,t.model],[`detail.state`,n(D[t.state])],...this.uplinkRows(e,t.id,n,!0),[`detail.clients`,r?n(`detail.clients_value`,{total:r.total,wired:r.wired,wireless:r.wireless}):void 0],[`detail.via_hidden`,i.length>0?i.map(e=>n(lt[e])).join(`, `):void 0]])}
    ${t.ha_device_id?C`<button
          class="action"
          @click=${()=>this.openDevice(t.ha_device_id)}
        >
          ${w(Ce)}${n(`detail.open_device`)}
        </button>`:_}`}clientBody(e,t,n){return C`${this.menu(t,n)}${this.rows([[`detail.state`,n(D[t.state])],[`detail.connection`,t.connection?n(dt[t.connection]):void 0],[`detail.vlan`,t.vlan_id===void 0?void 0:String(t.vlan_id)],[`detail.network`,t.network_name],...this.uplinkRows(e,t.id,n,!1)])}`}groupBody(e,t){let n=this.memberQuery.trim().toLowerCase(),r=n?e.members.filter(e=>e.name.toLowerCase().includes(n)):e.members,i=e.counts;return C`${this.rows([[`detail.clients`,t(`detail.clients_value`,{total:i.total,wired:i.wired,wireless:i.wireless})]])}
      <input
        type="search"
        .value=${this.memberQuery}
        placeholder=${t(`detail.search_members`)}
        aria-label=${t(`detail.search_members`)}
        @input=${e=>{this.memberQuery=e.target.value}}
      />
      <ul class="members">
        ${r.map(e=>C`<li>
              <button
                class="member ${e.state}"
                @click=${()=>s(this,`uit-select`,{id:e.id})}
              >
                ${w(De(e))}<span class="name" title=${e.name}
                  >${e.name}</span
                >
                ${e.state===`online`?_:C`<span class="state-text"
                      >${t(D[e.state])}</span
                    >`}
              </button>
            </li>`)}
      </ul>`}static styles=[se,Se,h`
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
        max-height: calc(100% - 8px);
      }
      .panel {
        pointer-events: auto;
        box-sizing: border-box;
        flex: 1 1 auto;
        min-height: 0;
        overflow: auto;
        padding: 0 16px 16px;
        background: var(--card-background-color);
        border: 1px solid var(--uit-line);
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, none);
      }
      header {
        position: sticky;
        top: 0;
        z-index: 1;
        display: flex;
        align-items: center;
        gap: 8px;
        padding-top: 4px;
        background: var(--card-background-color);
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
      .status.has-message {
        margin-top: 8px;
        color: var(--secondary-text-color);
      }
      .manual {
        display: block;
        margin-top: 4px;
        padding: 6px 8px;
        border: 1px solid var(--uit-line);
        border-radius: 8px;
        color: var(--primary-text-color);
        overflow-wrap: anywhere;
        user-select: text;
      }
      dialog {
        pointer-events: auto;
        box-sizing: border-box;
        width: min(400px, calc(100% - 32px));
        max-width: none;
        max-height: calc(100% - 32px);
        padding: 0;
        border: none;
        background: none;
        color: inherit;
        overflow: visible;
      }
      dialog::backdrop {
        background: rgba(0, 0, 0, 0.32);
      }
      dialog .panel {
        max-height: calc(100vh - 32px);
        max-height: calc(100dvh - 32px);
      }
    `]};E(`uit-detail-panel`,zt);var Bt=class{pointers=new Set;origin={x:0,y:0,moved:!1};down(e){e.isPrimary?(this.pointers=new Set([e.pointerId]),this.origin={x:e.clientX,y:e.clientY,moved:!1}):(this.pointers.add(e.pointerId),this.origin.moved=!0)}move(e){!this.origin.moved&&this.pointers.has(e.pointerId)&&Math.hypot(e.clientX-this.origin.x,e.clientY-this.origin.y)>8&&(this.origin.moved=!0)}end(e){this.pointers.delete(e.pointerId)}get allowsMenu(){return!this.origin.moved&&this.pointers.size<=1}},Vt={svg:`http://www.w3.org/2000/svg`,xhtml:`http://www.w3.org/1999/xhtml`,xlink:`http://www.w3.org/1999/xlink`,xml:`http://www.w3.org/XML/1998/namespace`,xmlns:`http://www.w3.org/2000/xmlns/`};function Ht(e){var t=e+=``,n=t.indexOf(`:`);return n>=0&&(t=e.slice(0,n))!==`xmlns`&&(e=e.slice(n+1)),Vt.hasOwnProperty(t)?{space:Vt[t],local:e}:e}function Ut(e){return function(){var t=this.ownerDocument,n=this.namespaceURI;return n===`http://www.w3.org/1999/xhtml`&&t.documentElement.namespaceURI===`http://www.w3.org/1999/xhtml`?t.createElement(e):t.createElementNS(n,e)}}function Wt(e){return function(){return this.ownerDocument.createElementNS(e.space,e.local)}}function Gt(e){var t=Ht(e);return(t.local?Wt:Ut)(t)}function Kt(){}function qt(e){return e==null?Kt:function(){return this.querySelector(e)}}function Jt(e){typeof e!=`function`&&(e=qt(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=Array(o),c,l,u=0;u<o;++u)(c=a[u])&&(l=e.call(c,c.__data__,u,a))&&(`__data__`in c&&(l.__data__=c.__data__),s[u]=l);return new j(r,this._parents)}function Yt(e){return e==null?[]:Array.isArray(e)?e:Array.from(e)}function Xt(){return[]}function Zt(e){return e==null?Xt:function(){return this.querySelectorAll(e)}}function Qt(e){return function(){return Yt(e.apply(this,arguments))}}function $t(e){e=typeof e==`function`?Qt(e):Zt(e);for(var t=this._groups,n=t.length,r=[],i=[],a=0;a<n;++a)for(var o=t[a],s=o.length,c,l=0;l<s;++l)(c=o[l])&&(r.push(e.call(c,c.__data__,l,o)),i.push(c));return new j(r,i)}function en(e){return function(){return this.matches(e)}}function tn(e){return function(t){return t.matches(e)}}var nn=Array.prototype.find;function rn(e){return function(){return nn.call(this.children,e)}}function an(){return this.firstElementChild}function on(e){return this.select(e==null?an:rn(typeof e==`function`?e:tn(e)))}var sn=Array.prototype.filter;function cn(){return Array.from(this.children)}function ln(e){return function(){return sn.call(this.children,e)}}function un(e){return this.selectAll(e==null?cn:ln(typeof e==`function`?e:tn(e)))}function dn(e){typeof e!=`function`&&(e=en(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=[],c,l=0;l<o;++l)(c=a[l])&&e.call(c,c.__data__,l,a)&&s.push(c);return new j(r,this._parents)}function fn(e){return Array(e.length)}function pn(){return new j(this._enter||this._groups.map(fn),this._parents)}function mn(e,t){this.ownerDocument=e.ownerDocument,this.namespaceURI=e.namespaceURI,this._next=null,this._parent=e,this.__data__=t}mn.prototype={constructor:mn,appendChild:function(e){return this._parent.insertBefore(e,this._next)},insertBefore:function(e,t){return this._parent.insertBefore(e,t)},querySelector:function(e){return this._parent.querySelector(e)},querySelectorAll:function(e){return this._parent.querySelectorAll(e)}};function hn(e){return function(){return e}}function gn(e,t,n,r,i,a){for(var o=0,s,c=t.length,l=a.length;o<l;++o)(s=t[o])?(s.__data__=a[o],r[o]=s):n[o]=new mn(e,a[o]);for(;o<c;++o)(s=t[o])&&(i[o]=s)}function _n(e,t,n,r,i,a,o){var s,c,l=new Map,u=t.length,d=a.length,f=Array(u),p;for(s=0;s<u;++s)(c=t[s])&&(f[s]=p=o.call(c,c.__data__,s,t)+``,l.has(p)?i[s]=c:l.set(p,c));for(s=0;s<d;++s)p=o.call(e,a[s],s,a)+``,(c=l.get(p))?(r[s]=c,c.__data__=a[s],l.delete(p)):n[s]=new mn(e,a[s]);for(s=0;s<u;++s)(c=t[s])&&l.get(f[s])===c&&(i[s]=c)}function vn(e){return e.__data__}function yn(e,t){if(!arguments.length)return Array.from(this,vn);var n=t?_n:gn,r=this._parents,i=this._groups;typeof e!=`function`&&(e=hn(e));for(var a=i.length,o=Array(a),s=Array(a),c=Array(a),l=0;l<a;++l){var u=r[l],d=i[l],f=d.length,p=bn(e.call(u,u&&u.__data__,l,r)),m=p.length,h=s[l]=Array(m),g=o[l]=Array(m);n(u,d,h,g,c[l]=Array(f),p,t);for(var _=0,v=0,y,b;_<m;++_)if(y=h[_]){for(_>=v&&(v=_+1);!(b=g[v])&&++v<m;);y._next=b||null}}return o=new j(o,r),o._enter=s,o._exit=c,o}function bn(e){return typeof e==`object`&&`length`in e?e:Array.from(e)}function xn(){return new j(this._exit||this._groups.map(fn),this._parents)}function Sn(e,t,n){var r=this.enter(),i=this,a=this.exit();return typeof e==`function`?(r=e(r),r&&=r.selection()):r=r.append(e+``),t!=null&&(i=t(i),i&&=i.selection()),n==null?a.remove():n(a),r&&i?r.merge(i).order():i}function Cn(e){for(var t=e.selection?e.selection():e,n=this._groups,r=t._groups,i=n.length,a=r.length,o=Math.min(i,a),s=Array(i),c=0;c<o;++c)for(var l=n[c],u=r[c],d=l.length,f=s[c]=Array(d),p,m=0;m<d;++m)(p=l[m]||u[m])&&(f[m]=p);for(;c<i;++c)s[c]=n[c];return new j(s,this._parents)}function wn(){for(var e=this._groups,t=-1,n=e.length;++t<n;)for(var r=e[t],i=r.length-1,a=r[i],o;--i>=0;)(o=r[i])&&(a&&o.compareDocumentPosition(a)^4&&a.parentNode.insertBefore(o,a),a=o);return this}function Tn(e){e||=En;function t(t,n){return t&&n?e(t.__data__,n.__data__):!t-!n}for(var n=this._groups,r=n.length,i=Array(r),a=0;a<r;++a){for(var o=n[a],s=o.length,c=i[a]=Array(s),l,u=0;u<s;++u)(l=o[u])&&(c[u]=l);c.sort(t)}return new j(i,this._parents).order()}function En(e,t){return e<t?-1:e>t?1:e>=t?0:NaN}function Dn(){var e=arguments[0];return arguments[0]=this,e.apply(null,arguments),this}function On(){return Array.from(this)}function kn(){for(var e=this._groups,t=0,n=e.length;t<n;++t)for(var r=e[t],i=0,a=r.length;i<a;++i){var o=r[i];if(o)return o}return null}function An(){let e=0;for(let t of this)++e;return e}function jn(){return!this.node()}function Mn(e){for(var t=this._groups,n=0,r=t.length;n<r;++n)for(var i=t[n],a=0,o=i.length,s;a<o;++a)(s=i[a])&&e.call(s,s.__data__,a,i);return this}function Nn(e){return function(){this.removeAttribute(e)}}function Pn(e){return function(){this.removeAttributeNS(e.space,e.local)}}function Fn(e,t){return function(){this.setAttribute(e,t)}}function In(e,t){return function(){this.setAttributeNS(e.space,e.local,t)}}function Ln(e,t){return function(){var n=t.apply(this,arguments);n==null?this.removeAttribute(e):this.setAttribute(e,n)}}function Rn(e,t){return function(){var n=t.apply(this,arguments);n==null?this.removeAttributeNS(e.space,e.local):this.setAttributeNS(e.space,e.local,n)}}function zn(e,t){var n=Ht(e);if(arguments.length<2){var r=this.node();return n.local?r.getAttributeNS(n.space,n.local):r.getAttribute(n)}return this.each((t==null?n.local?Pn:Nn:typeof t==`function`?n.local?Rn:Ln:n.local?In:Fn)(n,t))}function Bn(e){return e.ownerDocument&&e.ownerDocument.defaultView||e.document&&e||e.defaultView}function Vn(e){return function(){this.style.removeProperty(e)}}function Hn(e,t,n){return function(){this.style.setProperty(e,t,n)}}function Un(e,t,n){return function(){var r=t.apply(this,arguments);r==null?this.style.removeProperty(e):this.style.setProperty(e,r,n)}}function Wn(e,t,n){return arguments.length>1?this.each((t==null?Vn:typeof t==`function`?Un:Hn)(e,t,n??``)):A(this.node(),e)}function A(e,t){return e.style.getPropertyValue(t)||Bn(e).getComputedStyle(e,null).getPropertyValue(t)}function Gn(e){return function(){delete this[e]}}function Kn(e,t){return function(){this[e]=t}}function qn(e,t){return function(){var n=t.apply(this,arguments);n==null?delete this[e]:this[e]=n}}function Jn(e,t){return arguments.length>1?this.each((t==null?Gn:typeof t==`function`?qn:Kn)(e,t)):this.node()[e]}function Yn(e){return e.trim().split(/^|\s+/)}function Xn(e){return e.classList||new Zn(e)}function Zn(e){this._node=e,this._names=Yn(e.getAttribute(`class`)||``)}Zn.prototype={add:function(e){this._names.indexOf(e)<0&&(this._names.push(e),this._node.setAttribute(`class`,this._names.join(` `)))},remove:function(e){var t=this._names.indexOf(e);t>=0&&(this._names.splice(t,1),this._node.setAttribute(`class`,this._names.join(` `)))},contains:function(e){return this._names.indexOf(e)>=0}};function Qn(e,t){for(var n=Xn(e),r=-1,i=t.length;++r<i;)n.add(t[r])}function $n(e,t){for(var n=Xn(e),r=-1,i=t.length;++r<i;)n.remove(t[r])}function er(e){return function(){Qn(this,e)}}function tr(e){return function(){$n(this,e)}}function nr(e,t){return function(){(t.apply(this,arguments)?Qn:$n)(this,e)}}function rr(e,t){var n=Yn(e+``);if(arguments.length<2){for(var r=Xn(this.node()),i=-1,a=n.length;++i<a;)if(!r.contains(n[i]))return!1;return!0}return this.each((typeof t==`function`?nr:t?er:tr)(n,t))}function ir(){this.textContent=``}function ar(e){return function(){this.textContent=e}}function or(e){return function(){var t=e.apply(this,arguments);this.textContent=t??``}}function sr(e){return arguments.length?this.each(e==null?ir:(typeof e==`function`?or:ar)(e)):this.node().textContent}function cr(){this.innerHTML=``}function lr(e){return function(){this.innerHTML=e}}function ur(e){return function(){var t=e.apply(this,arguments);this.innerHTML=t??``}}function dr(e){return arguments.length?this.each(e==null?cr:(typeof e==`function`?ur:lr)(e)):this.node().innerHTML}function fr(){this.nextSibling&&this.parentNode.appendChild(this)}function pr(){return this.each(fr)}function mr(){this.previousSibling&&this.parentNode.insertBefore(this,this.parentNode.firstChild)}function hr(){return this.each(mr)}function gr(e){var t=typeof e==`function`?e:Gt(e);return this.select(function(){return this.appendChild(t.apply(this,arguments))})}function _r(){return null}function vr(e,t){var n=typeof e==`function`?e:Gt(e),r=t==null?_r:typeof t==`function`?t:qt(t);return this.select(function(){return this.insertBefore(n.apply(this,arguments),r.apply(this,arguments)||null)})}function yr(){var e=this.parentNode;e&&e.removeChild(this)}function br(){return this.each(yr)}function xr(){var e=this.cloneNode(!1),t=this.parentNode;return t?t.insertBefore(e,this.nextSibling):e}function Sr(){var e=this.cloneNode(!0),t=this.parentNode;return t?t.insertBefore(e,this.nextSibling):e}function Cr(e){return this.select(e?Sr:xr)}function wr(e){return arguments.length?this.property(`__data__`,e):this.node().__data__}function Tr(e){return function(t){e.call(this,t,this.__data__)}}function Er(e){return e.trim().split(/^|\s+/).map(function(e){var t=``,n=e.indexOf(`.`);return n>=0&&(t=e.slice(n+1),e=e.slice(0,n)),{type:e,name:t}})}function Dr(e){return function(){var t=this.__on;if(t){for(var n=0,r=-1,i=t.length,a;n<i;++n)a=t[n],(!e.type||a.type===e.type)&&a.name===e.name?this.removeEventListener(a.type,a.listener,a.options):t[++r]=a;++r?t.length=r:delete this.__on}}}function Or(e,t,n){return function(){var r=this.__on,i,a=Tr(t);if(r){for(var o=0,s=r.length;o<s;++o)if((i=r[o]).type===e.type&&i.name===e.name){this.removeEventListener(i.type,i.listener,i.options),this.addEventListener(i.type,i.listener=a,i.options=n),i.value=t;return}}this.addEventListener(e.type,a,n),i={type:e.type,name:e.name,value:t,listener:a,options:n},r?r.push(i):this.__on=[i]}}function kr(e,t,n){var r=Er(e+``),i,a=r.length,o;if(arguments.length<2){var s=this.node().__on;if(s){for(var c=0,l=s.length,u;c<l;++c)for(i=0,u=s[c];i<a;++i)if((o=r[i]).type===u.type&&o.name===u.name)return u.value}}else{for(s=t?Or:Dr,i=0;i<a;++i)this.each(s(r[i],t,n));return this}}function Ar(e,t,n){var r=Bn(e),i=r.CustomEvent;typeof i==`function`?i=new i(t,n):(i=r.document.createEvent(`Event`),n?(i.initEvent(t,n.bubbles,n.cancelable),i.detail=n.detail):i.initEvent(t,!1,!1)),e.dispatchEvent(i)}function jr(e,t){return function(){return Ar(this,e,t)}}function Mr(e,t){return function(){return Ar(this,e,t.apply(this,arguments))}}function Nr(e,t){return this.each((typeof t==`function`?Mr:jr)(e,t))}function*Pr(){for(var e=this._groups,t=0,n=e.length;t<n;++t)for(var r=e[t],i=0,a=r.length,o;i<a;++i)(o=r[i])&&(yield o)}var Fr=[null];function j(e,t){this._groups=e,this._parents=t}function Ir(){return new j([[document.documentElement]],Fr)}function Lr(){return this}j.prototype=Ir.prototype={constructor:j,select:Jt,selectAll:$t,selectChild:on,selectChildren:un,filter:dn,data:yn,enter:pn,exit:xn,join:Sn,merge:Cn,selection:Lr,order:wn,sort:Tn,call:Dn,nodes:On,node:kn,size:An,empty:jn,each:Mn,attr:zn,style:Wn,property:Jn,classed:rr,text:sr,html:dr,raise:pr,lower:hr,append:gr,insert:vr,remove:br,clone:Cr,datum:wr,on:kr,dispatch:Nr,[Symbol.iterator]:Pr};function M(e){return typeof e==`string`?new j([[document.querySelector(e)]],[document.documentElement]):new j([[e]],Fr)}function Rr(e){let t;for(;t=e.sourceEvent;)e=t;return e}function N(e,t){if(e=Rr(e),t===void 0&&(t=e.currentTarget),t){var n=t.ownerSVGElement||t;if(n.createSVGPoint){var r=n.createSVGPoint();return r.x=e.clientX,r.y=e.clientY,r=r.matrixTransform(t.getScreenCTM().inverse()),[r.x,r.y]}if(t.getBoundingClientRect){var i=t.getBoundingClientRect();return[e.clientX-i.left-t.clientLeft,e.clientY-i.top-t.clientTop]}}return[e.pageX,e.pageY]}var zr={value:()=>{}};function Br(){for(var e=0,t=arguments.length,n={},r;e<t;++e){if(!(r=arguments[e]+``)||r in n||/[\s.]/.test(r))throw Error(`illegal type: `+r);n[r]=[]}return new Vr(n)}function Vr(e){this._=e}function Hr(e,t){return e.trim().split(/^|\s+/).map(function(e){var n=``,r=e.indexOf(`.`);if(r>=0&&(n=e.slice(r+1),e=e.slice(0,r)),e&&!t.hasOwnProperty(e))throw Error(`unknown type: `+e);return{type:e,name:n}})}Vr.prototype=Br.prototype={constructor:Vr,on:function(e,t){var n=this._,r=Hr(e+``,n),i,a=-1,o=r.length;if(arguments.length<2){for(;++a<o;)if((i=(e=r[a]).type)&&(i=Ur(n[i],e.name)))return i}else{if(t!=null&&typeof t!=`function`)throw Error(`invalid callback: `+t);for(;++a<o;)if(i=(e=r[a]).type)n[i]=Wr(n[i],e.name,t);else if(t==null)for(i in n)n[i]=Wr(n[i],e.name,null);return this}},copy:function(){var e={},t=this._;for(var n in t)e[n]=t[n].slice();return new Vr(e)},call:function(e,t){if((i=arguments.length-2)>0)for(var n=Array(i),r=0,i,a;r<i;++r)n[r]=arguments[r+2];if(!this._.hasOwnProperty(e))throw Error(`unknown type: `+e);for(a=this._[e],r=0,i=a.length;r<i;++r)a[r].value.apply(t,n)},apply:function(e,t,n){if(!this._.hasOwnProperty(e))throw Error(`unknown type: `+e);for(var r=this._[e],i=0,a=r.length;i<a;++i)r[i].value.apply(t,n)}};function Ur(e,t){for(var n=0,r=e.length,i;n<r;++n)if((i=e[n]).name===t)return i.value}function Wr(e,t,n){for(var r=0,i=e.length;r<i;++r)if(e[r].name===t){e[r]=zr,e=e.slice(0,r).concat(e.slice(r+1));break}return n!=null&&e.push({name:t,value:n}),e}var P=0,Gr=0,Kr=0,qr=1e3,Jr,Yr,Xr=0,F=0,Zr=0,I=typeof performance==`object`&&performance.now?performance:Date,Qr=typeof window==`object`&&window.requestAnimationFrame?window.requestAnimationFrame.bind(window):function(e){setTimeout(e,17)};function $r(){return F||=(Qr(ei),I.now()+Zr)}function ei(){F=0}function ti(){this._call=this._time=this._next=null}ti.prototype=ni.prototype={constructor:ti,restart:function(e,t,n){if(typeof e!=`function`)throw TypeError(`callback is not a function`);n=(n==null?$r():+n)+(t==null?0:+t),!this._next&&Yr!==this&&(Yr?Yr._next=this:Jr=this,Yr=this),this._call=e,this._time=n,si()},stop:function(){this._call&&(this._call=null,this._time=1/0,si())}};function ni(e,t,n){var r=new ti;return r.restart(e,t,n),r}function ri(){$r(),++P;for(var e=Jr,t;e;)(t=F-e._time)>=0&&e._call.call(void 0,t),e=e._next;--P}function ii(){F=(Xr=I.now())+Zr,P=Gr=0;try{ri()}finally{P=0,oi(),F=0}}function ai(){var e=I.now(),t=e-Xr;t>qr&&(Zr-=t,Xr=e)}function oi(){for(var e,t=Jr,n,r=1/0;t;)t._call?(r>t._time&&(r=t._time),e=t,t=t._next):(n=t._next,t._next=null,t=e?e._next=n:Jr=n);Yr=e,si(r)}function si(e){P||(Gr&&=clearTimeout(Gr),e-F>24?(e<1/0&&(Gr=setTimeout(ii,e-I.now()-Zr)),Kr&&=clearInterval(Kr)):(Kr||=(Xr=I.now(),setInterval(ai,qr)),P=1,Qr(ii)))}function ci(e,t,n){var r=new ti;return t=t==null?0:+t,r.restart(n=>{r.stop(),e(n+t)},t,n),r}var li=Br(`start`,`end`,`cancel`,`interrupt`),ui=[];function di(e,t,n,r,i,a){var o=e.__transition;if(!o)e.__transition={};else if(n in o)return;pi(e,n,{name:t,index:r,group:i,on:li,tween:ui,time:a.time,delay:a.delay,duration:a.duration,ease:a.ease,timer:null,state:0})}function fi(e,t){var n=R(e,t);if(n.state>0)throw Error(`too late; already scheduled`);return n}function L(e,t){var n=R(e,t);if(n.state>3)throw Error(`too late; already running`);return n}function R(e,t){var n=e.__transition;if(!n||!(n=n[t]))throw Error(`transition not found`);return n}function pi(e,t,n){var r=e.__transition,i;r[t]=n,n.timer=ni(a,0,n.time);function a(e){n.state=1,n.timer.restart(o,n.delay,n.time),n.delay<=e&&o(e-n.delay)}function o(a){var l,u,d,f;if(n.state!==1)return c();for(l in r)if(f=r[l],f.name===n.name){if(f.state===3)return ci(o);f.state===4?(f.state=6,f.timer.stop(),f.on.call(`interrupt`,e,e.__data__,f.index,f.group),delete r[l]):+l<t&&(f.state=6,f.timer.stop(),f.on.call(`cancel`,e,e.__data__,f.index,f.group),delete r[l])}if(ci(function(){n.state===3&&(n.state=4,n.timer.restart(s,n.delay,n.time),s(a))}),n.state=2,n.on.call(`start`,e,e.__data__,n.index,n.group),n.state===2){for(n.state=3,i=Array(d=n.tween.length),l=0,u=-1;l<d;++l)(f=n.tween[l].value.call(e,e.__data__,n.index,n.group))&&(i[++u]=f);i.length=u+1}}function s(t){for(var r=t<n.duration?n.ease.call(null,t/n.duration):(n.timer.restart(c),n.state=5,1),a=-1,o=i.length;++a<o;)i[a].call(e,r);n.state===5&&(n.on.call(`end`,e,e.__data__,n.index,n.group),c())}function c(){for(var i in n.state=6,n.timer.stop(),delete r[t],r)return;delete e.__transition}}function mi(e,t){var n=e.__transition,r,i,a=!0,o;if(n){for(o in t=t==null?null:t+``,n)(r=n[o]).name===t?(i=r.state>2&&r.state<5,r.state=6,r.timer.stop(),r.on.call(i?`interrupt`:`cancel`,e,e.__data__,r.index,r.group),delete n[o]):a=!1;a&&delete e.__transition}}function hi(e){return this.each(function(){mi(this,e)})}function gi(e,t,n){e.prototype=t.prototype=n,n.constructor=e}function _i(e,t){var n=Object.create(e.prototype);for(var r in t)n[r]=t[r];return n}function z(){}var B=.7,vi=1/B,V=`\\s*([+-]?\\d+)\\s*`,H=`\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)\\s*`,U=`\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)%\\s*`,yi=/^#([0-9a-f]{3,8})$/,bi=RegExp(`^rgb\\(${V},${V},${V}\\)$`),xi=RegExp(`^rgb\\(${U},${U},${U}\\)$`),Si=RegExp(`^rgba\\(${V},${V},${V},${H}\\)$`),Ci=RegExp(`^rgba\\(${U},${U},${U},${H}\\)$`),wi=RegExp(`^hsl\\(${H},${U},${U}\\)$`),Ti=RegExp(`^hsla\\(${H},${U},${U},${H}\\)$`),Ei={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074};gi(z,ji,{copy(e){return Object.assign(new this.constructor,this,e)},displayable(){return this.rgb().displayable()},hex:Di,formatHex:Di,formatHex8:Oi,formatHsl:ki,formatRgb:Ai,toString:Ai});function Di(){return this.rgb().formatHex()}function Oi(){return this.rgb().formatHex8()}function ki(){return Vi(this).formatHsl()}function Ai(){return this.rgb().formatRgb()}function ji(e){var t,n;return e=(e+``).trim().toLowerCase(),(t=yi.exec(e))?(n=t[1].length,t=parseInt(t[1],16),n===6?Mi(t):n===3?new W(t>>8&15|t>>4&240,t>>4&15|t&240,(t&15)<<4|t&15,1):n===8?Ni(t>>24&255,t>>16&255,t>>8&255,(t&255)/255):n===4?Ni(t>>12&15|t>>8&240,t>>8&15|t>>4&240,t>>4&15|t&240,((t&15)<<4|t&15)/255):null):(t=bi.exec(e))?new W(t[1],t[2],t[3],1):(t=xi.exec(e))?new W(t[1]*255/100,t[2]*255/100,t[3]*255/100,1):(t=Si.exec(e))?Ni(t[1],t[2],t[3],t[4]):(t=Ci.exec(e))?Ni(t[1]*255/100,t[2]*255/100,t[3]*255/100,t[4]):(t=wi.exec(e))?Bi(t[1],t[2]/100,t[3]/100,1):(t=Ti.exec(e))?Bi(t[1],t[2]/100,t[3]/100,t[4]):Ei.hasOwnProperty(e)?Mi(Ei[e]):e===`transparent`?new W(NaN,NaN,NaN,0):null}function Mi(e){return new W(e>>16&255,e>>8&255,e&255,1)}function Ni(e,t,n,r){return r<=0&&(e=t=n=NaN),new W(e,t,n,r)}function Pi(e){return e instanceof z||(e=ji(e)),e?(e=e.rgb(),new W(e.r,e.g,e.b,e.opacity)):new W}function Fi(e,t,n,r){return arguments.length===1?Pi(e):new W(e,t,n,r??1)}function W(e,t,n,r){this.r=+e,this.g=+t,this.b=+n,this.opacity=+r}gi(W,Fi,_i(z,{brighter(e){return e=e==null?vi:vi**+e,new W(this.r*e,this.g*e,this.b*e,this.opacity)},darker(e){return e=e==null?B:B**+e,new W(this.r*e,this.g*e,this.b*e,this.opacity)},rgb(){return this},clamp(){return new W(G(this.r),G(this.g),G(this.b),zi(this.opacity))},displayable(){return-.5<=this.r&&this.r<255.5&&-.5<=this.g&&this.g<255.5&&-.5<=this.b&&this.b<255.5&&0<=this.opacity&&this.opacity<=1},hex:Ii,formatHex:Ii,formatHex8:Li,formatRgb:Ri,toString:Ri}));function Ii(){return`#${K(this.r)}${K(this.g)}${K(this.b)}`}function Li(){return`#${K(this.r)}${K(this.g)}${K(this.b)}${K((isNaN(this.opacity)?1:this.opacity)*255)}`}function Ri(){let e=zi(this.opacity);return`${e===1?`rgb(`:`rgba(`}${G(this.r)}, ${G(this.g)}, ${G(this.b)}${e===1?`)`:`, ${e})`}`}function zi(e){return isNaN(e)?1:Math.max(0,Math.min(1,e))}function G(e){return Math.max(0,Math.min(255,Math.round(e)||0))}function K(e){return e=G(e),(e<16?`0`:``)+e.toString(16)}function Bi(e,t,n,r){return r<=0?e=t=n=NaN:n<=0||n>=1?e=t=NaN:t<=0&&(e=NaN),new q(e,t,n,r)}function Vi(e){if(e instanceof q)return new q(e.h,e.s,e.l,e.opacity);if(e instanceof z||(e=ji(e)),!e)return new q;if(e instanceof q)return e;e=e.rgb();var t=e.r/255,n=e.g/255,r=e.b/255,i=Math.min(t,n,r),a=Math.max(t,n,r),o=NaN,s=a-i,c=(a+i)/2;return s?(o=t===a?(n-r)/s+(n<r)*6:n===a?(r-t)/s+2:(t-n)/s+4,s/=c<.5?a+i:2-a-i,o*=60):s=c>0&&c<1?0:o,new q(o,s,c,e.opacity)}function Hi(e,t,n,r){return arguments.length===1?Vi(e):new q(e,t,n,r??1)}function q(e,t,n,r){this.h=+e,this.s=+t,this.l=+n,this.opacity=+r}gi(q,Hi,_i(z,{brighter(e){return e=e==null?vi:vi**+e,new q(this.h,this.s,this.l*e,this.opacity)},darker(e){return e=e==null?B:B**+e,new q(this.h,this.s,this.l*e,this.opacity)},rgb(){var e=this.h%360+(this.h<0)*360,t=isNaN(e)||isNaN(this.s)?0:this.s,n=this.l,r=n+(n<.5?n:1-n)*t,i=2*n-r;return new W(Gi(e>=240?e-240:e+120,i,r),Gi(e,i,r),Gi(e<120?e+240:e-120,i,r),this.opacity)},clamp(){return new q(Ui(this.h),Wi(this.s),Wi(this.l),zi(this.opacity))},displayable(){return(0<=this.s&&this.s<=1||isNaN(this.s))&&0<=this.l&&this.l<=1&&0<=this.opacity&&this.opacity<=1},formatHsl(){let e=zi(this.opacity);return`${e===1?`hsl(`:`hsla(`}${Ui(this.h)}, ${Wi(this.s)*100}%, ${Wi(this.l)*100}%${e===1?`)`:`, ${e})`}`}}));function Ui(e){return e=(e||0)%360,e<0?e+360:e}function Wi(e){return Math.max(0,Math.min(1,e||0))}function Gi(e,t,n){return(e<60?t+(n-t)*e/60:e<180?n:e<240?t+(n-t)*(240-e)/60:t)*255}var Ki=e=>()=>e;function qi(e,t){return function(n){return e+n*t}}function Ji(e,t,n){return e**=+n,t=t**+n-e,n=1/n,function(r){return(e+r*t)**+n}}function Yi(e){return(e=+e)==1?Xi:function(t,n){return n-t?Ji(t,n,e):Ki(isNaN(t)?n:t)}}function Xi(e,t){var n=t-e;return n?qi(e,n):Ki(isNaN(e)?t:e)}var Zi=(function e(t){var n=Yi(t);function r(e,t){var r=n((e=Fi(e)).r,(t=Fi(t)).r),i=n(e.g,t.g),a=n(e.b,t.b),o=Xi(e.opacity,t.opacity);return function(t){return e.r=r(t),e.g=i(t),e.b=a(t),e.opacity=o(t),e+``}}return r.gamma=e,r})(1);function J(e,t){return e=+e,t=+t,function(n){return e*(1-n)+t*n}}var Qi=/[-+]?(?:\d+\.?\d*|\.?\d+)(?:[eE][-+]?\d+)?/g,$i=new RegExp(Qi.source,`g`);function ea(e){return function(){return e}}function ta(e){return function(t){return e(t)+``}}function na(e,t){var n=Qi.lastIndex=$i.lastIndex=0,r,i,a,o=-1,s=[],c=[];for(e+=``,t+=``;(r=Qi.exec(e))&&(i=$i.exec(t));)(a=i.index)>n&&(a=t.slice(n,a),s[o]?s[o]+=a:s[++o]=a),(r=r[0])===(i=i[0])?s[o]?s[o]+=i:s[++o]=i:(s[++o]=null,c.push({i:o,x:J(r,i)})),n=$i.lastIndex;return n<t.length&&(a=t.slice(n),s[o]?s[o]+=a:s[++o]=a),s.length<2?c[0]?ta(c[0].x):ea(t):(t=c.length,function(e){for(var n=0,r;n<t;++n)s[(r=c[n]).i]=r.x(e);return s.join(``)})}var ra=180/Math.PI,ia={translateX:0,translateY:0,rotate:0,skewX:0,scaleX:1,scaleY:1};function aa(e,t,n,r,i,a){var o,s,c;return(o=Math.sqrt(e*e+t*t))&&(e/=o,t/=o),(c=e*n+t*r)&&(n-=e*c,r-=t*c),(s=Math.sqrt(n*n+r*r))&&(n/=s,r/=s,c/=s),e*r<t*n&&(e=-e,t=-t,c=-c,o=-o),{translateX:i,translateY:a,rotate:Math.atan2(t,e)*ra,skewX:Math.atan(c)*ra,scaleX:o,scaleY:s}}var oa;function sa(e){let t=new(typeof DOMMatrix==`function`?DOMMatrix:WebKitCSSMatrix)(e+``);return t.isIdentity?ia:aa(t.a,t.b,t.c,t.d,t.e,t.f)}function ca(e){return e==null||(oa||=document.createElementNS(`http://www.w3.org/2000/svg`,`g`),oa.setAttribute(`transform`,e),!(e=oa.transform.baseVal.consolidate()))?ia:(e=e.matrix,aa(e.a,e.b,e.c,e.d,e.e,e.f))}function la(e,t,n,r){function i(e){return e.length?e.pop()+` `:``}function a(e,r,i,a,o,s){if(e!==i||r!==a){var c=o.push(`translate(`,null,t,null,n);s.push({i:c-4,x:J(e,i)},{i:c-2,x:J(r,a)})}else(i||a)&&o.push(`translate(`+i+t+a+n)}function o(e,t,n,a){e===t?t&&n.push(i(n)+`rotate(`+t+r):(e-t>180?t+=360:t-e>180&&(e+=360),a.push({i:n.push(i(n)+`rotate(`,null,r)-2,x:J(e,t)}))}function s(e,t,n,a){e===t?t&&n.push(i(n)+`skewX(`+t+r):a.push({i:n.push(i(n)+`skewX(`,null,r)-2,x:J(e,t)})}function c(e,t,n,r,a,o){if(e!==n||t!==r){var s=a.push(i(a)+`scale(`,null,`,`,null,`)`);o.push({i:s-4,x:J(e,n)},{i:s-2,x:J(t,r)})}else(n!==1||r!==1)&&a.push(i(a)+`scale(`+n+`,`+r+`)`)}return function(t,n){var r=[],i=[];return t=e(t),n=e(n),a(t.translateX,t.translateY,n.translateX,n.translateY,r,i),o(t.rotate,n.rotate,r,i),s(t.skewX,n.skewX,r,i),c(t.scaleX,t.scaleY,n.scaleX,n.scaleY,r,i),t=n=null,function(e){for(var t=-1,n=i.length,a;++t<n;)r[(a=i[t]).i]=a.x(e);return r.join(``)}}}var ua=la(sa,`px, `,`px)`,`deg)`),da=la(ca,`, `,`)`,`)`),fa=1e-12;function pa(e){return((e=Math.exp(e))+1/e)/2}function ma(e){return((e=Math.exp(e))-1/e)/2}function ha(e){return((e=Math.exp(2*e))-1)/(e+1)}var ga=(function e(t,n,r){function i(e,i){var a=e[0],o=e[1],s=e[2],c=i[0],l=i[1],u=i[2],d=c-a,f=l-o,p=d*d+f*f,m,h;if(p<fa)h=Math.log(u/s)/t,m=function(e){return[a+e*d,o+e*f,s*Math.exp(t*e*h)]};else{var g=Math.sqrt(p),_=(u*u-s*s+r*p)/(2*s*n*g),v=(u*u-s*s-r*p)/(2*u*n*g),y=Math.log(Math.sqrt(_*_+1)-_);h=(Math.log(Math.sqrt(v*v+1)-v)-y)/t,m=function(e){var r=e*h,i=pa(y),c=s/(n*g)*(i*ha(t*r+y)-ma(y));return[a+c*d,o+c*f,s*i/pa(t*r+y)]}}return m.duration=h*1e3*t/Math.SQRT2,m}return i.rho=function(t){var n=Math.max(.001,+t),r=n*n;return e(n,r,r*r)},i})(Math.SQRT2,2,4);function _a(e,t){var n,r;return function(){var i=L(this,e),a=i.tween;if(a!==n){r=n=a;for(var o=0,s=r.length;o<s;++o)if(r[o].name===t){r=r.slice(),r.splice(o,1);break}}i.tween=r}}function va(e,t,n){var r,i;if(typeof n!=`function`)throw Error();return function(){var a=L(this,e),o=a.tween;if(o!==r){i=(r=o).slice();for(var s={name:t,value:n},c=0,l=i.length;c<l;++c)if(i[c].name===t){i[c]=s;break}c===l&&i.push(s)}a.tween=i}}function ya(e,t){var n=this._id;if(e+=``,arguments.length<2){for(var r=R(this.node(),n).tween,i=0,a=r.length,o;i<a;++i)if((o=r[i]).name===e)return o.value;return null}return this.each((t==null?_a:va)(n,e,t))}function ba(e,t,n){var r=e._id;return e.each(function(){var e=L(this,r);(e.value||={})[t]=n.apply(this,arguments)}),function(e){return R(e,r).value[t]}}function xa(e,t){var n;return(typeof t==`number`?J:t instanceof ji?Zi:(n=ji(t))?(t=n,Zi):na)(e,t)}function Sa(e){return function(){this.removeAttribute(e)}}function Ca(e){return function(){this.removeAttributeNS(e.space,e.local)}}function wa(e,t,n){var r,i=n+``,a;return function(){var o=this.getAttribute(e);return o===i?null:o===r?a:a=t(r=o,n)}}function Ta(e,t,n){var r,i=n+``,a;return function(){var o=this.getAttributeNS(e.space,e.local);return o===i?null:o===r?a:a=t(r=o,n)}}function Ea(e,t,n){var r,i,a;return function(){var o,s=n(this),c;return s==null?void this.removeAttribute(e):(o=this.getAttribute(e),c=s+``,o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s)))}}function Da(e,t,n){var r,i,a;return function(){var o,s=n(this),c;return s==null?void this.removeAttributeNS(e.space,e.local):(o=this.getAttributeNS(e.space,e.local),c=s+``,o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s)))}}function Oa(e,t){var n=Ht(e),r=n===`transform`?da:xa;return this.attrTween(e,typeof t==`function`?(n.local?Da:Ea)(n,r,ba(this,`attr.`+e,t)):t==null?(n.local?Ca:Sa)(n):(n.local?Ta:wa)(n,r,t))}function ka(e,t){return function(n){this.setAttribute(e,t.call(this,n))}}function Aa(e,t){return function(n){this.setAttributeNS(e.space,e.local,t.call(this,n))}}function ja(e,t){var n,r;function i(){var i=t.apply(this,arguments);return i!==r&&(n=(r=i)&&Aa(e,i)),n}return i._value=t,i}function Ma(e,t){var n,r;function i(){var i=t.apply(this,arguments);return i!==r&&(n=(r=i)&&ka(e,i)),n}return i._value=t,i}function Na(e,t){var n=`attr.`+e;if(arguments.length<2)return(n=this.tween(n))&&n._value;if(t==null)return this.tween(n,null);if(typeof t!=`function`)throw Error();var r=Ht(e);return this.tween(n,(r.local?ja:Ma)(r,t))}function Pa(e,t){return function(){fi(this,e).delay=+t.apply(this,arguments)}}function Fa(e,t){return t=+t,function(){fi(this,e).delay=t}}function Ia(e){var t=this._id;return arguments.length?this.each((typeof e==`function`?Pa:Fa)(t,e)):R(this.node(),t).delay}function La(e,t){return function(){L(this,e).duration=+t.apply(this,arguments)}}function Ra(e,t){return t=+t,function(){L(this,e).duration=t}}function za(e){var t=this._id;return arguments.length?this.each((typeof e==`function`?La:Ra)(t,e)):R(this.node(),t).duration}function Ba(e,t){if(typeof t!=`function`)throw Error();return function(){L(this,e).ease=t}}function Va(e){var t=this._id;return arguments.length?this.each(Ba(t,e)):R(this.node(),t).ease}function Ha(e,t){return function(){var n=t.apply(this,arguments);if(typeof n!=`function`)throw Error();L(this,e).ease=n}}function Ua(e){if(typeof e!=`function`)throw Error();return this.each(Ha(this._id,e))}function Wa(e){typeof e!=`function`&&(e=en(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=[],c,l=0;l<o;++l)(c=a[l])&&e.call(c,c.__data__,l,a)&&s.push(c);return new Y(r,this._parents,this._name,this._id)}function Ga(e){if(e._id!==this._id)throw Error();for(var t=this._groups,n=e._groups,r=t.length,i=n.length,a=Math.min(r,i),o=Array(r),s=0;s<a;++s)for(var c=t[s],l=n[s],u=c.length,d=o[s]=Array(u),f,p=0;p<u;++p)(f=c[p]||l[p])&&(d[p]=f);for(;s<r;++s)o[s]=t[s];return new Y(o,this._parents,this._name,this._id)}function Ka(e){return(e+``).trim().split(/^|\s+/).every(function(e){var t=e.indexOf(`.`);return t>=0&&(e=e.slice(0,t)),!e||e===`start`})}function qa(e,t,n){var r,i,a=Ka(t)?fi:L;return function(){var o=a(this,e),s=o.on;s!==r&&(i=(r=s).copy()).on(t,n),o.on=i}}function Ja(e,t){var n=this._id;return arguments.length<2?R(this.node(),n).on.on(e):this.each(qa(n,e,t))}function Ya(e){return function(){var t=this.parentNode;for(var n in this.__transition)if(+n!==e)return;t&&t.removeChild(this)}}function Xa(){return this.on(`end.remove`,Ya(this._id))}function Za(e){var t=this._name,n=this._id;typeof e!=`function`&&(e=qt(e));for(var r=this._groups,i=r.length,a=Array(i),o=0;o<i;++o)for(var s=r[o],c=s.length,l=a[o]=Array(c),u,d,f=0;f<c;++f)(u=s[f])&&(d=e.call(u,u.__data__,f,s))&&(`__data__`in u&&(d.__data__=u.__data__),l[f]=d,di(l[f],t,n,f,l,R(u,n)));return new Y(a,this._parents,t,n)}function Qa(e){var t=this._name,n=this._id;typeof e!=`function`&&(e=Zt(e));for(var r=this._groups,i=r.length,a=[],o=[],s=0;s<i;++s)for(var c=r[s],l=c.length,u,d=0;d<l;++d)if(u=c[d]){for(var f=e.call(u,u.__data__,d,c),p,m=R(u,n),h=0,g=f.length;h<g;++h)(p=f[h])&&di(p,t,n,h,f,m);a.push(f),o.push(u)}return new Y(a,o,t,n)}var $a=Ir.prototype.constructor;function eo(){return new $a(this._groups,this._parents)}function to(e,t){var n,r,i;return function(){var a=A(this,e),o=(this.style.removeProperty(e),A(this,e));return a===o?null:a===n&&o===r?i:i=t(n=a,r=o)}}function no(e){return function(){this.style.removeProperty(e)}}function ro(e,t,n){var r,i=n+``,a;return function(){var o=A(this,e);return o===i?null:o===r?a:a=t(r=o,n)}}function io(e,t,n){var r,i,a;return function(){var o=A(this,e),s=n(this),c=s+``;return s??(c=s=(this.style.removeProperty(e),A(this,e))),o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s))}}function ao(e,t){var n,r,i,a=`style.`+t,o=`end.`+a,s;return function(){var c=L(this,e),l=c.on,u=c.value[a]==null?s||=no(t):void 0;(l!==n||i!==u)&&(r=(n=l).copy()).on(o,i=u),c.on=r}}function oo(e,t,n){var r=(e+=``)==`transform`?ua:xa;return t==null?this.styleTween(e,to(e,r)).on(`end.style.`+e,no(e)):typeof t==`function`?this.styleTween(e,io(e,r,ba(this,`style.`+e,t))).each(ao(this._id,e)):this.styleTween(e,ro(e,r,t),n).on(`end.style.`+e,null)}function so(e,t,n){return function(r){this.style.setProperty(e,t.call(this,r),n)}}function co(e,t,n){var r,i;function a(){var a=t.apply(this,arguments);return a!==i&&(r=(i=a)&&so(e,a,n)),r}return a._value=t,a}function lo(e,t,n){var r=`style.`+(e+=``);if(arguments.length<2)return(r=this.tween(r))&&r._value;if(t==null)return this.tween(r,null);if(typeof t!=`function`)throw Error();return this.tween(r,co(e,t,n??``))}function uo(e){return function(){this.textContent=e}}function fo(e){return function(){var t=e(this);this.textContent=t??``}}function po(e){return this.tween(`text`,typeof e==`function`?fo(ba(this,`text`,e)):uo(e==null?``:e+``))}function mo(e){return function(t){this.textContent=e.call(this,t)}}function ho(e){var t,n;function r(){var r=e.apply(this,arguments);return r!==n&&(t=(n=r)&&mo(r)),t}return r._value=e,r}function go(e){var t=`text`;if(arguments.length<1)return(t=this.tween(t))&&t._value;if(e==null)return this.tween(t,null);if(typeof e!=`function`)throw Error();return this.tween(t,ho(e))}function _o(){for(var e=this._name,t=this._id,n=bo(),r=this._groups,i=r.length,a=0;a<i;++a)for(var o=r[a],s=o.length,c,l=0;l<s;++l)if(c=o[l]){var u=R(c,t);di(c,e,n,l,o,{time:u.time+u.delay+u.duration,delay:0,duration:u.duration,ease:u.ease})}return new Y(r,this._parents,e,n)}function vo(){var e,t,n=this,r=n._id,i=n.size();return new Promise(function(a,o){var s={value:o},c={value:function(){--i===0&&a()}};n.each(function(){var n=L(this,r),i=n.on;i!==e&&(t=(e=i).copy(),t._.cancel.push(s),t._.interrupt.push(s),t._.end.push(c)),n.on=t}),i===0&&a()})}var yo=0;function Y(e,t,n,r){this._groups=e,this._parents=t,this._name=n,this._id=r}function bo(){return++yo}var X=Ir.prototype;Y.prototype={constructor:Y,select:Za,selectAll:Qa,selectChild:X.selectChild,selectChildren:X.selectChildren,filter:Wa,merge:Ga,selection:eo,transition:_o,call:X.call,nodes:X.nodes,node:X.node,size:X.size,empty:X.empty,each:X.each,on:Ja,attr:Oa,attrTween:Na,style:oo,styleTween:lo,text:po,textTween:go,remove:Xa,tween:ya,delay:Ia,duration:za,ease:Va,easeVarying:Ua,end:vo,[Symbol.iterator]:X[Symbol.iterator]};function xo(e){return((e*=2)<=1?e*e*e:(e-=2)*e*e+2)/2}var So={time:null,delay:0,duration:250,ease:xo};function Co(e,t){for(var n;!(n=e.__transition)||!(n=n[t]);)if(!(e=e.parentNode))throw Error(`transition ${t} not found`);return n}function wo(e){var t,n;e instanceof Y?(t=e._id,e=e._name):(t=bo(),(n=So).time=$r(),e=e==null?null:e+``);for(var r=this._groups,i=r.length,a=0;a<i;++a)for(var o=r[a],s=o.length,c,l=0;l<s;++l)(c=o[l])&&di(c,e,t,l,o,n||Co(c,t));return new Y(r,this._parents,e,t)}Ir.prototype.interrupt=hi,Ir.prototype.transition=wo;var To={capture:!0,passive:!1};function Eo(e){e.preventDefault(),e.stopImmediatePropagation()}function Do(e){var t=e.document.documentElement,n=M(e).on(`dragstart.drag`,Eo,To);`onselectstart`in t?n.on(`selectstart.drag`,Eo,To):(t.__noselect=t.style.MozUserSelect,t.style.MozUserSelect=`none`)}function Oo(e,t){var n=e.document.documentElement,r=M(e).on(`dragstart.drag`,null);t&&(r.on(`click.drag`,Eo,To),setTimeout(function(){r.on(`click.drag`,null)},0)),`onselectstart`in n?r.on(`selectstart.drag`,null):(n.style.MozUserSelect=n.__noselect,delete n.__noselect)}var ko=e=>()=>e;function Ao(e,{sourceEvent:t,target:n,transform:r,dispatch:i}){Object.defineProperties(this,{type:{value:e,enumerable:!0,configurable:!0},sourceEvent:{value:t,enumerable:!0,configurable:!0},target:{value:n,enumerable:!0,configurable:!0},transform:{value:r,enumerable:!0,configurable:!0},_:{value:i}})}function Z(e,t,n){this.k=e,this.x=t,this.y=n}Z.prototype={constructor:Z,scale:function(e){return e===1?this:new Z(this.k*e,this.x,this.y)},translate:function(e,t){return e===0&t===0?this:new Z(this.k,this.x+this.k*e,this.y+this.k*t)},apply:function(e){return[e[0]*this.k+this.x,e[1]*this.k+this.y]},applyX:function(e){return e*this.k+this.x},applyY:function(e){return e*this.k+this.y},invert:function(e){return[(e[0]-this.x)/this.k,(e[1]-this.y)/this.k]},invertX:function(e){return(e-this.x)/this.k},invertY:function(e){return(e-this.y)/this.k},rescaleX:function(e){return e.copy().domain(e.range().map(this.invertX,this).map(e.invert,e))},rescaleY:function(e){return e.copy().domain(e.range().map(this.invertY,this).map(e.invert,e))},toString:function(){return`translate(`+this.x+`,`+this.y+`) scale(`+this.k+`)`}};var jo=new Z(1,0,0);Mo.prototype=Z.prototype;function Mo(e){for(;!e.__zoom;)if(!(e=e.parentNode))return jo;return e.__zoom}function No(e){e.stopImmediatePropagation()}function Po(e){e.preventDefault(),e.stopImmediatePropagation()}function Fo(e){return(!e.ctrlKey||e.type===`wheel`)&&!e.button}function Io(){var e=this;return e instanceof SVGElement?(e=e.ownerSVGElement||e,e.hasAttribute(`viewBox`)?(e=e.viewBox.baseVal,[[e.x,e.y],[e.x+e.width,e.y+e.height]]):[[0,0],[e.width.baseVal.value,e.height.baseVal.value]]):[[0,0],[e.clientWidth,e.clientHeight]]}function Lo(){return this.__zoom||jo}function Ro(e){return-e.deltaY*(e.deltaMode===1?.05:e.deltaMode?1:.002)*(e.ctrlKey?10:1)}function zo(){return navigator.maxTouchPoints||`ontouchstart`in this}function Bo(e,t,n){var r=e.invertX(t[0][0])-n[0][0],i=e.invertX(t[1][0])-n[1][0],a=e.invertY(t[0][1])-n[0][1],o=e.invertY(t[1][1])-n[1][1];return e.translate(i>r?(r+i)/2:Math.min(0,r)||Math.max(0,i),o>a?(a+o)/2:Math.min(0,a)||Math.max(0,o))}function Vo(){var e=Fo,t=Io,n=Bo,r=Ro,i=zo,a=[0,1/0],o=[[-1/0,-1/0],[1/0,1/0]],s=250,c=ga,l=Br(`start`,`zoom`,`end`),u,d,f,p=500,m=150,h=0,g=10;function _(e){e.property(`__zoom`,Lo).on(`wheel.zoom`,ee,{passive:!1}).on(`mousedown.zoom`,te).on(`dblclick.zoom`,ne).filter(i).on(`touchstart.zoom`,w).on(`touchmove.zoom`,re).on(`touchend.zoom touchcancel.zoom`,ie).style(`-webkit-tap-highlight-color`,`rgba(0,0,0,0)`)}_.transform=function(e,t,n,r){var i=e.selection?e.selection():e;i.property(`__zoom`,Lo),e===i?i.interrupt().each(function(){S(this,arguments).event(r).start().zoom(null,typeof t==`function`?t.apply(this,arguments):t).end()}):x(e,t,n,r)},_.scaleBy=function(e,t,n,r){_.scaleTo(e,function(){return this.__zoom.k*(typeof t==`function`?t.apply(this,arguments):t)},n,r)},_.scaleTo=function(e,r,i,a){_.transform(e,function(){var e=t.apply(this,arguments),a=this.__zoom,s=i==null?b(e):typeof i==`function`?i.apply(this,arguments):i,c=a.invert(s),l=typeof r==`function`?r.apply(this,arguments):r;return n(y(v(a,l),s,c),e,o)},i,a)},_.translateBy=function(e,r,i,a){_.transform(e,function(){return n(this.__zoom.translate(typeof r==`function`?r.apply(this,arguments):r,typeof i==`function`?i.apply(this,arguments):i),t.apply(this,arguments),o)},null,a)},_.translateTo=function(e,r,i,a,s){_.transform(e,function(){var e=t.apply(this,arguments),s=this.__zoom,c=a==null?b(e):typeof a==`function`?a.apply(this,arguments):a;return n(jo.translate(c[0],c[1]).scale(s.k).translate(typeof r==`function`?-r.apply(this,arguments):-r,typeof i==`function`?-i.apply(this,arguments):-i),e,o)},a,s)};function v(e,t){return t=Math.max(a[0],Math.min(a[1],t)),t===e.k?e:new Z(t,e.x,e.y)}function y(e,t,n){var r=t[0]-n[0]*e.k,i=t[1]-n[1]*e.k;return r===e.x&&i===e.y?e:new Z(e.k,r,i)}function b(e){return[(+e[0][0]+ +e[1][0])/2,(+e[0][1]+ +e[1][1])/2]}function x(e,n,r,i){e.on(`start.zoom`,function(){S(this,arguments).event(i).start()}).on(`interrupt.zoom end.zoom`,function(){S(this,arguments).event(i).end()}).tween(`zoom`,function(){var e=this,a=arguments,o=S(e,a).event(i),s=t.apply(e,a),l=r==null?b(s):typeof r==`function`?r.apply(e,a):r,u=Math.max(s[1][0]-s[0][0],s[1][1]-s[0][1]),d=e.__zoom,f=typeof n==`function`?n.apply(e,a):n,p=c(d.invert(l).concat(u/d.k),f.invert(l).concat(u/f.k));return function(e){if(e===1)e=f;else{var t=p(e),n=u/t[2];e=new Z(n,l[0]-t[0]*n,l[1]-t[1]*n)}o.zoom(null,e)}})}function S(e,t,n){return!n&&e.__zooming||new C(e,t)}function C(e,n){this.that=e,this.args=n,this.active=0,this.sourceEvent=null,this.extent=t.apply(e,n),this.taps=0}C.prototype={event:function(e){return e&&(this.sourceEvent=e),this},start:function(){return++this.active===1&&(this.that.__zooming=this,this.emit(`start`)),this},zoom:function(e,t){return this.mouse&&e!==`mouse`&&(this.mouse[1]=t.invert(this.mouse[0])),this.touch0&&e!==`touch`&&(this.touch0[1]=t.invert(this.touch0[0])),this.touch1&&e!==`touch`&&(this.touch1[1]=t.invert(this.touch1[0])),this.that.__zoom=t,this.emit(`zoom`),this},end:function(){return--this.active===0&&(delete this.that.__zooming,this.emit(`end`)),this},emit:function(e){var t=M(this.that).datum();l.call(e,this.that,new Ao(e,{sourceEvent:this.sourceEvent,target:_,type:e,transform:this.that.__zoom,dispatch:l}),t)}};function ee(t,...i){if(!e.apply(this,arguments))return;var s=S(this,i).event(t),c=this.__zoom,l=Math.max(a[0],Math.min(a[1],c.k*2**r.apply(this,arguments))),u=N(t);if(s.wheel)(s.mouse[0][0]!==u[0]||s.mouse[0][1]!==u[1])&&(s.mouse[1]=c.invert(s.mouse[0]=u)),clearTimeout(s.wheel);else if(c.k===l)return;else s.mouse=[u,c.invert(u)],mi(this),s.start();Po(t),s.wheel=setTimeout(d,m),s.zoom(`mouse`,n(y(v(c,l),s.mouse[0],s.mouse[1]),s.extent,o));function d(){s.wheel=null,s.end()}}function te(t,...r){if(f||!e.apply(this,arguments))return;var i=t.currentTarget,a=S(this,r,!0).event(t),s=M(t.view).on(`mousemove.zoom`,d,!0).on(`mouseup.zoom`,p,!0),c=N(t,i),l=t.clientX,u=t.clientY;Do(t.view),No(t),a.mouse=[c,this.__zoom.invert(c)],mi(this),a.start();function d(e){if(Po(e),!a.moved){var t=e.clientX-l,r=e.clientY-u;a.moved=t*t+r*r>h}a.event(e).zoom(`mouse`,n(y(a.that.__zoom,a.mouse[0]=N(e,i),a.mouse[1]),a.extent,o))}function p(e){s.on(`mousemove.zoom mouseup.zoom`,null),Oo(e.view,a.moved),Po(e),a.event(e).end()}}function ne(r,...i){if(e.apply(this,arguments)){var a=this.__zoom,c=N(r.changedTouches?r.changedTouches[0]:r,this),l=a.invert(c),u=a.k*(r.shiftKey?.5:2),d=n(y(v(a,u),c,l),t.apply(this,i),o);Po(r),s>0?M(this).transition().duration(s).call(x,d,c,r):M(this).call(_.transform,d,c,r)}}function w(t,...n){if(e.apply(this,arguments)){var r=t.touches,i=r.length,a=S(this,n,t.changedTouches.length===i).event(t),o,s,c,l;for(No(t),s=0;s<i;++s)c=r[s],l=N(c,this),l=[l,this.__zoom.invert(l),c.identifier],a.touch0?!a.touch1&&a.touch0[2]!==l[2]&&(a.touch1=l,a.taps=0):(a.touch0=l,o=!0,a.taps=1+!!u);u&&=clearTimeout(u),o&&(a.taps<2&&(d=l[0],u=setTimeout(function(){u=null},p)),mi(this),a.start())}}function re(e,...t){if(this.__zooming){var r=S(this,t).event(e),i=e.changedTouches,a=i.length,s,c,l,u;for(Po(e),s=0;s<a;++s)c=i[s],l=N(c,this),r.touch0&&r.touch0[2]===c.identifier?r.touch0[0]=l:r.touch1&&r.touch1[2]===c.identifier&&(r.touch1[0]=l);if(c=r.that.__zoom,r.touch1){var d=r.touch0[0],f=r.touch0[1],p=r.touch1[0],m=r.touch1[1],h=(h=p[0]-d[0])*h+(h=p[1]-d[1])*h,g=(g=m[0]-f[0])*g+(g=m[1]-f[1])*g;c=v(c,Math.sqrt(h/g)),l=[(d[0]+p[0])/2,(d[1]+p[1])/2],u=[(f[0]+m[0])/2,(f[1]+m[1])/2]}else if(r.touch0)l=r.touch0[0],u=r.touch0[1];else return;r.zoom(`touch`,n(y(c,l,u),r.extent,o))}}function ie(e,...t){if(this.__zooming){var n=S(this,t).event(e),r=e.changedTouches,i=r.length,a,o;for(No(e),f&&clearTimeout(f),f=setTimeout(function(){f=null},p),a=0;a<i;++a)o=r[a],n.touch0&&n.touch0[2]===o.identifier?delete n.touch0:n.touch1&&n.touch1[2]===o.identifier&&delete n.touch1;if(n.touch1&&!n.touch0&&(n.touch0=n.touch1,delete n.touch1),n.touch0)n.touch0[1]=this.__zoom.invert(n.touch0[0]);else if(n.end(),n.taps===2&&(o=N(o,this),Math.hypot(d[0]-o[0],d[1]-o[1])<g)){var s=M(this).on(`dblclick.zoom`);s&&s.apply(this,arguments)}}}return _.wheelDelta=function(e){return arguments.length?(r=typeof e==`function`?e:ko(+e),_):r},_.filter=function(t){return arguments.length?(e=typeof t==`function`?t:ko(!!t),_):e},_.touchable=function(e){return arguments.length?(i=typeof e==`function`?e:ko(!!e),_):i},_.extent=function(e){return arguments.length?(t=typeof e==`function`?e:ko([[+e[0][0],+e[0][1]],[+e[1][0],+e[1][1]]]),_):t},_.scaleExtent=function(e){return arguments.length?(a[0]=+e[0],a[1]=+e[1],_):[a[0],a[1]]},_.translateExtent=function(e){return arguments.length?(o[0][0]=+e[0][0],o[1][0]=+e[1][0],o[0][1]=+e[0][1],o[1][1]=+e[1][1],_):[[o[0][0],o[0][1]],[o[1][0],o[1][1]]]},_.constrain=function(e){return arguments.length?(n=e,_):n},_.duration=function(e){return arguments.length?(s=+e,_):s},_.interpolate=function(e){return arguments.length?(c=e,_):c},_.on=function(){var e=l.on.apply(l,arguments);return e===l?_:e},_.clickDistance=function(e){return arguments.length?(h=(e=+e)*e,_):Math.sqrt(h)},_.tapDistance=function(e){return arguments.length?(g=+e,_):g},_}function Ho(e){var t=0,n=e.children,r=n&&n.length;if(!r)t=1;else for(;--r>=0;)t+=n[r].value;e.value=t}function Uo(){return this.eachAfter(Ho)}function Wo(e,t){let n=-1;for(let r of this)e.call(t,r,++n,this);return this}function Go(e,t){for(var n=this,r=[n],i,a,o=-1;n=r.pop();)if(e.call(t,n,++o,this),i=n.children)for(a=i.length-1;a>=0;--a)r.push(i[a]);return this}function Ko(e,t){for(var n=this,r=[n],i=[],a,o,s,c=-1;n=r.pop();)if(i.push(n),a=n.children)for(o=0,s=a.length;o<s;++o)r.push(a[o]);for(;n=i.pop();)e.call(t,n,++c,this);return this}function qo(e,t){let n=-1;for(let r of this)if(e.call(t,r,++n,this))return r}function Jo(e){return this.eachAfter(function(t){for(var n=+e(t.data)||0,r=t.children,i=r&&r.length;--i>=0;)n+=r[i].value;t.value=n})}function Yo(e){return this.eachBefore(function(t){t.children&&t.children.sort(e)})}function Xo(e){for(var t=this,n=Zo(t,e),r=[t];t!==n;)t=t.parent,r.push(t);for(var i=r.length;e!==n;)r.splice(i,0,e),e=e.parent;return r}function Zo(e,t){if(e===t)return e;var n=e.ancestors(),r=t.ancestors(),i=null;for(e=n.pop(),t=r.pop();e===t;)i=e,e=n.pop(),t=r.pop();return i}function Qo(){for(var e=this,t=[e];e=e.parent;)t.push(e);return t}function $o(){return Array.from(this)}function es(){var e=[];return this.eachBefore(function(t){t.children||e.push(t)}),e}function ts(){var e=this,t=[];return e.each(function(n){n!==e&&t.push({source:n.parent,target:n})}),t}function*ns(){var e=this,t,n=[e],r,i,a;do for(t=n.reverse(),n=[];e=t.pop();)if(yield e,r=e.children)for(i=0,a=r.length;i<a;++i)n.push(r[i]);while(n.length)}function rs(e,t){e instanceof Map?(e=[void 0,e],t===void 0&&(t=os)):t===void 0&&(t=as);for(var n=new ls(e),r,i=[n],a,o,s,c;r=i.pop();)if((o=t(r.data))&&(c=(o=Array.from(o)).length))for(r.children=o,s=c-1;s>=0;--s)i.push(a=o[s]=new ls(o[s])),a.parent=r,a.depth=r.depth+1;return n.eachBefore(cs)}function is(){return rs(this).eachBefore(ss)}function as(e){return e.children}function os(e){return Array.isArray(e)?e[1]:null}function ss(e){e.data.value!==void 0&&(e.value=e.data.value),e.data=e.data.data}function cs(e){var t=0;do e.height=t;while((e=e.parent)&&e.height<++t)}function ls(e){this.data=e,this.depth=this.height=0,this.parent=null}ls.prototype=rs.prototype={constructor:ls,count:Uo,each:Wo,eachAfter:Ko,eachBefore:Go,find:qo,sum:Jo,sort:Yo,path:Xo,ancestors:Qo,descendants:$o,leaves:es,links:ts,copy:is,[Symbol.iterator]:ns};function us(e,t){return e.parent===t.parent?1:2}function ds(e){var t=e.children;return t?t[0]:e.t}function fs(e){var t=e.children;return t?t[t.length-1]:e.t}function ps(e,t,n){var r=n/(t.i-e.i);t.c-=r,t.s+=n,e.c+=r,t.z+=n,t.m+=n}function ms(e){for(var t=0,n=0,r=e.children,i=r.length,a;--i>=0;)a=r[i],a.z+=t,a.m+=t,t+=a.s+(n+=a.c)}function hs(e,t,n){return e.a.parent===t.parent?e.a:n}function gs(e,t){this._=e,this.parent=null,this.children=null,this.A=null,this.a=this,this.z=0,this.m=0,this.c=0,this.s=0,this.t=null,this.i=t}gs.prototype=Object.create(ls.prototype);function _s(e){for(var t=new gs(e,0),n,r=[t],i,a,o,s;n=r.pop();)if(a=n._.children)for(n.children=Array(s=a.length),o=s-1;o>=0;--o)r.push(i=n.children[o]=new gs(a[o],o)),i.parent=n;return(t.parent=new gs(null,0)).children=[t],t}function vs(){var e=us,t=1,n=1,r=null;function i(i){var s=_s(i);if(s.eachAfter(a),s.parent.m=-s.z,s.eachBefore(o),r)i.eachBefore(c);else{var l=i,u=i,d=i;i.eachBefore(function(e){e.x<l.x&&(l=e),e.x>u.x&&(u=e),e.depth>d.depth&&(d=e)});var f=l===u?1:e(l,u)/2,p=f-l.x,m=t/(u.x+f+p),h=n/(d.depth||1);i.eachBefore(function(e){e.x=(e.x+p)*m,e.y=e.depth*h})}return i}function a(t){var n=t.children,r=t.parent.children,i=t.i?r[t.i-1]:null;if(n){ms(t);var a=(n[0].z+n[n.length-1].z)/2;i?(t.z=i.z+e(t._,i._),t.m=t.z-a):t.z=a}else i&&(t.z=i.z+e(t._,i._));t.parent.A=s(t,i,t.parent.A||r[0])}function o(e){e._.x=e.z+e.parent.m,e.m+=e.parent.m}function s(t,n,r){if(n){for(var i=t,a=t,o=n,s=i.parent.children[0],c=i.m,l=a.m,u=o.m,d=s.m,f;o=fs(o),i=ds(i),o&&i;)s=ds(s),a=fs(a),a.a=t,f=o.z+u-i.z-c+e(o._,i._),f>0&&(ps(hs(o,t,r),t,f),c+=f,l+=f),u+=o.m,c+=i.m,d+=s.m,l+=a.m;o&&!fs(a)&&(a.t=o,a.m+=u-l),i&&!ds(s)&&(s.t=i,s.m+=c-d,r=t)}return r}function c(e){e.x*=t,e.y=e.depth*n}return i.separation=function(t){return arguments.length?(e=t,i):e},i.size=function(e){return arguments.length?(r=!1,t=+e[0],n=+e[1],i):r?null:[t,n]},i.nodeSize=function(e){return arguments.length?(r=!0,t=+e[0],n=+e[1],i):r?[t,n]:null},i}var ys={comfortable:{breadth:132,depth:150},compact:{breadth:92,depth:112}},bs=`\0root`,xs=()=>({positions:new Map,bounds:{minX:0,minY:0,maxX:0,maxY:0}}),Ss=(e,t,n)=>n===`vertical`?{x:e,y:t}:{x:t,y:e};function Cs(e){let t={minX:1/0,minY:1/0,maxX:-1/0,maxY:-1/0};for(let n of e.values())t.minX=Math.min(t.minX,n.x),t.minY=Math.min(t.minY,n.y),t.maxX=Math.max(t.maxX,n.x),t.maxY=Math.max(t.maxY,n.y);return{positions:e,bounds:t}}function ws(e,t,n,r=`tree`){return r===`tiered`?ks(e,t,n):Ts(e,t,n)}function Ts(e,t,n){if(e.roots.length===0)return xs();let{breadth:r,depth:i}=ys[t],a=rs(bs,t=>t===bs?e.roots:e.children.get(t)),o=vs().nodeSize([r,i]).separation((e,t)=>e.parent===t.parent?1:1.25)(a),s=new Map;for(let e of o.descendants())e.data!==bs&&s.set(e.data,Ss(e.x,(e.depth-1)*i,n));return Cs(s)}var Es={gateway:0,switch:1,access_point:2,other:3,client:4},Ds=Es.client+1,Os=e=>e.type===`group`?Es.client:Es[e.node.kind]??Es.other;function ks(e,t,n){if(e.roots.length===0)return xs();let{breadth:r,depth:i}=ys[t],a=new Map,o=[...e.roots].reverse(),s=[],c=Array(Ds).fill(0);for(;o.length>0;){let t=o.pop();s.push(t);let n=Os(e.visuals.get(t)),r=e.parentOf.get(t),i=r===void 0?void 0:a.get(r),l=Math.max(n,i?.tier??n),u={tier:l,sub:i?.tier===l?i.sub+1:0};a.set(t,u),c[u.tier]=Math.max(c[u.tier],u.sub+1),o.push(...[...e.children.get(t)??[]].reverse())}let l=[],u=0;for(let e of c)l.push(u),u+=e;let d=Array.from({length:u},()=>[]);for(let e of s){let{tier:t,sub:n}=a.get(e);d[l[t]+n].push(e)}let f=new Map;return d.forEach((e,t)=>{e.forEach((a,o)=>{let s=(o-(e.length-1)/2)*r;f.set(a,Ss(s,t*i,n))})}),Cs(f)}function As(e,t,n,r=48){let i=Math.max(e.maxX-e.minX,1),a=Math.max(e.maxY-e.minY,1),o=Math.min(1.5,Math.max(.2,Math.min((t-2*r)/i,(n-2*r)/a))),s=(e.minX+e.maxX)/2,c=(e.minY+e.maxY)/2;return{k:o,x:t/2-s*o,y:n/2-c*o}}function js(e,t,n,r,i=120){let a=new Set;for(let[o,s]of e.positions){let e=s.x*t.k+t.x,c=s.y*t.k+t.y;e>=-i&&e<=n+i&&c>=-i&&c<=r+i&&a.add(o)}return a}function Ms(e,t,n,r){let i=r===`vertical`,a={parent:i?`ArrowUp`:`ArrowLeft`,child:i?`ArrowDown`:`ArrowRight`,previous:i?`ArrowLeft`:`ArrowUp`,next:i?`ArrowRight`:`ArrowDown`};if(!Object.values(a).includes(n))return;if(t===void 0||!e.visuals.has(t))return e.roots[0];let o=st(e,t),s=o.indexOf(t);switch(n){case a.parent:return e.parentOf.get(t)??t;case a.child:return e.children.get(t)?.[0]??t;case a.previous:return o[s-1]??t;default:return o[s+1]??t}}var Ns={comfortable:22,compact:16},Ps=250,Fs=22;function Is(e,t){if(e.type===`wheel`){let n=e;return t&&!n.ctrlKey&&!n.metaKey?`hint`:`zoom`}let n=e;return n.ctrlKey||(n.button??0)!==0?`ignore`:`zoom`}var Ls=class extends T{static properties={model:{attribute:!1},density:{attribute:!1},orientation:{attribute:!1},layoutMode:{attribute:!1},showLabels:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},siteName:{attribute:!1},ctrlZoom:{attribute:!1},reducedMotion:{attribute:!1},focusId:{state:!0},hintVisible:{state:!0}};layout;entering=new Set;exiting=new Map;lastVisuals=new Map;exitTimer;hintTimer;transform={x:0,y:0,k:1};width=0;height=0;fitted=!1;zoomBehavior;resizeObserver;gesture=new Bt;constructor(){super(),this.density=`comfortable`,this.orientation=`vertical`,this.layoutMode=`tree`,this.showLabels=!0,this.siteName=``,this.ctrlZoom=!0,this.reducedMotion=!1,this.hintVisible=!1}connectedCallback(){super.connectedCallback(),this.resizeObserver=new ResizeObserver(e=>{let t=e[0]?.contentRect;t&&this.setViewportSize(t.width,t.height)}),this.resizeObserver.observe(this)}disconnectedCallback(){super.disconnectedCallback(),this.resizeObserver?.disconnect(),this.exitTimer!==void 0&&clearTimeout(this.exitTimer),this.hintTimer!==void 0&&clearTimeout(this.hintTimer),this.exitTimer=void 0,this.hintTimer=void 0}setViewportSize(e,t){this.width=e,this.height=t,this.fitted?this.needsCulling&&this.requestUpdate():this.tryInitialFit()}get needsCulling(){return(this.layout?.positions.size??0)>300}get svgEl(){return this.renderRoot.querySelector(`svg.canvas`)}willUpdate(e){if(e.has(`layoutMode`)&&(this.fitted=!1),this.model&&(e.has(`model`)||e.has(`density`)||e.has(`orientation`)||e.has(`layoutMode`))){let e=ws(this.model,this.density,this.orientation,this.layoutMode),t=this.layout;this.entering=new Set(t?[...e.positions.keys()].filter(e=>!t.positions.has(e)):[]);for(let t of e.positions.keys())this.exiting.delete(t);if(t&&!this.reducedMotion){for(let[n,r]of t.positions){let t=this.lastVisuals.get(n);!e.positions.has(n)&&t&&this.exiting.set(n,{point:r,visual:t})}this.scheduleExitCleanup()}this.layout=e,this.lastVisuals=new Map(this.model.visuals),(this.focusId===void 0||!this.model.visuals.has(this.focusId))&&(this.focusId=this.model.roots[0])}}firstUpdated(){let e=this.svgEl;e&&(this.zoomBehavior=Vo().scaleExtent([.2,4]).extent(()=>[[0,0],[Math.max(this.width,1),Math.max(this.height,1)]]).filter(e=>{let t=Is(e,this.ctrlZoom);return t===`hint`&&this.flashHint(),t===`zoom`}).on(`zoom`,e=>this.onZoom(e.transform)).on(`end`,()=>{this.needsCulling&&this.requestUpdate()}),M(e).call(this.zoomBehavior).on(`dblclick.zoom`,null),this.tryInitialFit())}updated(){this.tryInitialFit()}tryInitialFit(){this.fitted||!this.layout||!this.zoomBehavior||this.width<=0||this.height<=0||(this.fitted=!0,this.fit(!1))}onZoom(e){this.transform={x:e.x,y:e.y,k:e.k},this.renderRoot.querySelector(`g.viewport`)?.setAttribute(`transform`,this.transformAttr())}transformAttr(){let{x:e,y:t,k:n}=this.transform;return`translate(${e},${t}) scale(${n})`}fit(e=!0){let t=this.svgEl;if(!this.layout||!this.zoomBehavior||!t)return;let n=As(this.layout.bounds,this.width,this.height),r=jo.translate(n.x,n.y).scale(n.k);e&&!this.reducedMotion?this.zoomBehavior.transform(M(t).transition().duration(300),r):this.zoomBehavior.transform(M(t),r)}zoomBy(e){let t=this.svgEl;this.zoomBehavior&&t&&(this.reducedMotion?this.zoomBehavior.scaleBy(M(t),e):this.zoomBehavior.scaleBy(M(t).transition().duration(200),e))}async focusNode(e){this.focusId=e,await this.updateComplete;let t=this.layout?.positions.get(e),n=this.svgEl;if(t&&n&&this.zoomBehavior&&this.width>0){let e=t.x*this.transform.k+this.transform.x,r=t.y*this.transform.k+this.transform.y;(e<40||e>this.width-40||r<40||r>this.height-40)&&(this.zoomBehavior.translateTo(M(n),t.x,t.y),await this.updateComplete)}for(let t of this.renderRoot.querySelectorAll(`g.nodes g.node`))t.getAttribute(`data-id`)===e&&t.focus()}flashHint(){this.hintVisible=!0,this.hintTimer!==void 0&&clearTimeout(this.hintTimer),this.hintTimer=setTimeout(()=>{this.hintVisible=!1},1500)}scheduleExitCleanup(){this.exiting.size!==0&&this.exitTimer===void 0&&(this.exitTimer=setTimeout(()=>{this.exitTimer=void 0,this.exiting.clear(),this.requestUpdate()},Ps))}highlightedPath(){let e=new Set,t=this.model;if(!t||this.selectedId===void 0)return e;let n=t.visuals.has(this.selectedId)?this.selectedId:ct(t,this.selectedId)?.id;for(;n!==void 0;)e.add(n),n=t.parentOf.get(n);return e}onKeydown(e){let t=this.model;if(!t)return;let n=Ms(t,this.focusId,e.key,this.orientation);n===void 0?(e.key===`Enter`||e.key===` `)&&this.focusId!==void 0?(e.preventDefault(),s(this,`uit-activate`,{id:this.focusId})):e.key===`+`||e.key===`=`?(e.preventDefault(),this.zoomBy(1.25)):e.key===`-`?(e.preventDefault(),this.zoomBy(.8)):e.key===`0`?(e.preventDefault(),this.fit()):(e.key===`ContextMenu`||e.key===`F10`&&e.shiftKey)&&this.focusId!==void 0&&(e.preventDefault(),s(this,`uit-context`,{id:this.focusId})):(e.preventDefault(),this.focusNode(n))}onPointerDown(e){this.gesture.down(e)}onPointerMove(e){this.gesture.move(e)}onPointerEnd(e){this.gesture.end(e)}onContextMenu(e,t){e.preventDefault(),this.gesture.allowsMenu&&s(this,`uit-context`,{id:t})}render(){let{model:e,layout:t,localize:n}=this;if(!e||!t||!n)return _;let r=Ns[this.density],i=[...t.positions.keys()],a=[...e.links.values()];if(this.needsCulling&&this.width>0){let e=js(t,this.transform,this.width,this.height);this.focusId!==void 0&&e.add(this.focusId),this.selectedId!==void 0&&e.add(this.selectedId),i=i.filter(t=>e.has(t)),a=a.filter(t=>e.has(t.childId)||e.has(t.parentId))}let o=this.highlightedPath();return C`
      <svg
        class="canvas ${this.reducedMotion?`still`:``}"
        role="application"
        aria-roledescription=${n(`graph.roledescription`)}
        aria-label=${n(`graph.label`,{site:this.siteName,devices:e.stats.devices,clients:e.stats.clients})}
        @keydown=${this.onKeydown}
        @pointerdown=${this.onPointerDown}
        @pointermove=${this.onPointerMove}
        @pointerup=${this.onPointerEnd}
        @pointercancel=${this.onPointerEnd}
      >
        <g class="viewport" transform=${this.transformAttr()}>
          <g class="links">
            ${Ft(a,e=>e.childId,e=>this.renderLink(e,t,o))}
          </g>
          <g class="nodes">
            ${Ft(i,e=>e,n=>this.renderNode(e,e.visuals.get(n),t.positions.get(n),r,o,!0))}
          </g>
          <g class="exits" aria-hidden="true">
            ${Ft([...this.exiting],([e])=>e,([,t])=>this.renderGhost(e,t,r))}
          </g>
        </g>
      </svg>
      <div class="hint" aria-hidden="true" ?hidden=${!this.hintVisible}>
        ${n(`zoom.hint`)}
      </div>
    `}renderLink(e,t,n){let r=t.positions.get(e.parentId),i=t.positions.get(e.childId);if(!r||!i)return _;let a=this.orientation===`vertical`?(r.y+i.y)/2:(r.x+i.x)/2,o=this.orientation===`vertical`?`M${r.x},${r.y} C${r.x},${a} ${i.x},${a} ${i.x},${i.y}`:`M${r.x},${r.y} C${a},${r.y} ${a},${i.y} ${i.x},${i.y}`,s=this.showLabels?gt(e.edge):``,c=[`link`,e.edge?.medium??`unknown`,e.viaHidden.length>0?`via-hidden`:``,n.has(e.childId)?`on-path`:``];return f`<path class=${c.join(` `)} d=${o}></path>${s?f`<text class="link-label" x=${(r.x+i.x)/2} y=${(r.y+i.y)/2}>${s}</text>`:_}`}renderNode(e,t,n,i,a,o){let c=this.localize,l=t.id,u=_t(t),d=O(t,c),p=t.type===`group`?`group`:t.node.kind,m=[`node`,t.type,p,u,l===this.selectedId?`selected`:``,a.has(l)?`on-path`:``,this.entering.has(l)?`enter`:``],h=t.type===`group`?r:De(t.node),g=i+16;return f`<g
      class=${m.join(` `)}
      data-id=${l}
      role=${o?`button`:_}
      tabindex=${o?l===this.focusId?0:-1:_}
      aria-label=${o?vt(e,t,c):_}
      aria-expanded=${o&&t.type===`group`?String(t.expanded):_}
      style=${`transform: translate(${n.x}px, ${n.y}px)`}
      @click=${o?()=>s(this,`uit-activate`,{id:l}):_}
      @contextmenu=${o?e=>this.onContextMenu(e,l):_}
      @focus=${o?()=>{this.focusId=l}:_}
    >
      <title>${d}</title>
      <circle class="hit" r=${Math.max(i,22)}></circle>
      <circle class="ring" r=${i+5}></circle>
      <circle class="disc" r=${i}></circle>
      <svg class="glyph" x=${-i*.6} y=${-i*.6} width=${i*1.2} height=${i*1.2} viewBox="0 0 24 24" aria-hidden="true">
        <path d=${h}></path>
      </svg>
      <circle class="status" cx=${i*.72} cy=${-i*.72} r=${Math.max(4,i*.24)}></circle>
      ${t.type===`group`?f`<text class="badge" x=${i*.95} y=${i+2}>${t.counts.total}</text>`:_}
      ${this.showLabels?f`<text class="label" y=${g}>${ft(d,Fs)}</text>`:_}
      ${u===`offline`?f`<text class="state-text" y=${this.showLabels?g+14:g}>${c(D.offline)}</text>`:_}
    </g>`}renderGhost(e,t,n){return this.renderNode(e,t.visual,t.point,n,new Set,!1)}static styles=[se,h`
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
        stroke: color-mix(in srgb, var(--primary-color) 40%, var(--uit-line));
        stroke-width: 2;
        filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.1));
      }
      .selected .disc,
      .on-path .disc {
        stroke: var(--uit-focus);
      }
      .selected .disc {
        stroke-width: 3;
      }
      .glyph path {
        fill: var(--primary-color);
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
        font-weight: 500;
        fill: var(--primary-text-color);
        text-anchor: middle;
        dominant-baseline: hanging;
      }
      .badge {
        font-weight: 700;
        text-anchor: start;
      }
      .state-text {
        fill: var(--uit-offline);
        font-weight: 600;
      }
      .link {
        fill: none;
        stroke: color-mix(
          in srgb,
          var(--primary-color) 45%,
          var(--secondary-text-color)
        );
        stroke-opacity: 0.65;
        stroke-width: 1.75;
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
    `]};E(`uit-graph-view`,Ls);function Rs(e,t){return e.type===`group`?e.members.some(e=>e.name.toLowerCase().includes(t)):e.node.name.toLowerCase().includes(t)}function zs(e,t,n){let r=n.trim().toLowerCase(),i;if(r){i=new Set;for(let[t,n]of e.visuals)if(Rs(n,r))for(let n=t;n!==void 0&&!i.has(n);n=e.parentOf.get(n))i.add(n)}let a=[],o=(n,s,c)=>{let l=i?n.filter(e=>i.has(e)):n;l.forEach((n,i)=>{let u=e.visuals.get(n),d=e.children.get(n)??[],f=u.type===`group`,p=f||d.length>0,m=f?u.expanded:r!==``||!t.has(n);a.push({id:n,visual:u,level:s,posinset:i+1,setsize:l.length,hasChildren:p,expanded:p&&m,parentId:c}),m&&d.length>0&&o(d,s+1,n)})};return o(e.roots,1,void 0),a}var Bs=class extends T{static properties={model:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},siteName:{attribute:!1},query:{state:!0},collapsed:{state:!0},focusId:{state:!0}};rows=[];gesture=new Bt;typeahead=``;typeaheadTimer;constructor(){super(),this.siteName=``,this.query=``,this.collapsed=new Set}willUpdate(){this.model&&(this.rows=zs(this.model,this.collapsed,this.query),this.rows.some(e=>e.id===this.focusId)||(this.focusId=this.rows[0]?.id))}render(){let{model:e,localize:t}=this;return!e||!t?_:C`
      <div class="search">
        <input
          type="search"
          .value=${this.query}
          placeholder=${t(`list.search`)}
          aria-label=${t(`list.search`)}
          @input=${e=>{this.query=e.target.value}}
        />
      </div>
      ${this.rows.length===0?C`<p class="empty">${t(`list.no_matches`)}</p>`:C`<div
            class="tree"
            role="tree"
            aria-label=${t(`list.label`,{site:this.siteName})}
            @keydown=${this.onKeydown}
          >
            ${Ft(this.rows,e=>e.id,n=>this.renderRow(e,n,t))}
          </div>`}
    `}renderRow(e,t,n){let i=t.visual,a=O(i,n),o=_t(i);return C`<div
      class="row ${o} ${t.id===this.selectedId?`selected`:``}"
      role="treeitem"
      data-id=${t.id}
      aria-level=${t.level}
      aria-setsize=${t.setsize}
      aria-posinset=${t.posinset}
      aria-selected=${String(t.id===this.selectedId)}
      aria-expanded=${t.hasChildren?String(t.expanded):_}
      aria-label=${vt(e,i,n)}
      tabindex=${t.id===this.focusId?0:-1}
      style=${`--level: ${t.level}`}
      @click=${()=>s(this,`uit-activate`,{id:t.id})}
      @pointerdown=${e=>this.gesture.down(e)}
      @pointermove=${e=>this.gesture.move(e)}
      @pointerup=${e=>this.gesture.end(e)}
      @pointercancel=${e=>this.gesture.end(e)}
      @contextmenu=${e=>{e.preventDefault(),this.gesture.allowsMenu&&s(this,`uit-context`,{id:t.id})}}
      @focus=${()=>{this.focusId=t.id}}
    >
      <span
        class="chevron"
        aria-hidden="true"
        @click=${e=>{e.stopPropagation(),t.hasChildren&&this.toggle(t)}}
        >${t.hasChildren?w(t.expanded?ie:d):_}</span
      >
      ${w(i.type===`group`?r:De(i.node))}
      <span class="name" title=${a}>${a}</span>
      ${i.type===`group`?C`<span class="count">${i.counts.total}</span>`:C`<span class="dot" aria-hidden="true"></span>${o===`online`?_:C`<span class="state-text"
                  >${n(D[o])}</span
                >`}`}
    </div>`}toggle(e){if(e.visual.type===`group`){s(this,`uit-toggle-group`,{id:e.id});return}let t=new Set(this.collapsed);t.has(e.id)?t.delete(e.id):t.add(e.id),this.collapsed=t}onKeydown(e){let t=this.rows,n=t.findIndex(e=>e.id===this.focusId),r=t[n];if(!r)return;if(e.key===`ContextMenu`||e.key===`F10`&&e.shiftKey){e.preventDefault(),s(this,`uit-context`,{id:r.id});return}let i;switch(e.key){case`ArrowDown`:i=t[n+1]?.id;break;case`ArrowUp`:i=t[n-1]?.id;break;case`Home`:i=t[0]?.id;break;case`End`:i=t.at(-1)?.id;break;case`ArrowRight`:r.hasChildren&&!r.expanded?this.toggle(r):r.expanded&&(i=t[n+1]?.id);break;case`ArrowLeft`:r.expanded?this.toggle(r):i=r.parentId;break;case`Enter`:case` `:s(this,`uit-activate`,{id:r.id});break;default:e.key.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&(e.preventDefault(),this.typeAhead(e.key,n));return}e.preventDefault(),i!==void 0&&this.focusRow(i)}typeAhead(e,t){this.typeahead+=e.toLowerCase(),this.typeaheadTimer!==void 0&&clearTimeout(this.typeaheadTimer),this.typeaheadTimer=setTimeout(()=>{this.typeahead=``},500);let n=this.rows;for(let e=1;e<=n.length;e++){let r=n[(t+e)%n.length];if(O(r.visual,this.localize).toLowerCase().startsWith(this.typeahead)){this.focusRow(r.id);return}}}async focusRow(e){this.focusId=e,await this.updateComplete;let t=this.renderRoot.querySelectorAll(`[role="treeitem"]`);for(let n of t)n.getAttribute(`data-id`)===e&&n.focus()}static styles=[se,Se,h`
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
        background: color-mix(in srgb, var(--uit-focus) 16%, transparent);
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
    `]};E(`uit-list-view`,Bs);var Vs=600,Hs=`/config/integrations/integration/unifi_insights`,Us={integration:`action.integration`,edit:`action.edit`},Ws={loading:{key:`state.loading`},no_sources:{key:`state.no_sources`,action:`integration`},unconfigured:{key:`state.unconfigured`,action:`edit`},empty:{key:`state.empty`},incompatible:{key:`state.incompatible`},reloading:{key:`state.reconnecting`}},Gs=e=>e?.nodes.filter(e=>e.kind!==`client`&&e.state===`offline`).length??0,Ks=class extends T{static properties={hass:{attribute:!1},layout:{attribute:!1},config:{state:!0},sources:{state:!0},snapshot:{state:!0},lastGood:{state:!0},error:{state:!0},incompatible:{state:!0},disconnected:{state:!0},ui:{state:!0},view:{state:!0},selectedId:{state:!0},menuRequest:{state:!0},siteOverride:{state:!0},narrow:{state:!0},reducedMotion:{state:!0},announcement:{state:!0}};subscription=new Je({onSnapshot:e=>this.applySnapshot(e),onError:e=>{this.error=e},onIncompatible:()=>{this.incompatible=!0},onDisconnected:()=>{this.disconnected=!0},onReconnected:()=>{this.hass&&this.loadSources(this.hass)}});details=new Fe(()=>this.requestUpdate());selectionScope;buildModel=ot();announcer=new Re(e=>{this.announcement=e});sourcesFor;sourcesPending=!1;sourcesRetry;sourcesAttempt=0;sourcesError;boundKey;cardState={phase:`loading`,stale:!1,notices:[]};model;resizeObserver;motionQuery;localizeLang;localizeFn;constructor(){super(),this.incompatible=!1,this.disconnected=!1,this.ui={kinds:new Set(b),clients:`collapsed`,toggledGroups:new Set},this.view=`graph`,this.narrow=!1,this.reducedMotion=!1,this.announcement=``}setConfig(e){let t=ce(ne(e));this.config=t,this.view=t.view,this.ui={kinds:new Set(t.kinds),clients:t.clients,toggledGroups:new Set},this.siteOverride=void 0}getCardSize(){return 8}getGridOptions(){return{columns:12,rows:8,min_columns:6,min_rows:4}}static getConfigElement(){return document.createElement(ye)}static async getStubConfig(e){try{let t=Ee(await e.callWS({type:u}))[0];if(t)return{type:le,...t.binding}}catch{}return{type:le}}connectedCallback(){super.connectedCallback(),this.resizeObserver=new ResizeObserver(e=>{let t=e[0]?.contentRect.width??0;this.narrow=t>0&&t<Vs}),this.resizeObserver.observe(this),this.motionQuery=window.matchMedia(`(prefers-reduced-motion: reduce)`),this.motionQuery.addEventListener(`change`,this.onMotionChange),this.onMotionChange(),this.sync()}disconnectedCallback(){super.disconnectedCallback(),this.subscription.stop(),this.details.stop(),this.menuRequest=void 0,this.announcer.dispose(),this.resizeObserver?.disconnect(),this.resizeObserver=void 0,this.motionQuery?.removeEventListener(`change`,this.onMotionChange),this.sourcesFor=void 0,this.clearSourcesRetry()}shouldUpdate(e){if(e.size!==1||!e.has(`hass`))return!0;let t=e.get(`hass`),n=this.hass;return!t||!n||t.connection!==n.connection||(t.locale?.language??t.language)!==(n.locale?.language??n.language)||x(t)!==x(n)}willUpdate(e){(e.has(`hass`)||e.has(`config`)||e.has(`sources`)||e.has(`siteOverride`))&&this.sync();let t=this.config;if(!t)return;this.cardState=Ue({sources:this.sources,binding:this.binding,snapshot:this.snapshot,lastGood:this.lastGood,error:this.error,incompatible:this.incompatible,disconnected:this.disconnected,maxClients:t.max_clients}),this.model=this.cardState.render?this.buildModel(this.cardState.render,this.ui):void 0;let n=this.selectedId;n!==void 0&&!(this.model?.visuals.has(n)||this.model?.nodes.has(n))&&this.deselect();let r=this.binding,i=r&&this.selectedId!==void 0?{...r,node_id:this.selectedId}:void 0,a=JSON.stringify(i);a!==this.selectionScope&&(this.selectionScope=a,JSON.stringify(this.menuRequest)!==a&&(this.menuRequest=void 0)),this.details.select(this.isConnected?this.hass:void 0,i)}get binding(){return this.config?this.siteOverride??Ae(this.config,this.sources):void 0}get localize(){let e=this.hass?.locale?.language??this.hass?.language??`en`;return(e!==this.localizeLang||!this.localizeFn)&&(this.localizeLang=e,this.localizeFn=Ne(e)),this.localizeFn}get graphView(){return this.renderRoot.querySelector(`uit-graph-view`)}sync(){let{hass:e,config:t}=this;if(!this.isConnected||!e||!t)return;this.sourcesFor!==e.connection&&(this.sourcesFor=e.connection,this.disconnected=!1,this.clearSourcesRetry(),this.sourcesAttempt=0,this.loadSources(e));let n=this.binding,r=n?`${n.entry_id}\u0000${n.site_id}`:void 0;r!==this.boundKey&&(this.boundKey=r,this.snapshot=void 0,this.lastGood=void 0,this.error=void 0,this.sourcesError=void 0,this.incompatible=!1,this.deselect()),this.subscription.update(e.connection,n?{...n,max_clients:t.max_clients}:void 0)}async loadSources(e){if(this.sourcesPending)return;this.sourcesPending=!0,this.clearSourcesRetry();let n=e.connection;try{let t=await e.callWS({type:u});if(this.sourcesFor!==n)return;this.sources=t,this.sourcesError&&this.error===this.sourcesError&&(this.error=void 0),this.sourcesError=void 0,t.length>0?this.sourcesAttempt=0:this.scheduleSourcesRetry()}catch(e){if(this.sourcesFor!==n)return;let r=this.sourcesError;this.sourcesError=t(e),(!this.error||this.error===r)&&(this.error=this.sourcesError),this.scheduleSourcesRetry()}finally{this.sourcesPending=!1,this.isConnected&&this.sourcesFor!==void 0&&this.sourcesFor!==n&&this.hass&&this.loadSources(this.hass)}}scheduleSourcesRetry(){this.isConnected&&(this.sourcesRetry=setTimeout(()=>{this.sourcesRetry=void 0,this.hass&&this.loadSources(this.hass)},qe(this.sourcesAttempt++)))}clearSourcesRetry(){this.sourcesRetry!==void 0&&clearTimeout(this.sourcesRetry),this.sourcesRetry=void 0}applySnapshot(e){let t=this.snapshot;this.snapshot=e,this.error=void 0,this.incompatible=!1,this.disconnected=!1,e.status!==`unavailable`&&e.nodes.length>0&&(this.lastGood=e),this.hass&&this.sources!==void 0&&!this.sources.some(t=>t.entry_id===e.entry_id)&&this.loadSources(this.hass);let n=this.localize,r=n(`announce.updated`),i=e.issues[0],a=Gs(e);if(e.status===`unavailable`&&i){let t=Ve(i,e,this.config?.max_clients??0);r=n(t.key,t.vars)}else a>0&&a!==Gs(t)&&(r=n(`announce.offline`,{count:a}));this.announcer.announce(r)}onMotionChange=()=>{this.reducedMotion=this.motionQuery?.matches??!1};onActivate=e=>{let t=e.detail.id;this.model?.visuals.get(t)?.type===`group`&&this.toggleGroup(t),this.selectedId=t};onSelect=e=>{let t=e.detail.id,n=this.model;if(n&&!n.visuals.has(t)){let e=ct(n,t);e&&!e.expanded&&this.toggleGroup(e.id)}this.selectedId=t};onToggleGroup=e=>{this.toggleGroup(e.detail.id)};onContext=e=>{let t=e.detail.id;if(!this.model?.visuals.has(t)&&!this.model?.nodes.has(t))return;this.onSelect(e);let n=this.binding;this.menuRequest=n&&!t.startsWith(`group:`)?{...n,node_id:t}:void 0};onClose=()=>{this.deselect()};onKeydown=e=>{e.key===`Escape`&&this.selectedId!==void 0&&!this.renderRoot.querySelector(`uit-detail-panel`)?.menuOpen&&(e.stopPropagation(),this.deselect())};deselect(){this.selectedId=void 0,this.menuRequest=void 0}toggleGroup(e){let t=new Set(this.ui.toggledGroups);t.has(e)?t.delete(e):t.add(e),this.ui={...this.ui,toggledGroups:t}}toggleKind(e){let t=new Set(this.ui.kinds);if(t.has(e)){if(t.size===1)return;t.delete(e)}else t.add(e);this.ui={...this.ui,kinds:t}}runAction(e){_e(e===`integration`?Hs:`${location.pathname}?edit=1`)}render(){let e=this.config;if(!e)return _;let t=this.localize,n=this.cardState,r=this.model,i=e.title??n.render?.site_name??this.snapshot?.site_name??t(`card.name`),a=n.render?.nodes??[],o=a.filter(e=>e.kind!==`client`).length,s=a.filter(e=>e.kind===`client`).length;return C`<ha-card>
      <div
        class="card ${this.narrow?`narrow`:``}"
        @keydown=${this.onKeydown}
        @uit-activate=${this.onActivate}
        @uit-select=${this.onSelect}
        @uit-context=${this.onContext}
        @uit-toggle-group=${this.onToggleGroup}
        @uit-close=${this.onClose}
      >
        <header>
          <div class="header-icon" aria-hidden="true">
            ${w(he)}
          </div>
          <div class="header-text">
            <h2 class="title" title=${i}>${i}</h2>
            ${a.length>0?C`<div class="subtitle">
                  ${t(`header.summary`,{devices:o,clients:s})}
                </div>`:_}
          </div>
          ${this.renderSiteSelector(e,t)}
        </header>
        ${r?this.renderToolbar(t):_}
        ${r?this.renderNotices(n.notices,t):_}
        <div class="body">
          ${r?this.renderContent(r,n,e,t):this.renderMessage(n,t)}
        </div>
        <div class="sr-only" role="status" aria-live="polite">
          ${this.announcement}
        </div>
      </div>
    </ha-card>`}renderSiteSelector(e,t){let n=Ee(this.sources??[]);if(!e.show_site_selector||n.length<2)return _;let r=this.binding;return C`<label class="site">
      <span class="sr-only">${t(`toolbar.site`)}</span>
      <select
        @change=${e=>{let t=n[Number(e.target.value)];t&&(this.siteOverride=t.binding)}}
      >
        ${n.map((e,t)=>C`<option
              value=${t}
              ?selected=${ke(e.binding,r)}
            >
              ${e.label}
            </option>`)}
      </select>
    </label>`}renderToolbar(e){let t=C`
      <div class="group" role="group" aria-label=${e(`toolbar.view`)}>
        ${oe.map(t=>C`<button
              aria-pressed=${String(this.view===t)}
              @click=${()=>{this.view=t}}
            >
              ${e(ut[t])}
            </button>`)}
      </div>
      <div class="group" role="group" aria-label=${e(`toolbar.filters`)}>
        ${b.map(t=>C`<button
              aria-pressed=${String(this.ui.kinds.has(t))}
              @click=${()=>this.toggleKind(t)}
            >
              ${e(lt[t])}
            </button>`)}
      </div>
      ${this.view===`graph`?C`<div
            class="group"
            role="group"
            aria-label=${e(`toolbar.zoom`)}
          >
            ${this.iconButton(we,e(`zoom.in`),()=>this.graphView?.zoomBy(1.25))}
            ${this.iconButton(ue,e(`zoom.out`),()=>this.graphView?.zoomBy(.8))}
            ${this.iconButton(te,e(`zoom.fit`),()=>this.graphView?.fit())}
          </div>`:_}
    `;return this.narrow?C`<details class="toolbar">
          <summary>${e(`toolbar.options`)}</summary>
          <div class="controls">${t}</div>
        </details>`:C`<div class="toolbar">
          <div class="controls">${t}</div>
        </div>`}iconButton(e,t,n){return C`<button
      class="icon-button"
      aria-label=${t}
      title=${t}
      @click=${n}
    >
      ${w(e)}
    </button>`}actionButton(e,t){return C`<button class="action" @click=${()=>this.runAction(e)}>
      ${t(Us[e])}
    </button>`}renderNotices(e,t){return e.length===0?_:C`<ul class="notices">
      ${e.map(e=>C`<li class=${e.severity}>
            <span>${t(e.key,e.vars)}</span>${e.action?this.actionButton(e.action,t):_}
          </li>`)}
    </ul>`}renderMessage(e,t){let n=Ws[e.phase],r={site:this.snapshot?.site_name??``},i=[];return n&&i.push({...n,vars:r}),i.push(...e.notices),C`<div class="message ${e.phase}">
      ${e.phase===`loading`?C`<svg class="skeleton" viewBox="0 0 120 60" aria-hidden="true">
            <path d="M60 18 L30 37 M60 18 L90 37"></path>
            <circle cx="60" cy="10" r="8"></circle>
            <circle cx="30" cy="45" r="8"></circle>
            <circle cx="90" cy="45" r="8"></circle>
          </svg>`:_}
      ${i.map(e=>C`<p>${t(e.key,e.vars)}</p>
            ${e.action?this.actionButton(e.action,t):_}`)}
    </div>`}renderContent(e,t,n,r){let i=n.density??(this.narrow?`compact`:`comfortable`),a=t.render?.site_name??``,o=t.phase===`reloading`?`${r(`state.stale`)} · ${r(`state.reconnecting`)}`:r(`state.stale`);return C`<div class="content ${t.stale?`stale`:``}">
      ${t.stale?C`<span class="badge stale">${o}</span>`:_}
      ${this.view===`graph`?C`<uit-graph-view
            .model=${e}
            .density=${i}
            .orientation=${n.orientation}
            .layoutMode=${n.layout}
            .showLabels=${n.show_labels}
            .selectedId=${this.selectedId}
            .localize=${r}
            .siteName=${a}
            .ctrlZoom=${this.layout!==`panel`}
            .reducedMotion=${this.reducedMotion}
          ></uit-graph-view>`:C`<uit-list-view
            .model=${e}
            .selectedId=${this.selectedId}
            .localize=${r}
            .siteName=${a}
          ></uit-list-view>`}
      <uit-detail-panel
        .model=${e}
        .selectedId=${this.selectedId}
        .hass=${this.hass}
        .menuRequest=${this.menuRequest}
        .details=${this.details.state.status===`ready`?this.details.state.details:void 0}
        .localize=${r}
        ?narrow=${this.narrow}
      ></uit-detail-panel>
    </div>`}static styles=[se,Se,h`
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
        padding: 14px 16px 6px;
      }
      .header-icon {
        width: 38px;
        height: 38px;
        border-radius: 12px;
        display: grid;
        place-items: center;
        background: color-mix(in srgb, var(--primary-color) 15%, transparent);
        color: var(--primary-color);
        flex: none;
      }
      .header-text {
        flex: 1;
        min-width: 0;
      }
      .title {
        margin: 0;
        font-size: 1.05rem;
        font-weight: 600;
        line-height: 1.25;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .subtitle {
        font-size: 0.76rem;
        color: var(--secondary-text-color);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .toolbar {
        padding: 4px 16px 8px;
      }
      details.toolbar > summary {
        min-height: 38px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
        padding: 0 14px;
        border-radius: 999px;
        border: 1px solid var(--uit-line);
        background: color-mix(
          in srgb,
          var(--primary-text-color) 5%,
          transparent
        );
        font-size: 0.82rem;
        font-weight: 600;
        list-style: none;
      }
      details.toolbar > summary::-webkit-details-marker {
        display: none;
      }
      details.toolbar[open] > .controls {
        margin-top: 8px;
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
        justify-content: center;
      }
      .notices {
        list-style: none;
        margin: 4px 16px;
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
        background: color-mix(in srgb, var(--uit-warning) 12%, transparent);
      }
      .notices li.info {
        border-color: var(--uit-focus);
        background: color-mix(in srgb, var(--uit-focus) 10%, transparent);
      }
      .notices li.error {
        border-color: var(--uit-offline);
        background: color-mix(in srgb, var(--uit-offline) 12%, transparent);
      }
      .notices li span {
        flex: 1;
      }
      .body {
        position: relative;
        display: flex;
        flex: 1 1 280px;
        min-height: 0;
        margin: 4px 12px 12px;
        border-radius: 14px;
        border: 1px solid var(--uit-line);
        background-color: color-mix(
          in srgb,
          var(--primary-text-color) 2.5%,
          transparent
        );
        background-image: radial-gradient(
          color-mix(in srgb, var(--primary-text-color) 12%, transparent) 1px,
          transparent 1px
        );
        background-size: 18px 18px;
        overflow: hidden;
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
    `]},qs=`current`,Js=``,Ys={collapsed:`clients.collapsed`,expanded:`clients.expanded`,hidden:`clients.hidden`},Xs={auto:`density.auto`,comfortable:`density.comfortable`,compact:`density.compact`},Zs={vertical:`orientation.vertical`,horizontal:`orientation.horizontal`},Qs={tree:`layout.tree`,tiered:`layout.tiered`},$s={site:`editor.site`,title:`editor.title`,view:`editor.view`,clients:`editor.clients`,kinds:`editor.kinds`,density:`editor.density`,orientation:`editor.orientation`,layout:`editor.layout`,show_site_selector:`editor.show_site_selector`,show_labels:`editor.show_labels`,max_clients:`editor.max_clients`};function Q(e,t,n){return e.map(e=>({value:e,label:n(t[e])}))}var $=(e,t)=>typeof e==`string`&&t.includes(e);function ec(e,t){let{entry_id:n,site_id:r}=e;if(n===void 0||r===void 0)return Js;let i=t.findIndex(e=>ke(e.binding,{entry_id:n,site_id:r}));return i>=0?String(i):qs}function tc(e,t,n){let r=t.map((e,t)=>({value:String(t),label:e.label}));return ec(e,t)===`current`&&r.push({value:qs,label:n(`editor.site_unavailable`,{site:e.site_id??``})}),[{name:`site`,selector:{select:{mode:`dropdown`,options:r}}},{name:`title`,selector:{text:{}}},{name:``,type:`grid`,schema:[{name:`view`,selector:{select:{mode:`dropdown`,options:Q(oe,ut,n)}}},{name:`clients`,selector:{select:{mode:`dropdown`,options:Q(de,Ys,n)}}},{name:`density`,selector:{select:{mode:`dropdown`,options:Q([`auto`,...be],Xs,n)}}},{name:`orientation`,selector:{select:{mode:`dropdown`,options:Q(fe,Zs,n)}}},{name:`layout`,selector:{select:{mode:`dropdown`,options:Q(pe,Qs,n)}}}]},{name:`kinds`,selector:{select:{multiple:!0,mode:`list`,options:Q(b,lt,n)}}},{name:`show_site_selector`,selector:{boolean:{}}},{name:`show_labels`,selector:{boolean:{}}},{name:`max_clients`,selector:{number:{min:1,max:500,mode:`box`}}}]}function nc(e,t){return{site:ec(e,t),title:e.title??``,view:e.view??`graph`,clients:e.clients??`collapsed`,density:e.density??`auto`,orientation:e.orientation??`vertical`,layout:e.layout??`tree`,kinds:e.kinds?[...e.kinds]:[...b],show_site_selector:e.show_site_selector??!1,show_labels:e.show_labels??!0,max_clients:e.max_clients??500}}function rc(e,t,n){let r={...t},i=e.site??Js;if(i===Js)delete r.entry_id,delete r.site_id;else if(i!==`current`){let e=n[Number(i)];e&&(r.entry_id=e.binding.entry_id,r.site_id=e.binding.site_id)}e.title?r.title=e.title:delete r.title,$(e.view,oe)&&(r.view=e.view),$(e.clients,de)&&(r.clients=e.clients),$(e.orientation,fe)&&(r.orientation=e.orientation),e.layout===`tree`?delete r.layout:$(e.layout,pe)&&(r.layout=e.layout),$(e.density,be)?r.density=e.density:e.density===`auto`&&delete r.density;let a=(e.kinds??[]).filter(e=>$(e,b));a.length===b.length?delete r.kinds:a.length>0&&(r.kinds=b.filter(e=>a.includes(e))),typeof e.show_site_selector==`boolean`&&(r.show_site_selector=e.show_site_selector),typeof e.show_labels==`boolean`&&(r.show_labels=e.show_labels);let o=e.max_clients;return o===500?delete r.max_clients:typeof o==`number`&&Number.isInteger(o)&&o>=1&&o<=500&&(r.max_clients=o),r}async function ic(e=customElements,t=window.loadCardHelpers){e.get(`ha-form`)||await((await t?.())?.createCardElement({type:`entities`,entities:[]})?.constructor)?.getConfigElement?.()}var ac=class extends T{static properties={hass:{attribute:!1},config:{state:!0},sources:{state:!0},formReady:{state:!0}};sourcesRequested=!1;constructor(){super(),this.formReady=!1}setConfig(e){this.config={...e}}connectedCallback(){super.connectedCallback(),ic().catch(()=>void 0).then(()=>{this.formReady=!0})}willUpdate(){this.hass&&!this.sourcesRequested&&(this.sourcesRequested=!0,this.hass.callWS({type:u}).then(e=>{this.sources=e},()=>{this.sources=[]}))}render(){let{hass:e,config:t}=this;if(!e||!t)return _;let n=Ne(e.locale?.language??e.language);if(!this.formReady)return C`<p>${n(`state.loading`)}</p>`;let r=Ee(this.sources??[]);return C`<ha-form
      .hass=${e}
      .data=${nc(t,r)}
      .schema=${tc(t,r,n)}
      .computeLabel=${e=>{let t=$s[e.name];return t?n(t):``}}
      @value-changed=${this.onValueChanged}
    ></ha-form>`}onValueChanged=e=>{e.stopPropagation();let t=this.config;if(!t)return;let n=e.detail.value,r=rc(n,t,Ee(this.sources??[]));this.config=r,s(this,`config-changed`,{config:r})}};E(Te,Ks),E(ye,ac);var oc=Ne(`en`);window.customCards??=[],window.customCards.some(e=>e.type===`unifi-insights-topology-card`)||window.customCards.push({type:Te,name:oc(`card.name`),description:oc(`card.description`),preview:!0,documentationURL:`https://github.com/tinkerologie/ha-unifi-insights#network-topology-card`});