import{Dt as e,U as t,j as n,k as r,n as i,o as a,r as o,s,t as c,v as l,w as u,y as d}from"./chunks/register-dashboard-card-DFoe8fM2.js";c({tag:a,editorTag:s,card:class extends i{static editorTag=s;get cardType(){return`custom:${a}`}get sourceCommand(){return e}get subscribeCommand(){return`unifi_insights/performance/subscribe`}get defaultTitle(){return`Device Performance`}get headerIcon(){return t}renderHeaderBadge(){let e=Array.isArray(this.snapshot?.devices)?this.snapshot.devices:[];return this.snapshot?n`<span class="chip ok">${e.length} Devices</span>`:r}renderContent(){let e=this.snapshot;if(!e)return n`<div class="state">No devices</div>`;let t=Array.isArray(e.devices)?e.devices:[],i=t.map(e=>Number(e.cpu_pct)).filter(e=>Number.isFinite(e)&&e>=0),a=t.map(e=>Number(e.memory_pct)).filter(e=>Number.isFinite(e)&&e>=0),o=i.length>0?Math.round(i.reduce((e,t)=>e+t,0)/i.length):0,s=a.length>0?Math.round(a.reduce((e,t)=>e+t,0)/a.length):0;return n`
            <div class="ring-strip">
                <div class="ring-card">
                    <div
                        class="ring-gauge"
                        style=${`--pct: ${o}; --ring-color: var(--uit-${d(o)===`ok`?`online`:d(o)===`warning`?`warning`:`offline`})`}
                    >
                        <span>${o}%</span>
                    </div>
                    <div>
                        <div class="kpi-top">Avg CPU</div>
                        <div class="kpi-sub">${t.length} Devices</div>
                    </div>
                </div>
                <div class="ring-card">
                    <div
                        class="ring-gauge"
                        style=${`--pct: ${s}; --ring-color: var(--primary-color)`}
                    >
                        <span>${s}%</span>
                    </div>
                    <div>
                        <div class="kpi-top">Avg Memory</div>
                        <div class="kpi-sub">System Load</div>
                    </div>
                </div>
            </div>

            <div class="list">
                ${t.slice(0,6).map(e=>{let t=String(e.name??`Device`),i=String(e.kind??`other`),a=e.cpu_pct==null?null:Math.round(Number(e.cpu_pct)),o=e.memory_pct==null?null:Math.round(Number(e.memory_pct)),s=a==null?`ok`:d(a),c=typeof e.clients==`number`?`${e.clients} clients`:void 0;return n`
                        <div class="item-card">
                            <div class="item-icon">
                                ${u(l(i))}
                            </div>
                            <div class="item-body">
                                <div class="item-top">
                                    <span class="item-name">${t}</span>
                                    <span class="item-value">
                                        ${a==null?`--`:`${a}%`}
                                    </span>
                                </div>
                                <div class="bar-track" aria-hidden="true">
                                    <div
                                        class="bar-fill ${s}"
                                        style=${`width: ${a??0}%`}
                                    ></div>
                                </div>
                                ${o!=null||c?n`<div class="item-meta">
                                          ${o==null?r:n`<span>RAM ${o}%</span>`}
                                          ${c?n`<span>· ${c}</span>`:r}
                                      </div>`:r}
                            </div>
                        </div>
                    `})}
            </div>
        `}},editor:class extends o{constructor(){super(a,e)}},name:`UniFi Device Performance`,description:`Infrastructure CPU, memory, PoE, client load, and throughput summary.`});