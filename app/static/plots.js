import {element} from './client.js';

function zone(target, className, text) {
  const box = element('div', undefined, {class:className});
  if (text) box.append(element('span',text));
  target.append(box);
  return box;
}

function fill(layer, value, max, label) {
  const mark = zone(layer, 'mark-piece', label);
  mark.style.setProperty('--part', `${Math.max(0,Math.min(100,100*value/Math.max(1,max)))}%`);
  return mark;
}

export function visualize(report, selected) {
  const target = document.querySelector('#visual');
  target.replaceChildren();
  if (report.mode === 'allocation') {
    renderAllocation(target, report, selected);
    return;
  }
  const row = report.cases?.find(item=>item.case===selected && item.measure);
  if (!row) { target.append(element('p','该分组暂无计算值')); return; }
  const {evidence:e, value, unit} = row.measure;
  render(target, e, value, unit);
}

function renderAllocation(target, report, selected) {
  const row = report.cases?.find(item=>item.case===selected && item.allocation);
  if (!row) { target.append(element('p','该合同暂无归属结果')); return; }
  const a = row.allocation;
  const maximum = Math.max(1, ...a.departments.map(d=>d.amount_cents));
  const shelf = zone(target,'bridge-columns');
  for (const d of a.departments) {
    const col = zone(shelf,'bridge-tower');
    fill(col, d.amount_cents, maximum, `${d.amount_cents}`);
    col.append(element('span', d.department));
  }
  zone(target,'bridge-total',`部门合计 ${a.department_total_cents} / 合同收入 ${a.revenue_cents} 分`);
}

function render(target,e,value,unit) {
  const items=[['新增',e.new_cents],['扩张',e.expansion_cents],['收缩',e.contraction_cents],['流失',e.churn_cents]];
  const shelf=zone(target,'bridge-columns');
  const maximum=Math.max(1,...items.map(([,n])=>n));
  items.forEach(([label,n],i)=>{
    const col=zone(shelf,`bridge-tower bridge-${i}`);
    fill(col,n,maximum,`${i>1&&n?'-':''}${n}`); col.append(element('span',label));
  });
  zone(target,'bridge-total',`期末 ${value} 分`);
}
