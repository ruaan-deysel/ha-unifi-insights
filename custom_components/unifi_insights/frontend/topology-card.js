import{A as e,C as t,Ct as n,D as r,Dt as i,E as a,Et as o,H as s,J as c,M as l,N as u,O as d,Ot as f,P as p,Q as m,S as h,St as g,T as _,Tt as v,V as y,W as b,Y as ee,Z as x,_t as te,at as ne,b as re,bt as ie,ct as ae,dt as oe,ft as se,gt as ce,ht as le,it as ue,j as S,k as C,kt as de,lt as fe,mt as pe,ot as me,pt as he,q as ge,rt as w,st as _e,ut as ve,vt as ye,w as T,wt as be,x as xe,xt as Se,yt as Ce}from"./chunks/register-dashboard-card-DFoe8fM2.js";import"./internet-activity-card.js";import"./performance-card.js";import"./protect-status-card.js";import"./site-health-card.js";import"./timeline-card.js";var we={"card.name":`UniFi Topology`,"card.description":`Interactive network topology of a UniFi site, from UniFi Insights.`,"header.summary":`{devices} devices · {clients} clients`,"state.loading":`Loading network topology…`,"state.no_sources":`No UniFi Insights integration is loaded.`,"state.unconfigured":`Choose a site to show.`,"state.empty":`No devices reported for {site}.`,"state.incompatible":`Card and integration versions don't match. Refresh the browser (clear cache) after updating.`,"state.stale":`Stale`,"state.reconnecting":`Reconnecting…`,"state.online":`Online`,"state.offline":`Offline`,"state.unknown":`Unknown`,"issue.site_unavailable":`Site data temporarily unavailable; will recover automatically.`,"issue.devices_unavailable":`Device data unavailable; showing last known layout.`,"issue.legacy_uplink_missing":`Uplink details unavailable; device links may be missing.`,"issue.parents_unresolved":`{count} nodes couldn't be placed under a parent.`,"issue.clients_truncated":`Showing {included} of {total} clients (limit {max}).`,"issue.entry_unloaded":`Integration is reloading.`,"issue.unknown":`Topology problem: {code}.`,"error.entry_not_found":`The configured site no longer exists or is disabled.`,"error.site_not_selected":`The configured site no longer exists or is disabled.`,"error.entry_not_loaded":`Integration isn't loaded (retrying).`,"error.unknown":`Could not load the topology ({code}).`,"action.integration":`Integration`,"action.edit":`Edit card`,"view.graph":`Graph`,"view.list":`List`,"toolbar.view":`View`,"toolbar.filters":`Show`,"toolbar.zoom":`Zoom`,"toolbar.options":`Options`,"toolbar.site":`Site`,"zoom.in":`Zoom in`,"zoom.out":`Zoom out`,"zoom.fit":`Fit to view`,"zoom.hint":`Use Ctrl + scroll to zoom`,"kind.gateway":`Gateway`,"kind.switch":`Switch`,"kind.access_point":`Access point`,"kind.client":`Client`,"kind.other":`Other`,"medium.wired":`Wired`,"medium.wireless":`Wireless`,"medium.unknown":`Unknown`,"group.clients":`{count} clients`,"group.client_one":`1 client`,"group.unconnected":`Unconnected clients`,"group.root":`Clients`,"group.summary":`{wireless} wireless, {offline} offline`,"graph.label":`{site} topology, {devices} devices, {clients} clients`,"graph.roledescription":`network topology`,"node.label":`{kind} {name}, {state}`,"node.clients":`{count} clients`,"node.client_one":`1 client`,"node.uplink":`uplink port {port}`,"node.uplink_speed":`uplink port {port} at {speed}`,"list.label":`{site} devices and clients`,"list.search":`Search`,"list.no_matches":`No matches`,"detail.close":`Close`,"detail.kind":`Type`,"detail.model":`Model`,"detail.state":`State`,"detail.parent":`Connected to`,"detail.port":`Port`,"detail.speed":`Speed`,"detail.medium":`Link`,"detail.poe":`PoE`,"detail.clients":`Clients`,"detail.clients_value":`{total} ({wired} wired, {wireless} wireless)`,"detail.connection":`Connection`,"detail.vlan":`VLAN`,"detail.network":`Network`,"detail.via_hidden":`Via hidden`,"detail.open_device":`Open device`,"detail.search_members":`Search clients`,"announce.updated":`Topology updated.`,"announce.offline":`{count} devices offline.`,"editor.site":`Site`,"editor.site_unavailable":`{site} (unavailable)`,"editor.title":`Title`,"editor.view":`Default view`,"editor.clients":`Clients`,"editor.kinds":`Show node types`,"editor.density":`Density`,"editor.orientation":`Orientation`,"editor.show_site_selector":`Show site selector`,"editor.show_labels":`Show labels`,"editor.max_clients":`Maximum clients`,"clients.collapsed":`Grouped`,"clients.expanded":`Expanded`,"clients.hidden":`Hidden`,"density.auto":`Automatic`,"density.comfortable":`Comfortable`,"density.compact":`Compact`,"orientation.vertical":`Top to bottom`,"orientation.horizontal":`Left to right`},Te={en:we};function Ee(e){let t=(e??`en`).toLowerCase(),n=Te[t]??Te[t.split(`-`)[0]??`en`]??{};return(e,t)=>{let r=n[e]??we[e];if(t)for(let[e,n]of Object.entries(t))r=r.replaceAll(`{${e}}`,String(n));return r}}var De=class{last=-1/0;pending;timer;emit;intervalMs;constructor(e,t=5e3){this.emit=e,this.intervalMs=t}announce(e){let t=this.last+this.intervalMs-Date.now();if(t<=0&&this.timer===void 0){this.last=Date.now(),this.emit(e);return}this.pending=e,this.timer??=setTimeout(()=>{this.timer=void 0;let e=this.pending;this.pending=void 0,e!==void 0&&(this.last=Date.now(),this.emit(e))},Math.max(t,0))}dispose(){this.timer!==void 0&&clearTimeout(this.timer),this.timer=void 0,this.pending=void 0}},Oe={[be]:{key:`issue.site_unavailable`},[ie]:{key:`issue.devices_unavailable`,action:`integration`},[g]:{key:`issue.legacy_uplink_missing`},[n]:{key:`issue.parents_unresolved`},[Ce]:{key:`issue.clients_truncated`},[Se]:{key:`issue.entry_unloaded`}},ke={[ce]:{key:`error.entry_not_found`,action:`edit`},[ye]:{key:`error.site_not_selected`,action:`edit`},[te]:{key:`error.entry_not_loaded`,action:`integration`}};function Ae(e,t,n){let r=Oe[e.code];if(!r)return{code:e.code,severity:e.severity,key:`issue.unknown`,vars:{code:e.code}};let i={code:e.code,severity:e.severity,key:r.key};return e.code===`parents_unresolved`&&(i.vars={count:t.unresolved.length}),e.code===`clients_truncated`&&t.truncation&&(i.vars={included:t.truncation.clients_included,total:t.truncation.clients_total,max:n}),r.action&&(i.action=r.action),i}function je(e){let t=ke[e.code];if(!t)return{code:e.code,severity:`error`,key:`error.unknown`,vars:{code:e.code}};let n={code:e.code,severity:`error`,key:t.key};return t.action&&(n.action=t.action),n}function Me(e){if(e.incompatible)return{phase:`incompatible`,stale:!1,notices:[]};if(e.error)return{phase:`error`,render:e.lastGood,stale:e.lastGood!==void 0,notices:[je(e.error)]};if(e.disconnected){let t=e.snapshot,n=t&&t.nodes.length>0?t:e.lastGood;if(n)return{phase:`reloading`,render:n,stale:!0,notices:[]}}if(e.sources!==void 0&&e.sources.length===0&&e.snapshot===void 0)return{phase:`no_sources`,stale:!1,notices:[]};if(e.binding===void 0)return{phase:e.sources===void 0?`loading`:`unconfigured`,stale:!1,notices:[]};let t=e.snapshot;if(t===void 0)return{phase:`loading`,stale:!1,notices:[]};let n=t.issues.map(n=>Ae(n,t,e.maxClients));if(t.status===`unavailable`){let r=t.issues.some(e=>e.code===Se),i=t.nodes.length>0?t:e.lastGood;return{phase:r?`reloading`:`unavailable`,render:i,stale:i!==void 0,notices:n}}return t.nodes.length===0?{phase:`empty`,stale:!1,notices:n}:{phase:t.status===`partial`?`partial`:`ok`,render:t,stale:!1,notices:n}}var Ne=new Set([te,`unknown_command`]),Pe=2e3,Fe=6e4;function Ie(e,t=Math.random){let n=Math.min(Pe*2**e,Fe);return Math.round(n*(.8+.4*t()))}var Le=class{generation=0;connection;key;keyId;unsubscribe;retryTimer;attempt=0;lastRevision;isLive=!1;handlers;random;constructor(e,t=Math.random){this.handlers=e,this.random=t}get live(){return this.isLive}update(e,t){let n=t?JSON.stringify([t.entry_id,t.site_id,t.max_clients]):void 0;(e!==this.connection||n!==this.keyId)&&(this.stop(),this.connection=e,this.key=t,this.keyId=n,e&&(e.addEventListener(`ready`,this.onReady),e.addEventListener(`disconnected`,this.onDisconnected)),e&&t&&this.open())}stop(){this.generation++,this.clearRetry(),this.attempt=0,this.release(),this.connection?.removeEventListener(`ready`,this.onReady),this.connection?.removeEventListener(`disconnected`,this.onDisconnected),this.connection=void 0,this.key=void 0,this.keyId=void 0}clearRetry(){this.retryTimer!==void 0&&clearTimeout(this.retryTimer),this.retryTimer=void 0}drop(){this.generation++,this.clearRetry(),this.unsubscribe=void 0,this.isLive=!1,this.lastRevision=void 0}onDisconnected=()=>{this.drop(),this.handlers.onDisconnected()};onReady=()=>{this.drop(),this.attempt=0,this.key&&this.open(),this.handlers.onReconnected()};release(){let e=this.unsubscribe;this.unsubscribe=void 0,this.isLive=!1,this.lastRevision=void 0,e&&e().catch(()=>void 0)}open(){let e=++this.generation,{connection:t,key:n}=this;t&&n&&t.subscribeMessage(t=>{e===this.generation&&this.receive(t)},{type:f,entry_id:n.entry_id,site_id:n.site_id,max_clients:n.max_clients},{resubscribe:!1}).then(t=>{e===this.generation?this.unsubscribe=t:t().catch(()=>void 0)},t=>{if(e!==this.generation)return;let n=r(t);this.handlers.onError(n),Ne.has(n.code)&&this.scheduleRetry()})}receive(e){let t;try{t=de(e)}catch(e){e instanceof v?this.handlers.onIncompatible():this.handlers.onError({code:`invalid_payload`,message:String(e)});return}let n=t.issues.some(e=>e.code===Se);n||(this.isLive=!0,this.attempt=0),(t.revision===``||t.revision!==this.lastRevision)&&(this.lastRevision=t.revision,this.handlers.onSnapshot(t),n&&(this.generation++,this.release(),this.scheduleRetry()))}scheduleRetry(){let e=this.generation,t=Ie(this.attempt++,this.random);this.retryTimer=setTimeout(()=>{this.retryTimer=void 0,e===this.generation&&this.open()},t)}},Re=`group:unconnected`,ze=`group:root`,Be=e=>`group:${e}`,Ve={gateway:0,switch:1,access_point:2,other:3,client:4},He=(e,t)=>e.name.localeCompare(t.name)||e.id.localeCompare(t.id),Ue=(e,t)=>Ve[e.kind]-Ve[t.kind]||He(e,t);function We(e,t){let n=e.toggledGroups.has(t);return e.clients===`expanded`?!n:n}var Ge=()=>({total:0,wired:0,wireless:0,offline:0});function Ke(e,t){e.total++,t.connection===`wired`&&e.wired++,t.connection===`wireless`&&e.wireless++,t.state===`offline`&&e.offline++}function qe(e,t,n){let r=new Set;for(let i of e){let e=new Set,a=i.id;for(;a!==void 0&&!r.has(a);){e.add(a);let r=t.get(a);if(r!==void 0&&e.has(r)){t.delete(a),n.delete(a);break}a=r}for(let t of e)r.add(t)}}function Je(e,t){let n=new Map(e.nodes.map(e=>[e.id,e])),r=new Map,i=new Map;for(let t of e.edges){let e=n.get(t.source),a=n.get(t.target);e&&a&&e.id!==a.id&&a.kind!==`client`&&!r.has(e.id)&&(r.set(e.id,a.id),i.set(e.id,t))}qe(e.nodes,r,i);let a=e.nodes.filter(e=>e.kind!==`client`).sort(Ue),o=e.nodes.filter(e=>e.kind===`client`).sort(He),s=new Map;for(let e of o){let t=r.get(e.id);if(t===void 0)continue;let n=s.get(t);n||s.set(t,n=Ge()),Ke(n,e)}let c=new Map,l=new Map,u=new Map,d=new Map,f=[],p=e=>t.kinds.has(e.kind),m=e=>{let t=[],i=r.get(e);for(;i!==void 0;){let e=n.get(i);if(p(e))return{id:i,skipped:t};t.push(e.kind),i=r.get(i)}return{id:void 0,skipped:t}},h=(e,t,n,r)=>{if(t===void 0){f.push(e);return}u.set(e,t),d.set(e,{childId:e,parentId:t,edge:n,viaHidden:[...new Set(r)]});let i=l.get(t);i?i.push(e):l.set(t,[e])};for(let e of a){if(!p(e))continue;c.set(e.id,{type:`device`,id:e.id,node:e});let t=m(e.id);h(e.id,t.id,i.get(e.id),t.skipped)}if(t.clients!==`hidden`&&t.kinds.has(`client`)){let e=new Map;for(let t of o){let i=r.get(t.id),a,o=[],s;if(i===void 0)s=Re;else{let e=n.get(i);if(p(e))a=i;else{let t=m(i);a=t.id,o=[e.kind,...t.skipped]}s=a===void 0?ze:Be(a)}let c=e.get(s);c||e.set(s,c={parent:a,members:[],skipped:new Set}),c.members.push(t);for(let e of o)c.skipped.add(e)}let a=[...e].sort(([e],[t])=>Number(e===Re)-Number(t===Re));for(let[e,n]of a){let r=Ge();for(let e of n.members)Ke(r,e);let a=We(t,e);if(c.set(e,{type:`group`,id:e,members:n.members,counts:r,expanded:a}),h(e,n.parent,void 0,n.skipped),a)for(let t of n.members)c.set(t.id,{type:`client`,id:t.id,node:t}),h(t.id,e,i.get(t.id),[])}}return{snapshot:e,roots:f,visuals:c,children:l,parentOf:u,links:d,nodes:n,realParent:r,edges:i,clientCounts:s,stats:{devices:a.length,clients:o.length,offlineDevices:a.filter(e=>e.state===`offline`).length}}}function Ye(){let e,t,n;return(r,i)=>n&&r===e&&i===t?n:(e=r,t=i,n=Je(r,i),n)}function Xe(e,t){let n=e.parentOf.get(t);return n===void 0?e.roots:e.children.get(n)??[]}function Ze(e,t){for(let n of e.visuals.values())if(n.type===`group`&&n.members.some(e=>e.id===t))return n}var Qe={gateway:`kind.gateway`,switch:`kind.switch`,access_point:`kind.access_point`,client:`kind.client`,other:`kind.other`},E={online:`state.online`,offline:`state.offline`,unknown:`state.unknown`},$e={graph:`view.graph`,list:`view.list`},et={wired:`medium.wired`,wireless:`medium.wireless`,unknown:`medium.unknown`};function tt(e,t){let n=[...e];return n.length>t?`${n.slice(0,t-1).join(``)}…`:e}var nt=e=>Number.isInteger(e)?String(e):e.toFixed(1);function rt(e){return e>=1e3?`${nt(e/1e3)}G`:`${e}M`}function it(e){return e>=1e3?`${nt(e/1e3)} gigabit`:`${e} megabit`}function at(e){if(!e)return``;let t=[];return e.parent_port!==void 0&&t.push(`p${e.parent_port}`),e.speed_mbps&&t.push(rt(e.speed_mbps)),e.poe_power_w!==void 0&&t.push(`PoE`),t.join(` · `)}function D(e,t){return e.type===`group`?e.id===`group:unconnected`?t(`group.unconnected`):e.id===`group:root`?t(`group.root`):e.counts.total===1?t(`group.client_one`):t(`group.clients`,{count:e.counts.total}):e.node.name}function ot(e){return e.type===`group`?e.counts.offline===e.counts.total?`offline`:`online`:e.node.state}function st(e,t,n){if(t.type===`group`)return`${D(t,n)}: ${n(`group.summary`,{wireless:t.counts.wireless,offline:t.counts.offline})}`;let r=t.node,i=[n(`node.label`,{kind:n(Qe[r.kind]),name:r.name,state:n(E[r.state]).toLocaleLowerCase()})],a=e.clientCounts.get(r.id)?.total??0;a>0&&i.push(a===1?n(`node.client_one`):n(`node.clients`,{count:a}));let o=e.edges.get(r.id);return o?.parent_port===void 0?r.connection&&i.push(n(et[r.connection]).toLocaleLowerCase()):i.push(o.speed_mbps?n(`node.uplink_speed`,{port:o.parent_port,speed:it(o.speed_mbps)}):n(`node.uplink`,{port:o.parent_port})),i.join(`, `)}var ct=class extends d{static properties={model:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},narrow:{type:Boolean,reflect:!0},memberQuery:{state:!0}};constructor(){super(),this.narrow=!1,this.memberQuery=``}willUpdate(e){e.has(`selectedId`)&&(this.memberQuery=``)}render(){let{model:e,selectedId:t,localize:n}=this;if(!e||!t||!n)return C;let r=e.visuals.get(t);if(r?.type===`group`)return this.shell(D(r,n),this.groupBody(r,n));let i=e.nodes.get(t);if(!i)return C;let a=i.kind===`client`?this.clientBody(e,i,n):this.deviceBody(e,i,n);return this.shell(i.name,a)}shell(e,t){let n=this.localize;return S`<section class="panel" role="region" aria-label=${e}>
            <header>
                <h3 title=${e}>${e}</h3>
                <button
                    class="close"
                    aria-label=${n(`detail.close`)}
                    title=${n(`detail.close`)}
                    @click=${()=>_(this,`uit-close`)}
                >
                    ${T(b)}
                </button>
            </header>
            ${t}
        </section>`}rows(e){let t=e.filter(e=>e[1]!==void 0&&e[1]!==``);return S`<dl>
            ${t.map(([e,t])=>S`<div class="row">
                        <dt>${this.localize(e)}</dt>
                        <dd>${t}</dd>
                    </div>`)}
        </dl>`}uplinkRows(e,t,n,r){let i=e.realParent.get(t),a=e.edges.get(t),o;return a?.parent_port!==void 0&&(o=a.child_port===void 0?String(a.parent_port):`${a.parent_port} → ${a.child_port}`),[[`detail.parent`,i===void 0?void 0:e.nodes.get(i)?.name],[`detail.port`,o],[`detail.speed`,a?.speed_mbps?rt(a.speed_mbps):void 0],[`detail.medium`,r&&a?n(et[a.medium]):void 0],[`detail.poe`,a?.poe_power_w===void 0?void 0:`${a.poe_power_w.toFixed(1)} W`]]}deviceBody(e,t,n){let r=e.clientCounts.get(t.id),i=e.links.get(t.id)?.viaHidden??[];return S`${this.rows([[`detail.kind`,n(Qe[t.kind])],[`detail.model`,t.model],[`detail.state`,n(E[t.state])],...this.uplinkRows(e,t.id,n,!0),[`detail.clients`,r?n(`detail.clients_value`,{total:r.total,wired:r.wired,wireless:r.wireless}):void 0],[`detail.via_hidden`,i.length>0?i.map(e=>n(Qe[e])).join(`, `):void 0]])}
        ${t.ha_device_id?S`<button
                  class="action"
                  @click=${()=>a(`/config/devices/device/${encodeURIComponent(t.ha_device_id)}`)}
              >
                  ${T(x)}${n(`detail.open_device`)}
              </button>`:C}`}clientBody(e,t,n){return this.rows([[`detail.state`,n(E[t.state])],[`detail.connection`,t.connection?n(et[t.connection]):void 0],[`detail.vlan`,t.vlan_id===void 0?void 0:String(t.vlan_id)],[`detail.network`,t.network_name],...this.uplinkRows(e,t.id,n,!1)])}groupBody(e,n){let r=this.memberQuery.trim().toLowerCase(),i=r?e.members.filter(e=>e.name.toLowerCase().includes(r)):e.members,a=e.counts;return S`${this.rows([[`detail.clients`,n(`detail.clients_value`,{total:a.total,wired:a.wired,wireless:a.wireless})]])}
            <input
                type="search"
                .value=${this.memberQuery}
                placeholder=${n(`detail.search_members`)}
                aria-label=${n(`detail.search_members`)}
                @input=${e=>{this.memberQuery=e.target.value}}
            />
            <ul class="members">
                ${i.map(e=>S`<li>
                            <button
                                class="member ${e.state}"
                                @click=${()=>_(this,`uit-select`,{id:e.id})}
                            >
                                ${T(t(e))}<span
                                    class="name"
                                    title=${e.name}
                                    >${e.name}</span
                                >
                                ${e.state===`online`?C:S`<span class="state-text"
                                          >${n(E[e.state])}</span
                                      >`}
                            </button>
                        </li>`)}
            </ul>`}static styles=[xe,re,p`
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
        `]};w(`uit-detail-panel`,ct);var lt={svg:`http://www.w3.org/2000/svg`,xhtml:`http://www.w3.org/1999/xhtml`,xlink:`http://www.w3.org/1999/xlink`,xml:`http://www.w3.org/XML/1998/namespace`,xmlns:`http://www.w3.org/2000/xmlns/`};function ut(e){var t=e+=``,n=t.indexOf(`:`);return n>=0&&(t=e.slice(0,n))!==`xmlns`&&(e=e.slice(n+1)),lt.hasOwnProperty(t)?{space:lt[t],local:e}:e}function dt(e){return function(){var t=this.ownerDocument,n=this.namespaceURI;return n===`http://www.w3.org/1999/xhtml`&&t.documentElement.namespaceURI===`http://www.w3.org/1999/xhtml`?t.createElement(e):t.createElementNS(n,e)}}function ft(e){return function(){return this.ownerDocument.createElementNS(e.space,e.local)}}function pt(e){var t=ut(e);return(t.local?ft:dt)(t)}function mt(){}function ht(e){return e==null?mt:function(){return this.querySelector(e)}}function gt(e){typeof e!=`function`&&(e=ht(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=Array(o),c,l,u=0;u<o;++u)(c=a[u])&&(l=e.call(c,c.__data__,u,a))&&(`__data__`in c&&(l.__data__=c.__data__),s[u]=l);return new k(r,this._parents)}function _t(e){return e==null?[]:Array.isArray(e)?e:Array.from(e)}function vt(){return[]}function yt(e){return e==null?vt:function(){return this.querySelectorAll(e)}}function bt(e){return function(){return _t(e.apply(this,arguments))}}function xt(e){e=typeof e==`function`?bt(e):yt(e);for(var t=this._groups,n=t.length,r=[],i=[],a=0;a<n;++a)for(var o=t[a],s=o.length,c,l=0;l<s;++l)(c=o[l])&&(r.push(e.call(c,c.__data__,l,o)),i.push(c));return new k(r,i)}function St(e){return function(){return this.matches(e)}}function Ct(e){return function(t){return t.matches(e)}}var wt=Array.prototype.find;function Tt(e){return function(){return wt.call(this.children,e)}}function Et(){return this.firstElementChild}function Dt(e){return this.select(e==null?Et:Tt(typeof e==`function`?e:Ct(e)))}var Ot=Array.prototype.filter;function kt(){return Array.from(this.children)}function At(e){return function(){return Ot.call(this.children,e)}}function jt(e){return this.selectAll(e==null?kt:At(typeof e==`function`?e:Ct(e)))}function Mt(e){typeof e!=`function`&&(e=St(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=[],c,l=0;l<o;++l)(c=a[l])&&e.call(c,c.__data__,l,a)&&s.push(c);return new k(r,this._parents)}function Nt(e){return Array(e.length)}function Pt(){return new k(this._enter||this._groups.map(Nt),this._parents)}function Ft(e,t){this.ownerDocument=e.ownerDocument,this.namespaceURI=e.namespaceURI,this._next=null,this._parent=e,this.__data__=t}Ft.prototype={constructor:Ft,appendChild:function(e){return this._parent.insertBefore(e,this._next)},insertBefore:function(e,t){return this._parent.insertBefore(e,t)},querySelector:function(e){return this._parent.querySelector(e)},querySelectorAll:function(e){return this._parent.querySelectorAll(e)}};function It(e){return function(){return e}}function Lt(e,t,n,r,i,a){for(var o=0,s,c=t.length,l=a.length;o<l;++o)(s=t[o])?(s.__data__=a[o],r[o]=s):n[o]=new Ft(e,a[o]);for(;o<c;++o)(s=t[o])&&(i[o]=s)}function Rt(e,t,n,r,i,a,o){var s,c,l=new Map,u=t.length,d=a.length,f=Array(u),p;for(s=0;s<u;++s)(c=t[s])&&(f[s]=p=o.call(c,c.__data__,s,t)+``,l.has(p)?i[s]=c:l.set(p,c));for(s=0;s<d;++s)p=o.call(e,a[s],s,a)+``,(c=l.get(p))?(r[s]=c,c.__data__=a[s],l.delete(p)):n[s]=new Ft(e,a[s]);for(s=0;s<u;++s)(c=t[s])&&l.get(f[s])===c&&(i[s]=c)}function zt(e){return e.__data__}function Bt(e,t){if(!arguments.length)return Array.from(this,zt);var n=t?Rt:Lt,r=this._parents,i=this._groups;typeof e!=`function`&&(e=It(e));for(var a=i.length,o=Array(a),s=Array(a),c=Array(a),l=0;l<a;++l){var u=r[l],d=i[l],f=d.length,p=Vt(e.call(u,u&&u.__data__,l,r)),m=p.length,h=s[l]=Array(m),g=o[l]=Array(m);n(u,d,h,g,c[l]=Array(f),p,t);for(var _=0,v=0,y,b;_<m;++_)if(y=h[_]){for(_>=v&&(v=_+1);!(b=g[v])&&++v<m;);y._next=b||null}}return o=new k(o,r),o._enter=s,o._exit=c,o}function Vt(e){return typeof e==`object`&&`length`in e?e:Array.from(e)}function Ht(){return new k(this._exit||this._groups.map(Nt),this._parents)}function Ut(e,t,n){var r=this.enter(),i=this,a=this.exit();return typeof e==`function`?(r=e(r),r&&=r.selection()):r=r.append(e+``),t!=null&&(i=t(i),i&&=i.selection()),n==null?a.remove():n(a),r&&i?r.merge(i).order():i}function Wt(e){for(var t=e.selection?e.selection():e,n=this._groups,r=t._groups,i=n.length,a=r.length,o=Math.min(i,a),s=Array(i),c=0;c<o;++c)for(var l=n[c],u=r[c],d=l.length,f=s[c]=Array(d),p,m=0;m<d;++m)(p=l[m]||u[m])&&(f[m]=p);for(;c<i;++c)s[c]=n[c];return new k(s,this._parents)}function Gt(){for(var e=this._groups,t=-1,n=e.length;++t<n;)for(var r=e[t],i=r.length-1,a=r[i],o;--i>=0;)(o=r[i])&&(a&&o.compareDocumentPosition(a)^4&&a.parentNode.insertBefore(o,a),a=o);return this}function Kt(e){e||=qt;function t(t,n){return t&&n?e(t.__data__,n.__data__):!t-!n}for(var n=this._groups,r=n.length,i=Array(r),a=0;a<r;++a){for(var o=n[a],s=o.length,c=i[a]=Array(s),l,u=0;u<s;++u)(l=o[u])&&(c[u]=l);c.sort(t)}return new k(i,this._parents).order()}function qt(e,t){return e<t?-1:e>t?1:e>=t?0:NaN}function Jt(){var e=arguments[0];return arguments[0]=this,e.apply(null,arguments),this}function Yt(){return Array.from(this)}function Xt(){for(var e=this._groups,t=0,n=e.length;t<n;++t)for(var r=e[t],i=0,a=r.length;i<a;++i){var o=r[i];if(o)return o}return null}function Zt(){let e=0;for(let t of this)++e;return e}function Qt(){return!this.node()}function $t(e){for(var t=this._groups,n=0,r=t.length;n<r;++n)for(var i=t[n],a=0,o=i.length,s;a<o;++a)(s=i[a])&&e.call(s,s.__data__,a,i);return this}function en(e){return function(){this.removeAttribute(e)}}function tn(e){return function(){this.removeAttributeNS(e.space,e.local)}}function nn(e,t){return function(){this.setAttribute(e,t)}}function rn(e,t){return function(){this.setAttributeNS(e.space,e.local,t)}}function an(e,t){return function(){var n=t.apply(this,arguments);n==null?this.removeAttribute(e):this.setAttribute(e,n)}}function on(e,t){return function(){var n=t.apply(this,arguments);n==null?this.removeAttributeNS(e.space,e.local):this.setAttributeNS(e.space,e.local,n)}}function sn(e,t){var n=ut(e);if(arguments.length<2){var r=this.node();return n.local?r.getAttributeNS(n.space,n.local):r.getAttribute(n)}return this.each((t==null?n.local?tn:en:typeof t==`function`?n.local?on:an:n.local?rn:nn)(n,t))}function cn(e){return e.ownerDocument&&e.ownerDocument.defaultView||e.document&&e||e.defaultView}function ln(e){return function(){this.style.removeProperty(e)}}function un(e,t,n){return function(){this.style.setProperty(e,t,n)}}function dn(e,t,n){return function(){var r=t.apply(this,arguments);r==null?this.style.removeProperty(e):this.style.setProperty(e,r,n)}}function fn(e,t,n){return arguments.length>1?this.each((t==null?ln:typeof t==`function`?dn:un)(e,t,n??``)):O(this.node(),e)}function O(e,t){return e.style.getPropertyValue(t)||cn(e).getComputedStyle(e,null).getPropertyValue(t)}function pn(e){return function(){delete this[e]}}function mn(e,t){return function(){this[e]=t}}function hn(e,t){return function(){var n=t.apply(this,arguments);n==null?delete this[e]:this[e]=n}}function gn(e,t){return arguments.length>1?this.each((t==null?pn:typeof t==`function`?hn:mn)(e,t)):this.node()[e]}function _n(e){return e.trim().split(/^|\s+/)}function vn(e){return e.classList||new yn(e)}function yn(e){this._node=e,this._names=_n(e.getAttribute(`class`)||``)}yn.prototype={add:function(e){this._names.indexOf(e)<0&&(this._names.push(e),this._node.setAttribute(`class`,this._names.join(` `)))},remove:function(e){var t=this._names.indexOf(e);t>=0&&(this._names.splice(t,1),this._node.setAttribute(`class`,this._names.join(` `)))},contains:function(e){return this._names.indexOf(e)>=0}};function bn(e,t){for(var n=vn(e),r=-1,i=t.length;++r<i;)n.add(t[r])}function xn(e,t){for(var n=vn(e),r=-1,i=t.length;++r<i;)n.remove(t[r])}function Sn(e){return function(){bn(this,e)}}function Cn(e){return function(){xn(this,e)}}function wn(e,t){return function(){(t.apply(this,arguments)?bn:xn)(this,e)}}function Tn(e,t){var n=_n(e+``);if(arguments.length<2){for(var r=vn(this.node()),i=-1,a=n.length;++i<a;)if(!r.contains(n[i]))return!1;return!0}return this.each((typeof t==`function`?wn:t?Sn:Cn)(n,t))}function En(){this.textContent=``}function Dn(e){return function(){this.textContent=e}}function On(e){return function(){var t=e.apply(this,arguments);this.textContent=t??``}}function kn(e){return arguments.length?this.each(e==null?En:(typeof e==`function`?On:Dn)(e)):this.node().textContent}function An(){this.innerHTML=``}function jn(e){return function(){this.innerHTML=e}}function Mn(e){return function(){var t=e.apply(this,arguments);this.innerHTML=t??``}}function Nn(e){return arguments.length?this.each(e==null?An:(typeof e==`function`?Mn:jn)(e)):this.node().innerHTML}function Pn(){this.nextSibling&&this.parentNode.appendChild(this)}function Fn(){return this.each(Pn)}function In(){this.previousSibling&&this.parentNode.insertBefore(this,this.parentNode.firstChild)}function Ln(){return this.each(In)}function Rn(e){var t=typeof e==`function`?e:pt(e);return this.select(function(){return this.appendChild(t.apply(this,arguments))})}function zn(){return null}function Bn(e,t){var n=typeof e==`function`?e:pt(e),r=t==null?zn:typeof t==`function`?t:ht(t);return this.select(function(){return this.insertBefore(n.apply(this,arguments),r.apply(this,arguments)||null)})}function Vn(){var e=this.parentNode;e&&e.removeChild(this)}function Hn(){return this.each(Vn)}function Un(){var e=this.cloneNode(!1),t=this.parentNode;return t?t.insertBefore(e,this.nextSibling):e}function Wn(){var e=this.cloneNode(!0),t=this.parentNode;return t?t.insertBefore(e,this.nextSibling):e}function Gn(e){return this.select(e?Wn:Un)}function Kn(e){return arguments.length?this.property(`__data__`,e):this.node().__data__}function qn(e){return function(t){e.call(this,t,this.__data__)}}function Jn(e){return e.trim().split(/^|\s+/).map(function(e){var t=``,n=e.indexOf(`.`);return n>=0&&(t=e.slice(n+1),e=e.slice(0,n)),{type:e,name:t}})}function Yn(e){return function(){var t=this.__on;if(t){for(var n=0,r=-1,i=t.length,a;n<i;++n)a=t[n],(!e.type||a.type===e.type)&&a.name===e.name?this.removeEventListener(a.type,a.listener,a.options):t[++r]=a;++r?t.length=r:delete this.__on}}}function Xn(e,t,n){return function(){var r=this.__on,i,a=qn(t);if(r){for(var o=0,s=r.length;o<s;++o)if((i=r[o]).type===e.type&&i.name===e.name){this.removeEventListener(i.type,i.listener,i.options),this.addEventListener(i.type,i.listener=a,i.options=n),i.value=t;return}}this.addEventListener(e.type,a,n),i={type:e.type,name:e.name,value:t,listener:a,options:n},r?r.push(i):this.__on=[i]}}function Zn(e,t,n){var r=Jn(e+``),i,a=r.length,o;if(arguments.length<2){var s=this.node().__on;if(s){for(var c=0,l=s.length,u;c<l;++c)for(i=0,u=s[c];i<a;++i)if((o=r[i]).type===u.type&&o.name===u.name)return u.value}return}for(s=t?Xn:Yn,i=0;i<a;++i)this.each(s(r[i],t,n));return this}function Qn(e,t,n){var r=cn(e),i=r.CustomEvent;typeof i==`function`?i=new i(t,n):(i=r.document.createEvent(`Event`),n?(i.initEvent(t,n.bubbles,n.cancelable),i.detail=n.detail):i.initEvent(t,!1,!1)),e.dispatchEvent(i)}function $n(e,t){return function(){return Qn(this,e,t)}}function er(e,t){return function(){return Qn(this,e,t.apply(this,arguments))}}function tr(e,t){return this.each((typeof t==`function`?er:$n)(e,t))}function*nr(){for(var e=this._groups,t=0,n=e.length;t<n;++t)for(var r=e[t],i=0,a=r.length,o;i<a;++i)(o=r[i])&&(yield o)}var rr=[null];function k(e,t){this._groups=e,this._parents=t}function A(){return new k([[document.documentElement]],rr)}function ir(){return this}k.prototype=A.prototype={constructor:k,select:gt,selectAll:xt,selectChild:Dt,selectChildren:jt,filter:Mt,data:Bt,enter:Pt,exit:Ht,join:Ut,merge:Wt,selection:ir,order:Gt,sort:Kt,call:Jt,nodes:Yt,node:Xt,size:Zt,empty:Qt,each:$t,attr:sn,style:fn,property:gn,classed:Tn,text:kn,html:Nn,raise:Fn,lower:Ln,append:Rn,insert:Bn,remove:Hn,clone:Gn,datum:Kn,on:Zn,dispatch:tr,[Symbol.iterator]:nr};function j(e){return typeof e==`string`?new k([[document.querySelector(e)]],[document.documentElement]):new k([[e]],rr)}function ar(e){let t;for(;t=e.sourceEvent;)e=t;return e}function M(e,t){if(e=ar(e),t===void 0&&(t=e.currentTarget),t){var n=t.ownerSVGElement||t;if(n.createSVGPoint){var r=n.createSVGPoint();return r.x=e.clientX,r.y=e.clientY,r=r.matrixTransform(t.getScreenCTM().inverse()),[r.x,r.y]}if(t.getBoundingClientRect){var i=t.getBoundingClientRect();return[e.clientX-i.left-t.clientLeft,e.clientY-i.top-t.clientTop]}}return[e.pageX,e.pageY]}var or={value:()=>{}};function sr(){for(var e=0,t=arguments.length,n={},r;e<t;++e){if(!(r=arguments[e]+``)||r in n||/[\s.]/.test(r))throw Error(`illegal type: `+r);n[r]=[]}return new cr(n)}function cr(e){this._=e}function lr(e,t){return e.trim().split(/^|\s+/).map(function(e){var n=``,r=e.indexOf(`.`);if(r>=0&&(n=e.slice(r+1),e=e.slice(0,r)),e&&!t.hasOwnProperty(e))throw Error(`unknown type: `+e);return{type:e,name:n}})}cr.prototype=sr.prototype={constructor:cr,on:function(e,t){var n=this._,r=lr(e+``,n),i,a=-1,o=r.length;if(arguments.length<2){for(;++a<o;)if((i=(e=r[a]).type)&&(i=ur(n[i],e.name)))return i;return}if(t!=null&&typeof t!=`function`)throw Error(`invalid callback: `+t);for(;++a<o;)if(i=(e=r[a]).type)n[i]=dr(n[i],e.name,t);else if(t==null)for(i in n)n[i]=dr(n[i],e.name,null);return this},copy:function(){var e={},t=this._;for(var n in t)e[n]=t[n].slice();return new cr(e)},call:function(e,t){if((i=arguments.length-2)>0)for(var n=Array(i),r=0,i,a;r<i;++r)n[r]=arguments[r+2];if(!this._.hasOwnProperty(e))throw Error(`unknown type: `+e);for(a=this._[e],r=0,i=a.length;r<i;++r)a[r].value.apply(t,n)},apply:function(e,t,n){if(!this._.hasOwnProperty(e))throw Error(`unknown type: `+e);for(var r=this._[e],i=0,a=r.length;i<a;++i)r[i].value.apply(t,n)}};function ur(e,t){for(var n=0,r=e.length,i;n<r;++n)if((i=e[n]).name===t)return i.value}function dr(e,t,n){for(var r=0,i=e.length;r<i;++r)if(e[r].name===t){e[r]=or,e=e.slice(0,r).concat(e.slice(r+1));break}return n!=null&&e.push({name:t,value:n}),e}var N=0,fr=0,pr=0,mr=1e3,hr,gr,_r=0,P=0,vr=0,yr=typeof performance==`object`&&performance.now?performance:Date,br=typeof window==`object`&&window.requestAnimationFrame?window.requestAnimationFrame.bind(window):function(e){setTimeout(e,17)};function xr(){return P||=(br(Sr),yr.now()+vr)}function Sr(){P=0}function Cr(){this._call=this._time=this._next=null}Cr.prototype=wr.prototype={constructor:Cr,restart:function(e,t,n){if(typeof e!=`function`)throw TypeError(`callback is not a function`);n=(n==null?xr():+n)+(t==null?0:+t),!this._next&&gr!==this&&(gr?gr._next=this:hr=this,gr=this),this._call=e,this._time=n,kr()},stop:function(){this._call&&(this._call=null,this._time=1/0,kr())}};function wr(e,t,n){var r=new Cr;return r.restart(e,t,n),r}function Tr(){xr(),++N;for(var e=hr,t;e;)(t=P-e._time)>=0&&e._call.call(void 0,t),e=e._next;--N}function Er(){P=(_r=yr.now())+vr,N=fr=0;try{Tr()}finally{N=0,Or(),P=0}}function Dr(){var e=yr.now(),t=e-_r;t>mr&&(vr-=t,_r=e)}function Or(){for(var e,t=hr,n,r=1/0;t;)t._call?(r>t._time&&(r=t._time),e=t,t=t._next):(n=t._next,t._next=null,t=e?e._next=n:hr=n);gr=e,kr(r)}function kr(e){N||(fr&&=clearTimeout(fr),e-P>24?(e<1/0&&(fr=setTimeout(Er,e-yr.now()-vr)),pr&&=clearInterval(pr)):(pr||=(_r=yr.now(),setInterval(Dr,mr)),N=1,br(Er)))}function Ar(e,t,n){var r=new Cr;return t=t==null?0:+t,r.restart(n=>{r.stop(),e(n+t)},t,n),r}var jr=sr(`start`,`end`,`cancel`,`interrupt`),Mr=[];function Nr(e,t,n,r,i,a){var o=e.__transition;if(!o)e.__transition={};else if(n in o)return;Fr(e,n,{name:t,index:r,group:i,on:jr,tween:Mr,time:a.time,delay:a.delay,duration:a.duration,ease:a.ease,timer:null,state:0})}function Pr(e,t){var n=I(e,t);if(n.state>0)throw Error(`too late; already scheduled`);return n}function F(e,t){var n=I(e,t);if(n.state>3)throw Error(`too late; already running`);return n}function I(e,t){var n=e.__transition;if(!n||!(n=n[t]))throw Error(`transition not found`);return n}function Fr(e,t,n){var r=e.__transition,i;r[t]=n,n.timer=wr(a,0,n.time);function a(e){n.state=1,n.timer.restart(o,n.delay,n.time),n.delay<=e&&o(e-n.delay)}function o(a){var l,u,d,f;if(n.state!==1)return c();for(l in r)if(f=r[l],f.name===n.name){if(f.state===3)return Ar(o);f.state===4?(f.state=6,f.timer.stop(),f.on.call(`interrupt`,e,e.__data__,f.index,f.group),delete r[l]):+l<t&&(f.state=6,f.timer.stop(),f.on.call(`cancel`,e,e.__data__,f.index,f.group),delete r[l])}if(Ar(function(){n.state===3&&(n.state=4,n.timer.restart(s,n.delay,n.time),s(a))}),n.state=2,n.on.call(`start`,e,e.__data__,n.index,n.group),n.state===2){for(n.state=3,i=Array(d=n.tween.length),l=0,u=-1;l<d;++l)(f=n.tween[l].value.call(e,e.__data__,n.index,n.group))&&(i[++u]=f);i.length=u+1}}function s(t){for(var r=t<n.duration?n.ease.call(null,t/n.duration):(n.timer.restart(c),n.state=5,1),a=-1,o=i.length;++a<o;)i[a].call(e,r);n.state===5&&(n.on.call(`end`,e,e.__data__,n.index,n.group),c())}function c(){for(var i in n.state=6,n.timer.stop(),delete r[t],r)return;delete e.__transition}}function Ir(e,t){var n=e.__transition,r,i,a=!0,o;if(n){for(o in t=t==null?null:t+``,n){if((r=n[o]).name!==t){a=!1;continue}i=r.state>2&&r.state<5,r.state=6,r.timer.stop(),r.on.call(i?`interrupt`:`cancel`,e,e.__data__,r.index,r.group),delete n[o]}a&&delete e.__transition}}function Lr(e){return this.each(function(){Ir(this,e)})}function Rr(e,t,n){e.prototype=t.prototype=n,n.constructor=e}function zr(e,t){var n=Object.create(e.prototype);for(var r in t)n[r]=t[r];return n}function L(){}var R=.7,Br=1/R,z=`\\s*([+-]?\\d+)\\s*`,B=`\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)\\s*`,V=`\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)%\\s*`,Vr=/^#([0-9a-f]{3,8})$/,Hr=RegExp(`^rgb\\(${z},${z},${z}\\)$`),Ur=RegExp(`^rgb\\(${V},${V},${V}\\)$`),Wr=RegExp(`^rgba\\(${z},${z},${z},${B}\\)$`),Gr=RegExp(`^rgba\\(${V},${V},${V},${B}\\)$`),Kr=RegExp(`^hsl\\(${B},${V},${V}\\)$`),qr=RegExp(`^hsla\\(${B},${V},${V},${B}\\)$`),Jr={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074};Rr(L,H,{copy(e){return Object.assign(new this.constructor,this,e)},displayable(){return this.rgb().displayable()},hex:Yr,formatHex:Yr,formatHex8:Xr,formatHsl:Zr,formatRgb:Qr,toString:Qr});function Yr(){return this.rgb().formatHex()}function Xr(){return this.rgb().formatHex8()}function Zr(){return ci(this).formatHsl()}function Qr(){return this.rgb().formatRgb()}function H(e){var t,n;return e=(e+``).trim().toLowerCase(),(t=Vr.exec(e))?(n=t[1].length,t=parseInt(t[1],16),n===6?$r(t):n===3?new U(t>>8&15|t>>4&240,t>>4&15|t&240,(t&15)<<4|t&15,1):n===8?ei(t>>24&255,t>>16&255,t>>8&255,(t&255)/255):n===4?ei(t>>12&15|t>>8&240,t>>8&15|t>>4&240,t>>4&15|t&240,((t&15)<<4|t&15)/255):null):(t=Hr.exec(e))?new U(t[1],t[2],t[3],1):(t=Ur.exec(e))?new U(t[1]*255/100,t[2]*255/100,t[3]*255/100,1):(t=Wr.exec(e))?ei(t[1],t[2],t[3],t[4]):(t=Gr.exec(e))?ei(t[1]*255/100,t[2]*255/100,t[3]*255/100,t[4]):(t=Kr.exec(e))?si(t[1],t[2]/100,t[3]/100,1):(t=qr.exec(e))?si(t[1],t[2]/100,t[3]/100,t[4]):Jr.hasOwnProperty(e)?$r(Jr[e]):e===`transparent`?new U(NaN,NaN,NaN,0):null}function $r(e){return new U(e>>16&255,e>>8&255,e&255,1)}function ei(e,t,n,r){return r<=0&&(e=t=n=NaN),new U(e,t,n,r)}function ti(e){return e instanceof L||(e=H(e)),e?(e=e.rgb(),new U(e.r,e.g,e.b,e.opacity)):new U}function ni(e,t,n,r){return arguments.length===1?ti(e):new U(e,t,n,r??1)}function U(e,t,n,r){this.r=+e,this.g=+t,this.b=+n,this.opacity=+r}Rr(U,ni,zr(L,{brighter(e){return e=e==null?Br:Br**+e,new U(this.r*e,this.g*e,this.b*e,this.opacity)},darker(e){return e=e==null?R:R**+e,new U(this.r*e,this.g*e,this.b*e,this.opacity)},rgb(){return this},clamp(){return new U(W(this.r),W(this.g),W(this.b),oi(this.opacity))},displayable(){return-.5<=this.r&&this.r<255.5&&-.5<=this.g&&this.g<255.5&&-.5<=this.b&&this.b<255.5&&0<=this.opacity&&this.opacity<=1},hex:ri,formatHex:ri,formatHex8:ii,formatRgb:ai,toString:ai}));function ri(){return`#${G(this.r)}${G(this.g)}${G(this.b)}`}function ii(){return`#${G(this.r)}${G(this.g)}${G(this.b)}${G((isNaN(this.opacity)?1:this.opacity)*255)}`}function ai(){let e=oi(this.opacity);return`${e===1?`rgb(`:`rgba(`}${W(this.r)}, ${W(this.g)}, ${W(this.b)}${e===1?`)`:`, ${e})`}`}function oi(e){return isNaN(e)?1:Math.max(0,Math.min(1,e))}function W(e){return Math.max(0,Math.min(255,Math.round(e)||0))}function G(e){return e=W(e),(e<16?`0`:``)+e.toString(16)}function si(e,t,n,r){return r<=0?e=t=n=NaN:n<=0||n>=1?e=t=NaN:t<=0&&(e=NaN),new K(e,t,n,r)}function ci(e){if(e instanceof K)return new K(e.h,e.s,e.l,e.opacity);if(e instanceof L||(e=H(e)),!e)return new K;if(e instanceof K)return e;e=e.rgb();var t=e.r/255,n=e.g/255,r=e.b/255,i=Math.min(t,n,r),a=Math.max(t,n,r),o=NaN,s=a-i,c=(a+i)/2;return s?(o=t===a?(n-r)/s+(n<r)*6:n===a?(r-t)/s+2:(t-n)/s+4,s/=c<.5?a+i:2-a-i,o*=60):s=c>0&&c<1?0:o,new K(o,s,c,e.opacity)}function li(e,t,n,r){return arguments.length===1?ci(e):new K(e,t,n,r??1)}function K(e,t,n,r){this.h=+e,this.s=+t,this.l=+n,this.opacity=+r}Rr(K,li,zr(L,{brighter(e){return e=e==null?Br:Br**+e,new K(this.h,this.s,this.l*e,this.opacity)},darker(e){return e=e==null?R:R**+e,new K(this.h,this.s,this.l*e,this.opacity)},rgb(){var e=this.h%360+(this.h<0)*360,t=isNaN(e)||isNaN(this.s)?0:this.s,n=this.l,r=n+(n<.5?n:1-n)*t,i=2*n-r;return new U(fi(e>=240?e-240:e+120,i,r),fi(e,i,r),fi(e<120?e+240:e-120,i,r),this.opacity)},clamp(){return new K(ui(this.h),di(this.s),di(this.l),oi(this.opacity))},displayable(){return(0<=this.s&&this.s<=1||isNaN(this.s))&&0<=this.l&&this.l<=1&&0<=this.opacity&&this.opacity<=1},formatHsl(){let e=oi(this.opacity);return`${e===1?`hsl(`:`hsla(`}${ui(this.h)}, ${di(this.s)*100}%, ${di(this.l)*100}%${e===1?`)`:`, ${e})`}`}}));function ui(e){return e=(e||0)%360,e<0?e+360:e}function di(e){return Math.max(0,Math.min(1,e||0))}function fi(e,t,n){return(e<60?t+(n-t)*e/60:e<180?n:e<240?t+(n-t)*(240-e)/60:t)*255}var pi=e=>()=>e;function mi(e,t){return function(n){return e+n*t}}function hi(e,t,n){return e**=+n,t=t**+n-e,n=1/n,function(r){return(e+r*t)**+n}}function gi(e){return(e=+e)==1?_i:function(t,n){return n-t?hi(t,n,e):pi(isNaN(t)?n:t)}}function _i(e,t){var n=t-e;return n?mi(e,n):pi(isNaN(e)?t:e)}var vi=(function e(t){var n=gi(t);function r(e,t){var r=n((e=ni(e)).r,(t=ni(t)).r),i=n(e.g,t.g),a=n(e.b,t.b),o=_i(e.opacity,t.opacity);return function(t){return e.r=r(t),e.g=i(t),e.b=a(t),e.opacity=o(t),e+``}}return r.gamma=e,r})(1);function q(e,t){return e=+e,t=+t,function(n){return e*(1-n)+t*n}}var yi=/[-+]?(?:\d+\.?\d*|\.?\d+)(?:[eE][-+]?\d+)?/g,bi=new RegExp(yi.source,`g`);function xi(e){return function(){return e}}function Si(e){return function(t){return e(t)+``}}function Ci(e,t){var n=yi.lastIndex=bi.lastIndex=0,r,i,a,o=-1,s=[],c=[];for(e+=``,t+=``;(r=yi.exec(e))&&(i=bi.exec(t));)(a=i.index)>n&&(a=t.slice(n,a),s[o]?s[o]+=a:s[++o]=a),(r=r[0])===(i=i[0])?s[o]?s[o]+=i:s[++o]=i:(s[++o]=null,c.push({i:o,x:q(r,i)})),n=bi.lastIndex;return n<t.length&&(a=t.slice(n),s[o]?s[o]+=a:s[++o]=a),s.length<2?c[0]?Si(c[0].x):xi(t):(t=c.length,function(e){for(var n=0,r;n<t;++n)s[(r=c[n]).i]=r.x(e);return s.join(``)})}var wi=180/Math.PI,Ti={translateX:0,translateY:0,rotate:0,skewX:0,scaleX:1,scaleY:1};function Ei(e,t,n,r,i,a){var o,s,c;return(o=Math.sqrt(e*e+t*t))&&(e/=o,t/=o),(c=e*n+t*r)&&(n-=e*c,r-=t*c),(s=Math.sqrt(n*n+r*r))&&(n/=s,r/=s,c/=s),e*r<t*n&&(e=-e,t=-t,c=-c,o=-o),{translateX:i,translateY:a,rotate:Math.atan2(t,e)*wi,skewX:Math.atan(c)*wi,scaleX:o,scaleY:s}}var Di;function Oi(e){let t=new(typeof DOMMatrix==`function`?DOMMatrix:WebKitCSSMatrix)(e+``);return t.isIdentity?Ti:Ei(t.a,t.b,t.c,t.d,t.e,t.f)}function ki(e){return e==null||(Di||=document.createElementNS(`http://www.w3.org/2000/svg`,`g`),Di.setAttribute(`transform`,e),!(e=Di.transform.baseVal.consolidate()))?Ti:(e=e.matrix,Ei(e.a,e.b,e.c,e.d,e.e,e.f))}function Ai(e,t,n,r){function i(e){return e.length?e.pop()+` `:``}function a(e,r,i,a,o,s){if(e!==i||r!==a){var c=o.push(`translate(`,null,t,null,n);s.push({i:c-4,x:q(e,i)},{i:c-2,x:q(r,a)})}else(i||a)&&o.push(`translate(`+i+t+a+n)}function o(e,t,n,a){e===t?t&&n.push(i(n)+`rotate(`+t+r):(e-t>180?t+=360:t-e>180&&(e+=360),a.push({i:n.push(i(n)+`rotate(`,null,r)-2,x:q(e,t)}))}function s(e,t,n,a){e===t?t&&n.push(i(n)+`skewX(`+t+r):a.push({i:n.push(i(n)+`skewX(`,null,r)-2,x:q(e,t)})}function c(e,t,n,r,a,o){if(e!==n||t!==r){var s=a.push(i(a)+`scale(`,null,`,`,null,`)`);o.push({i:s-4,x:q(e,n)},{i:s-2,x:q(t,r)})}else(n!==1||r!==1)&&a.push(i(a)+`scale(`+n+`,`+r+`)`)}return function(t,n){var r=[],i=[];return t=e(t),n=e(n),a(t.translateX,t.translateY,n.translateX,n.translateY,r,i),o(t.rotate,n.rotate,r,i),s(t.skewX,n.skewX,r,i),c(t.scaleX,t.scaleY,n.scaleX,n.scaleY,r,i),t=n=null,function(e){for(var t=-1,n=i.length,a;++t<n;)r[(a=i[t]).i]=a.x(e);return r.join(``)}}}var ji=Ai(Oi,`px, `,`px)`,`deg)`),Mi=Ai(ki,`, `,`)`,`)`),Ni=1e-12;function Pi(e){return((e=Math.exp(e))+1/e)/2}function Fi(e){return((e=Math.exp(e))-1/e)/2}function Ii(e){return((e=Math.exp(2*e))-1)/(e+1)}var Li=(function e(t,n,r){function i(e,i){var a=e[0],o=e[1],s=e[2],c=i[0],l=i[1],u=i[2],d=c-a,f=l-o,p=d*d+f*f,m,h;if(p<Ni)h=Math.log(u/s)/t,m=function(e){return[a+e*d,o+e*f,s*Math.exp(t*e*h)]};else{var g=Math.sqrt(p),_=(u*u-s*s+r*p)/(2*s*n*g),v=(u*u-s*s-r*p)/(2*u*n*g),y=Math.log(Math.sqrt(_*_+1)-_);h=(Math.log(Math.sqrt(v*v+1)-v)-y)/t,m=function(e){var r=e*h,i=Pi(y),c=s/(n*g)*(i*Ii(t*r+y)-Fi(y));return[a+c*d,o+c*f,s*i/Pi(t*r+y)]}}return m.duration=h*1e3*t/Math.SQRT2,m}return i.rho=function(t){var n=Math.max(.001,+t),r=n*n;return e(n,r,r*r)},i})(Math.SQRT2,2,4);function Ri(e,t){var n,r;return function(){var i=F(this,e),a=i.tween;if(a!==n){r=n=a;for(var o=0,s=r.length;o<s;++o)if(r[o].name===t){r=r.slice(),r.splice(o,1);break}}i.tween=r}}function zi(e,t,n){var r,i;if(typeof n!=`function`)throw Error();return function(){var a=F(this,e),o=a.tween;if(o!==r){i=(r=o).slice();for(var s={name:t,value:n},c=0,l=i.length;c<l;++c)if(i[c].name===t){i[c]=s;break}c===l&&i.push(s)}a.tween=i}}function Bi(e,t){var n=this._id;if(e+=``,arguments.length<2){for(var r=I(this.node(),n).tween,i=0,a=r.length,o;i<a;++i)if((o=r[i]).name===e)return o.value;return null}return this.each((t==null?Ri:zi)(n,e,t))}function Vi(e,t,n){var r=e._id;return e.each(function(){var e=F(this,r);(e.value||={})[t]=n.apply(this,arguments)}),function(e){return I(e,r).value[t]}}function Hi(e,t){var n;return(typeof t==`number`?q:t instanceof H?vi:(n=H(t))?(t=n,vi):Ci)(e,t)}function Ui(e){return function(){this.removeAttribute(e)}}function Wi(e){return function(){this.removeAttributeNS(e.space,e.local)}}function Gi(e,t,n){var r,i=n+``,a;return function(){var o=this.getAttribute(e);return o===i?null:o===r?a:a=t(r=o,n)}}function Ki(e,t,n){var r,i=n+``,a;return function(){var o=this.getAttributeNS(e.space,e.local);return o===i?null:o===r?a:a=t(r=o,n)}}function qi(e,t,n){var r,i,a;return function(){var o,s=n(this),c;return s==null?void this.removeAttribute(e):(o=this.getAttribute(e),c=s+``,o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s)))}}function Ji(e,t,n){var r,i,a;return function(){var o,s=n(this),c;return s==null?void this.removeAttributeNS(e.space,e.local):(o=this.getAttributeNS(e.space,e.local),c=s+``,o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s)))}}function Yi(e,t){var n=ut(e),r=n===`transform`?Mi:Hi;return this.attrTween(e,typeof t==`function`?(n.local?Ji:qi)(n,r,Vi(this,`attr.`+e,t)):t==null?(n.local?Wi:Ui)(n):(n.local?Ki:Gi)(n,r,t))}function Xi(e,t){return function(n){this.setAttribute(e,t.call(this,n))}}function Zi(e,t){return function(n){this.setAttributeNS(e.space,e.local,t.call(this,n))}}function Qi(e,t){var n,r;function i(){var i=t.apply(this,arguments);return i!==r&&(n=(r=i)&&Zi(e,i)),n}return i._value=t,i}function $i(e,t){var n,r;function i(){var i=t.apply(this,arguments);return i!==r&&(n=(r=i)&&Xi(e,i)),n}return i._value=t,i}function ea(e,t){var n=`attr.`+e;if(arguments.length<2)return(n=this.tween(n))&&n._value;if(t==null)return this.tween(n,null);if(typeof t!=`function`)throw Error();var r=ut(e);return this.tween(n,(r.local?Qi:$i)(r,t))}function ta(e,t){return function(){Pr(this,e).delay=+t.apply(this,arguments)}}function na(e,t){return t=+t,function(){Pr(this,e).delay=t}}function ra(e){var t=this._id;return arguments.length?this.each((typeof e==`function`?ta:na)(t,e)):I(this.node(),t).delay}function ia(e,t){return function(){F(this,e).duration=+t.apply(this,arguments)}}function aa(e,t){return t=+t,function(){F(this,e).duration=t}}function oa(e){var t=this._id;return arguments.length?this.each((typeof e==`function`?ia:aa)(t,e)):I(this.node(),t).duration}function sa(e,t){if(typeof t!=`function`)throw Error();return function(){F(this,e).ease=t}}function ca(e){var t=this._id;return arguments.length?this.each(sa(t,e)):I(this.node(),t).ease}function la(e,t){return function(){var n=t.apply(this,arguments);if(typeof n!=`function`)throw Error();F(this,e).ease=n}}function ua(e){if(typeof e!=`function`)throw Error();return this.each(la(this._id,e))}function da(e){typeof e!=`function`&&(e=St(e));for(var t=this._groups,n=t.length,r=Array(n),i=0;i<n;++i)for(var a=t[i],o=a.length,s=r[i]=[],c,l=0;l<o;++l)(c=a[l])&&e.call(c,c.__data__,l,a)&&s.push(c);return new J(r,this._parents,this._name,this._id)}function fa(e){if(e._id!==this._id)throw Error();for(var t=this._groups,n=e._groups,r=t.length,i=n.length,a=Math.min(r,i),o=Array(r),s=0;s<a;++s)for(var c=t[s],l=n[s],u=c.length,d=o[s]=Array(u),f,p=0;p<u;++p)(f=c[p]||l[p])&&(d[p]=f);for(;s<r;++s)o[s]=t[s];return new J(o,this._parents,this._name,this._id)}function pa(e){return(e+``).trim().split(/^|\s+/).every(function(e){var t=e.indexOf(`.`);return t>=0&&(e=e.slice(0,t)),!e||e===`start`})}function ma(e,t,n){var r,i,a=pa(t)?Pr:F;return function(){var o=a(this,e),s=o.on;s!==r&&(i=(r=s).copy()).on(t,n),o.on=i}}function ha(e,t){var n=this._id;return arguments.length<2?I(this.node(),n).on.on(e):this.each(ma(n,e,t))}function ga(e){return function(){var t=this.parentNode;for(var n in this.__transition)if(+n!==e)return;t&&t.removeChild(this)}}function _a(){return this.on(`end.remove`,ga(this._id))}function va(e){var t=this._name,n=this._id;typeof e!=`function`&&(e=ht(e));for(var r=this._groups,i=r.length,a=Array(i),o=0;o<i;++o)for(var s=r[o],c=s.length,l=a[o]=Array(c),u,d,f=0;f<c;++f)(u=s[f])&&(d=e.call(u,u.__data__,f,s))&&(`__data__`in u&&(d.__data__=u.__data__),l[f]=d,Nr(l[f],t,n,f,l,I(u,n)));return new J(a,this._parents,t,n)}function ya(e){var t=this._name,n=this._id;typeof e!=`function`&&(e=yt(e));for(var r=this._groups,i=r.length,a=[],o=[],s=0;s<i;++s)for(var c=r[s],l=c.length,u,d=0;d<l;++d)if(u=c[d]){for(var f=e.call(u,u.__data__,d,c),p,m=I(u,n),h=0,g=f.length;h<g;++h)(p=f[h])&&Nr(p,t,n,h,f,m);a.push(f),o.push(u)}return new J(a,o,t,n)}var ba=A.prototype.constructor;function xa(){return new ba(this._groups,this._parents)}function Sa(e,t){var n,r,i;return function(){var a=O(this,e),o=(this.style.removeProperty(e),O(this,e));return a===o?null:a===n&&o===r?i:i=t(n=a,r=o)}}function Ca(e){return function(){this.style.removeProperty(e)}}function wa(e,t,n){var r,i=n+``,a;return function(){var o=O(this,e);return o===i?null:o===r?a:a=t(r=o,n)}}function Ta(e,t,n){var r,i,a;return function(){var o=O(this,e),s=n(this),c=s+``;return s??(c=s=(this.style.removeProperty(e),O(this,e))),o===c?null:o===r&&c===i?a:(i=c,a=t(r=o,s))}}function Ea(e,t){var n,r,i,a=`style.`+t,o=`end.`+a,s;return function(){var c=F(this,e),l=c.on,u=c.value[a]==null?s||=Ca(t):void 0;(l!==n||i!==u)&&(r=(n=l).copy()).on(o,i=u),c.on=r}}function Da(e,t,n){var r=(e+=``)==`transform`?ji:Hi;return t==null?this.styleTween(e,Sa(e,r)).on(`end.style.`+e,Ca(e)):typeof t==`function`?this.styleTween(e,Ta(e,r,Vi(this,`style.`+e,t))).each(Ea(this._id,e)):this.styleTween(e,wa(e,r,t),n).on(`end.style.`+e,null)}function Oa(e,t,n){return function(r){this.style.setProperty(e,t.call(this,r),n)}}function ka(e,t,n){var r,i;function a(){var a=t.apply(this,arguments);return a!==i&&(r=(i=a)&&Oa(e,a,n)),r}return a._value=t,a}function Aa(e,t,n){var r=`style.`+(e+=``);if(arguments.length<2)return(r=this.tween(r))&&r._value;if(t==null)return this.tween(r,null);if(typeof t!=`function`)throw Error();return this.tween(r,ka(e,t,n??``))}function ja(e){return function(){this.textContent=e}}function Ma(e){return function(){var t=e(this);this.textContent=t??``}}function Na(e){return this.tween(`text`,typeof e==`function`?Ma(Vi(this,`text`,e)):ja(e==null?``:e+``))}function Pa(e){return function(t){this.textContent=e.call(this,t)}}function Fa(e){var t,n;function r(){var r=e.apply(this,arguments);return r!==n&&(t=(n=r)&&Pa(r)),t}return r._value=e,r}function Ia(e){var t=`text`;if(arguments.length<1)return(t=this.tween(t))&&t._value;if(e==null)return this.tween(t,null);if(typeof e!=`function`)throw Error();return this.tween(t,Fa(e))}function La(){for(var e=this._name,t=this._id,n=Ba(),r=this._groups,i=r.length,a=0;a<i;++a)for(var o=r[a],s=o.length,c,l=0;l<s;++l)if(c=o[l]){var u=I(c,t);Nr(c,e,n,l,o,{time:u.time+u.delay+u.duration,delay:0,duration:u.duration,ease:u.ease})}return new J(r,this._parents,e,n)}function Ra(){var e,t,n=this,r=n._id,i=n.size();return new Promise(function(a,o){var s={value:o},c={value:function(){--i===0&&a()}};n.each(function(){var n=F(this,r),i=n.on;i!==e&&(t=(e=i).copy(),t._.cancel.push(s),t._.interrupt.push(s),t._.end.push(c)),n.on=t}),i===0&&a()})}var za=0;function J(e,t,n,r){this._groups=e,this._parents=t,this._name=n,this._id=r}function Ba(){return++za}var Y=A.prototype;J.prototype={constructor:J,select:va,selectAll:ya,selectChild:Y.selectChild,selectChildren:Y.selectChildren,filter:da,merge:fa,selection:xa,transition:La,call:Y.call,nodes:Y.nodes,node:Y.node,size:Y.size,empty:Y.empty,each:Y.each,on:ha,attr:Yi,attrTween:ea,style:Da,styleTween:Aa,text:Na,textTween:Ia,remove:_a,tween:Bi,delay:ra,duration:oa,ease:ca,easeVarying:ua,end:Ra,[Symbol.iterator]:Y[Symbol.iterator]};function Va(e){return((e*=2)<=1?e*e*e:(e-=2)*e*e+2)/2}var Ha={time:null,delay:0,duration:250,ease:Va};function Ua(e,t){for(var n;!(n=e.__transition)||!(n=n[t]);)if(!(e=e.parentNode))throw Error(`transition ${t} not found`);return n}function Wa(e){var t,n;e instanceof J?(t=e._id,e=e._name):(t=Ba(),(n=Ha).time=xr(),e=e==null?null:e+``);for(var r=this._groups,i=r.length,a=0;a<i;++a)for(var o=r[a],s=o.length,c,l=0;l<s;++l)(c=o[l])&&Nr(c,e,t,l,o,n||Ua(c,t));return new J(r,this._parents,e,t)}A.prototype.interrupt=Lr,A.prototype.transition=Wa;var Ga={capture:!0,passive:!1};function Ka(e){e.preventDefault(),e.stopImmediatePropagation()}function qa(e){var t=e.document.documentElement,n=j(e).on(`dragstart.drag`,Ka,Ga);`onselectstart`in t?n.on(`selectstart.drag`,Ka,Ga):(t.__noselect=t.style.MozUserSelect,t.style.MozUserSelect=`none`)}function Ja(e,t){var n=e.document.documentElement,r=j(e).on(`dragstart.drag`,null);t&&(r.on(`click.drag`,Ka,Ga),setTimeout(function(){r.on(`click.drag`,null)},0)),`onselectstart`in n?r.on(`selectstart.drag`,null):(n.style.MozUserSelect=n.__noselect,delete n.__noselect)}var Ya=e=>()=>e;function Xa(e,{sourceEvent:t,target:n,transform:r,dispatch:i}){Object.defineProperties(this,{type:{value:e,enumerable:!0,configurable:!0},sourceEvent:{value:t,enumerable:!0,configurable:!0},target:{value:n,enumerable:!0,configurable:!0},transform:{value:r,enumerable:!0,configurable:!0},_:{value:i}})}function X(e,t,n){this.k=e,this.x=t,this.y=n}X.prototype={constructor:X,scale:function(e){return e===1?this:new X(this.k*e,this.x,this.y)},translate:function(e,t){return e===0&t===0?this:new X(this.k,this.x+this.k*e,this.y+this.k*t)},apply:function(e){return[e[0]*this.k+this.x,e[1]*this.k+this.y]},applyX:function(e){return e*this.k+this.x},applyY:function(e){return e*this.k+this.y},invert:function(e){return[(e[0]-this.x)/this.k,(e[1]-this.y)/this.k]},invertX:function(e){return(e-this.x)/this.k},invertY:function(e){return(e-this.y)/this.k},rescaleX:function(e){return e.copy().domain(e.range().map(this.invertX,this).map(e.invert,e))},rescaleY:function(e){return e.copy().domain(e.range().map(this.invertY,this).map(e.invert,e))},toString:function(){return`translate(`+this.x+`,`+this.y+`) scale(`+this.k+`)`}};var Za=new X(1,0,0);Qa.prototype=X.prototype;function Qa(e){for(;!e.__zoom;)if(!(e=e.parentNode))return Za;return e.__zoom}function $a(e){e.stopImmediatePropagation()}function eo(e){e.preventDefault(),e.stopImmediatePropagation()}function to(e){return(!e.ctrlKey||e.type===`wheel`)&&!e.button}function no(){var e=this;return e instanceof SVGElement?(e=e.ownerSVGElement||e,e.hasAttribute(`viewBox`)?(e=e.viewBox.baseVal,[[e.x,e.y],[e.x+e.width,e.y+e.height]]):[[0,0],[e.width.baseVal.value,e.height.baseVal.value]]):[[0,0],[e.clientWidth,e.clientHeight]]}function ro(){return this.__zoom||Za}function io(e){return-e.deltaY*(e.deltaMode===1?.05:e.deltaMode?1:.002)*(e.ctrlKey?10:1)}function ao(){return navigator.maxTouchPoints||`ontouchstart`in this}function oo(e,t,n){var r=e.invertX(t[0][0])-n[0][0],i=e.invertX(t[1][0])-n[1][0],a=e.invertY(t[0][1])-n[0][1],o=e.invertY(t[1][1])-n[1][1];return e.translate(i>r?(r+i)/2:Math.min(0,r)||Math.max(0,i),o>a?(a+o)/2:Math.min(0,a)||Math.max(0,o))}function so(){var e=to,t=no,n=oo,r=io,i=ao,a=[0,1/0],o=[[-1/0,-1/0],[1/0,1/0]],s=250,c=Li,l=sr(`start`,`zoom`,`end`),u,d,f,p=500,m=150,h=0,g=10;function _(e){e.property(`__zoom`,ro).on(`wheel.zoom`,ne,{passive:!1}).on(`mousedown.zoom`,re).on(`dblclick.zoom`,ie).filter(i).on(`touchstart.zoom`,ae).on(`touchmove.zoom`,oe).on(`touchend.zoom touchcancel.zoom`,se).style(`-webkit-tap-highlight-color`,`rgba(0,0,0,0)`)}_.transform=function(e,t,n,r){var i=e.selection?e.selection():e;i.property(`__zoom`,ro),e===i?i.interrupt().each(function(){x(this,arguments).event(r).start().zoom(null,typeof t==`function`?t.apply(this,arguments):t).end()}):ee(e,t,n,r)},_.scaleBy=function(e,t,n,r){_.scaleTo(e,function(){return this.__zoom.k*(typeof t==`function`?t.apply(this,arguments):t)},n,r)},_.scaleTo=function(e,r,i,a){_.transform(e,function(){var e=t.apply(this,arguments),a=this.__zoom,s=i==null?b(e):typeof i==`function`?i.apply(this,arguments):i,c=a.invert(s),l=typeof r==`function`?r.apply(this,arguments):r;return n(y(v(a,l),s,c),e,o)},i,a)},_.translateBy=function(e,r,i,a){_.transform(e,function(){return n(this.__zoom.translate(typeof r==`function`?r.apply(this,arguments):r,typeof i==`function`?i.apply(this,arguments):i),t.apply(this,arguments),o)},null,a)},_.translateTo=function(e,r,i,a,s){_.transform(e,function(){var e=t.apply(this,arguments),s=this.__zoom,c=a==null?b(e):typeof a==`function`?a.apply(this,arguments):a;return n(Za.translate(c[0],c[1]).scale(s.k).translate(typeof r==`function`?-r.apply(this,arguments):-r,typeof i==`function`?-i.apply(this,arguments):-i),e,o)},a,s)};function v(e,t){return t=Math.max(a[0],Math.min(a[1],t)),t===e.k?e:new X(t,e.x,e.y)}function y(e,t,n){var r=t[0]-n[0]*e.k,i=t[1]-n[1]*e.k;return r===e.x&&i===e.y?e:new X(e.k,r,i)}function b(e){return[(+e[0][0]+ +e[1][0])/2,(+e[0][1]+ +e[1][1])/2]}function ee(e,n,r,i){e.on(`start.zoom`,function(){x(this,arguments).event(i).start()}).on(`interrupt.zoom end.zoom`,function(){x(this,arguments).event(i).end()}).tween(`zoom`,function(){var e=this,a=arguments,o=x(e,a).event(i),s=t.apply(e,a),l=r==null?b(s):typeof r==`function`?r.apply(e,a):r,u=Math.max(s[1][0]-s[0][0],s[1][1]-s[0][1]),d=e.__zoom,f=typeof n==`function`?n.apply(e,a):n,p=c(d.invert(l).concat(u/d.k),f.invert(l).concat(u/f.k));return function(e){if(e===1)e=f;else{var t=p(e),n=u/t[2];e=new X(n,l[0]-t[0]*n,l[1]-t[1]*n)}o.zoom(null,e)}})}function x(e,t,n){return!n&&e.__zooming||new te(e,t)}function te(e,n){this.that=e,this.args=n,this.active=0,this.sourceEvent=null,this.extent=t.apply(e,n),this.taps=0}te.prototype={event:function(e){return e&&(this.sourceEvent=e),this},start:function(){return++this.active===1&&(this.that.__zooming=this,this.emit(`start`)),this},zoom:function(e,t){return this.mouse&&e!==`mouse`&&(this.mouse[1]=t.invert(this.mouse[0])),this.touch0&&e!==`touch`&&(this.touch0[1]=t.invert(this.touch0[0])),this.touch1&&e!==`touch`&&(this.touch1[1]=t.invert(this.touch1[0])),this.that.__zoom=t,this.emit(`zoom`),this},end:function(){return--this.active===0&&(delete this.that.__zooming,this.emit(`end`)),this},emit:function(e){var t=j(this.that).datum();l.call(e,this.that,new Xa(e,{sourceEvent:this.sourceEvent,target:_,type:e,transform:this.that.__zoom,dispatch:l}),t)}};function ne(t,...i){if(!e.apply(this,arguments))return;var s=x(this,i).event(t),c=this.__zoom,l=Math.max(a[0],Math.min(a[1],c.k*2**r.apply(this,arguments))),u=M(t);if(s.wheel)(s.mouse[0][0]!==u[0]||s.mouse[0][1]!==u[1])&&(s.mouse[1]=c.invert(s.mouse[0]=u)),clearTimeout(s.wheel);else if(c.k===l)return;else s.mouse=[u,c.invert(u)],Ir(this),s.start();eo(t),s.wheel=setTimeout(d,m),s.zoom(`mouse`,n(y(v(c,l),s.mouse[0],s.mouse[1]),s.extent,o));function d(){s.wheel=null,s.end()}}function re(t,...r){if(f||!e.apply(this,arguments))return;var i=t.currentTarget,a=x(this,r,!0).event(t),s=j(t.view).on(`mousemove.zoom`,d,!0).on(`mouseup.zoom`,p,!0),c=M(t,i),l=t.clientX,u=t.clientY;qa(t.view),$a(t),a.mouse=[c,this.__zoom.invert(c)],Ir(this),a.start();function d(e){if(eo(e),!a.moved){var t=e.clientX-l,r=e.clientY-u;a.moved=t*t+r*r>h}a.event(e).zoom(`mouse`,n(y(a.that.__zoom,a.mouse[0]=M(e,i),a.mouse[1]),a.extent,o))}function p(e){s.on(`mousemove.zoom mouseup.zoom`,null),Ja(e.view,a.moved),eo(e),a.event(e).end()}}function ie(r,...i){if(e.apply(this,arguments)){var a=this.__zoom,c=M(r.changedTouches?r.changedTouches[0]:r,this),l=a.invert(c),u=a.k*(r.shiftKey?.5:2),d=n(y(v(a,u),c,l),t.apply(this,i),o);eo(r),s>0?j(this).transition().duration(s).call(ee,d,c,r):j(this).call(_.transform,d,c,r)}}function ae(t,...n){if(e.apply(this,arguments)){var r=t.touches,i=r.length,a=x(this,n,t.changedTouches.length===i).event(t),o,s,c,l;for($a(t),s=0;s<i;++s)c=r[s],l=M(c,this),l=[l,this.__zoom.invert(l),c.identifier],a.touch0?!a.touch1&&a.touch0[2]!==l[2]&&(a.touch1=l,a.taps=0):(a.touch0=l,o=!0,a.taps=1+!!u);u&&=clearTimeout(u),o&&(a.taps<2&&(d=l[0],u=setTimeout(function(){u=null},p)),Ir(this),a.start())}}function oe(e,...t){if(this.__zooming){var r=x(this,t).event(e),i=e.changedTouches,a=i.length,s,c,l,u;for(eo(e),s=0;s<a;++s)c=i[s],l=M(c,this),r.touch0&&r.touch0[2]===c.identifier?r.touch0[0]=l:r.touch1&&r.touch1[2]===c.identifier&&(r.touch1[0]=l);if(c=r.that.__zoom,r.touch1){var d=r.touch0[0],f=r.touch0[1],p=r.touch1[0],m=r.touch1[1],h=(h=p[0]-d[0])*h+(h=p[1]-d[1])*h,g=(g=m[0]-f[0])*g+(g=m[1]-f[1])*g;c=v(c,Math.sqrt(h/g)),l=[(d[0]+p[0])/2,(d[1]+p[1])/2],u=[(f[0]+m[0])/2,(f[1]+m[1])/2]}else if(r.touch0)l=r.touch0[0],u=r.touch0[1];else return;r.zoom(`touch`,n(y(c,l,u),r.extent,o))}}function se(e,...t){if(this.__zooming){var n=x(this,t).event(e),r=e.changedTouches,i=r.length,a,o;for($a(e),f&&clearTimeout(f),f=setTimeout(function(){f=null},p),a=0;a<i;++a)o=r[a],n.touch0&&n.touch0[2]===o.identifier?delete n.touch0:n.touch1&&n.touch1[2]===o.identifier&&delete n.touch1;if(n.touch1&&!n.touch0&&(n.touch0=n.touch1,delete n.touch1),n.touch0)n.touch0[1]=this.__zoom.invert(n.touch0[0]);else if(n.end(),n.taps===2&&(o=M(o,this),Math.hypot(d[0]-o[0],d[1]-o[1])<g)){var s=j(this).on(`dblclick.zoom`);s&&s.apply(this,arguments)}}}return _.wheelDelta=function(e){return arguments.length?(r=typeof e==`function`?e:Ya(+e),_):r},_.filter=function(t){return arguments.length?(e=typeof t==`function`?t:Ya(!!t),_):e},_.touchable=function(e){return arguments.length?(i=typeof e==`function`?e:Ya(!!e),_):i},_.extent=function(e){return arguments.length?(t=typeof e==`function`?e:Ya([[+e[0][0],+e[0][1]],[+e[1][0],+e[1][1]]]),_):t},_.scaleExtent=function(e){return arguments.length?(a[0]=+e[0],a[1]=+e[1],_):[a[0],a[1]]},_.translateExtent=function(e){return arguments.length?(o[0][0]=+e[0][0],o[1][0]=+e[1][0],o[0][1]=+e[0][1],o[1][1]=+e[1][1],_):[[o[0][0],o[0][1]],[o[1][0],o[1][1]]]},_.constrain=function(e){return arguments.length?(n=e,_):n},_.duration=function(e){return arguments.length?(s=+e,_):s},_.interpolate=function(e){return arguments.length?(c=e,_):c},_.on=function(){var e=l.on.apply(l,arguments);return e===l?_:e},_.clickDistance=function(e){return arguments.length?(h=(e=+e)*e,_):Math.sqrt(h)},_.tapDistance=function(e){return arguments.length?(g=+e,_):g},_}var co={ATTRIBUTE:1,CHILD:2,PROPERTY:3,BOOLEAN_ATTRIBUTE:4,EVENT:5,ELEMENT:6},lo=e=>(...t)=>({_$litDirective$:e,values:t}),uo=class{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,n){this._$Ct=e,this._$AM=t,this._$Ci=n}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}},{I:fo}=l,po=e=>e,mo=()=>document.createComment(``),Z=(e,t,n)=>{let r=e._$AA.parentNode,i=t===void 0?e._$AB:t._$AA;if(n===void 0)n=new fo(r.insertBefore(mo(),i),r.insertBefore(mo(),i),e,e.options);else{let t=n._$AB.nextSibling,a=n._$AM,o=a!==e;if(o){let t;n._$AQ?.(e),n._$AM=e,n._$AP!==void 0&&(t=e._$AU)!==a._$AU&&n._$AP(t)}if(t!==i||o){let e=n._$AA;for(;e!==t;){let t=po(e).nextSibling;po(r).insertBefore(e,i),e=t}}}return n},Q=(e,t,n=e)=>(e._$AI(t,n),e),ho={},go=(e,t=ho)=>e._$AH=t,_o=e=>e._$AH,vo=e=>{e._$AR(),e._$AA.remove()},yo=(e,t,n)=>{let r=new Map;for(let i=t;i<=n;i++)r.set(e[i],i);return r},bo=lo(class extends uo{constructor(e){if(super(e),e.type!==co.CHILD)throw Error(`repeat() can only be used in text expressions`)}dt(e,t,n){let r;n===void 0?n=t:t!==void 0&&(r=t);let i=[],a=[],o=0;for(let t of e)i[o]=r?r(t,o):o,a[o]=n(t,o),o++;return{values:a,keys:i}}render(e,t,n){return this.dt(e,t,n).values}update(t,[n,r,i]){let a=_o(t),{values:o,keys:s}=this.dt(n,r,i);if(!Array.isArray(a))return this.ut=s,o;let c=this.ut??=[],l=[],u,d,f=0,p=a.length-1,m=0,h=o.length-1;for(;f<=p&&m<=h;)if(a[f]===null)f++;else if(a[p]===null)p--;else if(c[f]===s[m])l[m]=Q(a[f],o[m]),f++,m++;else if(c[p]===s[h])l[h]=Q(a[p],o[h]),p--,h--;else if(c[f]===s[h])l[h]=Q(a[f],o[h]),Z(t,l[h+1],a[f]),f++,h--;else if(c[p]===s[m])l[m]=Q(a[p],o[m]),Z(t,a[f],a[p]),p--,m++;else if(u===void 0&&(u=yo(s,m,h),d=yo(c,f,p)),u.has(c[f])){if(u.has(c[p])){let e=d.get(s[m]),n=e===void 0?null:a[e];if(n===null){let e=Z(t,a[f]);Q(e,o[m]),l[m]=e}else l[m]=Q(n,o[m]),Z(t,a[f],n),a[e]=null;m++}else vo(a[p]),p--}else vo(a[f]),f++;for(;m<=h;){let e=Z(t,l[h+1]);Q(e,o[m]),l[m++]=e}for(;f<=p;){let e=a[f++];e!==null&&vo(e)}return this.ut=s,go(t,l),e}});function xo(e){var t=0,n=e.children,r=n&&n.length;if(!r)t=1;else for(;--r>=0;)t+=n[r].value;e.value=t}function So(){return this.eachAfter(xo)}function Co(e,t){let n=-1;for(let r of this)e.call(t,r,++n,this);return this}function wo(e,t){for(var n=this,r=[n],i,a,o=-1;n=r.pop();)if(e.call(t,n,++o,this),i=n.children)for(a=i.length-1;a>=0;--a)r.push(i[a]);return this}function To(e,t){for(var n=this,r=[n],i=[],a,o,s,c=-1;n=r.pop();)if(i.push(n),a=n.children)for(o=0,s=a.length;o<s;++o)r.push(a[o]);for(;n=i.pop();)e.call(t,n,++c,this);return this}function Eo(e,t){let n=-1;for(let r of this)if(e.call(t,r,++n,this))return r}function Do(e){return this.eachAfter(function(t){for(var n=+e(t.data)||0,r=t.children,i=r&&r.length;--i>=0;)n+=r[i].value;t.value=n})}function Oo(e){return this.eachBefore(function(t){t.children&&t.children.sort(e)})}function ko(e){for(var t=this,n=Ao(t,e),r=[t];t!==n;)t=t.parent,r.push(t);for(var i=r.length;e!==n;)r.splice(i,0,e),e=e.parent;return r}function Ao(e,t){if(e===t)return e;var n=e.ancestors(),r=t.ancestors(),i=null;for(e=n.pop(),t=r.pop();e===t;)i=e,e=n.pop(),t=r.pop();return i}function jo(){for(var e=this,t=[e];e=e.parent;)t.push(e);return t}function Mo(){return Array.from(this)}function No(){var e=[];return this.eachBefore(function(t){t.children||e.push(t)}),e}function Po(){var e=this,t=[];return e.each(function(n){n!==e&&t.push({source:n.parent,target:n})}),t}function*Fo(){var e=this,t,n=[e],r,i,a;do for(t=n.reverse(),n=[];e=t.pop();)if(yield e,r=e.children)for(i=0,a=r.length;i<a;++i)n.push(r[i]);while(n.length)}function Io(e,t){e instanceof Map?(e=[void 0,e],t===void 0&&(t=zo)):t===void 0&&(t=Ro);for(var n=new Ho(e),r,i=[n],a,o,s,c;r=i.pop();)if((o=t(r.data))&&(c=(o=Array.from(o)).length))for(r.children=o,s=c-1;s>=0;--s)i.push(a=o[s]=new Ho(o[s])),a.parent=r,a.depth=r.depth+1;return n.eachBefore(Vo)}function Lo(){return Io(this).eachBefore(Bo)}function Ro(e){return e.children}function zo(e){return Array.isArray(e)?e[1]:null}function Bo(e){e.data.value!==void 0&&(e.value=e.data.value),e.data=e.data.data}function Vo(e){var t=0;do e.height=t;while((e=e.parent)&&e.height<++t)}function Ho(e){this.data=e,this.depth=this.height=0,this.parent=null}Ho.prototype=Io.prototype={constructor:Ho,count:So,each:Co,eachAfter:To,eachBefore:wo,find:Eo,sum:Do,sort:Oo,path:ko,ancestors:jo,descendants:Mo,leaves:No,links:Po,copy:Lo,[Symbol.iterator]:Fo};function Uo(e,t){return e.parent===t.parent?1:2}function Wo(e){var t=e.children;return t?t[0]:e.t}function Go(e){var t=e.children;return t?t[t.length-1]:e.t}function Ko(e,t,n){var r=n/(t.i-e.i);t.c-=r,t.s+=n,e.c+=r,t.z+=n,t.m+=n}function qo(e){for(var t=0,n=0,r=e.children,i=r.length,a;--i>=0;)a=r[i],a.z+=t,a.m+=t,t+=a.s+(n+=a.c)}function Jo(e,t,n){return e.a.parent===t.parent?e.a:n}function Yo(e,t){this._=e,this.parent=null,this.children=null,this.A=null,this.a=this,this.z=0,this.m=0,this.c=0,this.s=0,this.t=null,this.i=t}Yo.prototype=Object.create(Ho.prototype);function Xo(e){for(var t=new Yo(e,0),n,r=[t],i,a,o,s;n=r.pop();)if(a=n._.children)for(n.children=Array(s=a.length),o=s-1;o>=0;--o)r.push(i=n.children[o]=new Yo(a[o],o)),i.parent=n;return(t.parent=new Yo(null,0)).children=[t],t}function Zo(){var e=Uo,t=1,n=1,r=null;function i(i){var s=Xo(i);if(s.eachAfter(a),s.parent.m=-s.z,s.eachBefore(o),r)i.eachBefore(c);else{var l=i,u=i,d=i;i.eachBefore(function(e){e.x<l.x&&(l=e),e.x>u.x&&(u=e),e.depth>d.depth&&(d=e)});var f=l===u?1:e(l,u)/2,p=f-l.x,m=t/(u.x+f+p),h=n/(d.depth||1);i.eachBefore(function(e){e.x=(e.x+p)*m,e.y=e.depth*h})}return i}function a(t){var n=t.children,r=t.parent.children,i=t.i?r[t.i-1]:null;if(n){qo(t);var a=(n[0].z+n[n.length-1].z)/2;i?(t.z=i.z+e(t._,i._),t.m=t.z-a):t.z=a}else i&&(t.z=i.z+e(t._,i._));t.parent.A=s(t,i,t.parent.A||r[0])}function o(e){e._.x=e.z+e.parent.m,e.m+=e.parent.m}function s(t,n,r){if(n){for(var i=t,a=t,o=n,s=i.parent.children[0],c=i.m,l=a.m,u=o.m,d=s.m,f;o=Go(o),i=Wo(i),o&&i;)s=Wo(s),a=Go(a),a.a=t,f=o.z+u-i.z-c+e(o._,i._),f>0&&(Ko(Jo(o,t,r),t,f),c+=f,l+=f),u+=o.m,c+=i.m,d+=s.m,l+=a.m;o&&!Go(a)&&(a.t=o,a.m+=u-l),i&&!Wo(s)&&(s.t=i,s.m+=c-d,r=t)}return r}function c(e){e.x*=t,e.y=e.depth*n}return i.separation=function(t){return arguments.length?(e=t,i):e},i.size=function(e){return arguments.length?(r=!1,t=+e[0],n=+e[1],i):r?null:[t,n]},i.nodeSize=function(e){return arguments.length?(r=!0,t=+e[0],n=+e[1],i):r?[t,n]:null},i}var Qo={comfortable:{breadth:132,depth:150},compact:{breadth:92,depth:112}},$o=`\0root`;function es(e,t,n){let r=new Map;if(e.roots.length===0)return{positions:r,bounds:{minX:0,minY:0,maxX:0,maxY:0}};let{breadth:i,depth:a}=Qo[t],o=Io($o,t=>t===$o?e.roots:e.children.get(t)),s=Zo().nodeSize([i,a]).separation((e,t)=>e.parent===t.parent?1:1.25)(o),c={minX:1/0,minY:1/0,maxX:-1/0,maxY:-1/0};for(let e of s.descendants()){if(e.data===$o)continue;let t=e.x,i=(e.depth-1)*a,o=n===`vertical`?{x:t,y:i}:{x:i,y:t};r.set(e.data,o),c.minX=Math.min(c.minX,o.x),c.minY=Math.min(c.minY,o.y),c.maxX=Math.max(c.maxX,o.x),c.maxY=Math.max(c.maxY,o.y)}return{positions:r,bounds:c}}function ts(e,t,n,r=48){let i=Math.max(e.maxX-e.minX,1),a=Math.max(e.maxY-e.minY,1),o=Math.min(1.5,Math.max(.2,Math.min((t-2*r)/i,(n-2*r)/a))),s=(e.minX+e.maxX)/2,c=(e.minY+e.maxY)/2;return{k:o,x:t/2-s*o,y:n/2-c*o}}function ns(e,t,n,r,i=120){let a=new Set;for(let[o,s]of e.positions){let e=s.x*t.k+t.x,c=s.y*t.k+t.y;e>=-i&&e<=n+i&&c>=-i&&c<=r+i&&a.add(o)}return a}function rs(e,t,n,r){let i=r===`vertical`,a={parent:i?`ArrowUp`:`ArrowLeft`,child:i?`ArrowDown`:`ArrowRight`,previous:i?`ArrowLeft`:`ArrowUp`,next:i?`ArrowRight`:`ArrowDown`};if(!Object.values(a).includes(n))return;if(t===void 0||!e.visuals.has(t))return e.roots[0];let o=Xe(e,t),s=o.indexOf(t);switch(n){case a.parent:return e.parentOf.get(t)??t;case a.child:return e.children.get(t)?.[0]??t;case a.previous:return o[s-1]??t;default:return o[s+1]??t}}var is={comfortable:22,compact:16},as=250,os=22;function ss(e,t){if(e.type===`wheel`){let n=e;return t&&!n.ctrlKey&&!n.metaKey?`hint`:`zoom`}let n=e;return n.ctrlKey||(n.button??0)!==0?`ignore`:`zoom`}var cs=class extends d{static properties={model:{attribute:!1},density:{attribute:!1},orientation:{attribute:!1},showLabels:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},siteName:{attribute:!1},ctrlZoom:{attribute:!1},reducedMotion:{attribute:!1},focusId:{state:!0},hintVisible:{state:!0}};layout;entering=new Set;exiting=new Map;lastVisuals=new Map;exitTimer;hintTimer;transform={x:0,y:0,k:1};width=0;height=0;fitted=!1;zoomBehavior;resizeObserver;constructor(){super(),this.density=`comfortable`,this.orientation=`vertical`,this.showLabels=!0,this.siteName=``,this.ctrlZoom=!0,this.reducedMotion=!1,this.hintVisible=!1}connectedCallback(){super.connectedCallback(),this.resizeObserver=new ResizeObserver(e=>{let t=e[0]?.contentRect;t&&this.setViewportSize(t.width,t.height)}),this.resizeObserver.observe(this)}disconnectedCallback(){super.disconnectedCallback(),this.resizeObserver?.disconnect(),this.exitTimer!==void 0&&clearTimeout(this.exitTimer),this.hintTimer!==void 0&&clearTimeout(this.hintTimer),this.exitTimer=void 0,this.hintTimer=void 0}setViewportSize(e,t){this.width=e,this.height=t,this.fitted?this.needsCulling&&this.requestUpdate():this.tryInitialFit()}get needsCulling(){return(this.layout?.positions.size??0)>300}get svgEl(){return this.renderRoot.querySelector(`svg.canvas`)}willUpdate(e){if(this.model&&(e.has(`model`)||e.has(`density`)||e.has(`orientation`))){let e=es(this.model,this.density,this.orientation),t=this.layout;this.entering=new Set(t?[...e.positions.keys()].filter(e=>!t.positions.has(e)):[]);for(let t of e.positions.keys())this.exiting.delete(t);if(t&&!this.reducedMotion){for(let[n,r]of t.positions){let t=this.lastVisuals.get(n);!e.positions.has(n)&&t&&this.exiting.set(n,{point:r,visual:t})}this.scheduleExitCleanup()}this.layout=e,this.lastVisuals=new Map(this.model.visuals),(this.focusId===void 0||!this.model.visuals.has(this.focusId))&&(this.focusId=this.model.roots[0])}}firstUpdated(){let e=this.svgEl;e&&(this.zoomBehavior=so().scaleExtent([.2,4]).extent(()=>[[0,0],[Math.max(this.width,1),Math.max(this.height,1)]]).filter(e=>{let t=ss(e,this.ctrlZoom);return t===`hint`&&this.flashHint(),t===`zoom`}).on(`zoom`,e=>this.onZoom(e.transform)).on(`end`,()=>{this.needsCulling&&this.requestUpdate()}),j(e).call(this.zoomBehavior).on(`dblclick.zoom`,null),this.tryInitialFit())}updated(){this.tryInitialFit()}tryInitialFit(){this.fitted||!this.layout||!this.zoomBehavior||this.width<=0||this.height<=0||(this.fitted=!0,this.fit(!1))}onZoom(e){this.transform={x:e.x,y:e.y,k:e.k},this.renderRoot.querySelector(`g.viewport`)?.setAttribute(`transform`,this.transformAttr())}transformAttr(){let{x:e,y:t,k:n}=this.transform;return`translate(${e},${t}) scale(${n})`}fit(e=!0){let t=this.svgEl;if(!this.layout||!this.zoomBehavior||!t)return;let n=ts(this.layout.bounds,this.width,this.height),r=Za.translate(n.x,n.y).scale(n.k);e&&!this.reducedMotion?this.zoomBehavior.transform(j(t).transition().duration(300),r):this.zoomBehavior.transform(j(t),r)}zoomBy(e){let t=this.svgEl;this.zoomBehavior&&t&&(this.reducedMotion?this.zoomBehavior.scaleBy(j(t),e):this.zoomBehavior.scaleBy(j(t).transition().duration(200),e))}async focusNode(e){this.focusId=e,await this.updateComplete;let t=this.layout?.positions.get(e),n=this.svgEl;if(t&&n&&this.zoomBehavior&&this.width>0){let e=t.x*this.transform.k+this.transform.x,r=t.y*this.transform.k+this.transform.y;(e<40||e>this.width-40||r<40||r>this.height-40)&&(this.zoomBehavior.translateTo(j(n),t.x,t.y),await this.updateComplete)}for(let t of this.renderRoot.querySelectorAll(`g.nodes g.node`))t.getAttribute(`data-id`)===e&&t.focus()}flashHint(){this.hintVisible=!0,this.hintTimer!==void 0&&clearTimeout(this.hintTimer),this.hintTimer=setTimeout(()=>{this.hintVisible=!1},1500)}scheduleExitCleanup(){this.exiting.size!==0&&this.exitTimer===void 0&&(this.exitTimer=setTimeout(()=>{this.exitTimer=void 0,this.exiting.clear(),this.requestUpdate()},as))}highlightedPath(){let e=new Set,t=this.model;if(!t||this.selectedId===void 0)return e;let n=t.visuals.has(this.selectedId)?this.selectedId:Ze(t,this.selectedId)?.id;for(;n!==void 0;)e.add(n),n=t.parentOf.get(n);return e}onKeydown(e){let t=this.model;if(!t)return;let n=rs(t,this.focusId,e.key,this.orientation);if(n!==void 0){e.preventDefault(),this.focusNode(n);return}(e.key===`Enter`||e.key===` `)&&this.focusId!==void 0?(e.preventDefault(),_(this,`uit-activate`,{id:this.focusId})):e.key===`+`||e.key===`=`?(e.preventDefault(),this.zoomBy(1.25)):e.key===`-`?(e.preventDefault(),this.zoomBy(.8)):e.key===`0`&&(e.preventDefault(),this.fit())}render(){let{model:e,layout:t,localize:n}=this;if(!e||!t||!n)return C;let r=is[this.density],i=[...t.positions.keys()],a=[...e.links.values()];if(this.needsCulling&&this.width>0){let e=ns(t,this.transform,this.width,this.height);this.focusId!==void 0&&e.add(this.focusId),this.selectedId!==void 0&&e.add(this.selectedId),i=i.filter(t=>e.has(t)),a=a.filter(t=>e.has(t.childId)||e.has(t.parentId))}let o=this.highlightedPath();return S`
            <svg
                class="canvas ${this.reducedMotion?`still`:``}"
                role="application"
                aria-roledescription=${n(`graph.roledescription`)}
                aria-label=${n(`graph.label`,{site:this.siteName,devices:e.stats.devices,clients:e.stats.clients})}
                @keydown=${this.onKeydown}
            >
                <g class="viewport" transform=${this.transformAttr()}>
                    <g class="links">
                        ${bo(a,e=>e.childId,e=>this.renderLink(e,t,o))}
                    </g>
                    <g class="nodes">
                        ${bo(i,e=>e,n=>this.renderNode(e,e.visuals.get(n),t.positions.get(n),r,o,!0))}
                    </g>
                    <g class="exits" aria-hidden="true">
                        ${bo([...this.exiting],([e])=>e,([,t])=>this.renderGhost(e,t,r))}
                    </g>
                </g>
            </svg>
            <div class="hint" aria-hidden="true" ?hidden=${!this.hintVisible}>
                ${n(`zoom.hint`)}
            </div>
        `}renderLink(e,t,n){let r=t.positions.get(e.parentId),i=t.positions.get(e.childId);if(!r||!i)return C;let a=this.orientation===`vertical`?(r.y+i.y)/2:(r.x+i.x)/2,o=this.orientation===`vertical`?`M${r.x},${r.y} C${r.x},${a} ${i.x},${a} ${i.x},${i.y}`:`M${r.x},${r.y} C${a},${r.y} ${a},${i.y} ${i.x},${i.y}`,s=this.showLabels?at(e.edge):``,c=[`link`,e.edge?.medium??`unknown`,e.viaHidden.length>0?`via-hidden`:``,n.has(e.childId)?`on-path`:``];return u`<path class=${c.join(` `)} d=${o}></path>${s?u`<text class="link-label" x=${(r.x+i.x)/2} y=${(r.y+i.y)/2}>${s}</text>`:C}`}renderNode(e,n,r,i,a,o){let s=this.localize,c=n.id,l=ot(n),d=D(n,s),f=n.type===`group`?`group`:n.node.kind,p=[`node`,n.type,f,l,c===this.selectedId?`selected`:``,a.has(c)?`on-path`:``,this.entering.has(c)?`enter`:``],m=n.type===`group`?h:t(n.node),g=i+16;return u`<g
      class=${p.join(` `)}
      data-id=${c}
      role=${o?`button`:C}
      tabindex=${o?c===this.focusId?0:-1:C}
      aria-label=${o?st(e,n,s):C}
      aria-expanded=${o&&n.type===`group`?String(n.expanded):C}
      style=${`transform: translate(${r.x}px, ${r.y}px)`}
      @click=${o?()=>_(this,`uit-activate`,{id:c}):C}
      @focus=${o?()=>{this.focusId=c}:C}
    >
      <title>${d}</title>
      <circle class="hit" r=${Math.max(i,22)}></circle>
      <circle class="ring" r=${i+5}></circle>
      <circle class="disc" r=${i}></circle>
      <svg class="glyph" x=${-i*.6} y=${-i*.6} width=${i*1.2} height=${i*1.2} viewBox="0 0 24 24" aria-hidden="true">
        <path d=${m}></path>
      </svg>
      <circle class="status" cx=${i*.72} cy=${-i*.72} r=${Math.max(4,i*.24)}></circle>
      ${n.type===`group`?u`<text class="badge" x=${i*.95} y=${i+2}>${n.counts.total}</text>`:C}
      ${this.showLabels?u`<text class="label" y=${g}>${tt(d,os)}</text>`:C}
      ${l===`offline`?u`<text class="state-text" y=${this.showLabels?g+14:g}>${s(E.offline)}</text>`:C}
    </g>`}renderGhost(e,t,n){return this.renderNode(e,t.visual,t.point,n,new Set,!1)}static styles=[xe,p`
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
        `]};w(`uit-graph-view`,cs);function ls(e,t){return e.type===`group`?e.members.some(e=>e.name.toLowerCase().includes(t)):e.node.name.toLowerCase().includes(t)}function us(e,t,n){let r=n.trim().toLowerCase(),i;if(r){i=new Set;for(let[t,n]of e.visuals)if(ls(n,r))for(let n=t;n!==void 0&&!i.has(n);n=e.parentOf.get(n))i.add(n)}let a=[],o=(n,s,c)=>{let l=i?n.filter(e=>i.has(e)):n;l.forEach((n,i)=>{let u=e.visuals.get(n),d=e.children.get(n)??[],f=u.type===`group`,p=f||d.length>0,m=f?u.expanded:r!==``||!t.has(n);a.push({id:n,visual:u,level:s,posinset:i+1,setsize:l.length,hasChildren:p,expanded:p&&m,parentId:c}),m&&d.length>0&&o(d,s+1,n)})};return o(e.roots,1,void 0),a}var ds=class extends d{static properties={model:{attribute:!1},selectedId:{attribute:!1},localize:{attribute:!1},siteName:{attribute:!1},query:{state:!0},collapsed:{state:!0},focusId:{state:!0}};rows=[];typeahead=``;typeaheadTimer;constructor(){super(),this.siteName=``,this.query=``,this.collapsed=new Set}willUpdate(){this.model&&(this.rows=us(this.model,this.collapsed,this.query),this.rows.some(e=>e.id===this.focusId)||(this.focusId=this.rows[0]?.id))}render(){let{model:e,localize:t}=this;return!e||!t?C:S`
            <div class="search">
                <input
                    type="search"
                    .value=${this.query}
                    placeholder=${t(`list.search`)}
                    aria-label=${t(`list.search`)}
                    @input=${e=>{this.query=e.target.value}}
                />
            </div>
            ${this.rows.length===0?S`<p class="empty">${t(`list.no_matches`)}</p>`:S`<div
                      class="tree"
                      role="tree"
                      aria-label=${t(`list.label`,{site:this.siteName})}
                      @keydown=${this.onKeydown}
                  >
                      ${bo(this.rows,e=>e.id,n=>this.renderRow(e,n,t))}
                  </div>`}
        `}renderRow(e,n,r){let i=n.visual,a=D(i,r),o=ot(i);return S`<div
            class="row ${o} ${n.id===this.selectedId?`selected`:``}"
            role="treeitem"
            data-id=${n.id}
            aria-level=${n.level}
            aria-setsize=${n.setsize}
            aria-posinset=${n.posinset}
            aria-selected=${String(n.id===this.selectedId)}
            aria-expanded=${n.hasChildren?String(n.expanded):C}
            aria-label=${st(e,i,r)}
            tabindex=${n.id===this.focusId?0:-1}
            style=${`--level: ${n.level}`}
            @click=${()=>_(this,`uit-activate`,{id:n.id})}
            @focus=${()=>{this.focusId=n.id}}
        >
            <span
                class="chevron"
                aria-hidden="true"
                @click=${e=>{e.stopPropagation(),n.hasChildren&&this.toggle(n)}}
                >${n.hasChildren?T(n.expanded?y:s):C}</span
            >
            ${T(i.type===`group`?h:t(i.node))}
            <span class="name" title=${a}>${a}</span>
            ${i.type===`group`?S`<span class="count">${i.counts.total}</span>`:S`<span class="dot" aria-hidden="true"></span>${o===`online`?C:S`<span class="state-text"
                                >${r(E[o])}</span
                            >`}`}
        </div>`}toggle(e){if(e.visual.type===`group`){_(this,`uit-toggle-group`,{id:e.id});return}let t=new Set(this.collapsed);t.has(e.id)?t.delete(e.id):t.add(e.id),this.collapsed=t}onKeydown(e){let t=this.rows,n=t.findIndex(e=>e.id===this.focusId),r=t[n];if(!r)return;let i;switch(e.key){case`ArrowDown`:i=t[n+1]?.id;break;case`ArrowUp`:i=t[n-1]?.id;break;case`Home`:i=t[0]?.id;break;case`End`:i=t.at(-1)?.id;break;case`ArrowRight`:r.hasChildren&&!r.expanded?this.toggle(r):r.expanded&&(i=t[n+1]?.id);break;case`ArrowLeft`:r.expanded?this.toggle(r):i=r.parentId;break;case`Enter`:case` `:_(this,`uit-activate`,{id:r.id});break;default:e.key.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&(e.preventDefault(),this.typeAhead(e.key,n));return}e.preventDefault(),i!==void 0&&this.focusRow(i)}typeAhead(e,t){this.typeahead+=e.toLowerCase(),this.typeaheadTimer!==void 0&&clearTimeout(this.typeaheadTimer),this.typeaheadTimer=setTimeout(()=>{this.typeahead=``},500);let n=this.rows;for(let e=1;e<=n.length;e++){let r=n[(t+e)%n.length];if(D(r.visual,this.localize).toLowerCase().startsWith(this.typeahead)){this.focusRow(r.id);return}}}async focusRow(e){this.focusId=e,await this.updateComplete;let t=this.renderRoot.querySelectorAll(`[role="treeitem"]`);for(let n of t)n.getAttribute(`data-id`)===e&&n.focus()}static styles=[xe,re,p`
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
        `]};w(`uit-list-view`,ds);var fs=600,ps=`/config/integrations/integration/unifi_insights`,ms={integration:`action.integration`,edit:`action.edit`},hs={loading:{key:`state.loading`},no_sources:{key:`state.no_sources`,action:`integration`},unconfigured:{key:`state.unconfigured`,action:`edit`},empty:{key:`state.empty`},incompatible:{key:`state.incompatible`},reloading:{key:`state.reconnecting`}},gs=e=>e?.nodes.filter(e=>e.kind!==`client`&&e.state===`offline`).length??0,_s=class extends d{static properties={hass:{attribute:!1},layout:{attribute:!1},config:{state:!0},sources:{state:!0},snapshot:{state:!0},lastGood:{state:!0},error:{state:!0},incompatible:{state:!0},disconnected:{state:!0},ui:{state:!0},view:{state:!0},selectedId:{state:!0},siteOverride:{state:!0},narrow:{state:!0},reducedMotion:{state:!0},announcement:{state:!0}};subscription=new Le({onSnapshot:e=>this.applySnapshot(e),onError:e=>{this.error=e},onIncompatible:()=>{this.incompatible=!0},onDisconnected:()=>{this.disconnected=!0},onReconnected:()=>{this.hass&&this.loadSources(this.hass)}});buildModel=Ye();announcer=new De(e=>{this.announcement=e});sourcesFor;sourcesPending=!1;sourcesRetry;sourcesAttempt=0;sourcesError;boundKey;cardState={phase:`loading`,stale:!1,notices:[]};model;resizeObserver;motionQuery;localizeLang;localizeFn;constructor(){super(),this.incompatible=!1,this.disconnected=!1,this.ui={kinds:new Set(o),clients:`collapsed`,toggledGroups:new Set},this.view=`graph`,this.narrow=!1,this.reducedMotion=!1,this.announcement=``}setConfig(e){let t=he(le(e));this.config=t,this.view=t.view,this.ui={kinds:new Set(t.kinds),clients:t.clients,toggledGroups:new Set},this.siteOverride=void 0}getCardSize(){return 8}getGridOptions(){return{columns:12,rows:8,min_columns:6,min_rows:4}}static getConfigElement(){return document.createElement(ae)}static async getStubConfig(e){try{let t=oe(await e.callWS({type:i}))[0];if(t)return{type:ne,...t.binding}}catch{}return{type:ne}}connectedCallback(){super.connectedCallback(),this.resizeObserver=new ResizeObserver(e=>{let t=e[0]?.contentRect.width??0;this.narrow=t>0&&t<fs}),this.resizeObserver.observe(this),this.motionQuery=window.matchMedia(`(prefers-reduced-motion: reduce)`),this.motionQuery.addEventListener(`change`,this.onMotionChange),this.onMotionChange(),this.sync()}disconnectedCallback(){super.disconnectedCallback(),this.subscription.stop(),this.announcer.dispose(),this.resizeObserver?.disconnect(),this.resizeObserver=void 0,this.motionQuery?.removeEventListener(`change`,this.onMotionChange),this.sourcesFor=void 0,this.clearSourcesRetry()}shouldUpdate(e){if(e.size!==1||!e.has(`hass`))return!0;let t=e.get(`hass`),n=this.hass;return!t||!n||t.connection!==n.connection||(t.locale?.language??t.language)!==(n.locale?.language??n.language)}willUpdate(e){(e.has(`hass`)||e.has(`config`)||e.has(`sources`)||e.has(`siteOverride`))&&this.sync();let t=this.config;if(!t)return;this.cardState=Me({sources:this.sources,binding:this.binding,snapshot:this.snapshot,lastGood:this.lastGood,error:this.error,incompatible:this.incompatible,disconnected:this.disconnected,maxClients:t.max_clients}),this.model=this.cardState.render?this.buildModel(this.cardState.render,this.ui):void 0;let n=this.selectedId;n!==void 0&&!(this.model?.visuals.has(n)||this.model?.nodes.has(n))&&(this.selectedId=void 0)}get binding(){return this.config?this.siteOverride??se(this.config,this.sources):void 0}get localize(){let e=this.hass?.locale?.language??this.hass?.language??`en`;return(e!==this.localizeLang||!this.localizeFn)&&(this.localizeLang=e,this.localizeFn=Ee(e)),this.localizeFn}get graphView(){return this.renderRoot.querySelector(`uit-graph-view`)}sync(){let{hass:e,config:t}=this;if(!this.isConnected||!e||!t)return;this.sourcesFor!==e.connection&&(this.sourcesFor=e.connection,this.disconnected=!1,this.clearSourcesRetry(),this.sourcesAttempt=0,this.loadSources(e));let n=this.binding,r=n?`${n.entry_id}\u0000${n.site_id}`:void 0;r!==this.boundKey&&(this.boundKey=r,this.snapshot=void 0,this.lastGood=void 0,this.error=void 0,this.sourcesError=void 0,this.incompatible=!1,this.selectedId=void 0),this.subscription.update(e.connection,n?{...n,max_clients:t.max_clients}:void 0)}async loadSources(e){if(this.sourcesPending)return;this.sourcesPending=!0,this.clearSourcesRetry();let t=e.connection;try{let n=await e.callWS({type:i});if(this.sourcesFor!==t)return;this.sources=n,this.sourcesError&&this.error===this.sourcesError&&(this.error=void 0),this.sourcesError=void 0,n.length>0?this.sourcesAttempt=0:this.scheduleSourcesRetry()}catch(e){if(this.sourcesFor!==t)return;let n=this.sourcesError;this.sourcesError=r(e),(!this.error||this.error===n)&&(this.error=this.sourcesError),this.scheduleSourcesRetry()}finally{this.sourcesPending=!1,this.isConnected&&this.sourcesFor!==void 0&&this.sourcesFor!==t&&this.hass&&this.loadSources(this.hass)}}scheduleSourcesRetry(){this.isConnected&&(this.sourcesRetry=setTimeout(()=>{this.sourcesRetry=void 0,this.hass&&this.loadSources(this.hass)},Ie(this.sourcesAttempt++)))}clearSourcesRetry(){this.sourcesRetry!==void 0&&clearTimeout(this.sourcesRetry),this.sourcesRetry=void 0}applySnapshot(e){let t=this.snapshot;this.snapshot=e,this.error=void 0,this.incompatible=!1,this.disconnected=!1,e.status!==`unavailable`&&e.nodes.length>0&&(this.lastGood=e),this.hass&&this.sources!==void 0&&!this.sources.some(t=>t.entry_id===e.entry_id)&&this.loadSources(this.hass);let n=this.localize,r=n(`announce.updated`),i=e.issues[0],a=gs(e);if(e.status===`unavailable`&&i){let t=Ae(i,e,this.config?.max_clients??0);r=n(t.key,t.vars)}else a>0&&a!==gs(t)&&(r=n(`announce.offline`,{count:a}));this.announcer.announce(r)}onMotionChange=()=>{this.reducedMotion=this.motionQuery?.matches??!1};onActivate=e=>{let t=e.detail.id;this.model?.visuals.get(t)?.type===`group`&&this.toggleGroup(t),this.selectedId=t};onSelect=e=>{let t=e.detail.id,n=this.model;if(n&&!n.visuals.has(t)){let e=Ze(n,t);e&&!e.expanded&&this.toggleGroup(e.id)}this.selectedId=t};onToggleGroup=e=>{this.toggleGroup(e.detail.id)};onClose=()=>{this.selectedId=void 0};onKeydown=e=>{e.key===`Escape`&&this.selectedId!==void 0&&(e.stopPropagation(),this.selectedId=void 0)};toggleGroup(e){let t=new Set(this.ui.toggledGroups);t.has(e)?t.delete(e):t.add(e),this.ui={...this.ui,toggledGroups:t}}toggleKind(e){let t=new Set(this.ui.kinds);if(t.has(e)){if(t.size===1)return;t.delete(e)}else t.add(e);this.ui={...this.ui,kinds:t}}runAction(e){a(e===`integration`?ps:`${location.pathname}?edit=1`)}render(){let e=this.config;if(!e)return C;let t=this.localize,n=this.cardState,r=this.model,i=e.title??n.render?.site_name??this.snapshot?.site_name??t(`card.name`),a=n.render?.nodes??[],o=a.filter(e=>e.kind!==`client`).length,s=a.filter(e=>e.kind===`client`).length;return S`<ha-card>
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
                        ${T(m)}
                    </div>
                    <div class="header-text">
                        <h2 class="title" title=${i}>${i}</h2>
                        ${a.length>0?S`<div class="subtitle">
                                  ${t(`header.summary`,{devices:o,clients:s})}
                              </div>`:C}
                    </div>
                    ${this.renderSiteSelector(e,t)}
                </header>
                ${r?this.renderToolbar(t):C}
                ${r?this.renderNotices(n.notices,t):C}
                <div class="body">
                    ${r?this.renderContent(r,n,e,t):this.renderMessage(n,t)}
                </div>
                <div class="sr-only" role="status" aria-live="polite">
                    ${this.announcement}
                </div>
            </div>
        </ha-card>`}renderSiteSelector(e,t){let n=oe(this.sources??[]);if(!e.show_site_selector||n.length<2)return C;let r=this.binding;return S`<label class="site">
            <span class="sr-only">${t(`toolbar.site`)}</span>
            <select
                @change=${e=>{let t=n[Number(e.target.value)];t&&(this.siteOverride=t.binding)}}
            >
                ${n.map((e,t)=>S`<option
                            value=${t}
                            ?selected=${pe(e.binding,r)}
                        >
                            ${e.label}
                        </option>`)}
            </select>
        </label>`}renderToolbar(e){let t=S`
            <div
                class="group"
                role="group"
                aria-label=${e(`toolbar.view`)}
            >
                ${ve.map(t=>S`<button
                            aria-pressed=${String(this.view===t)}
                            @click=${()=>{this.view=t}}
                        >
                            ${e($e[t])}
                        </button>`)}
            </div>
            <div
                class="group"
                role="group"
                aria-label=${e(`toolbar.filters`)}
            >
                ${o.map(t=>S`<button
                            aria-pressed=${String(this.ui.kinds.has(t))}
                            @click=${()=>this.toggleKind(t)}
                        >
                            ${e(Qe[t])}
                        </button>`)}
            </div>
            ${this.view===`graph`?S`<div
                      class="group"
                      role="group"
                      aria-label=${e(`toolbar.zoom`)}
                  >
                      ${this.iconButton(ee,e(`zoom.in`),()=>this.graphView?.zoomBy(1.25))}
                      ${this.iconButton(c,e(`zoom.out`),()=>this.graphView?.zoomBy(.8))}
                      ${this.iconButton(ge,e(`zoom.fit`),()=>this.graphView?.fit())}
                  </div>`:C}
        `;return this.narrow?S`<details class="toolbar">
                  <summary>${e(`toolbar.options`)}</summary>
                  <div class="controls">${t}</div>
              </details>`:S`<div class="toolbar">
                  <div class="controls">${t}</div>
              </div>`}iconButton(e,t,n){return S`<button
            class="icon-button"
            aria-label=${t}
            title=${t}
            @click=${n}
        >
            ${T(e)}
        </button>`}actionButton(e,t){return S`<button
            class="action"
            @click=${()=>this.runAction(e)}
        >
            ${t(ms[e])}
        </button>`}renderNotices(e,t){return e.length===0?C:S`<ul class="notices">
            ${e.map(e=>S`<li class=${e.severity}>
                        <span>${t(e.key,e.vars)}</span>${e.action?this.actionButton(e.action,t):C}
                    </li>`)}
        </ul>`}renderMessage(e,t){let n=hs[e.phase],r={site:this.snapshot?.site_name??``},i=[];return n&&i.push({...n,vars:r}),i.push(...e.notices),S`<div class="message ${e.phase}">
            ${e.phase===`loading`?S`<svg
                      class="skeleton"
                      viewBox="0 0 120 60"
                      aria-hidden="true"
                  >
                      <path d="M60 18 L30 37 M60 18 L90 37"></path>
                      <circle cx="60" cy="10" r="8"></circle>
                      <circle cx="30" cy="45" r="8"></circle>
                      <circle cx="90" cy="45" r="8"></circle>
                  </svg>`:C}
            ${i.map(e=>S`<p>${t(e.key,e.vars)}</p>
                        ${e.action?this.actionButton(e.action,t):C}`)}
        </div>`}renderContent(e,t,n,r){let i=n.density??(this.narrow?`compact`:`comfortable`),a=t.render?.site_name??``,o=t.phase===`reloading`?`${r(`state.stale`)} · ${r(`state.reconnecting`)}`:r(`state.stale`);return S`<div class="content ${t.stale?`stale`:``}">
            ${t.stale?S`<span class="badge stale">${o}</span>`:C}
            ${this.view===`graph`?S`<uit-graph-view
                      .model=${e}
                      .density=${i}
                      .orientation=${n.orientation}
                      .showLabels=${n.show_labels}
                      .selectedId=${this.selectedId}
                      .localize=${r}
                      .siteName=${a}
                      .ctrlZoom=${this.layout!==`panel`}
                      .reducedMotion=${this.reducedMotion}
                  ></uit-graph-view>`:S`<uit-list-view
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
        </div>`}static styles=[xe,re,p`
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
        `]},vs=`current`,ys=``,bs={collapsed:`clients.collapsed`,expanded:`clients.expanded`,hidden:`clients.hidden`},xs={auto:`density.auto`,comfortable:`density.comfortable`,compact:`density.compact`},Ss={vertical:`orientation.vertical`,horizontal:`orientation.horizontal`},Cs={site:`editor.site`,title:`editor.title`,view:`editor.view`,clients:`editor.clients`,kinds:`editor.kinds`,density:`editor.density`,orientation:`editor.orientation`,show_site_selector:`editor.show_site_selector`,show_labels:`editor.show_labels`,max_clients:`editor.max_clients`};function ws(e,t,n){return e.map(e=>({value:e,label:n(t[e])}))}var $=(e,t)=>typeof e==`string`&&t.includes(e);function Ts(e,t){let{entry_id:n,site_id:r}=e;if(n===void 0||r===void 0)return ys;let i=t.findIndex(e=>pe(e.binding,{entry_id:n,site_id:r}));return i>=0?String(i):vs}function Es(e,t,n){let r=t.map((e,t)=>({value:String(t),label:e.label}));return Ts(e,t)===`current`&&r.push({value:vs,label:n(`editor.site_unavailable`,{site:e.site_id??``})}),[{name:`site`,selector:{select:{mode:`dropdown`,options:r}}},{name:`title`,selector:{text:{}}},{name:``,type:`grid`,schema:[{name:`view`,selector:{select:{mode:`dropdown`,options:ws(ve,$e,n)}}},{name:`clients`,selector:{select:{mode:`dropdown`,options:ws(me,bs,n)}}},{name:`density`,selector:{select:{mode:`dropdown`,options:ws([`auto`,..._e],xs,n)}}},{name:`orientation`,selector:{select:{mode:`dropdown`,options:ws(fe,Ss,n)}}}]},{name:`kinds`,selector:{select:{multiple:!0,mode:`list`,options:ws(o,Qe,n)}}},{name:`show_site_selector`,selector:{boolean:{}}},{name:`show_labels`,selector:{boolean:{}}},{name:`max_clients`,selector:{number:{min:1,max:500,mode:`box`}}}]}function Ds(e,t){return{site:Ts(e,t),title:e.title??``,view:e.view??`graph`,clients:e.clients??`collapsed`,density:e.density??`auto`,orientation:e.orientation??`vertical`,kinds:e.kinds?[...e.kinds]:[...o],show_site_selector:e.show_site_selector??!1,show_labels:e.show_labels??!0,max_clients:e.max_clients??500}}function Os(e,t,n){let r={...t},i=e.site??ys;if(i===ys)delete r.entry_id,delete r.site_id;else if(i!==`current`){let e=n[Number(i)];e&&(r.entry_id=e.binding.entry_id,r.site_id=e.binding.site_id)}e.title?r.title=e.title:delete r.title,$(e.view,ve)&&(r.view=e.view),$(e.clients,me)&&(r.clients=e.clients),$(e.orientation,fe)&&(r.orientation=e.orientation),$(e.density,_e)?r.density=e.density:e.density===`auto`&&delete r.density;let a=(e.kinds??[]).filter(e=>$(e,o));a.length===o.length?delete r.kinds:a.length>0&&(r.kinds=o.filter(e=>a.includes(e))),typeof e.show_site_selector==`boolean`&&(r.show_site_selector=e.show_site_selector),typeof e.show_labels==`boolean`&&(r.show_labels=e.show_labels);let s=e.max_clients;return s===500?delete r.max_clients:typeof s==`number`&&Number.isInteger(s)&&s>=1&&s<=500&&(r.max_clients=s),r}async function ks(e=customElements,t=window.loadCardHelpers){e.get(`ha-form`)||await((await t?.())?.createCardElement({type:`entities`,entities:[]})?.constructor)?.getConfigElement?.()}var As=class extends d{static properties={hass:{attribute:!1},config:{state:!0},sources:{state:!0},formReady:{state:!0}};sourcesRequested=!1;constructor(){super(),this.formReady=!1}setConfig(e){this.config={...e}}connectedCallback(){super.connectedCallback(),ks().catch(()=>void 0).then(()=>{this.formReady=!0})}willUpdate(){this.hass&&!this.sourcesRequested&&(this.sourcesRequested=!0,this.hass.callWS({type:i}).then(e=>{this.sources=e},()=>{this.sources=[]}))}render(){let{hass:e,config:t}=this;if(!e||!t)return C;let n=Ee(e.locale?.language??e.language);if(!this.formReady)return S`<p>${n(`state.loading`)}</p>`;let r=oe(this.sources??[]);return S`<ha-form
            .hass=${e}
            .data=${Ds(t,r)}
            .schema=${Es(t,r,n)}
            .computeLabel=${e=>{let t=Cs[e.name];return t?n(t):``}}
            @value-changed=${this.onValueChanged}
        ></ha-form>`}onValueChanged=e=>{e.stopPropagation();let t=this.config;if(!t)return;let n=e.detail.value,r=Os(n,t,oe(this.sources??[]));this.config=r,_(this,`config-changed`,{config:r})}};w(ue,_s),w(ae,As);var js=Ee(`en`);window.customCards??=[],window.customCards.some(e=>e.type===`unifi-insights-topology-card`)||window.customCards.push({type:ue,name:js(`card.name`),description:js(`card.description`),preview:!0,documentationURL:`https://github.com/ruaan-deysel/ha-unifi-insights#network-topology-card`});