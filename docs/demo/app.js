'use strict';
(function() {
    const data = window.CIRCULAR_DATA;
    const byId = id => document.getElementById(id);
    const currency = value => new Intl.NumberFormat('en-US',{style:'currency',currency:'BRL',maximumFractionDigits:2}).format(value);
    const integer = value => new Intl.NumberFormat('en-US').format(value);
    const routes = ['Resale','Repair','Recycle'];
    const colors = {Resale:'var(--blue)',Repair:'var(--mint)',Recycle:'var(--yellow)'};
    let activeId = 'DEMO-001';
    let active;
    const sliders = ['condition','failure','repair','credit'];
    function loadCase(id) {
        activeId = id;
        active = data.assets.find(a=>a.equipment_id===id);
        byId('asset-id').textContent=id;
        byId('asset-name').textContent=active.model;
        byId('asset-supplier').textContent=active.supplier;
        byId('condition').value=active.condition_score;
        byId('failure').value=Math.round(active.inputs.failure_probability*100);
        byId('repair').value=active.inputs.repair_cost;
        byId('credit').value=active.inputs.acquisition_credit;
        document.querySelectorAll('[data-case]').forEach(b=>{b.classList.toggle('active',b.dataset.case===id);b.setAttribute('aria-pressed',String(b.dataset.case===id));});
        update();
    }
    function update() {
        const condition=Number(byId('condition').value),failure=Number(byId('failure').value)/100;
        const repair=Number(byId('repair').value),credit=Number(byId('credit').value),i=active.inputs;
        const base=credit+i.logistics_cost;
        const values={Resale:i.resale_price-base,Repair:(1-failure)*i.refurbished_price+failure*i.salvage_value-repair-base,Recycle:i.salvage_value-base};
        const eligible=routes.filter(r=>r==='Resale'?condition>=70:r==='Repair'?condition>=30:true);
        const winner=eligible.reduce((best,r)=>values[r]>values[best]+1e-8?r:best,eligible[0]);
        byId('condition-value').textContent=condition+' / 100';
        byId('failure-value').textContent=Math.round(failure*100)+'%';
        byId('repair-value').textContent=currency(repair);
        byId('credit-value').textContent=currency(credit);
        byId('winning-route').textContent=winner;
        byId('winning-net').textContent=currency(values[winner]);
        const negative=values[winner]<-1e-8;
        const manager=negative||credit>500;
        byId('review-badge').classList.toggle('warning',manager);
        byId('review-badge').textContent=negative?'Negative contribution · manager review required':manager?'Credit above BRL 500 · manager approval required':'Nonnegative contribution · ordinary approval eligible';
        const container=byId('route-comparison');container.replaceChildren();
        for(const r of routes){const row=document.createElement('div');row.className='comparison-row'+(!eligible.includes(r)?' ineligible':'');const label=document.createElement('span');label.textContent=r;const badge=document.createElement('small');badge.textContent=!eligible.includes(r)?'ineligible: condition gate':r===winner?'recommended':'';label.append(badge);const value=document.createElement('b');value.textContent=currency(values[r]);if(r===winner)value.style.color=colors[r];row.append(label,value);container.append(row);}
        byId('explanation').textContent=winner==='Repair'?'Expected repair receipt = '+Math.round((1-failure)*100)+'% × '+currency(i.refurbished_price)+' + '+Math.round(failure*100)+'% × '+currency(i.salvage_value)+'. Subtract '+currency(repair)+' repair, '+currency(credit)+' credit and '+currency(i.logistics_cost)+' logistics.':winner==='Resale'?'Direct resale is eligible at condition 70 or above. '+currency(i.resale_price)+' receipt − '+currency(credit)+' credit − '+currency(i.logistics_cost)+' logistics gives the best eligible contribution.':'Salvage '+currency(i.salvage_value)+' − '+currency(credit)+' credit − '+currency(i.logistics_cost)+' logistics. '+(condition<30?'Condition below 30 excludes both resale and repair.':'Recycling has the highest eligible expected contribution.')+(negative?' The best route is still negative; revise the offer before accepting.':'');
        byId('input-facts').textContent='RESALE '+currency(i.resale_price)+'  /  REFURBISHED '+currency(i.refurbished_price)+'  /  SALVAGE '+currency(i.salvage_value);
    }
    document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>loadCase(b.dataset.case)));
    sliders.forEach(id=>byId(id).addEventListener('input',update));
    byId('reset').addEventListener('click',()=>loadCase(activeId));
    const s=data.summary;
    const metricData=[['DEVICES ANALYZED',integer(s.assets),'Latest valid state per device'],['EXPECTED CONTRIBUTION',currency(s.expected_net),'Modeled amount, not realized profit'],['EXPECTED POLICY GAIN',currency(s.decision_gain),'Versus the defined naive baseline'],['REVIEW REQUIRED',integer(s.review_assets),'Devices with negative expected net']];
    for(const [label,value,note] of metricData){const tile=document.createElement('div');tile.className='metric';const l=document.createElement('small');l.textContent=label;const v=document.createElement('b');v.textContent=value;const n=document.createElement('p');n.textContent=note;tile.append(l,v,n);byId('metrics').append(tile);}
    for(const route of routes){const count=s.route_counts[route]||0;const row=document.createElement('div');row.className='bar-row';const label=document.createElement('div');label.className='bar-label';const name=document.createElement('span');name.textContent=route;const value=document.createElement('span');value.textContent=count+' devices · '+Math.round(count/s.assets*100)+'%';label.append(name,value);const track=document.createElement('div');track.className='bar-track';track.setAttribute('aria-hidden','true');const fill=document.createElement('div');fill.className='bar-fill';fill.style.width=count/s.assets*100+'%';fill.style.background=colors[route];track.append(fill);row.append(label,track);byId('route-bars').append(row);}
    for(const [label,value] of [['Raw source rows',s.raw_rows],['Repeated payloads removed',s.duplicate_rows],['Invalid events quarantined',s.quarantined_events],['Older valid events superseded',s.superseded_events],['Final device states',s.assets]]){const row=document.createElement('div');row.className='quality-row';const l=document.createElement('span');l.textContent=label;const v=document.createElement('b');v.textContent=value;row.append(l,v);byId('quality-list').append(row);}
    for(const model of data.by_model){const row=document.createElement('tr');for(const value of [model.model,model.assets,currency(model.expected_net),model.review_assets]){const cell=document.createElement('td');cell.textContent=value;row.append(cell);}byId('model-table').append(row);}
    loadCase(activeId);
})();
