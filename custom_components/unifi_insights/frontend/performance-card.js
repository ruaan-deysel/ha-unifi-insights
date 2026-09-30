import{Dt as e,U as t,a as n,b as r,c as i,j as a,k as o,l as s,n as c,t as l,w as u,x as d}from"./chunks/register-dashboard-card-BLc74zCS.js";l({tag:i,editorTag:s,card:class extends c{static editorTag=s;get cardType(){return`custom:${i}`}get sourceCommand(){return e}get subscribeCommand(){return`unifi_insights/performance/subscribe`}get defaultTitle(){return`Device Performance`}get headerIcon(){return t}renderHeaderBadge(){let e=Array.isArray(this.snapshot?.devices)?this.snapshot.devices:[];return this.snapshot?a`<span class="chip ok">${e.length} Devices</span>`:o}renderContent(){let e=this.snapshot;if(!e)return a`<div class="state">No devices</div>`;let t=Array.isArray(e.devices)?e.devices:[],n=t.map(e=>Number(e.cpu_pct)).filter(e=>Number.isFinite(e)&&e>=0),i=t.map(e=>Number(e.memory_pct)).filter(e=>Number.isFinite(e)&&e>=0),s=n.length>0?Math.round(n.reduce((e,t)=>e+t,0)/n.length):0,c=i.length>0?Math.round(i.reduce((e,t)=>e+t,0)/i.length):0;return a`
            <div class="ring-strip">
                <div class="ring-card">
                    <div
                        class="ring-gauge"
                        style=${`--pct: ${s}; --ring-color: var(--uit-${d(s)===`ok`?`online`:d(s)===`warning`?`warning`:`offline`})`}
                    >
                        <span>${s}%</span>
                    </div>
                    <div>
                        <div class="kpi-top">Avg CPU</div>
                        <div class="kpi-sub">${t.length} Devices</div>
                    </div>
                </div>
                <div class="ring-card">
                    <div
                        class="ring-gauge"
                        style=${`--pct: ${c}; --ring-color: var(--primary-color)`}
                    >
                        <span>${c}%</span>
                    </div>
                    <div>
                        <div class="kpi-top">Avg Memory</div>
                        <div class="kpi-sub">System Load</div>
                    </div>
                </div>
            </div>

            <div class="list">
                ${t.slice(0,6).map(e=>{let t=String(e.name??`Device`),n=String(e.kind??`other`),i=Number(e.cpu_pct),s=e.cpu_pct==null||!Number.isFinite(i)?null:Math.min(100,Math.max(0,Math.round(i))),c=e.memory_pct==null?null:Math.round(Number(e.memory_pct)),l=s==null?`ok`:d(s),f=typeof e.clients==`number`?`${e.clients} clients`:void 0;return a`
                        <div class="item-card">
                            <div class="item-icon">
                                ${u(r(n))}
                            </div>
                            <div class="item-body">
                                <div class="item-top">
                                    <span class="item-name">${t}</span>
                                    <span class="item-value">
                                        ${s==null?`--`:`${s}%`}
                                    </span>
                                </div>
                                <div class="bar-track" aria-hidden="true">
                                    <div
                                        class="bar-fill ${l}"
                                        style=${`width: ${s??0}%`}
                                    ></div>
                                </div>
                                ${c!=null||f?a`<div class="item-meta">
                                          ${c==null?o:a`<span>RAM ${c}%</span>`}
                                          ${f?a`<span>· ${f}</span>`:o}
                                      </div>`:o}
                            </div>
                        </div>
                    `})}
            </div>
        `}},editor:class extends n{constructor(){super(i,e)}},name:`UniFi Device Performance`,description:`Infrastructure CPU, memory, PoE, client load, and throughput summary.`});