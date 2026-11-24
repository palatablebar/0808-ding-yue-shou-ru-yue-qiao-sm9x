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
  const row = report.cases?.find(item=>item.case===selected && item.measure);
  target.replaceChildren();
  if (!row) { target.append(element('p','该分组暂无计算值')); return; }
  const {evidence:e, value, expected, unit} = row.measure;
  render(target, e, value, expected, unit);
}

function render(target,e,value,expected,unit) {
  const items=[['新增',e.new_cents],['扩张',e.expansion_cents],['收缩',e.contraction_cents],['流失',e.churn_cents]];
  const shelf=zone(target,'bridge-columns');
  const maximum=Math.max(1,...items.map(([,n])=>n));
  items.forEach(([label,n],i)=>{
    const col=zone(shelf,`bridge-tower bridge-${i}`);
    fill(col,n,maximum,`${i>1&&n?'-':''}${n}`); col.append(element('span',label));
  });
  zone(target,'bridge-total',`期末 ${value} 分`);
}
