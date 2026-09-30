import{A as e,C as t,Ct as n,D as r,Dt as i,E as a,Et as o,H as s,J as c,M as l,N as u,O as d,Ot as f,P as p,Q as m,S as h,St as g,T as _,Tt as v,V as y,W as b,Y as ee,Z as x,_t as te,at as ne,bt as re,ct as ie,dt as S,ft as ae,gt as oe,ht as se,i as ce,it as le,j as C,k as w,kt as ue,lt as de,mt as fe,ot as pe,pt as me,q as he,r as ge,rt as T,st as _e,ut as ve,vt as ye,w as E,wt as be,xt as xe,yt as Se}from"./chunks/register-dashboard-card-BLc74zCS.js";import"./internet-activity-card.js";import"./performance-card.js";import"./protect-status-card.js";import"./site-health-card.js";import"./timeline-card.js";var Ce={"card.name":`UniFi Topology`,"card.description":`Interactive network topology of a UniFi site, from UniFi Insights.`,"header.summary":`{devices} devices · {clients} clients`,"state.loading":`Loading network topology…`,"state.no_sources":`No UniFi Insights integration is loaded.`,"state.unconfigured":`Choose a site to show.`,"state.empty":`No devices reported for {site}.`,"state.incompatible":`Card and integration versions don't match. Refresh the browser (clear cache) after updating.`,"state.stale":`Stale`,"state.reconnecting":`Reconnecting…`,"state.online":`Online`,"state.offline":`Offline`,"state.unknown":`Unknown`,"issue.site_unavailable":`Site data temporarily unavailable; will recover automatically.`,"issue.devices_unavailable":`Device data unavailable; showing last known layout.`,"issue.legacy_uplink_missing":`Uplink details unavailable; device links may be missing.`,"issue.parents_unresolved":`{count} nodes couldn't be placed under a parent.`,"issue.clients_truncated":`Showing {included} of {total} clients (limit {max}).`,"issue.entry_unloaded":`Integration is reloading.`,"issue.unknown":`Topology problem: {code}.`,"error.entry_not_found":`The configured site no longer exists or is disabled.`,"error.site_not_selected":`The configured site no longer exists or is disabled.`,"error.entry_not_loaded":`Integration isn't loaded (retrying).`,"error.unknown":`Could not load the topology ({code}).`,"action.integration":`Integration`,"action.edit":`Edit card`,"view.graph":`Graph`,"view.list":`List`,"toolbar.view":`View`,"toolbar.filters":`Show`,"toolbar.zoom":`Zoom`,"toolbar.options":`Options`,"toolbar.site":`Site`,"zoom.in":`Zoom in`,"zoom.out":`Zoom out`,"zoom.fit":`Fit to view`,"zoom.hint":`Use Ctrl + scroll to zoom`,"kind.gateway":`Gateway`,"kind.switch":`Switch`,"kind.access_point":`Access point`,"kind.client":`Client`,"kind.other":`Other`,"medium.wired":`Wired`,"medium.wireless":`Wireless`,"medium.unknown":`Unknown`,"group.clients":`{count} clients`,"group.client_one":`1 client`,"group.unconnected":`Unconnected clients`,"group.root":`Clients`,"group.summary":`{wireless} wireless, {offline} offline`,"graph.label":`{site} topology, {devices} devices, {clients} clients`,"graph.roledescription":`network topology`,"node.label":`{kind} {name}, {state}`,"node.clients":`{count} clients`,"node.client_one":`1 client`,"node.uplink":`uplink port {port}`,"node.uplink_speed":`uplink port {port} at {speed}`,"list.label":`{site} devices and clients`,"list.search":`Search`,"list.no_matches":`No matches`,"detail.close":`Close`,"detail.kind":`Type`,"detail.model":`Model`,"detail.state":`State`,"detail.parent":`Connected to`,"detail.port":`Port`,"detail.speed":`Speed`,"detail.medium":`Link`,"detail.poe":`PoE`,"detail.clients":`Clients`,"detail.clients_value":`{total} ({wired} wired, {wireless} wireless)`,"detail.connection":`Connection`,"detail.vlan":`VLAN`,"detail.network":`Network`,"detail.via_hidden":`Via hidden`,"detail.open_device":`Open device`,"detail.search_members":`Search clients`,"announce.updated":`Topology updated.`,"announce.offline":`{count} devices offline.`,"editor.site":`Site`,"editor.site_unavailable":`{site} (unavailable)`,"editor.title":`Title`,"editor.view":`Default view`,"editor.clients":`Clients`,"editor.kinds":`Show node types`,"editor.density":`Density`,"editor.orientation":`Orientation`,"editor.show_site_selector":`Show site selector`,"editor.show_labels":`Show labels`,"editor.max_clients":`Maximum clients`,"clients.collapsed":`Grouped`,"clients.expanded":`Expanded`,"clients.hidden":`Hidden`,"density.auto":`Automatic`,"density.comfortable":`Comfortable`,"density.compact":`Compact`,"orientation.vertical":`Top to bottom`,"orientation.horizontal":`Left to right`},we={en:Ce};function Te(e){let t=(e??`en`).toLowerCase(),n=we[t]??we[t.split(`-`)[0]??`en`]??{};return(e,t)=>{let r=n[e]??Ce[e];if(t)for(let[e,n]of Object.entries(t))r=r.replaceAll(`{${e}}`,String(n));return r}}var Ee=class{last=-1/0;pending;timer;emit;intervalMs;constructor(e,t=5e3){this.emit=e,this.intervalMs=t}announce(e){let t=this.last+this.intervalMs-Date.now();if(t<=0&&this.timer===void 0){this.last=Date.now(),this.emit(e);return}this.pending=e,this.timer??=setTimeout(()=>{this.timer=void 0;let e=this.pending;this.pending=void 0,e!==void 0&&(this.last=Date.now(),this.emit(e))},Math.max(t,0))}dispose(){this.timer!==void 0&&clearTimeout(this.timer),this.timer=void 0,this.pending=void 0}},De={[be]:{key:`issue.site_unavailable`},[re]:{key:`issue.devices_unavailable`,action:`integration`},[g]:{key:`issue.legacy_uplink_missing`},[n]:{key:`issue.parents_unresolved`},[Se]:{key:`issue.clients_truncated`},[xe]:{key:`issue.entry_unloaded`}},Oe={[oe]:{key:`error.entry_not_found`,action:`edit`},[ye]:{key:`error.site_not_selected`,action:`edit`},[te]:{key:`error.entry_not_loaded`,action:`integration`}};function ke(e,t,n){let r=De[e.code];if(!r)return{code:e.code,severity:e.severity,key:`issue.unknown`,vars:{code:e.code}};let i={code:e.code,severity:e.severity,key:r.key};return e.code===`parents_unresolved`&&(i.vars={count:t.unresolved.length}),e.code===`clients_truncated`&&t.truncation&&(i.vars={included:t.truncation.clients_included,total:t.truncation.clients_total,max:n}),r.action&&(i.action=r.action),i}function Ae(e){let t=Oe[e.code];if(!t)return{code:e.code,severity:`error`,key:`error.unknown`,vars:{code:e.code}};let n={code:e.code,severity:`error`,key:t.key};return t.action&&(n.action=t.action),n}function je(e){if(e.incompatible)return{phase:`incompatible`,stale:!1,notices:[]};if(e.error)return{phase:`error`,render:e.lastGood,stale:e.lastGood!==void 0,notices:[Ae(e.error)]};if(e.disconnected){let t=e.snapshot,n=t&&t.nodes.length>0?t:e.lastGood;if(n)return{phase:`reloading`,render:n,stale:!0,notices:[]}}if(e.sources!==void 0&&e.sources.length===0&&e.snapshot===void 0)return{phase:`no_sources`,stale:!1,notices:[]};if(e.binding===void 0)return{phase:e.sources===void 0?`loading`:`unconfigured`,stale:!1,notices:[]};let t=e.snapshot;if(t===void 0)return{phase:`loading`,stale:!1,notices:[]};let n=t.issues.map(n=>ke(n,t,e.maxClients));if(t.status===`unavailable`){let r=t.issues.some(e=>e.code===xe),i=t.nodes.length>0?t:e.lastGood;return{phase:r?`reloading`:`unavailable`,render:i,stale:i!==void 0,notices:n}}return t.nodes.length===0?{phase:`empty`,stale:!1,notices:n}:{phase:t.status===`partial`?`partial`:`ok`,render:t,stale:!1,notices:n}}var Me=new Set([te,`unknown_command`]),Ne=2e3,Pe=6e4;function Fe(e,t=Math.random){let n=Math.min(Ne*2**e,Pe);return Math.round(n*(.8+.4*t()))}var Ie=class{generation=0;connection;key;keyId;unsubscribe;retryTimer;attempt=0;lastRevision;isLive=!1;handlers;random;constructor(e,t=Math.random){this.handlers=e,this.random=t}get live(){return this.isLive}update(e,t){let n=t?JSON.stringify([t.entry_id,t.site_id,t.max_clients]):void 0;(e!==this.connection||n!==this.keyId)&&(this.stop(),this.connection=e,this.key=t,this.keyId=n,e&&(e.addEventListener(`ready`,this.onReady),e.addEventListener(`disconnected`,this.onDisconnected)),e&&t&&this.open())}stop(){this.generation++,this.clearRetry(),this.attempt=0,this.release(),this.connection?.removeEventListener(`ready`,this.onReady),this.connection?.removeEventListener(`disconnected`,this.onDisconnected),this.connection=void 0,this.key=void 0,this.keyId=void 0}clearRetry(){this.retryTimer!==void 0&&clearTimeout(this.retryTimer),this.retryTimer=void 0}drop(){this.generation++,this.clearRetry(),this.unsubscribe=void 0,this.isLive=!1,this.lastRevision=void 0}onDisconnected=()=>{this.drop(),this.handlers.onDisconnected()};onReady=()=>{this.drop(),this.attempt=0,this.key&&this.open(),this.handlers.onReconnected()};release(){let e=this.unsubscribe;this.unsubscribe=void 0,this.isLive=!1,this.lastRevision=void 0,e&&e().catch(()=>void 0)}open(){let e=++this.generation,{connection:t,key:n}=this;t&&n&&t.subscribeMessage(t=>{e===this.generation&&this.receive(t)},{type:f,entry_id:n.entry_id,site_id:n.site_id,max_clients:n.max_clients},{resubscribe:!1}).then(t=>{e===this.generation?this.unsubscribe=t:t().catch(()=>void 0)},t=>{if(e!==this.generation)return;let n=r(t);this.handlers.onError(n),Me.has(n.code)&&this.scheduleRetry()})}receive(e){let t;try{t=ue(e)}catch(e){e instanceof v?this.handlers.onIncompatible():this.handlers.onError({code:`invalid_payload`,message:String(e)});return}let n=t.issues.some(e=>e.code===xe);n||(this.isLive=!0,this.attempt=0),(t.revision===``||t.revision!==this.lastRevision)&&(this.lastRevision=t.revision,this.handlers.onSnapshot(t),n&&(this.generation++,this.release(),this.scheduleRetry()))}scheduleRetry(){let e=this.generation,t=Fe(this.attempt++,this.random);this.retryTimer=setTimeout(()=>{this.retryTimer=void 0,e===this.generation&&this.open()},t)}},Le=`group:unconnected`,Re=`group:root`,ze=e=>`group:${e}`,Be={gateway:0,switch:1,access_point:2,other:3,client:4},Ve=(e,t)=>e.name.localeCompare(t.name)||e.id.localeCompare(t.id),He=(e,t)=>Be[e.kind]-Be[t.kind]||Ve(e,t);function Ue(e,t){let n=e.toggledGroups.has(t);return e.clients===`expanded`?!n:n}var We=()=>({total:0,wired:0,wireless:0,offline:0});function Ge(e,t){e.total++,t.connection===`wired`&&e.wired++,t.connection===`wireless`&&e.wireless++,t.state===`offline`&&e.offline++}function Ke(e,t,n){let r=new Set;for(let i of e){let e=new Set,a=i.id;for(;a!==void 0&&!r.has(a);){e.add(a);let r=t.get(a);if(r!==void 0&&e.has(r)){t.delete(a),n.delete(a);break}a=r}for(let t of e)r.add(t)}}function qe(e,t){let n=new Map(e.nodes.map(e=>[e.id,e])),r=new Map,i=new Map;for(let t of e.edges){let e=n.get(t.source),a=n.get(t.target);e&&a&&e.id!==a.id&&a.kind!==`client`&&!r.has(e.id)&&(r.set(e.id,a.id),i.set(e.id,t))}Ke(e.nodes,r,i);let a=e.nodes.filter(e=>e.kind!==`client`).sort(He),o=e.nodes.filter(e=>e.kind===`client`).sort(Ve),s=new Map;for(let e of o){let t=r.get(e.id);if(t===void 0)continue;let n=s.get(t);n||s.set(t,n=We()),Ge(n,e)}let c=new Map,l=new Map,u=new Map,d=new Map,f=[],p=e=>t.kinds.has(e.kind),m=e=>{let t=[],i=r.get(e);for(;i!==void 0;){let e=n.get(i);if(p(e))return{id:i,skipped:t};t.push(e.kind),i=r.get(i)}return{id:void 0,skipped:t}},h=(e,t,n,r)=>{if(t===void 0){f.push(e);return}u.set(e,t),d.set(e,{childId:e,parentId:t,edge:n,viaHidden:[...new Set(r)]});let i=l.get(t);i?i.push(e):l.set(t,[e])};for(let e of a){if(!p(e))continue;c.set(e.id,{type:`device`,id:e.id,node:e});let t=m(e.id);h(e.id,t.id,i.get(e.id),t.skipped)}if(t.clients!==`hidden`&&t.kinds.has(`client`)){let e=new Map;for(let t of o){let i=r.get(t.id),a,o=[],s;if(i===void 0)s=Le;else{let e=n.get(i);if(p(e))a=i;else{let t=m(i);a=t.id,o=[e.kind,...t.skipped]}s=a===void 0?Re:ze(a)}let c=e.get(s);c||e.set(s,c={parent:a,members:[],skipped:new Set}),c.members.push(t);for(let e of o)c.skipped.add(e)}let a=[...e].sort(([e],[t])=>Number(e===Le)-Number(t===Le));for(let[e,n]of a){let r=We();for(let e of n.members)Ge(r,e);let a=Ue(t,e);if(c.set(e,{type:`group`,id:e,members:n.members,counts:r,expanded:a}),h(e,n.parent,void 0,n.skipped),a)for(let t of n.members)c.set(t.id,{type:`client`,id:t.id,node:t}),h(t.id,e,i.get(t.id),[])}}return{snapshot:e,roots:f,visuals:c,children:l,parentOf:u,links:d,nodes:n,realParent:r,edges:i,clientCounts:s,stats:{devices:a.length,clients:o.length,offlineDevices:a.filter(e=>e.state===`offline`).length}}}function Je(){let e,t,n;return(r,i)=>n&&r===e&&i===t?n:(e=r,t=i,n=qe(r,i),n)}function Ye(e,t){let n=e.parentOf.get(t);return n===void 0?e.roots:e.children.get(n)??[]}function Xe(e,t){for(let n of e.visuals.values())if(n.type===`group`&&n.members.some(e=>e.id===t))return n}var Ze={gateway:`kind.gateway`,switch:`kind.switch`,access_point:`kind.access_point`,client:`kind.client`,other:`kind.other`},D={online:`state.online`,offline:`state.offline`,unknown:`state.unknown`},Qe={graph:`view.graph`,list:`view.list`},$e={wired:`medium.wired`,wireless:`medium.wireless`,unknown:`medium.unknown`};function et(e,t){let n=[...e];return n.length>t?`${n.slice(0,t-1).join(``)}…`:e}var tt=e=>Number.isInteger(e)?String(e):e.toFixed(1);function nt(e){return e>=1e3?`${tt(e/1e3)}G`:`${e}M`}function rt(e){return e>=1e3?`${tt(e/1e3)} gigabit`:`${e} megabit`}function it(e){if(!e)return``;let t=[];return e.parent_port!==void 0&&t.push(`p${e.parent_port}`),e.speed_mbps&&t.push(nt(e.speed_mbps)),e.poe_power_w!==void 0&&t.push(`PoE`),t.join(` · `)}function O(e,t){return e.type===`group`?e.id===`group:unconnected`?t(`group.unconnected`):e.id===`group:root`?t(`group.root`):e.counts.total===1?t(`group.client_one`):t(`group.clients`,{count:e.counts.total}):e.node.name}function at(e){return e.type===`group`?e.counts.offline===e.counts.total?`offline`:`online`:e.node.state}function ot(e,t,n){if(t.type===`group`)return`${O(t,n)}: ${n(`group.summary`,{wireless:t.counts.wireless,offline:t.counts.offline})}`;let r=t.node,i=[n(`node.label`,{kind:n(Ze[r.kind]),name:r.name,state:n(D[r.state]).toLocaleLowerCase()})],a=e.clientCounts.get(r.id)?.total??0;a>0&&i.push(a===1?n(`node.client_one`):n(`node.clients`,{count:a}));let o=e.edges.get(r.id);return o?.parent_port===void 0?r.connection&&i.push(n($e[r.connection]).toLocaleLowerCase()):i.push(o.speed_mbps?n(`node.uplink_speed`,{port:o.parent_port,speed:rt(o.speed_mbps)}):n(`node.uplink`,{port:o.parent_port})),i.join(`, `)}var st=class extends d{static properties={model:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},narrow:{type:Boolean,reflect:!0},memberQuery:{state:!0}};constructor(){super(),this.narrow=!1,this.memberQuery=``}willUpdate(e){e.has(`selectedId`)&&(this.memberQuery=``)}render(){let{model:e,selectedId:t,localize:n}=this;if(!e||!t||!n)return w;let r=e.visuals.get(t);if(r?.type===`group`)return this.shell(O(r,n),this.groupBody(r,n));let i=e.nodes.get(t);if(!i)return w;let a=i.kind===`client`?this.clientBody(e,i,n):this.deviceBody(e,i,n);return this.shell(i.name,a)}shell(e,t){let n=this.localize;return C`<section class="panel" role="region" aria-label=${e}>
            <header>
                <h3 title=${e}>${e}</h3>
                <button
                    class="close"
                    aria-label=${n(`detail.close`)}
                    title=${n(`detail.close`)}
                    @click=${()=>_(this,`uit-close`)}
                >
                    ${E(b)}
                </button>
            </header>
            ${t}
        </section>`}rows(e){let t=e.filter(e=>e[1]!==void 0&&e[1]!==``);return C`<dl>
            ${t.map(([e,t])=>C`<div class="row">
                        <dt>${this.localize(e)}</dt>
                        <dd>${t}</dd>
                    </div>`)}
        </dl>`}uplinkRows(e,t,n,r){let i=e.realParent.get(t),a=e.edges.get(t),o;return a?.parent_port!==void 0&&(o=a.child_port===void 0?String(a.parent_port):`${a.parent_port} → ${a.child_port}`),[[`detail.parent`,i===void 0?void 0:e.nodes.get(i)?.name],[`detail.port`,o],[`detail.speed`,a?.speed_mbps?nt(a.speed_mbps):void 0],[`detail.medium`,r&&a?n($e[a.medium]):void 0],[`detail.poe`,a?.poe_power_w===void 0?void 0:`${a.poe_power_w.toFixed(1)} W`]]}deviceBody(e,t,n){let r=e.clientCounts.get(t.id),i=e.links.get(t.id)?.viaHidden??[];return C`${this.rows([[`detail.kind`,n(Ze[t.kind])],[`detail.model`,t.model],[`detail.state`,n(D[t.state])],...this.uplinkRows(e,t.id,n,!0),[`detail.clients`,r?n(`detail.clients_value`,{total:r.total,wired:r.wired,wireless:r.wireless}):void 0],[`detail.via_hidden`,i.length>0?i.map(e=>n(Ze[e])).join(`, `):void 0]])}
        ${t.ha_device_id?C`<button
                  class="action"
                  @click=${()=>a(`/config/devices/device/${encodeURIComponent(t.ha_device_id)}`)}
              >
                  ${E(x)}${n(`detail.open_device`)}
              </button>`:w}`}clientBody(e,t,n){return this.rows([[`detail.state`,n(D[t.state])],[`detail.connection`,t.connection?n($e[t.connection]):void 0],[`detail.vlan`,t.vlan_id===void 0?void 0:String(t.vlan_id)],[`detail.network`,t.network_name],...this.uplinkRows(e,t.id,n,!1)])}groupBody(e,n){let r=this.memberQuery.trim().toLowerCase(),i=r?e.members.filter(e=>e.name.toLowerCase().includes(r)):e.members,a=e.counts;return C`${this.rows([[`detail.clients`,n(`detail.clients_value`,{total:a.total,wired:a.wired,wireless:a.wireless})]])}
            <input
                type="search"
                .value=${this.memberQuery}
                placeholder=${n(`detail.search_members`)}
                aria-label=${n(`detail.search_members`)}
                @input=${e=>{this.memberQuery=e.target.value}}
            />
            <ul class="members">
                ${i.map(e=>C`<li>
                            <button
                                class="member ${e.state}"
                                @click=${()=>_(this,`uit-select`,{id:e.id})}
                            >
                                ${E(t(e))}<span
                                    class="name"
                                    title=${e.name}
                                    >${e.name}</span
                                >
                                ${e.state===`online`?w:C`<span class="state-text"
                                          >${n(D[e.state])}</span
                                      >`}
                            </button>
                        </li>`)}
            </ul>`}static styles=[ce,ge,p`
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
        `]};T(`uit-detail-panel`,st);var ct={svg:`http://www.w3.org/2000/svg`,xhtml:`http://www.w3.org/1999/xhtml`,xlink:`http://www.w3.org/1999/xlink`,xml:`http://www.w3.org/XML/1998/namespace`,xmlns:`http://www.w3.org/2000/xmlns/`};function lt(e){var t=e+=``,n=t.indexOf(`:`);return n>=0&&(t=e.slice(0,n))!==`xmlns`&&(e=e.slice(n+1)),ct.hasOwnProperty(t)?{space:ct[t],local:e}:e}function ut(e){return function(){var t=this.ownerDocument,n=this.namespaceURI;return n===`http://www.w3.org/1999/xhtml`&&t.documentElement.namespaceURI===`http://www.w3.org/1999/xhtml`?t.createElement(e):t.createElementNS(n,e)}}function dt(e){return function(){return this.ownerDocument.createElementNS(e.space,e.local)}}function ft(e){var t=lt(e);return(t.local?dt:ut)(t)}function pt(){}function mt(e){return e==null?pt:function(){return this.querySelector(e)}}function ht(e){typeof e!=`function`&&(e=mt(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=Array(o),c,l,u=0;u<o;++u)(c=a[u])&&(l=e.call(c,c.__data__,u,a))&&(`__data__`in c&&(l.__data__=c.__data__),s[u]=l);return new A(r,this._parents)}function gt(e){return e==null?[]:Array.isArray(e)?e:Array.from(e)}function _t(){return[]}function vt(e){return e==null?_t:function(){return this.querySelectorAll(e)}}function yt(e){return function(){return gt(e.apply(this,arguments))}}function bt(e){e=typeof e==`function`?yt(e):vt(e);for(var t=this._groups,n=t.length,r=[],i=[],a=0;a<n;++a)for(var o=t[a],s=o.length,c,l=0;l<s;++l)(c=o[l])&&(r.push(e.call(c,c.__data__,l,o)),i.push(c));return new A(r,i)}function xt(e){return function(){return this.matches(e)}}function St(e){return function(t){return t.matches(e)}}var Ct=Array.prototype.find;function wt(e){return function(){return Ct.call(this.children,e)}}function Tt(){return this.firstElementChild}function Et(e){return this.select(e==null?Tt:wt(typeof e==`function`?e:St(e)))}var Dt=Array.prototype.filter;function Ot(){return Array.from(this.children)}function kt(e){return function(){return Dt.call(this.children,e)}}function At(e){return this.selectAll(e==null?Ot:kt(typeof e==`function`?e:St(e)))}function jt(e){typeof e!=`function`&&(e=xt(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=[],c,l=0;l<o;++l)(c=a[l])&&e.call(c,c.__data__,l,a)&&s.push(c);return new A(r,this._parents)}function Mt(e){return Array(e.length)}function Nt(){return new A(this._enter||this._groups.map(Mt),this._parents)}function Pt(e,t){this.ownerDocument=e.ownerDocument,this.namespaceURI=e.namespaceURI,this._next=null,this._parent=e,this.__data__=t}Pt.prototype={constructor:Pt,appendChild:function(e){return this._parent.insertBefore(e,this._next)},insertBefore:function(e,t){return this._parent.insertBefore(e,t)},querySelector:function(e){return this._parent.querySelector(e)},querySelectorAll:function(e){return this._parent.querySelectorAll(e)}};function Ft(e){return function(){return e}}function It(e,t,n,r,i,a){for(var o=0,s,c=t.length,l=a.length;o<l;++o)(s=t[o])?(s.__data__=a[o],r[o]=s):n[o]=new Pt(e,a[o]);for(;o<c;++o)(s=t[o])&&(i[o]=s)}function Lt(e,t,n,r,i,a,o){var s,c,l=new Map,u=t.length,d=a.length,f=Array(u),p;for(s=0;s<u;++s)(c=t[s])&&(f[s]=p=o.call(c,c.__data__,s,t)+``,l.has(p)?i[s]=c:l.set(p,c));for(s=0;s<d;++s)p=o.call(e,a[s],s,a)+``,(c=l.get(p))?(r[s]=c,c.__data__=a[s],l.delete(p)):n[s]=new Pt(e,a[s]);for(s=0;s<u;++s)(c=t[s])&&l.get(f[s])===c&&(i[s]=c)}function Rt(e){return e.__data__}function zt(e,t){if(!arguments.length)return Array.from(this,Rt);var n=t?Lt:It,r=this._parents,i=this._groups;typeof e!=`function`&&(e=Ft(e));for(var a=i.length,o=Array(a),s=Array(a),c=Array(a),l=0;l<a;++l){var u=r[l],d=i[l],f=d.length,p=Bt(e.call(u,u&&u.__data__,l,r)),m=p.length,h=s[l]=Array(m),g=o[l]=Array(m);n(u,d,h,g,c[l]=Array(f),p,t);for(var _=0,v=0,y,b;_<m;++_)if(y=h[_]){for(_>=v&&(v=_+1);!(b=g[v])&&++v<m;);y._next=b||null}}return o=new A(o,r),o._enter=s,o._exit=c,o}function Bt(e){return typeof e==`object`&&`length`in e?e:Array.from(e)}function Vt(){return new A(this._exit||this._groups.map(Mt),this._parents)}function Ht(e,t,n){var r=this.enter(),i=this,a=this.exit();return typeof e==`function`?(r=e(r),r&&=r.selection()):r=r.append(e+``),t!=null&&(i=t(i),i&&=i.selection()),n==null?a.remove():n(a),r&&i?r.merge(i).order():i}function Ut(e){for(var t=e.selection?e.selection():e,n=this._groups,r=t._groups,i=n.length,a=r.length,o=Math.min(i,a),s=Array(i),c=0;c<o;++c)for(var l=n[c],u=r[c],d=l.length,f=s[c]=Array(d),p,m=0;m<d;++m)(p=l[m]||u[m])&&(f[m]=p);for(;c<i;++c)s[c]=n[c];return new A(s,this._parents)}function Wt(){for(var e=this._groups,t=-1,n=e.length;++t<n;)for(var r=e[t],i=r.length-1,a=r[i],o;--i>=0;)(o=r[i])&&(a&&o.compareDocumentPosition(a)^4&&a.parentNode.insertBefore(o,a),a=o);return this}function Gt(e){e||=Kt;function t(t,n){return t&&n?e(t.__data__,n.__data__):!t-!n}for(var n=this._groups,r=n.length,i=Array(r),a=0;a<r;++a){for(var o=n[a],s=o.length,c=i[a]=Array(s),l,u=0;u<s;++u)(l=o[u])&&(c[u]=l);c.sort(t)}return new A(i,this._parents).order()}function Kt(e,t){return e<t?-1:e>t?1:e>=t?0:NaN}function qt(){var e=arguments[0];return arguments[0]=this,e.apply(null,arguments),this}function Jt(){return Array.from(this)}function Yt(){for(var e=this._groups,t=0,n=e.length;t<n;++t)for(var r=e[t],i=0,a=r.length;i<a;++i){var o=r[i];if(o)return o}return null}function Xt(){let e=0;for(let t of this)++e;return e}function Zt(){return!this.node()}function Qt(e){for(var t=this._groups,n=0,r=t.length;n<r;++n)for(var i=t[n],a=0,o=i.length,s;a<o;++a)(s=i[a])&&e.call(s,s.__data__,a,i);return this}function $t(e){return function(){this.removeAttribute(e)}}function en(e){return function(){this.removeAttributeNS(e.space,e.local)}}function tn(e,t){return function(){this.setAttribute(e,t)}}function nn(e,t){return function(){this.setAttributeNS(e.space,e.local,t)}}function rn(e,t){return function(){var n=t.apply(this,arguments);n==null?this.removeAttribute(e):this.setAttribute(e,n)}}function an(e,t){return function(){var n=t.apply(this,arguments);n==null?this.removeAttributeNS(e.space,e.local):this.setAttributeNS(e.space,e.local,n)}}function on(e,t){var n=lt(e);if(arguments.length<2){var r=this.node();return n.local?r.getAttributeNS(n.space,n.local):r.getAttribute(n)}return this.each((t==null?n.local?en:$t:typeof t==`function`?n.local?an:rn:n.local?nn:tn)(n,t))}function sn(e){return e.ownerDocument&&e.ownerDocument.defaultView||e.document&&e||e.defaultView}function cn(e){return function(){this.style.removeProperty(e)}}function ln(e,t,n){return function(){this.style.setProperty(e,t,n)}}function un(e,t,n){return function(){var r=t.apply(this,arguments);r==null?this.style.removeProperty(e):this.style.setProperty(e,r,n)}}function dn(e,t,n){return arguments.length>1?this.each((t==null?cn:typeof t==`function`?un:ln)(e,t,n??``)):k(this.node(),e)}function k(e,t){return e.style.getPropertyValue(t)||sn(e).getComputedStyle(e,null).getPropertyValue(t)}function fn(e){return function(){delete this[e]}}function pn(e,t){return function(){this[e]=t}}function mn(e,t){return function(){var n=t.apply(this,arguments);n==null?delete this[e]:this[e]=n}}function hn(e,t){return arguments.length>1?this.each((t==null?fn:typeof t==`function`?mn:pn)(e,t)):this.node()[e]}function gn(e){return e.trim().split(/^|\s+/)}function _n(e){return e.classList||new vn(e)}function vn(e){this._node=e,this._names=gn(e.getAttribute(`class`)||``)}vn.prototype={add:function(e){this._names.indexOf(e)<0&&(this._names.push(e),this._node.setAttribute(`class`,this._names.join(` `)))},remove:function(e){var t=this._names.indexOf(e);t>=0&&(this._names.splice(t,1),this._node.setAttribute(`class`,this._names.join(` `)))},contains:function(e){return this._names.indexOf(e)>=0}};function yn(e,t){for(var n=_n(e),r=-1,i=t.length;++r<i;)n.add(t[r])}function bn(e,t){for(var n=_n(e),r=-1,i=t.length;++r<i;)n.remove(t[r])}function xn(e){return function(){yn(this,e)}}function Sn(e){return function(){bn(this,e)}}function Cn(e,t){return function(){(t.apply(this,arguments)?yn:bn)(this,e)}}function wn(e,t){var n=gn(e+``);if(arguments.length<2){for(var r=_n(this.node()),i=-1,a=n.length;++i<a;)if(!r.contains(n[i]))return!1;return!0}return this.each((typeof t==`function`?Cn:t?xn:Sn)(n,t))}function Tn(){this.textContent=``}function En(e){return function(){this.textContent=e}}function Dn(e){return function(){var t=e.apply(this,arguments);this.textContent=t??``}}function On(e){return arguments.length?this.each(e==null?Tn:(typeof e==`function`?Dn:En)(e)):this.node().textContent}function kn(){this.innerHTML=``}function An(e){return function(){this.innerHTML=e}}function jn(e){return function(){var t=e.apply(this,arguments);this.innerHTML=t??``}}function Mn(e){return arguments.length?this.each(e==null?kn:(typeof e==`function`?jn:An)(e)):this.node().innerHTML}function Nn(){this.nextSibling&&this.parentNode.appendChild(this)}function Pn(){return this.each(Nn)}function Fn(){this.previousSibling&&this.parentNode.insertBefore(this,this.parentNode.firstChild)}function In(){return this.each(Fn)}function Ln(e){var t=typeof e==`function`?e:ft(e);return this.select(function(){return this.appendChild(t.apply(this,arguments))})}function Rn(){return null}function zn(e,t){var n=typeof e==`function`?e:ft(e),r=t==null?Rn:typeof t==`function`?t:mt(t);return this.select(function(){return this.insertBefore(n.apply(this,arguments),r.apply(this,arguments)||null)})}function Bn(){var e=this.parentNode;e&&e.removeChild(this)}function Vn(){return this.each(Bn)}function Hn(){var e=this.cloneNode(!1),t=this.parentNode;return t?t.insertBefore(e,this.nextSibling):e}function Un(){var e=this.cloneNode(!0),t=this.parentNode;return t?t.insertBefore(e,this.nextSibling):e}function Wn(e){return this.select(e?Un:Hn)}function Gn(e){return arguments.length?this.property(`__data__`,e):this.node().__data__}function Kn(e){return function(t){e.call(this,t,this.__data__)}}function qn(e){return e.trim().split(/^|\s+/).map(function(e){var t=``,n=e.indexOf(`.`);return n>=0&&(t=e.slice(n+1),e=e.slice(0,n)),{type:e,name:t}})}function Jn(e){return function(){var t=this.__on;if(t){for(var n=0,r=-1,i=t.length,a;n<i;++n)a=t[n],(!e.type||a.type===e.type)&&a.name===e.name?this.removeEventListener(a.type,a.listener,a.options):t[++r]=a;++r?t.length=r:delete this.__on}}}function Yn(e,t,n){return function(){var r=this.__on,i,a=Kn(t);if(r){for(var o=0,s=r.length;o<s;++o)if((i=r[o]).type===e.type&&i.name===e.name){this.removeEventListener(i.type,i.listener,i.options),this.addEventListener(i.type,i.listener=a,i.options=n),i.value=t;return}}this.addEventListener(e.type,a,n),i={type:e.type,name:e.name,value:t,listener:a,options:n},r?r.push(i):this.__on=[i]}}function Xn(e,t,n){var r=qn(e+``),i,a=r.length,o;if(arguments.length<2){var s=this.node().__on;if(s){for(var c=0,l=s.length,u;c<l;++c)for(i=0,u=s[c];i<a;++i)if((o=r[i]).type===u.type&&o.name===u.name)return u.value}return}for(s=t?Yn:Jn,i=0;i<a;++i)this.each(s(r[i],t,n));return this}function Zn(e,t,n){var r=sn(e),i=r.CustomEvent;typeof i==`function`?i=new i(t,n):(i=r.document.createEvent(`Event`),n?(i.initEvent(t,n.bubbles,n.cancelable),i.detail=n.detail):i.initEvent(t,!1,!1)),e.dispatchEvent(i)}function Qn(e,t){return function(){return Zn(this,e,t)}}function $n(e,t){return function(){return Zn(this,e,t.apply(this,arguments))}}function er(e,t){return this.each((typeof t==`function`?$n:Qn)(e,t))}function*tr(){for(var e=this._groups,t=0,n=e.length;t<n;++t)for(var r=e[t],i=0,a=r.length,o;i<a;++i)(o=r[i])&&(yield o)}var nr=[null];function A(e,t){this._groups=e,this._parents=t}function j(){return new A([[document.documentElement]],nr)}function rr(){return this}A.prototype=j.prototype={constructor:A,select:ht,selectAll:bt,selectChild:Et,selectChildren:At,filter:jt,data:zt,enter:Nt,exit:Vt,join:Ht,merge:Ut,selection:rr,order:Wt,sort:Gt,call:qt,nodes:Jt,node:Yt,size:Xt,empty:Zt,each:Qt,attr:on,style:dn,property:hn,classed:wn,text:On,html:Mn,raise:Pn,lower:In,append:Ln,insert:zn,remove:Vn,clone:Wn,datum:Gn,on:Xn,dispatch:er,[Symbol.iterator]:tr};function M(e){return typeof e==`string`?new A([[document.querySelector(e)]],[document.documentElement]):new A([[e]],nr)}function ir(e){let t;for(;t=e.sourceEvent;)e=t;return e}function N(e,t){if(e=ir(e),t===void 0&&(t=e.currentTarget),t){var n=t.ownerSVGElement||t;if(n.createSVGPoint){var r=n.createSVGPoint();return r.x=e.clientX,r.y=e.clientY,r=r.matrixTransform(t.getScreenCTM().inverse()),[r.x,r.y]}if(t.getBoundingClientRect){var i=t.getBoundingClientRect();return[e.clientX-i.left-t.clientLeft,e.clientY-i.top-t.clientTop]}}return[e.pageX,e.pageY]}var ar={value:()=>{}};function or(){for(var e=0,t=arguments.length,n={},r;e<t;++e){if(!(r=arguments[e]+``)||r in n||/[\s.]/.test(r))throw Error(`illegal type: `+r);n[r]=[]}return new sr(n)}function sr(e){this._=e}function cr(e,t){return e.trim().split(/^|\s+/).map(function(e){var n=``,r=e.indexOf(`.`);if(r>=0&&(n=e.slice(r+1),e=e.slice(0,r)),e&&!t.hasOwnProperty(e))throw Error(`unknown type: `+e);return{type:e,name:n}})}sr.prototype=or.prototype={constructor:sr,on:function(e,t){var n=this._,r=cr(e+``,n),i,a=-1,o=r.length;if(arguments.length<2){for(;++a<o;)if((i=(e=r[a]).type)&&(i=lr(n[i],e.name)))return i;return}if(t!=null&&typeof t!=`function`)throw Error(`invalid callback: `+t);for(;++a<o;)if(i=(e=r[a]).type)n[i]=ur(n[i],e.name,t);else if(t==null)for(i in n)n[i]=ur(n[i],e.name,null);return this},copy:function(){var e={},t=this._;for(var n in t)e[n]=t[n].slice();return new sr(e)},call:function(e,t){if((i=arguments.length-2)>0)for(var n=Array(i),r=0,i,a;r<i;++r)n[r]=arguments[r+2];if(!this._.hasOwnProperty(e))throw Error(`unknown type: `+e);for(a=this._[e],r=0,i=a.length;r<i;++r)a[r].value.apply(t,n)},apply:function(e,t,n){if(!this._.hasOwnProperty(e))throw Error(`unknown type: `+e);for(var r=this._[e],i=0,a=r.length;i<a;++i)r[i].value.apply(t,n)}};function lr(e,t){for(var n=0,r=e.length,i;n<r;++n)if((i=e[n]).name===t)return i.value}function ur(e,t,n){for(var r=0,i=e.length;r<i;++r)if(e[r].name===t){e[r]=ar,e=e.slice(0,r).concat(e.slice(r+1));break}return n!=null&&e.push({name:t,value:n}),e}var P=0,dr=0,fr=0,pr=1e3,mr,F,hr=0,I=0,gr=0,L=typeof performance==`object`&&performance.now?performance:Date,_r=typeof window==`object`&&window.requestAnimationFrame?window.requestAnimationFrame.bind(window):function(e){setTimeout(e,17)};function vr(){return I||=(_r(yr),L.now()+gr)}function yr(){I=0}function br(){this._call=this._time=this._next=null}br.prototype=xr.prototype={constructor:br,restart:function(e,t,n){if(typeof e!=`function`)throw TypeError(`callback is not a function`);n=(n==null?vr():+n)+(t==null?0:+t),!this._next&&F!==this&&(F?F._next=this:mr=this,F=this),this._call=e,this._time=n,Er()},stop:function(){this._call&&(this._call=null,this._time=1/0,Er())}};function xr(e,t,n){var r=new br;return r.restart(e,t,n),r}function Sr(){vr(),++P;for(var e=mr,t;e;)(t=I-e._time)>=0&&e._call.call(void 0,t),e=e._next;--P}function Cr(){I=(hr=L.now())+gr,P=dr=0;try{Sr()}finally{P=0,Tr(),I=0}}function wr(){var e=L.now(),t=e-hr;t>pr&&(gr-=t,hr=e)}function Tr(){for(var e,t=mr,n,r=1/0;t;)t._call?(r>t._time&&(r=t._time),e=t,t=t._next):(n=t._next,t._next=null,t=e?e._next=n:mr=n);F=e,Er(r)}function Er(e){P||(dr&&=clearTimeout(dr),e-I>24?(e<1/0&&(dr=setTimeout(Cr,e-L.now()-gr)),fr&&=clearInterval(fr)):(fr||=(hr=L.now(),setInterval(wr,pr)),P=1,_r(Cr)))}function Dr(e,t,n){var r=new br;return t=t==null?0:+t,r.restart(n=>{r.stop(),e(n+t)},t,n),r}var Or=or(`start`,`end`,`cancel`,`interrupt`),kr=[];function Ar(e,t,n,r,i,a){var o=e.__transition;if(!o)e.__transition={};else if(n in o)return;Mr(e,n,{name:t,index:r,group:i,on:Or,tween:kr,time:a.time,delay:a.delay,duration:a.duration,ease:a.ease,timer:null,state:0})}function jr(e,t){var n=z(e,t);if(n.state>0)throw Error(`too late; already scheduled`);return n}function R(e,t){var n=z(e,t);if(n.state>3)throw Error(`too late; already running`);return n}function z(e,t){var n=e.__transition;if(!n||!(n=n[t]))throw Error(`transition not found`);return n}function Mr(e,t,n){var r=e.__transition,i;r[t]=n,n.timer=xr(a,0,n.time);function a(e){n.state=1,n.timer.restart(o,n.delay,n.time),n.delay<=e&&o(e-n.delay)}function o(a){var l,u,d,f;if(n.state!==1)return c();for(l in r)if(f=r[l],f.name===n.name){if(f.state===3)return Dr(o);f.state===4?(f.state=6,f.timer.stop(),f.on.call(`interrupt`,e,e.__data__,f.index,f.group),delete r[l]):+l<t&&(f.state=6,f.timer.stop(),f.on.call(`cancel`,e,e.__data__,f.index,f.group),delete r[l])}if(Dr(function(){n.state===3&&(n.state=4,n.timer.restart(s,n.delay,n.time),s(a))}),n.state=2,n.on.call(`start`,e,e.__data__,n.index,n.group),n.state===2){for(n.state=3,i=Array(d=n.tween.length),l=0,u=-1;l<d;++l)(f=n.tween[l].value.call(e,e.__data__,n.index,n.group))&&(i[++u]=f);i.length=u+1}}function s(t){for(var r=t<n.duration?n.ease.call(null,t/n.duration):(n.timer.restart(c),n.state=5,1),a=-1,o=i.length;++a<o;)i[a].call(e,r);n.state===5&&(n.on.call(`end`,e,e.__data__,n.index,n.group),c())}function c(){for(var i in n.state=6,n.timer.stop(),delete r[t],r)return;delete e.__transition}}function Nr(e,t){var n=e.__transition,r,i,a=!0,o;if(n){for(o in t=t==null?null:t+``,n){if((r=n[o]).name!==t){a=!1;continue}i=r.state>2&&r.state<5,r.state=6,r.timer.stop(),r.on.call(i?`interrupt`:`cancel`,e,e.__data__,r.index,r.group),delete n[o]}a&&delete e.__transition}}function Pr(e){return this.each(function(){Nr(this,e)})}function Fr(e,t,n){e.prototype=t.prototype=n,n.constructor=e}function Ir(e,t){var n=Object.create(e.prototype);for(var r in t)n[r]=t[r];return n}function Lr(){}var B=.7,Rr=1/B,V=`\\s*([+-]?\\d+)\\s*`,H=`\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)\\s*`,U=`\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)%\\s*`,zr=/^#([0-9a-f]{3,8})$/,Br=RegExp(`^rgb\\(${V},${V},${V}\\)$`),Vr=RegExp(`^rgb\\(${U},${U},${U}\\)$`),Hr=RegExp(`^rgba\\(${V},${V},${V},${H}\\)$`),Ur=RegExp(`^rgba\\(${U},${U},${U},${H}\\)$`),Wr=RegExp(`^hsl\\(${H},${U},${U}\\)$`),Gr=RegExp(`^hsla\\(${H},${U},${U},${H}\\)$`),Kr={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074};Fr(Lr,W,{copy(e){return Object.assign(new this.constructor,this,e)},displayable(){return this.rgb().displayable()},hex:qr,formatHex:qr,formatHex8:Jr,formatHsl:Yr,formatRgb:Xr,toString:Xr});function qr(){return this.rgb().formatHex()}function Jr(){return this.rgb().formatHex8()}function Yr(){return oi(this).formatHsl()}function Xr(){return this.rgb().formatRgb()}function W(e){var t,n;return e=(e+``).trim().toLowerCase(),(t=zr.exec(e))?(n=t[1].length,t=parseInt(t[1],16),n===6?Zr(t):n===3?new G(t>>8&15|t>>4&240,t>>4&15|t&240,(t&15)<<4|t&15,1):n===8?Qr(t>>24&255,t>>16&255,t>>8&255,(t&255)/255):n===4?Qr(t>>12&15|t>>8&240,t>>8&15|t>>4&240,t>>4&15|t&240,((t&15)<<4|t&15)/255):null):(t=Br.exec(e))?new G(t[1],t[2],t[3],1):(t=Vr.exec(e))?new G(t[1]*255/100,t[2]*255/100,t[3]*255/100,1):(t=Hr.exec(e))?Qr(t[1],t[2],t[3],t[4]):(t=Ur.exec(e))?Qr(t[1]*255/100,t[2]*255/100,t[3]*255/100,t[4]):(t=Wr.exec(e))?ai(t[1],t[2]/100,t[3]/100,1):(t=Gr.exec(e))?ai(t[1],t[2]/100,t[3]/100,t[4]):Kr.hasOwnProperty(e)?Zr(Kr[e]):e===`transparent`?new G(NaN,NaN,NaN,0):null}function Zr(e){return new G(e>>16&255,e>>8&255,e&255,1)}function Qr(e,t,n,r){return r<=0&&(e=t=n=NaN),new G(e,t,n,r)}function $r(e){return e instanceof Lr||(e=W(e)),e?(e=e.rgb(),new G(e.r,e.g,e.b,e.opacity)):new G}function ei(e,t,n,r){return arguments.length===1?$r(e):new G(e,t,n,r??1)}function G(e,t,n,r){this.r=+e,this.g=+t,this.b=+n,this.opacity=+r}Fr(G,ei,Ir(Lr,{brighter(e){return e=e==null?Rr:Rr**+e,new G(this.r*e,this.g*e,this.b*e,this.opacity)},darker(e){return e=e==null?B:B**+e,new G(this.r*e,this.g*e,this.b*e,this.opacity)},rgb(){return this},clamp(){return new G(K(this.r),K(this.g),K(this.b),ii(this.opacity))},displayable(){return-.5<=this.r&&this.r<255.5&&-.5<=this.g&&this.g<255.5&&-.5<=this.b&&this.b<255.5&&0<=this.opacity&&this.opacity<=1},hex:ti,formatHex:ti,formatHex8:ni,formatRgb:ri,toString:ri}));function ti(){return`#${q(this.r)}${q(this.g)}${q(this.b)}`}function ni(){return`#${q(this.r)}${q(this.g)}${q(this.b)}${q((isNaN(this.opacity)?1:this.opacity)*255)}`}function ri(){let e=ii(this.opacity);return`${e===1?`rgb(`:`rgba(`}${K(this.r)}, ${K(this.g)}, ${K(this.b)}${e===1?`)`:`, ${e})`}`}function ii(e){return isNaN(e)?1:Math.max(0,Math.min(1,e))}function K(e){return Math.max(0,Math.min(255,Math.round(e)||0))}function q(e){return e=K(e),(e<16?`0`:``)+e.toString(16)}function ai(e,t,n,r){return r<=0?e=t=n=NaN:n<=0||n>=1?e=t=NaN:t<=0&&(e=NaN),new J(e,t,n,r)}function oi(e){if(e instanceof J)return new J(e.h,e.s,e.l,e.opacity);if(e instanceof Lr||(e=W(e)),!e)return new J;if(e instanceof J)return e;e=e.rgb();var t=e.r/255,n=e.g/255,r=e.b/255,i=Math.min(t,n,r),a=Math.max(t,n,r),o=NaN,s=a-i,c=(a+i)/2;return s?(o=t===a?(n-r)/s+(n<r)*6:n===a?(r-t)/s+2:(t-n)/s+4,s/=c<.5?a+i:2-a-i,o*=60):s=c>0&&c<1?0:o,new J(o,s,c,e.opacity)}function si(e,t,n,r){return arguments.length===1?oi(e):new J(e,t,n,r??1)}function J(e,t,n,r){this.h=+e,this.s=+t,this.l=+n,this.opacity=+r}Fr(J,si,Ir(Lr,{brighter(e){return e=e==null?Rr:Rr**+e,new J(this.h,this.s,this.l*e,this.opacity)},darker(e){return e=e==null?B:B**+e,new J(this.h,this.s,this.l*e,this.opacity)},rgb(){var e=this.h%360+(this.h<0)*360,t=isNaN(e)||isNaN(this.s)?0:this.s,n=this.l,r=n+(n<.5?n:1-n)*t,i=2*n-r;return new G(ui(e>=240?e-240:e+120,i,r),ui(e,i,r),ui(e<120?e+240:e-120,i,r),this.opacity)},clamp(){return new J(ci(this.h),li(this.s),li(this.l),ii(this.opacity))},displayable(){return(0<=this.s&&this.s<=1||isNaN(this.s))&&0<=this.l&&this.l<=1&&0<=this.opacity&&this.opacity<=1},formatHsl(){let e=ii(this.opacity);return`${e===1?`hsl(`:`hsla(`}${ci(this.h)}, ${li(this.s)*100}%, ${li(this.l)*100}%${e===1?`)`:`, ${e})`}`}}));function ci(e){return e=(e||0)%360,e<0?e+360:e}function li(e){return Math.max(0,Math.min(1,e||0))}function ui(e,t,n){return(e<60?t+(n-t)*e/60:e<180?n:e<240?t+(n-t)*(240-e)/60:t)*255}var di=e=>()=>e;function fi(e,t){return function(n){return e+n*t}}function pi(e,t,n){return e**=+n,t=t**+n-e,n=1/n,function(r){return(e+r*t)**+n}}function mi(e){return(e=+e)==1?hi:function(t,n){return n-t?pi(t,n,e):di(isNaN(t)?n:t)}}function hi(e,t){var n=t-e;return n?fi(e,n):di(isNaN(e)?t:e)}var gi=(function e(t){var n=mi(t);function r(e,t){var r=n((e=ei(e)).r,(t=ei(t)).r),i=n(e.g,t.g),a=n(e.b,t.b),o=hi(e.opacity,t.opacity);return function(t){return e.r=r(t),e.g=i(t),e.b=a(t),e.opacity=o(t),e+``}}return r.gamma=e,r})(1);function Y(e,t){return e=+e,t=+t,function(n){return e*(1-n)+t*n}}var _i=/[-+]?(?:\d+\.?\d*|\.?\d+)(?:[eE][-+]?\d+)?/g,vi=new RegExp(_i.source,`g`);function yi(e){return function(){return e}}function bi(e){return function(t){return e(t)+``}}function xi(e,t){var n=_i.lastIndex=vi.lastIndex=0,r,i,a,o=-1,s=[],c=[];for(e+=``,t+=``;(r=_i.exec(e))&&(i=vi.exec(t));)(a=i.index)>n&&(a=t.slice(n,a),s[o]?s[o]+=a:s[++o]=a),(r=r[0])===(i=i[0])?s[o]?s[o]+=i:s[++o]=i:(s[++o]=null,c.push({i:o,x:Y(r,i)})),n=vi.lastIndex;return n<t.length&&(a=t.slice(n),s[o]?s[o]+=a:s[++o]=a),s.length<2?c[0]?bi(c[0].x):yi(t):(t=c.length,function(e){for(var n=0,r;n<t;++n)s[(r=c[n]).i]=r.x(e);return s.join(``)})}var Si=180/Math.PI,Ci={translateX:0,translateY:0,rotate:0,skewX:0,scaleX:1,scaleY:1};function wi(e,t,n,r,i,a){var o,s,c;return(o=Math.sqrt(e*e+t*t))&&(e/=o,t/=o),(c=e*n+t*r)&&(n-=e*c,r-=t*c),(s=Math.sqrt(n*n+r*r))&&(n/=s,r/=s,c/=s),e*r<t*n&&(e=-e,t=-t,c=-c,o=-o),{translateX:i,translateY:a,rotate:Math.atan2(t,e)*Si,skewX:Math.atan(c)*Si,scaleX:o,scaleY:s}}var Ti;function Ei(e){let t=new(typeof DOMMatrix==`function`?DOMMatrix:WebKitCSSMatrix)(e+``);return t.isIdentity?Ci:wi(t.a,t.b,t.c,t.d,t.e,t.f)}function Di(e){return e==null||(Ti||=document.createElementNS(`http://www.w3.org/2000/svg`,`g`),Ti.setAttribute(`transform`,e),!(e=Ti.transform.baseVal.consolidate()))?Ci:(e=e.matrix,wi(e.a,e.b,e.c,e.d,e.e,e.f))}function Oi(e,t,n,r){function i(e){return e.length?e.pop()+` `:``}function a(e,r,i,a,o,s){if(e!==i||r!==a){var c=o.push(`translate(`,null,t,null,n);s.push({i:c-4,x:Y(e,i)},{i:c-2,x:Y(r,a)})}else(i||a)&&o.push(`translate(`+i+t+a+n)}function o(e,t,n,a){e===t?t&&n.push(i(n)+`rotate(`+t+r):(e-t>180?t+=360:t-e>180&&(e+=360),a.push({i:n.push(i(n)+`rotate(`,null,r)-2,x:Y(e,t)}))}function s(e,t,n,a){e===t?t&&n.push(i(n)+`skewX(`+t+r):a.push({i:n.push(i(n)+`skewX(`,null,r)-2,x:Y(e,t)})}function c(e,t,n,r,a,o){if(e!==n||t!==r){var s=a.push(i(a)+`scale(`,null,`,`,null,`)`);o.push({i:s-4,x:Y(e,n)},{i:s-2,x:Y(t,r)})}else(n!==1||r!==1)&&a.push(i(a)+`scale(`+n+`,`+r+`)`)}return function(t,n){var r=[],i=[];return t=e(t),n=e(n),a(t.translateX,t.translateY,n.translateX,n.translateY,r,i),o(t.rotate,n.rotate,r,i),s(t.skewX,n.skewX,r,i),c(t.scaleX,t.scaleY,n.scaleX,n.scaleY,r,i),t=n=null,function(e){for(var t=-1,n=i.length,a;++t<n;)r[(a=i[t]).i]=a.x(e);return r.join(``)}}}var ki=Oi(Ei,`px, `,`px)`,`deg)`),Ai=Oi(Di,`, `,`)`,`)`),ji=1e-12;function Mi(e){return((e=Math.exp(e))+1/e)/2}function Ni(e){return((e=Math.exp(e))-1/e)/2}function Pi(e){return((e=Math.exp(2*e))-1)/(e+1)}var Fi=(function e(t,n,r){function i(e,i){var a=e[0],o=e[1],s=e[2],c=i[0],l=i[1],u=i[2],d=c-a,f=l-o,p=d*d+f*f,m,h;if(p<ji)h=Math.log(u/s)/t,m=function(e){return[a+e*d,o+e*f,s*Math.exp(t*e*h)]};else{var g=Math.sqrt(p),_=(u*u-s*s+r*p)/(2*s*n*g),v=(u*u-s*s-r*p)/(2*u*n*g),y=Math.log(Math.sqrt(_*_+1)-_);h=(Math.log(Math.sqrt(v*v+1)-v)-y)/t,m=function(e){var r=e*h,i=Mi(y),c=s/(n*g)*(i*Pi(t*r+y)-Ni(y));return[a+c*d,o+c*f,s*i/Mi(t*r+y)]}}return m.duration=h*1e3*t/Math.SQRT2,m}return i.rho=function(t){var n=Math.max(.001,+t),r=n*n;return e(n,r,r*r)},i})(Math.SQRT2,2,4);function Ii(e,t){var n,r;return function(){var i=R(this,e),a=i.tween;if(a!==n){r=n=a;for(var o=0,s=r.length;o<s;++o)if(r[o].name===t){r=r.slice(),r.splice(o,1);break}}i.tween=r}}function Li(e,t,n){var r,i;if(typeof n!=`function`)throw Error();return function(){var a=R(this,e),o=a.tween;if(o!==r){i=(r=o).slice();for(var s={name:t,value:n},c=0,l=i.length;c<l;++c)if(i[c].name===t){i[c]=s;break}c===l&&i.push(s)}a.tween=i}}function Ri(e,t){var n=this._id;if(e+=``,arguments.length<2){for(var r=z(this.node(),n).tween,i=0,a=r.length,o;i<a;++i)if((o=r[i]).name===e)return o.value;return null}return this.each((t==null?Ii:Li)(n,e,t))}function zi(e,t,n){var r=e._id;return e.each(function(){var e=R(this,r);(e.value||={})[t]=n.apply(this,arguments)}),function(e){return z(e,r).value[t]}}function Bi(e,t){var n;return(typeof t==`number`?Y:t instanceof W?gi:(n=W(t))?(t=n,gi):xi)(e,t)}function Vi(e){return function(){this.removeAttribute(e)}}function Hi(e){return function(){this.removeAttributeNS(e.space,e.local)}}function Ui(e,t,n){var r,i=n+``,a;return function(){var o=this.getAttribute(e);return o===i?null:o===r?a:a=t(r=o,n)}}function Wi(e,t,n){var r,i=n+``,a;return function(){var o=this.getAttributeNS(e.space,e.local);return o===i?null:o===r?a:a=t(r=o,n)}}function Gi(e,t,n){var r,i,a;return function(){var o,s=n(this),c;return s==null?void this.removeAttribute(e):(o=this.getAttribute(e),c=s+``,o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s)))}}function Ki(e,t,n){var r,i,a;return function(){var o,s=n(this),c;return s==null?void this.removeAttributeNS(e.space,e.local):(o=this.getAttributeNS(e.space,e.local),c=s+``,o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s)))}}function qi(e,t){var n=lt(e),r=n===`transform`?Ai:Bi;return this.attrTween(e,typeof t==`function`?(n.local?Ki:Gi)(n,r,zi(this,`attr.`+e,t)):t==null?(n.local?Hi:Vi)(n):(n.local?Wi:Ui)(n,r,t))}function Ji(e,t){return function(n){this.setAttribute(e,t.call(this,n))}}function Yi(e,t){return function(n){this.setAttributeNS(e.space,e.local,t.call(this,n))}}function Xi(e,t){var n,r;function i(){var i=t.apply(this,arguments);return i!==r&&(n=(r=i)&&Yi(e,i)),n}return i._value=t,i}function Zi(e,t){var n,r;function i(){var i=t.apply(this,arguments);return i!==r&&(n=(r=i)&&Ji(e,i)),n}return i._value=t,i}function Qi(e,t){var n=`attr.`+e;if(arguments.length<2)return(n=this.tween(n))&&n._value;if(t==null)return this.tween(n,null);if(typeof t!=`function`)throw Error();var r=lt(e);return this.tween(n,(r.local?Xi:Zi)(r,t))}function $i(e,t){return function(){jr(this,e).delay=+t.apply(this,arguments)}}function ea(e,t){return t=+t,function(){jr(this,e).delay=t}}function ta(e){var t=this._id;return arguments.length?this.each((typeof e==`function`?$i:ea)(t,e)):z(this.node(),t).delay}function na(e,t){return function(){R(this,e).duration=+t.apply(this,arguments)}}function ra(e,t){return t=+t,function(){R(this,e).duration=t}}function ia(e){var t=this._id;return arguments.length?this.each((typeof e==`function`?na:ra)(t,e)):z(this.node(),t).duration}function aa(e,t){if(typeof t!=`function`)throw Error();return function(){R(this,e).ease=t}}function oa(e){var t=this._id;return arguments.length?this.each(aa(t,e)):z(this.node(),t).ease}function sa(e,t){return function(){var n=t.apply(this,arguments);if(typeof n!=`function`)throw Error();R(this,e).ease=n}}function ca(e){if(typeof e!=`function`)throw Error();return this.each(sa(this._id,e))}function la(e){typeof e!=`function`&&(e=xt(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=[],c,l=0;l<o;++l)(c=a[l])&&e.call(c,c.__data__,l,a)&&s.push(c);return new X(r,this._parents,this._name,this._id)}function ua(e){if(e._id!==this._id)throw Error();for(var t=this._groups,n=e._groups,r=t.length,i=n.length,a=Math.min(r,i),o=Array(r),s=0;s<a;++s)for(var c=t[s],l=n[s],u=c.length,d=o[s]=Array(u),f,p=0;p<u;++p)(f=c[p]||l[p])&&(d[p]=f);for(;s<r;++s)o[s]=t[s];return new X(o,this._parents,this._name,this._id)}function da(e){return(e+``).trim().split(/^|\s+/).every(function(e){var t=e.indexOf(`.`);return t>=0&&(e=e.slice(0,t)),!e||e===`start`})}function fa(e,t,n){var r,i,a=da(t)?jr:R;return function(){var o=a(this,e),s=o.on;s!==r&&(i=(r=s).copy()).on(t,n),o.on=i}}function pa(e,t){var n=this._id;return arguments.length<2?z(this.node(),n).on.on(e):this.each(fa(n,e,t))}function ma(e){return function(){var t=this.parentNode;for(var n in this.__transition)if(+n!==e)return;t&&t.removeChild(this)}}function ha(){return this.on(`end.remove`,ma(this._id))}function ga(e){var t=this._name,n=this._id;typeof e!=`function`&&(e=mt(e));for(var r=this._groups,i=r.length,a=Array(i),o=0;o<i;++o)for(var s=r[o],c=s.length,l=a[o]=Array(c),u,d,f=0;f<c;++f)(u=s[f])&&(d=e.call(u,u.__data__,f,s))&&(`__data__`in u&&(d.__data__=u.__data__),l[f]=d,Ar(l[f],t,n,f,l,z(u,n)));return new X(a,this._parents,t,n)}function _a(e){var t=this._name,n=this._id;typeof e!=`function`&&(e=vt(e));for(var r=this._groups,i=r.length,a=[],o=[],s=0;s<i;++s)for(var c=r[s],l=c.length,u,d=0;d<l;++d)if(u=c[d]){for(var f=e.call(u,u.__data__,d,c),p,m=z(u,n),h=0,g=f.length;h<g;++h)(p=f[h])&&Ar(p,t,n,h,f,m);a.push(f),o.push(u)}return new X(a,o,t,n)}var va=j.prototype.constructor;function ya(){return new va(this._groups,this._parents)}function ba(e,t){var n,r,i;return function(){var a=k(this,e),o=(this.style.removeProperty(e),k(this,e));return a===o?null:a===n&&o===r?i:i=t(n=a,r=o)}}function xa(e){return function(){this.style.removeProperty(e)}}function Sa(e,t,n){var r,i=n+``,a;return function(){var o=k(this,e);return o===i?null:o===r?a:a=t(r=o,n)}}function Ca(e,t,n){var r,i,a;return function(){var o=k(this,e),s=n(this),c=s+``;return s??(c=s=(this.style.removeProperty(e),k(this,e))),o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s))}}function wa(e,t){var n,r,i,a=`style.`+t,o=`end.`+a,s;return function(){var c=R(this,e),l=c.on,u=c.value[a]==null?s||=xa(t):void 0;(l!==n||i!==u)&&(r=(n=l).copy()).on(o,i=u),c.on=r}}function Ta(e,t,n){var r=(e+=``)==`transform`?ki:Bi;return t==null?this.styleTween(e,ba(e,r)).on(`end.style.`+e,xa(e)):typeof t==`function`?this.styleTween(e,Ca(e,r,zi(this,`style.`+e,t))).each(wa(this._id,e)):this.styleTween(e,Sa(e,r,t),n).on(`end.style.`+e,null)}function Ea(e,t,n){return function(r){this.style.setProperty(e,t.call(this,r),n)}}function Da(e,t,n){var r,i;function a(){var a=t.apply(this,arguments);return a!==i&&(r=(i=a)&&Ea(e,a,n)),r}return a._value=t,a}function Oa(e,t,n){var r=`style.`+(e+=``);if(arguments.length<2)return(r=this.tween(r))&&r._value;if(t==null)return this.tween(r,null);if(typeof t!=`function`)throw Error();return this.tween(r,Da(e,t,n??``))}function ka(e){return function(){this.textContent=e}}function Aa(e){return function(){var t=e(this);this.textContent=t??``}}function ja(e){return this.tween(`text`,typeof e==`function`?Aa(zi(this,`text`,e)):ka(e==null?``:e+``))}function Ma(e){return function(t){this.textContent=e.call(this,t)}}function Na(e){var t,n;function r(){var r=e.apply(this,arguments);return r!==n&&(t=(n=r)&&Ma(r)),t}return r._value=e,r}function Pa(e){var t=`text`;if(arguments.length<1)return(t=this.tween(t))&&t._value;if(e==null)return this.tween(t,null);if(typeof e!=`function`)throw Error();return this.tween(t,Na(e))}function Fa(){for(var e=this._name,t=this._id,n=Ra(),r=this._groups,i=r.length,a=0;a<i;++a)for(var o=r[a],s=o.length,c,l=0;l<s;++l)if(c=o[l]){var u=z(c,t);Ar(c,e,n,l,o,{time:u.time+u.delay+u.duration,delay:0,duration:u.duration,ease:u.ease})}return new X(r,this._parents,e,n)}function Ia(){var e,t,n=this,r=n._id,i=n.size();return new Promise(function(a,o){var s={value:o},c={value:function(){--i===0&&a()}};n.each(function(){var n=R(this,r),i=n.on;i!==e&&(t=(e=i).copy(),t._.cancel.push(s),t._.interrupt.push(s),t._.end.push(c)),n.on=t}),i===0&&a()})}var La=0;function X(e,t,n,r){this._groups=e,this._parents=t,this._name=n,this._id=r}function Ra(){return++La}var Z=j.prototype;X.prototype={constructor:X,select:ga,selectAll:_a,selectChild:Z.selectChild,selectChildren:Z.selectChildren,filter:la,merge:ua,selection:ya,transition:Fa,call:Z.call,nodes:Z.nodes,node:Z.node,size:Z.size,empty:Z.empty,each:Z.each,on:pa,attr:qi,attrTween:Qi,style:Ta,styleTween:Oa,text:ja,textTween:Pa,remove:ha,tween:Ri,delay:ta,duration:ia,ease:oa,easeVarying:ca,end:Ia,[Symbol.iterator]:Z[Symbol.iterator]};function za(e){return((e*=2)<=1?e*e*e:(e-=2)*e*e+2)/2}var Ba={time:null,delay:0,duration:250,ease:za};function Va(e,t){for(var n;!(n=e.__transition)||!(n=n[t]);)if(!(e=e.parentNode))throw Error(`transition ${t} not found`);return n}function Ha(e){var t,n;e instanceof X?(t=e._id,e=e._name):(t=Ra(),(n=Ba).time=vr(),e=e==null?null:e+``);for(var r=this._groups,i=r.length,a=0;a<i;++a)for(var o=r[a],s=o.length,c,l=0;l<s;++l)(c=o[l])&&Ar(c,e,t,l,o,n||Va(c,t));return new X(r,this._parents,e,t)}j.prototype.interrupt=Pr,j.prototype.transition=Ha;var Ua={capture:!0,passive:!1};function Wa(e){e.preventDefault(),e.stopImmediatePropagation()}function Ga(e){var t=e.document.documentElement,n=M(e).on(`dragstart.drag`,Wa,Ua);`onselectstart`in t?n.on(`selectstart.drag`,Wa,Ua):(t.__noselect=t.style.MozUserSelect,t.style.MozUserSelect=`none`)}function Ka(e,t){var n=e.document.documentElement,r=M(e).on(`dragstart.drag`,null);t&&(r.on(`click.drag`,Wa,Ua),setTimeout(function(){r.on(`click.drag`,null)},0)),`onselectstart`in n?r.on(`selectstart.drag`,null):(n.style.MozUserSelect=n.__noselect,delete n.__noselect)}var qa=e=>()=>e;function Ja(e,{sourceEvent:t,target:n,transform:r,dispatch:i}){Object.defineProperties(this,{type:{value:e,enumerable:!0,configurable:!0},sourceEvent:{value:t,enumerable:!0,configurable:!0},target:{value:n,enumerable:!0,configurable:!0},transform:{value:r,enumerable:!0,configurable:!0},_:{value:i}})}function Q(e,t,n){this.k=e,this.x=t,this.y=n}Q.prototype={constructor:Q,scale:function(e){return e===1?this:new Q(this.k*e,this.x,this.y)},translate:function(e,t){return e===0&t===0?this:new Q(this.k,this.x+this.k*e,this.y+this.k*t)},apply:function(e){return[e[0]*this.k+this.x,e[1]*this.k+this.y]},applyX:function(e){return e*this.k+this.x},applyY:function(e){return e*this.k+this.y},invert:function(e){return[(e[0]-this.x)/this.k,(e[1]-this.y)/this.k]},invertX:function(e){return(e-this.x)/this.k},invertY:function(e){return(e-this.y)/this.k},rescaleX:function(e){return e.copy().domain(e.range().map(this.invertX,this).map(e.invert,e))},rescaleY:function(e){return e.copy().domain(e.range().map(this.invertY,this).map(e.invert,e))},toString:function(){return`translate(`+this.x+`,`+this.y+`) scale(`+this.k+`)`}};var Ya=new Q(1,0,0);Xa.prototype=Q.prototype;function Xa(e){for(;!e.__zoom;)if(!(e=e.parentNode))return Ya;return e.__zoom}function Za(e){e.stopImmediatePropagation()}function Qa(e){e.preventDefault(),e.stopImmediatePropagation()}function $a(e){return(!e.ctrlKey||e.type===`wheel`)&&!e.button}function eo(){var e=this;return e instanceof SVGElement?(e=e.ownerSVGElement||e,e.hasAttribute(`viewBox`)?(e=e.viewBox.baseVal,[[e.x,e.y],[e.x+e.width,e.y+e.height]]):[[0,0],[e.width.baseVal.value,e.height.baseVal.value]]):[[0,0],[e.clientWidth,e.clientHeight]]}function to(){return this.__zoom||Ya}function no(e){return-e.deltaY*(e.deltaMode===1?.05:e.deltaMode?1:.002)*(e.ctrlKey?10:1)}function ro(){return navigator.maxTouchPoints||`ontouchstart`in this}function io(e,t,n){var r=e.invertX(t[0][0])-n[0][0],i=e.invertX(t[1][0])-n[1][0],a=e.invertY(t[0][1])-n[0][1],o=e.invertY(t[1][1])-n[1][1];return e.translate(i>r?(r+i)/2:Math.min(0,r)||Math.max(0,i),o>a?(a+o)/2:Math.min(0,a)||Math.max(0,o))}function ao(){var e=$a,t=eo,n=io,r=no,i=ro,a=[0,1/0],o=[[-1/0,-1/0],[1/0,1/0]],s=250,c=Fi,l=or(`start`,`zoom`,`end`),u,d,f,p=500,m=150,h=0,g=10;function _(e){e.property(`__zoom`,to).on(`wheel.zoom`,ne,{passive:!1}).on(`mousedown.zoom`,re).on(`dblclick.zoom`,ie).filter(i).on(`touchstart.zoom`,S).on(`touchmove.zoom`,ae).on(`touchend.zoom touchcancel.zoom`,oe).style(`-webkit-tap-highlight-color`,`rgba(0,0,0,0)`)}_.transform=function(e,t,n,r){var i=e.selection?e.selection():e;i.property(`__zoom`,to),e===i?i.interrupt().each(function(){x(this,arguments).event(r).start().zoom(null,typeof t==`function`?t.apply(this,arguments):t).end()}):ee(e,t,n,r)},_.scaleBy=function(e,t,n,r){_.scaleTo(e,function(){return this.__zoom.k*(typeof t==`function`?t.apply(this,arguments):t)},n,r)},_.scaleTo=function(e,r,i,a){_.transform(e,function(){var e=t.apply(this,arguments),a=this.__zoom,s=i==null?b(e):typeof i==`function`?i.apply(this,arguments):i,c=a.invert(s),l=typeof r==`function`?r.apply(this,arguments):r;return n(y(v(a,l),s,c),e,o)},i,a)},_.translateBy=function(e,r,i,a){_.transform(e,function(){return n(this.__zoom.translate(typeof r==`function`?r.apply(this,arguments):r,typeof i==`function`?i.apply(this,arguments):i),t.apply(this,arguments),o)},null,a)},_.translateTo=function(e,r,i,a,s){_.transform(e,function(){var e=t.apply(this,arguments),s=this.__zoom,c=a==null?b(e):typeof a==`function`?a.apply(this,arguments):a;return n(Ya.translate(c[0],c[1]).scale(s.k).translate(typeof r==`function`?-r.apply(this,arguments):-r,typeof i==`function`?-i.apply(this,arguments):-i),e,o)},a,s)};function v(e,t){return t=Math.max(a[0],Math.min(a[1],t)),t===e.k?e:new Q(t,e.x,e.y)}function y(e,t,n){var r=t[0]-n[0]*e.k,i=t[1]-n[1]*e.k;return r===e.x&&i===e.y?e:new Q(e.k,r,i)}function b(e){return[(+e[0][0]+ +e[1][0])/2,(+e[0][1]+ +e[1][1])/2]}function ee(e,n,r,i){e.on(`start.zoom`,function(){x(this,arguments).event(i).start()}).on(`interrupt.zoom end.zoom`,function(){x(this,arguments).event(i).end()}).tween(`zoom`,function(){var e=this,a=arguments,o=x(e,a).event(i),s=t.apply(e,a),l=r==null?b(s):typeof r==`function`?r.apply(e,a):r,u=Math.max(s[1][0]-s[0][0],s[1][1]-s[0][1]),d=e.__zoom,f=typeof n==`function`?n.apply(e,a):n,p=c(d.invert(l).concat(u/d.k),f.invert(l).concat(u/f.k));return function(e){if(e===1)e=f;else{var t=p(e),n=u/t[2];e=new Q(n,l[0]-t[0]*n,l[1]-t[1]*n)}o.zoom(null,e)}})}function x(e,t,n){return!n&&e.__zooming||new te(e,t)}function te(e,n){this.that=e,this.args=n,this.active=0,this.sourceEvent=null,this.extent=t.apply(e,n),this.taps=0}te.prototype={event:function(e){return e&&(this.sourceEvent=e),this},start:function(){return++this.active===1&&(this.that.__zooming=this,this.emit(`start`)),this},zoom:function(e,t){return this.mouse&&e!==`mouse`&&(this.mouse[1]=t.invert(this.mouse[0])),this.touch0&&e!==`touch`&&(this.touch0[1]=t.invert(this.touch0[0])),this.touch1&&e!==`touch`&&(this.touch1[1]=t.invert(this.touch1[0])),this.that.__zoom=t,this.emit(`zoom`),this},end:function(){return--this.active===0&&(delete this.that.__zooming,this.emit(`end`)),this},emit:function(e){var t=M(this.that).datum();l.call(e,this.that,new Ja(e,{sourceEvent:this.sourceEvent,target:_,type:e,transform:this.that.__zoom,dispatch:l}),t)}};function ne(t,...i){if(!e.apply(this,arguments))return;var s=x(this,i).event(t),c=this.__zoom,l=Math.max(a[0],Math.min(a[1],c.k*2**r.apply(this,arguments))),u=N(t);if(s.wheel)(s.mouse[0][0]!==u[0]||s.mouse[0][1]!==u[1])&&(s.mouse[1]=c.invert(s.mouse[0]=u)),clearTimeout(s.wheel);else if(c.k===l)return;else s.mouse=[u,c.invert(u)],Nr(this),s.start();Qa(t),s.wheel=setTimeout(d,m),s.zoom(`mouse`,n(y(v(c,l),s.mouse[0],s.mouse[1]),s.extent,o));function d(){s.wheel=null,s.end()}}function re(t,...r){if(f||!e.apply(this,arguments))return;var i=t.currentTarget,a=x(this,r,!0).event(t),s=M(t.view).on(`mousemove.zoom`,d,!0).on(`mouseup.zoom`,p,!0),c=N(t,i),l=t.clientX,u=t.clientY;Ga(t.view),Za(t),a.mouse=[c,this.__zoom.invert(c)],Nr(this),a.start();function d(e){if(Qa(e),!a.moved){var t=e.clientX-l,r=e.clientY-u;a.moved=t*t+r*r>h}a.event(e).zoom(`mouse`,n(y(a.that.__zoom,a.mouse[0]=N(e,i),a.mouse[1]),a.extent,o))}function p(e){s.on(`mousemove.zoom mouseup.zoom`,null),Ka(e.view,a.moved),Qa(e),a.event(e).end()}}function ie(r,...i){if(e.apply(this,arguments)){var a=this.__zoom,c=N(r.changedTouches?r.changedTouches[0]:r,this),l=a.invert(c),u=a.k*(r.shiftKey?.5:2),d=n(y(v(a,u),c,l),t.apply(this,i),o);Qa(r),s>0?M(this).transition().duration(s).call(ee,d,c,r):M(this).call(_.transform,d,c,r)}}function S(t,...n){if(e.apply(this,arguments)){var r=t.touches,i=r.length,a=x(this,n,t.changedTouches.length===i).event(t),o,s,c,l;for(Za(t),s=0;s<i;++s)c=r[s],l=N(c,this),l=[l,this.__zoom.invert(l),c.identifier],a.touch0?!a.touch1&&a.touch0[2]!==l[2]&&(a.touch1=l,a.taps=0):(a.touch0=l,o=!0,a.taps=1+!!u);u&&=clearTimeout(u),o&&(a.taps<2&&(d=l[0],u=setTimeout(function(){u=null},p)),Nr(this),a.start())}}function ae(e,...t){if(this.__zooming){var r=x(this,t).event(e),i=e.changedTouches,a=i.length,s,c,l,u;for(Qa(e),s=0;s<a;++s)c=i[s],l=N(c,this),r.touch0&&r.touch0[2]===c.identifier?r.touch0[0]=l:r.touch1&&r.touch1[2]===c.identifier&&(r.touch1[0]=l);if(c=r.that.__zoom,r.touch1){var d=r.touch0[0],f=r.touch0[1],p=r.touch1[0],m=r.touch1[1],h=(h=p[0]-d[0])*h+(h=p[1]-d[1])*h,g=(g=m[0]-f[0])*g+(g=m[1]-f[1])*g;c=v(c,Math.sqrt(h/g)),l=[(d[0]+p[0])/2,(d[1]+p[1])/2],u=[(f[0]+m[0])/2,(f[1]+m[1])/2]}else if(r.touch0)l=r.touch0[0],u=r.touch0[1];else return;r.zoom(`touch`,n(y(c,l,u),r.extent,o))}}function oe(e,...t){if(this.__zooming){var n=x(this,t).event(e),r=e.changedTouches,i=r.length,a,o;for(Za(e),f&&clearTimeout(f),f=setTimeout(function(){f=null},p),a=0;a<i;++a)o=r[a],n.touch0&&n.touch0[2]===o.identifier?delete n.touch0:n.touch1&&n.touch1[2]===o.identifier&&delete n.touch1;if(n.touch1&&!n.touch0&&(n.touch0=n.touch1,delete n.touch1),n.touch0)n.touch0[1]=this.__zoom.invert(n.touch0[0]);else if(n.end(),n.taps===2&&(o=N(o,this),Math.hypot(d[0]-o[0],d[1]-o[1])<g)){var s=M(this).on(`dblclick.zoom`);s&&s.apply(this,arguments)}}}return _.wheelDelta=function(e){return arguments.length?(r=typeof e==`function`?e:qa(+e),_):r},_.filter=function(t){return arguments.length?(e=typeof t==`function`?t:qa(!!t),_):e},_.touchable=function(e){return arguments.length?(i=typeof e==`function`?e:qa(!!e),_):i},_.extent=function(e){return arguments.length?(t=typeof e==`function`?e:qa([[+e[0][0],+e[0][1]],[+e[1][0],+e[1][1]]]),_):t},_.scaleExtent=function(e){return arguments.length?(a[0]=+e[0],a[1]=+e[1],_):[a[0],a[1]]},_.translateExtent=function(e){return arguments.length?(o[0][0]=+e[0][0],o[1][0]=+e[1][0],o[0][1]=+e[0][1],o[1][1]=+e[1][1],_):[[o[0][0],o[0][1]],[o[1][0],o[1][1]]]},_.constrain=function(e){return arguments.length?(n=e,_):n},_.duration=function(e){return arguments.length?(s=+e,_):s},_.interpolate=function(e){return arguments.length?(c=e,_):c},_.on=function(){var e=l.on.apply(l,arguments);return e===l?_:e},_.clickDistance=function(e){return arguments.length?(h=(e=+e)*e,_):Math.sqrt(h)},_.tapDistance=function(e){return arguments.length?(g=+e,_):g},_}var oo={ATTRIBUTE:1,CHILD:2,PROPERTY:3,BOOLEAN_ATTRIBUTE:4,EVENT:5,ELEMENT:6},so=e=>(...t)=>({_$litDirective$:e,values:t}),co=class{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,n){this._$Ct=e,this._$AM=t,this._$Ci=n}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}},{I:lo}=l,uo=e=>e,fo=()=>document.createComment(``),po=(e,t,n)=>{let r=e._$AA.parentNode,i=t===void 0?e._$AB:t._$AA;if(n===void 0)n=new lo(r.insertBefore(fo(),i),r.insertBefore(fo(),i),e,e.options);else{let t=n._$AB.nextSibling,a=n._$AM,o=a!==e;if(o){let t;n._$AQ?.(e),n._$AM=e,n._$AP!==void 0&&(t=e._$AU)!==a._$AU&&n._$AP(t)}if(t!==i||o){let e=n._$AA;for(;e!==t;){let t=uo(e).nextSibling;uo(r).insertBefore(e,i),e=t}}}return n},$=(e,t,n=e)=>(e._$AI(t,n),e),mo={},ho=(e,t=mo)=>e._$AH=t,go=e=>e._$AH,_o=e=>{e._$AR(),e._$AA.remove()},vo=(e,t,n)=>{let r=new Map;for(let i=t;i<=n;i++)r.set(e[i],i);return r},yo=so(class extends co{constructor(e){if(super(e),e.type!==oo.CHILD)throw Error(`repeat() can only be used in text expressions`)}dt(e,t,n){let r;n===void 0?n=t:t!==void 0&&(r=t);let i=[],a=[],o=0;for(let t of e)i[o]=r?r(t,o):o,a[o]=n(t,o),o++;return{values:a,keys:i}}render(e,t,n){return this.dt(e,t,n).values}update(t,[n,r,i]){let a=go(t),{values:o,keys:s}=this.dt(n,r,i);if(!Array.isArray(a))return this.ut=s,o;let c=this.ut??=[],l=[],u,d,f=0,p=a.length-1,m=0,h=o.length-1;for(;f<=p&&m<=h;)if(a[f]===null)f++;else if(a[p]===null)p--;else if(c[f]===s[m])l[m]=$(a[f],o[m]),f++,m++;else if(c[p]===s[h])l[h]=$(a[p],o[h]),p--,h--;else if(c[f]===s[h])l[h]=$(a[f],o[h]),po(t,l[h+1],a[f]),f++,h--;else if(c[p]===s[m])l[m]=$(a[p],o[m]),po(t,a[f],a[p]),p--,m++;else if(u===void 0&&(u=vo(s,m,h),d=vo(c,f,p)),u.has(c[f])){if(u.has(c[p])){let e=d.get(s[m]),n=e===void 0?null:a[e];if(n===null){let e=po(t,a[f]);$(e,o[m]),l[m]=e}else l[m]=$(n,o[m]),po(t,a[f],n),a[e]=null;m++}else _o(a[p]),p--}else _o(a[f]),f++;for(;m<=h;){let e=po(t,l[h+1]);$(e,o[m]),l[m++]=e}for(;f<=p;){let e=a[f++];e!==null&&_o(e)}return this.ut=s,ho(t,l),e}});function bo(e){var t=0,n=e.children,r=n&&n.length;if(!r)t=1;else for(;--r>=0;)t+=n[r].value;e.value=t}function xo(){return this.eachAfter(bo)}function So(e,t){let n=-1;for(let r of this)e.call(t,r,++n,this);return this}function Co(e,t){for(var n=this,r=[n],i,a,o=-1;n=r.pop();)if(e.call(t,n,++o,this),i=n.children)for(a=i.length-1;a>=0;--a)r.push(i[a]);return this}function wo(e,t){for(var n=this,r=[n],i=[],a,o,s,c=-1;n=r.pop();)if(i.push(n),a=n.children)for(o=0,s=a.length;o<s;++o)r.push(a[o]);for(;n=i.pop();)e.call(t,n,++c,this);return this}function To(e,t){let n=-1;for(let r of this)if(e.call(t,r,++n,this))return r}function Eo(e){return this.eachAfter(function(t){for(var n=+e(t.data)||0,r=t.children,i=r&&r.length;--i>=0;)n+=r[i].value;t.value=n})}function Do(e){return this.eachBefore(function(t){t.children&&t.children.sort(e)})}function Oo(e){for(var t=this,n=ko(t,e),r=[t];t!==n;)t=t.parent,r.push(t);for(var i=r.length;e!==n;)r.splice(i,0,e),e=e.parent;return r}function ko(e,t){if(e===t)return e;var n=e.ancestors(),r=t.ancestors(),i=null;for(e=n.pop(),t=r.pop();e===t;)i=e,e=n.pop(),t=r.pop();return i}function Ao(){for(var e=this,t=[e];e=e.parent;)t.push(e);return t}function jo(){return Array.from(this)}function Mo(){var e=[];return this.eachBefore(function(t){t.children||e.push(t)}),e}function No(){var e=this,t=[];return e.each(function(n){n!==e&&t.push({source:n.parent,target:n})}),t}function*Po(){var e=this,t,n=[e],r,i,a;do for(t=n.reverse(),n=[];e=t.pop();)if(yield e,r=e.children)for(i=0,a=r.length;i<a;++i)n.push(r[i]);while(n.length)}function Fo(e,t){e instanceof Map?(e=[void 0,e],t===void 0&&(t=Ro)):t===void 0&&(t=Lo);for(var n=new Vo(e),r,i=[n],a,o,s,c;r=i.pop();)if((o=t(r.data))&&(c=(o=Array.from(o)).length))for(r.children=o,s=c-1;s>=0;--s)i.push(a=o[s]=new Vo(o[s])),a.parent=r,a.depth=r.depth+1;return n.eachBefore(Bo)}function Io(){return Fo(this).eachBefore(zo)}function Lo(e){return e.children}function Ro(e){return Array.isArray(e)?e[1]:null}function zo(e){e.data.value!==void 0&&(e.value=e.data.value),e.data=e.data.data}function Bo(e){var t=0;do e.height=t;while((e=e.parent)&&e.height<++t)}function Vo(e){this.data=e,this.depth=this.height=0,this.parent=null}Vo.prototype=Fo.prototype={constructor:Vo,count:xo,each:So,eachAfter:wo,eachBefore:Co,find:To,sum:Eo,sort:Do,path:Oo,ancestors:Ao,descendants:jo,leaves:Mo,links:No,copy:Io,[Symbol.iterator]:Po};function Ho(e,t){return e.parent===t.parent?1:2}function Uo(e){var t=e.children;return t?t[0]:e.t}function Wo(e){var t=e.children;return t?t[t.length-1]:e.t}function Go(e,t,n){var r=n/(t.i-e.i);t.c-=r,t.s+=n,e.c+=r,t.z+=n,t.m+=n}function Ko(e){for(var t=0,n=0,r=e.children,i=r.length,a;--i>=0;)a=r[i],a.z+=t,a.m+=t,t+=a.s+(n+=a.c)}function qo(e,t,n){return e.a.parent===t.parent?e.a:n}function Jo(e,t){this._=e,this.parent=null,this.children=null,this.A=null,this.a=this,this.z=0,this.m=0,this.c=0,this.s=0,this.t=null,this.i=t}Jo.prototype=Object.create(Vo.prototype);function Yo(e){for(var t=new Jo(e,0),n,r=[t],i,a,o,s;n=r.pop();)if(a=n._.children)for(n.children=Array(s=a.length),o=s-1;o>=0;--o)r.push(i=n.children[o]=new Jo(a[o],o)),i.parent=n;return(t.parent=new Jo(null,0)).children=[t],t}function Xo(){var e=Ho,t=1,n=1,r=null;function i(i){var s=Yo(i);if(s.eachAfter(a),s.parent.m=-s.z,s.eachBefore(o),r)i.eachBefore(c);else{var l=i,u=i,d=i;i.eachBefore(function(e){e.x<l.x&&(l=e),e.x>u.x&&(u=e),e.depth>d.depth&&(d=e)});var f=l===u?1:e(l,u)/2,p=f-l.x,m=t/(u.x+f+p),h=n/(d.depth||1);i.eachBefore(function(e){e.x=(e.x+p)*m,e.y=e.depth*h})}return i}function a(t){var n=t.children,r=t.parent.children,i=t.i?r[t.i-1]:null;if(n){Ko(t);var a=(n[0].z+n[n.length-1].z)/2;i?(t.z=i.z+e(t._,i._),t.m=t.z-a):t.z=a}else i&&(t.z=i.z+e(t._,i._));t.parent.A=s(t,i,t.parent.A||r[0])}function o(e){e._.x=e.z+e.parent.m,e.m+=e.parent.m}function s(t,n,r){if(n){for(var i=t,a=t,o=n,s=i.parent.children[0],c=i.m,l=a.m,u=o.m,d=s.m,f;o=Wo(o),i=Uo(i),o&&i;)s=Uo(s),a=Wo(a),a.a=t,f=o.z+u-i.z-c+e(o._,i._),f>0&&(Go(qo(o,t,r),t,f),c+=f,l+=f),u+=o.m,c+=i.m,d+=s.m,l+=a.m;o&&!Wo(a)&&(a.t=o,a.m+=u-l),i&&!Uo(s)&&(s.t=i,s.m+=c-d,r=t)}return r}function c(e){e.x*=t,e.y=e.depth*n}return i.separation=function(t){return arguments.length?(e=t,i):e},i.size=function(e){return arguments.length?(r=!1,t=+e[0],n=+e[1],i):r?null:[t,n]},i.nodeSize=function(e){return arguments.length?(r=!0,t=+e[0],n=+e[1],i):r?[t,n]:null},i}var Zo={comfortable:{breadth:132,depth:150},compact:{breadth:92,depth:112}},Qo=`\0root`;function $o(e,t,n){let r=new Map;if(e.roots.length===0)return{positions:r,bounds:{minX:0,minY:0,maxX:0,maxY:0}};let{breadth:i,depth:a}=Zo[t],o=Fo(Qo,t=>t===Qo?e.roots:e.children.get(t)),s=Xo().nodeSize([i,a]).separation((e,t)=>e.parent===t.parent?1:1.25)(o),c={minX:1/0,minY:1/0,maxX:-1/0,maxY:-1/0};for(let e of s.descendants()){if(e.data===Qo)continue;let t=e.x,i=(e.depth-1)*a,o=n===`vertical`?{x:t,y:i}:{x:i,y:t};r.set(e.data,o),c.minX=Math.min(c.minX,o.x),c.minY=Math.min(c.minY,o.y),c.maxX=Math.max(c.maxX,o.x),c.maxY=Math.max(c.maxY,o.y)}return{positions:r,bounds:c}}function es(e,t,n,r=48){let i=Math.max(e.maxX-e.minX,1),a=Math.max(e.maxY-e.minY,1),o=Math.min(1.5,Math.max(.2,Math.min((t-2*r)/i,(n-2*r)/a))),s=(e.minX+e.maxX)/2,c=(e.minY+e.maxY)/2;return{k:o,x:t/2-s*o,y:n/2-c*o}}function ts(e,t,n,r,i=120){let a=new Set;for(let[o,s]of e.positions){let e=s.x*t.k+t.x,c=s.y*t.k+t.y;e>=-i&&e<=n+i&&c>=-i&&c<=r+i&&a.add(o)}return a}function ns(e,t,n,r){let i=r===`vertical`,a={parent:i?`ArrowUp`:`ArrowLeft`,child:i?`ArrowDown`:`ArrowRight`,previous:i?`ArrowLeft`:`ArrowUp`,next:i?`ArrowRight`:`ArrowDown`};if(!Object.values(a).includes(n))return;if(t===void 0||!e.visuals.has(t))return e.roots[0];let o=Ye(e,t),s=o.indexOf(t);switch(n){case a.parent:return e.parentOf.get(t)??t;case a.child:return e.children.get(t)?.[0]??t;case a.previous:return o[s-1]??t;default:return o[s+1]??t}}var rs={comfortable:22,compact:16},is=250,as=22;function os(e,t){if(e.type===`wheel`){let n=e;return t&&!n.ctrlKey&&!n.metaKey?`hint`:`zoom`}let n=e;return n.ctrlKey||(n.button??0)!==0?`ignore`:`zoom`}var ss=class extends d{static properties={model:{attribute:!1},density:{attribute:!1},orientation:{attribute:!1},showLabels:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},siteName:{attribute:!1},ctrlZoom:{attribute:!1},reducedMotion:{attribute:!1},focusId:{state:!0},hintVisible:{state:!0}};layout;entering=new Set;exiting=new Map;lastVisuals=new Map;exitTimer;hintTimer;transform={x:0,y:0,k:1};width=0;height=0;fitted=!1;zoomBehavior;resizeObserver;constructor(){super(),this.density=`comfortable`,this.orientation=`vertical`,this.showLabels=!0,this.siteName=``,this.ctrlZoom=!0,this.reducedMotion=!1,this.hintVisible=!1}connectedCallback(){super.connectedCallback(),this.resizeObserver=new ResizeObserver(e=>{let t=e[0]?.contentRect;t&&this.setViewportSize(t.width,t.height)}),this.resizeObserver.observe(this)}disconnectedCallback(){super.disconnectedCallback(),this.resizeObserver?.disconnect(),this.exitTimer!==void 0&&clearTimeout(this.exitTimer),this.hintTimer!==void 0&&clearTimeout(this.hintTimer),this.exitTimer=void 0,this.hintTimer=void 0}setViewportSize(e,t){this.width=e,this.height=t,this.fitted?this.needsCulling&&this.requestUpdate():this.tryInitialFit()}get needsCulling(){return(this.layout?.positions.size??0)>300}get svgEl(){return this.renderRoot.querySelector(`svg.canvas`)}willUpdate(e){if(this.model&&(e.has(`model`)||e.has(`density`)||e.has(`orientation`))){let e=$o(this.model,this.density,this.orientation),t=this.layout;this.entering=new Set(t?[...e.positions.keys()].filter(e=>!t.positions.has(e)):[]);for(let t of e.positions.keys())this.exiting.delete(t);if(t&&!this.reducedMotion){for(let[n,r]of t.positions){let t=this.lastVisuals.get(n);!e.positions.has(n)&&t&&this.exiting.set(n,{point:r,visual:t})}this.scheduleExitCleanup()}this.layout=e,this.lastVisuals=new Map(this.model.visuals),(this.focusId===void 0||!this.model.visuals.has(this.focusId))&&(this.focusId=this.model.roots[0])}}firstUpdated(){let e=this.svgEl;e&&(this.zoomBehavior=ao().scaleExtent([.2,4]).extent(()=>[[0,0],[Math.max(this.width,1),Math.max(this.height,1)]]).filter(e=>{let t=os(e,this.ctrlZoom);return t===`hint`&&this.flashHint(),t===`zoom`}).on(`zoom`,e=>this.onZoom(e.transform)).on(`end`,()=>{this.needsCulling&&this.requestUpdate()}),M(e).call(this.zoomBehavior).on(`dblclick.zoom`,null),this.tryInitialFit())}updated(){this.tryInitialFit()}tryInitialFit(){this.fitted||!this.layout||!this.zoomBehavior||this.width<=0||this.height<=0||(this.fitted=!0,this.fit(!1))}onZoom(e){this.transform={x:e.x,y:e.y,k:e.k},this.renderRoot.querySelector(`g.viewport`)?.setAttribute(`transform`,this.transformAttr())}transformAttr(){let{x:e,y:t,k:n}=this.transform;return`translate(${e},${t}) scale(${n})`}fit(e=!0){let t=this.svgEl;if(!this.layout||!this.zoomBehavior||!t)return;let n=es(this.layout.bounds,this.width,this.height),r=Ya.translate(n.x,n.y).scale(n.k);e&&!this.reducedMotion?this.zoomBehavior.transform(M(t).transition().duration(300),r):this.zoomBehavior.transform(M(t),r)}zoomBy(e){let t=this.svgEl;this.zoomBehavior&&t&&(this.reducedMotion?this.zoomBehavior.scaleBy(M(t),e):this.zoomBehavior.scaleBy(M(t).transition().duration(200),e))}async focusNode(e){this.focusId=e,await this.updateComplete;let t=this.layout?.positions.get(e),n=this.svgEl;if(t&&n&&this.zoomBehavior&&this.width>0){let e=t.x*this.transform.k+this.transform.x,r=t.y*this.transform.k+this.transform.y;(e<40||e>this.width-40||r<40||r>this.height-40)&&(this.zoomBehavior.translateTo(M(n),t.x,t.y),await this.updateComplete)}for(let t of this.renderRoot.querySelectorAll(`g.nodes g.node`))t.getAttribute(`data-id`)===e&&t.focus()}flashHint(){this.hintVisible=!0,this.hintTimer!==void 0&&clearTimeout(this.hintTimer),this.hintTimer=setTimeout(()=>{this.hintVisible=!1},1500)}scheduleExitCleanup(){this.exiting.size!==0&&this.exitTimer===void 0&&(this.exitTimer=setTimeout(()=>{this.exitTimer=void 0,this.exiting.clear(),this.requestUpdate()},is))}highlightedPath(){let e=new Set,t=this.model;if(!t||this.selectedId===void 0)return e;let n=t.visuals.has(this.selectedId)?this.selectedId:Xe(t,this.selectedId)?.id;for(;n!==void 0;)e.add(n),n=t.parentOf.get(n);return e}onKeydown(e){let t=this.model;if(!t)return;let n=ns(t,this.focusId,e.key,this.orientation);if(n!==void 0){e.preventDefault(),this.focusNode(n);return}(e.key===`Enter`||e.key===` `)&&this.focusId!==void 0?(e.preventDefault(),_(this,`uit-activate`,{id:this.focusId})):e.key===`+`||e.key===`=`?(e.preventDefault(),this.zoomBy(1.25)):e.key===`-`?(e.preventDefault(),this.zoomBy(.8)):e.key===`0`&&(e.preventDefault(),this.fit())}render(){let{model:e,layout:t,localize:n}=this;if(!e||!t||!n)return w;let r=rs[this.density],i=[...t.positions.keys()],a=[...e.links.values()];if(this.needsCulling&&this.width>0){let e=ts(t,this.transform,this.width,this.height);this.focusId!==void 0&&e.add(this.focusId),this.selectedId!==void 0&&e.add(this.selectedId),i=i.filter(t=>e.has(t)),a=a.filter(t=>e.has(t.childId)||e.has(t.parentId))}let o=this.highlightedPath();return C`
            <svg
                class="canvas ${this.reducedMotion?`still`:``}"
                role="application"
                aria-roledescription=${n(`graph.roledescription`)}
                aria-label=${n(`graph.label`,{site:this.siteName,devices:e.stats.devices,clients:e.stats.clients})}
                @keydown=${this.onKeydown}
            >
                <g class="viewport" transform=${this.transformAttr()}>
                    <g class="links">
                        ${yo(a,e=>e.childId,e=>this.renderLink(e,t,o))}
                    </g>
                    <g class="nodes">
                        ${yo(i,e=>e,n=>this.renderNode(e,e.visuals.get(n),t.positions.get(n),r,o,!0))}
                    </g>
                    <g class="exits" aria-hidden="true">
                        ${yo([...this.exiting],([e])=>e,([,t])=>this.renderGhost(e,t,r))}
                    </g>
                </g>
            </svg>
            <div class="hint" aria-hidden="true" ?hidden=${!this.hintVisible}>
                ${n(`zoom.hint`)}
            </div>
        `}renderLink(e,t,n){let r=t.positions.get(e.parentId),i=t.positions.get(e.childId);if(!r||!i)return w;let a=this.orientation===`vertical`?(r.y+i.y)/2:(r.x+i.x)/2,o=this.orientation===`vertical`?`M${r.x},${r.y} C${r.x},${a} ${i.x},${a} ${i.x},${i.y}`:`M${r.x},${r.y} C${a},${r.y} ${a},${i.y} ${i.x},${i.y}`,s=this.showLabels?it(e.edge):``,c=[`link`,e.edge?.medium??`unknown`,e.viaHidden.length>0?`via-hidden`:``,n.has(e.childId)?`on-path`:``];return u`<path class=${c.join(` `)} d=${o}></path>${s?u`<text class="link-label" x=${(r.x+i.x)/2} y=${(r.y+i.y)/2}>${s}</text>`:w}`}renderNode(e,n,r,i,a,o){let s=this.localize,c=n.id,l=at(n),d=O(n,s),f=n.type===`group`?`group`:n.node.kind,p=[`node`,n.type,f,l,c===this.selectedId?`selected`:``,a.has(c)?`on-path`:``,this.entering.has(c)?`enter`:``],m=n.type===`group`?h:t(n.node),g=i+16;return u`<g
      class=${p.join(` `)}
      data-id=${c}
      role=${o?`button`:w}
      tabindex=${o?c===this.focusId?0:-1:w}
      aria-label=${o?ot(e,n,s):w}
      aria-expanded=${o&&n.type===`group`?String(n.expanded):w}
      style=${`transform: translate(${r.x}px, ${r.y}px)`}
      @click=${o?()=>_(this,`uit-activate`,{id:c}):w}
      @focus=${o?()=>{this.focusId=c}:w}
    >
      <title>${d}</title>
      <circle class="hit" r=${Math.max(i,22)}></circle>
      <circle class="ring" r=${i+5}></circle>
      <circle class="disc" r=${i}></circle>
      <svg class="glyph" x=${-i*.6} y=${-i*.6} width=${i*1.2} height=${i*1.2} viewBox="0 0 24 24" aria-hidden="true">
        <path d=${m}></path>
      </svg>
      <circle class="status" cx=${i*.72} cy=${-i*.72} r=${Math.max(4,i*.24)}></circle>
      ${n.type===`group`?u`<text class="badge" x=${i*.95} y=${i+2}>${n.counts.total}</text>`:w}
      ${this.showLabels?u`<text class="label" y=${g}>${et(d,as)}</text>`:w}
      ${l===`offline`?u`<text class="state-text" y=${this.showLabels?g+14:g}>${s(D.offline)}</text>`:w}
    </g>`}renderGhost(e,t,n){return this.renderNode(e,t.visual,t.point,n,new Set,!1)}static styles=[ce,p`
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
                stroke: color-mix(
                    in srgb,
                    var(--primary-color) 40%,
                    var(--uit-line)
                );
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
        `]};T(`uit-graph-view`,ss);function cs(e,t){return e.type===`group`?e.members.some(e=>e.name.toLowerCase().includes(t)):e.node.name.toLowerCase().includes(t)}function ls(e,t,n){let r=n.trim().toLowerCase(),i;if(r){i=new Set;for(let[t,n]of e.visuals)if(cs(n,r))for(let n=t;n!==void 0&&!i.has(n);n=e.parentOf.get(n))i.add(n)}let a=[],o=(n,s,c)=>{let l=i?n.filter(e=>i.has(e)):n;l.forEach((n,i)=>{let u=e.visuals.get(n),d=e.children.get(n)??[],f=u.type===`group`,p=f||d.length>0,m=f?u.expanded:r!==``||!t.has(n);a.push({id:n,visual:u,level:s,posinset:i+1,setsize:l.length,hasChildren:p,expanded:p&&m,parentId:c}),m&&d.length>0&&o(d,s+1,n)})};return o(e.roots,1,void 0),a}var us=class extends d{static properties={model:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},siteName:{attribute:!1},query:{state:!0},collapsed:{state:!0},focusId:{state:!0}};rows=[];typeahead=``;typeaheadTimer;constructor(){super(),this.siteName=``,this.query=``,this.collapsed=new Set}willUpdate(){this.model&&(this.rows=ls(this.model,this.collapsed,this.query),this.rows.some(e=>e.id===this.focusId)||(this.focusId=this.rows[0]?.id))}render(){let{model:e,localize:t}=this;return!e||!t?w:C`
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
                      ${yo(this.rows,e=>e.id,n=>this.renderRow(e,n,t))}
                  </div>`}
        `}renderRow(e,n,r){let i=n.visual,a=O(i,r),o=at(i);return C`<div
            class="row ${o} ${n.id===this.selectedId?`selected`:``}"
            role="treeitem"
            data-id=${n.id}
            aria-level=${n.level}
            aria-setsize=${n.setsize}
            aria-posinset=${n.posinset}
            aria-selected=${String(n.id===this.selectedId)}
            aria-expanded=${n.hasChildren?String(n.expanded):w}
            aria-label=${ot(e,i,r)}
            tabindex=${n.id===this.focusId?0:-1}
            style=${`--level: ${n.level}`}
            @click=${()=>_(this,`uit-activate`,{id:n.id})}
            @focus=${()=>{this.focusId=n.id}}
        >
            <span
                class="chevron"
                aria-hidden="true"
                @click=${e=>{e.stopPropagation(),n.hasChildren&&this.toggle(n)}}
                >${n.hasChildren?E(n.expanded?y:s):w}</span
            >
            ${E(i.type===`group`?h:t(i.node))}
            <span class="name" title=${a}>${a}</span>
            ${i.type===`group`?C`<span class="count">${i.counts.total}</span>`:C`<span class="dot" aria-hidden="true"></span>${o===`online`?w:C`<span class="state-text"
                                >${r(D[o])}</span
                            >`}`}
        </div>`}toggle(e){if(e.visual.type===`group`){_(this,`uit-toggle-group`,{id:e.id});return}let t=new Set(this.collapsed);t.has(e.id)?t.delete(e.id):t.add(e.id),this.collapsed=t}onKeydown(e){let t=this.rows,n=t.findIndex(e=>e.id===this.focusId),r=t[n];if(!r)return;let i;switch(e.key){case`ArrowDown`:i=t[n+1]?.id;break;case`ArrowUp`:i=t[n-1]?.id;break;case`Home`:i=t[0]?.id;break;case`End`:i=t.at(-1)?.id;break;case`ArrowRight`:r.hasChildren&&!r.expanded?this.toggle(r):r.expanded&&(i=t[n+1]?.id);break;case`ArrowLeft`:r.expanded?this.toggle(r):i=r.parentId;break;case`Enter`:case` `:_(this,`uit-activate`,{id:r.id});break;default:e.key.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&(e.preventDefault(),this.typeAhead(e.key,n));return}e.preventDefault(),i!==void 0&&this.focusRow(i)}typeAhead(e,t){this.typeahead+=e.toLowerCase(),this.typeaheadTimer!==void 0&&clearTimeout(this.typeaheadTimer),this.typeaheadTimer=setTimeout(()=>{this.typeahead=``},500);let n=this.rows;for(let e=1;e<=n.length;e++){let r=n[(t+e)%n.length];if(O(r.visual,this.localize).toLowerCase().startsWith(this.typeahead)){this.focusRow(r.id);return}}}async focusRow(e){this.focusId=e,await this.updateComplete;let t=this.renderRoot.querySelectorAll(`[role="treeitem"]`);for(let n of t)n.getAttribute(`data-id`)===e&&n.focus()}static styles=[ce,ge,p`
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
        `]};T(`uit-list-view`,us);var ds=600,fs=`/config/integrations/integration/unifi_insights`,ps={integration:`action.integration`,edit:`action.edit`},ms={loading:{key:`state.loading`},no_sources:{key:`state.no_sources`,action:`integration`},unconfigured:{key:`state.unconfigured`,action:`edit`},empty:{key:`state.empty`},incompatible:{key:`state.incompatible`},reloading:{key:`state.reconnecting`}},hs=e=>e?.nodes.filter(e=>e.kind!==`client`&&e.state===`offline`).length??0,gs=class extends d{static properties={hass:{attribute:!1},layout:{attribute:!1},config:{state:!0},sources:{state:!0},snapshot:{state:!0},lastGood:{state:!0},error:{state:!0},incompatible:{state:!0},disconnected:{state:!0},ui:{state:!0},view:{state:!0},selectedId:{state:!0},siteOverride:{state:!0},narrow:{state:!0},reducedMotion:{state:!0},announcement:{state:!0}};subscription=new Ie({onSnapshot:e=>this.applySnapshot(e),onError:e=>{this.error=e},onIncompatible:()=>{this.incompatible=!0},onDisconnected:()=>{this.disconnected=!0},onReconnected:()=>{this.hass&&this.loadSources(this.hass)}});buildModel=Je();announcer=new Ee(e=>{this.announcement=e});sourcesFor;sourcesPending=!1;sourcesRetry;sourcesAttempt=0;sourcesError;boundKey;cardState={phase:`loading`,stale:!1,notices:[]};model;resizeObserver;motionQuery;localizeLang;localizeFn;constructor(){super(),this.incompatible=!1,this.disconnected=!1,this.ui={kinds:new Set(o),clients:`collapsed`,toggledGroups:new Set},this.view=`graph`,this.narrow=!1,this.reducedMotion=!1,this.announcement=``}setConfig(e){let t=me(se(e));this.config=t,this.view=t.view,this.ui={kinds:new Set(t.kinds),clients:t.clients,toggledGroups:new Set},this.siteOverride=void 0}getCardSize(){return 8}getGridOptions(){return{columns:12,rows:8,min_columns:6,min_rows:4}}static getConfigElement(){return document.createElement(ie)}static async getStubConfig(e){try{let t=S(await e.callWS({type:i}))[0];if(t)return{type:ne,...t.binding}}catch{}return{type:ne}}connectedCallback(){super.connectedCallback(),this.resizeObserver=new ResizeObserver(e=>{let t=e[0]?.contentRect.width??0;this.narrow=t>0&&t<ds}),this.resizeObserver.observe(this),this.motionQuery=window.matchMedia(`(prefers-reduced-motion: reduce)`),this.motionQuery.addEventListener(`change`,this.onMotionChange),this.onMotionChange(),this.sync()}disconnectedCallback(){super.disconnectedCallback(),this.subscription.stop(),this.announcer.dispose(),this.resizeObserver?.disconnect(),this.resizeObserver=void 0,this.motionQuery?.removeEventListener(`change`,this.onMotionChange),this.sourcesFor=void 0,this.clearSourcesRetry()}shouldUpdate(e){if(e.size!==1||!e.has(`hass`))return!0;let t=e.get(`hass`),n=this.hass;return!t||!n||t.connection!==n.connection||(t.locale?.language??t.language)!==(n.locale?.language??n.language)}willUpdate(e){(e.has(`hass`)||e.has(`config`)||e.has(`sources`)||e.has(`siteOverride`))&&this.sync();let t=this.config;if(!t)return;this.cardState=je({sources:this.sources,binding:this.binding,snapshot:this.snapshot,lastGood:this.lastGood,error:this.error,incompatible:this.incompatible,disconnected:this.disconnected,maxClients:t.max_clients}),this.model=this.cardState.render?this.buildModel(this.cardState.render,this.ui):void 0;let n=this.selectedId;n!==void 0&&!(this.model?.visuals.has(n)||this.model?.nodes.has(n))&&(this.selectedId=void 0)}get binding(){return this.config?this.siteOverride??ae(this.config,this.sources):void 0}get localize(){let e=this.hass?.locale?.language??this.hass?.language??`en`;return(e!==this.localizeLang||!this.localizeFn)&&(this.localizeLang=e,this.localizeFn=Te(e)),this.localizeFn}get graphView(){return this.renderRoot.querySelector(`uit-graph-view`)}sync(){let{hass:e,config:t}=this;if(!this.isConnected||!e||!t)return;this.sourcesFor!==e.connection&&(this.sourcesFor=e.connection,this.disconnected=!1,this.clearSourcesRetry(),this.sourcesAttempt=0,this.loadSources(e));let n=this.binding,r=n?`${n.entry_id}\u0000${n.site_id}`:void 0;r!==this.boundKey&&(this.boundKey=r,this.snapshot=void 0,this.lastGood=void 0,this.error=void 0,this.sourcesError=void 0,this.incompatible=!1,this.selectedId=void 0),this.subscription.update(e.connection,n?{...n,max_clients:t.max_clients}:void 0)}async loadSources(e){if(this.sourcesPending)return;this.sourcesPending=!0,this.clearSourcesRetry();let t=e.connection;try{let n=await e.callWS({type:i});if(this.sourcesFor!==t)return;this.sources=n,this.sourcesError&&this.error===this.sourcesError&&(this.error=void 0),this.sourcesError=void 0,n.length>0?this.sourcesAttempt=0:this.scheduleSourcesRetry()}catch(e){if(this.sourcesFor!==t)return;let n=this.sourcesError;this.sourcesError=r(e),(!this.error||this.error===n)&&(this.error=this.sourcesError),this.scheduleSourcesRetry()}finally{this.sourcesPending=!1,this.isConnected&&this.sourcesFor!==void 0&&this.sourcesFor!==t&&this.hass&&this.loadSources(this.hass)}}scheduleSourcesRetry(){this.isConnected&&(this.sourcesRetry=setTimeout(()=>{this.sourcesRetry=void 0,this.hass&&this.loadSources(this.hass)},Fe(this.sourcesAttempt++)))}clearSourcesRetry(){this.sourcesRetry!==void 0&&clearTimeout(this.sourcesRetry),this.sourcesRetry=void 0}applySnapshot(e){let t=this.snapshot;this.snapshot=e,this.error=void 0,this.incompatible=!1,this.disconnected=!1,e.status!==`unavailable`&&e.nodes.length>0&&(this.lastGood=e),this.hass&&this.sources!==void 0&&!this.sources.some(t=>t.entry_id===e.entry_id)&&this.loadSources(this.hass);let n=this.localize,r=n(`announce.updated`),i=e.issues[0],a=hs(e);if(e.status===`unavailable`&&i){let t=ke(i,e,this.config?.max_clients??0);r=n(t.key,t.vars)}else a>0&&a!==hs(t)&&(r=n(`announce.offline`,{count:a}));this.announcer.announce(r)}onMotionChange=()=>{this.reducedMotion=this.motionQuery?.matches??!1};onActivate=e=>{let t=e.detail.id;this.model?.visuals.get(t)?.type===`group`&&this.toggleGroup(t),this.selectedId=t};onSelect=e=>{let t=e.detail.id,n=this.model;if(n&&!n.visuals.has(t)){let e=Xe(n,t);e&&!e.expanded&&this.toggleGroup(e.id)}this.selectedId=t};onToggleGroup=e=>{this.toggleGroup(e.detail.id)};onClose=()=>{this.selectedId=void 0};onKeydown=e=>{e.key===`Escape`&&this.selectedId!==void 0&&(e.stopPropagation(),this.selectedId=void 0)};toggleGroup(e){let t=new Set(this.ui.toggledGroups);t.has(e)?t.delete(e):t.add(e),this.ui={...this.ui,toggledGroups:t}}toggleKind(e){let t=new Set(this.ui.kinds);if(t.has(e)){if(t.size===1)return;t.delete(e)}else t.add(e);this.ui={...this.ui,kinds:t}}runAction(e){a(e===`integration`?fs:`${location.pathname}?edit=1`)}render(){let e=this.config;if(!e)return w;let t=this.localize,n=this.cardState,r=this.model,i=e.title??n.render?.site_name??this.snapshot?.site_name??t(`card.name`),a=n.render?.nodes??[],o=a.filter(e=>e.kind!==`client`).length,s=a.filter(e=>e.kind===`client`).length;return C`<ha-card>
            <div
                class="card ${this.narrow?`narrow`:``}"
                @keydown=${this.onKeydown}
                @uit-activate=${this.onActivate}
                @uit-select=${this.onSelect}
                @uit-toggle-group=${this.onToggleGroup}
                @uit-close=${this.onClose}
            >
                <header>
                    <div class="header-icon" aria-hidden="true">
                        ${E(m)}
                    </div>
                    <div class="header-text">
                        <h2 class="title" title=${i}>${i}</h2>
                        ${a.length>0?C`<div class="subtitle">
                                  ${t(`header.summary`,{devices:o,clients:s})}
                              </div>`:w}
                    </div>
                    ${this.renderSiteSelector(e,t)}
                </header>
                ${r?this.renderToolbar(t):w}
                ${r?this.renderNotices(n.notices,t):w}
                <div class="body">
                    ${r?this.renderContent(r,n,e,t):this.renderMessage(n,t)}
                </div>
                <div class="sr-only" role="status" aria-live="polite">
                    ${this.announcement}
                </div>
            </div>
        </ha-card>`}renderSiteSelector(e,t){let n=S(this.sources??[]);if(!e.show_site_selector||n.length<2)return w;let r=this.binding;return C`<label class="site">
            <span class="sr-only">${t(`toolbar.site`)}</span>
            <select
                @change=${e=>{let t=n[Number(e.target.value)];t&&(this.siteOverride=t.binding)}}
            >
                ${n.map((e,t)=>C`<option
                            value=${t}
                            ?selected=${fe(e.binding,r)}
                        >
                            ${e.label}
                        </option>`)}
            </select>
        </label>`}renderToolbar(e){let t=C`
            <div
                class="group"
                role="group"
                aria-label=${e(`toolbar.view`)}
            >
                ${ve.map(t=>C`<button
                            aria-pressed=${String(this.view===t)}
                            @click=${()=>{this.view=t}}
                        >
                            ${e(Qe[t])}
                        </button>`)}
            </div>
            <div
                class="group"
                role="group"
                aria-label=${e(`toolbar.filters`)}
            >
                ${o.map(t=>C`<button
                            aria-pressed=${String(this.ui.kinds.has(t))}
                            @click=${()=>this.toggleKind(t)}
                        >
                            ${e(Ze[t])}
                        </button>`)}
            </div>
            ${this.view===`graph`?C`<div
                      class="group"
                      role="group"
                      aria-label=${e(`toolbar.zoom`)}
                  >
                      ${this.iconButton(ee,e(`zoom.in`),()=>this.graphView?.zoomBy(1.25))}
                      ${this.iconButton(c,e(`zoom.out`),()=>this.graphView?.zoomBy(.8))}
                      ${this.iconButton(he,e(`zoom.fit`),()=>this.graphView?.fit())}
                  </div>`:w}
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
            ${E(e)}
        </button>`}actionButton(e,t){return C`<button
            class="action"
            @click=${()=>this.runAction(e)}
        >
            ${t(ps[e])}
        </button>`}renderNotices(e,t){return e.length===0?w:C`<ul class="notices">
            ${e.map(e=>C`<li class=${e.severity}>
                        <span>${t(e.key,e.vars)}</span>${e.action?this.actionButton(e.action,t):w}
                    </li>`)}
        </ul>`}renderMessage(e,t){let n=ms[e.phase],r={site:this.snapshot?.site_name??``},i=[];return n&&i.push({...n,vars:r}),i.push(...e.notices),C`<div class="message ${e.phase}">
            ${e.phase===`loading`?C`<svg
                      class="skeleton"
                      viewBox="0 0 120 60"
                      aria-hidden="true"
                  >
                      <path d="M60 18 L30 37 M60 18 L90 37"></path>
                      <circle cx="60" cy="10" r="8"></circle>
                      <circle cx="30" cy="45" r="8"></circle>
                      <circle cx="90" cy="45" r="8"></circle>
                  </svg>`:w}
            ${i.map(e=>C`<p>${t(e.key,e.vars)}</p>
                        ${e.action?this.actionButton(e.action,t):w}`)}
        </div>`}renderContent(e,t,n,r){let i=n.density??(this.narrow?`compact`:`comfortable`),a=t.render?.site_name??``,o=t.phase===`reloading`?`${r(`state.stale`)} · ${r(`state.reconnecting`)}`:r(`state.stale`);return C`<div class="content ${t.stale?`stale`:``}">
            ${t.stale?C`<span class="badge stale">${o}</span>`:w}
            ${this.view===`graph`?C`<uit-graph-view
                      .model=${e}
                      .density=${i}
                      .orientation=${n.orientation}
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
                .localize=${r}
                ?narrow=${this.narrow}
            ></uit-detail-panel>
        </div>`}static styles=[ce,ge,p`
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
                background: color-mix(
                    in srgb,
                    var(--primary-color) 15%,
                    transparent
                );
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
                border-radius: 50%;
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
                margin: 4px 12px 12px;
                border-radius: 14px;
                border: 1px solid var(--uit-line);
                background-color: color-mix(
                    in srgb,
                    var(--primary-text-color) 2.5%,
                    transparent
                );
                background-image: radial-gradient(
                    color-mix(
                        in srgb,
                        var(--primary-text-color) 12%,
                        transparent
                    )
                    1px,
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
        `]},_s=`current`,vs=``,ys={collapsed:`clients.collapsed`,expanded:`clients.expanded`,hidden:`clients.hidden`},bs={auto:`density.auto`,comfortable:`density.comfortable`,compact:`density.compact`},xs={vertical:`orientation.vertical`,horizontal:`orientation.horizontal`},Ss={site:`editor.site`,title:`editor.title`,view:`editor.view`,clients:`editor.clients`,kinds:`editor.kinds`,density:`editor.density`,orientation:`editor.orientation`,show_site_selector:`editor.show_site_selector`,show_labels:`editor.show_labels`,max_clients:`editor.max_clients`};function Cs(e,t,n){return e.map(e=>({value:e,label:n(t[e])}))}var ws=(e,t)=>typeof e==`string`&&t.includes(e);function Ts(e,t){let{entry_id:n,site_id:r}=e;if(n===void 0||r===void 0)return vs;let i=t.findIndex(e=>fe(e.binding,{entry_id:n,site_id:r}));return i>=0?String(i):_s}function Es(e,t,n){let r=t.map((e,t)=>({value:String(t),label:e.label}));return Ts(e,t)===`current`&&r.push({value:_s,label:n(`editor.site_unavailable`,{site:e.site_id??``})}),[{name:`site`,selector:{select:{mode:`dropdown`,options:r}}},{name:`title`,selector:{text:{}}},{name:``,type:`grid`,schema:[{name:`view`,selector:{select:{mode:`dropdown`,options:Cs(ve,Qe,n)}}},{name:`clients`,selector:{select:{mode:`dropdown`,options:Cs(pe,ys,n)}}},{name:`density`,selector:{select:{mode:`dropdown`,options:Cs([`auto`,..._e],bs,n)}}},{name:`orientation`,selector:{select:{mode:`dropdown`,options:Cs(de,xs,n)}}}]},{name:`kinds`,selector:{select:{multiple:!0,mode:`list`,options:Cs(o,Ze,n)}}},{name:`show_site_selector`,selector:{boolean:{}}},{name:`show_labels`,selector:{boolean:{}}},{name:`max_clients`,selector:{number:{min:1,max:500,mode:`box`}}}]}function Ds(e,t){return{site:Ts(e,t),title:e.title??``,view:e.view??`graph`,clients:e.clients??`collapsed`,density:e.density??`auto`,orientation:e.orientation??`vertical`,kinds:e.kinds?[...e.kinds]:[...o],show_site_selector:e.show_site_selector??!1,show_labels:e.show_labels??!0,max_clients:e.max_clients??500}}function Os(e,t,n){let r={...t},i=e.site??vs;if(i===vs)delete r.entry_id,delete r.site_id;else if(i!==`current`){let e=n[Number(i)];e&&(r.entry_id=e.binding.entry_id,r.site_id=e.binding.site_id)}e.title?r.title=e.title:delete r.title,ws(e.view,ve)&&(r.view=e.view),ws(e.clients,pe)&&(r.clients=e.clients),ws(e.orientation,de)&&(r.orientation=e.orientation),ws(e.density,_e)?r.density=e.density:e.density===`auto`&&delete r.density;let a=(e.kinds??[]).filter(e=>ws(e,o));a.length===o.length?delete r.kinds:a.length>0&&(r.kinds=o.filter(e=>a.includes(e))),typeof e.show_site_selector==`boolean`&&(r.show_site_selector=e.show_site_selector),typeof e.show_labels==`boolean`&&(r.show_labels=e.show_labels);let s=e.max_clients;return s===500?delete r.max_clients:typeof s==`number`&&Number.isInteger(s)&&s>=1&&s<=500&&(r.max_clients=s),r}async function ks(e=customElements,t=window.loadCardHelpers){e.get(`ha-form`)||await((await t?.())?.createCardElement({type:`entities`,entities:[]})?.constructor)?.getConfigElement?.()}var As=class extends d{static properties={hass:{attribute:!1},config:{state:!0},sources:{state:!0},formReady:{state:!0}};sourcesRequested=!1;constructor(){super(),this.formReady=!1}setConfig(e){this.config={...e}}connectedCallback(){super.connectedCallback(),ks().catch(()=>void 0).then(()=>{this.formReady=!0})}willUpdate(){this.hass&&!this.sourcesRequested&&(this.sourcesRequested=!0,this.hass.callWS({type:i}).then(e=>{this.sources=e},()=>{this.sources=[]}))}render(){let{hass:e,config:t}=this;if(!e||!t)return w;let n=Te(e.locale?.language??e.language);if(!this.formReady)return C`<p>${n(`state.loading`)}</p>`;let r=S(this.sources??[]);return C`<ha-form
            .hass=${e}
            .data=${Ds(t,r)}
            .schema=${Es(t,r,n)}
            .computeLabel=${e=>{let t=Ss[e.name];return t?n(t):``}}
            @value-changed=${this.onValueChanged}
        ></ha-form>`}onValueChanged=e=>{e.stopPropagation();let t=this.config;if(!t)return;let n=e.detail.value,r=Os(n,t,S(this.sources??[]));this.config=r,_(this,`config-changed`,{config:r})}};T(le,gs),T(ie,As);var js=Te(`en`);window.customCards??=[],window.customCards.some(e=>e.type===`unifi-insights-topology-card`)||window.customCards.push({type:le,name:js(`card.name`),description:js(`card.description`),preview:!0,documentationURL:`https://github.com/ruaan-deysel/ha-unifi-insights#network-topology-card`});