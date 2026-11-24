import {element, pretty} from './client.js';

const labels = {READY:'通过', MISMATCH:'差异待复核', PENDING:'待复核', APPROVED:'已签发', HELD:'已暂缓'};
const headers = ['业务分组', '输入行', '计算值', '参考值', '判定'];
const allocHeaders = ['合同分组', '席位数', '部门承担金额(分)', '合同收入(分)', '判定'];

export function badge(status) {
  return element('span', labels[status] || status, {class:'badge', 'data-result':status, title: status});
}

function bridgeRow(row, selected) {
  const tr = element('tr');
  const button = element('button',row.case,{type:'button','data-case':row.case,'aria-pressed':String(row.case===selected)});
  tr.insertCell().append(button);
  [row.records.length, row.measure?.value ?? '—', row.measure?.expected ?? '—'].forEach(value=>tr.insertCell().textContent=value);
  tr.insertCell().append(badge(row.status));
  return tr;
}

function allocationRow(row, selected) {
  const tr = element('tr');
  const button = element('button',row.case,{type:'button','data-case':row.case,'aria-pressed':String(row.case===selected)});
  tr.insertCell().append(button);
  const a = row.allocation;
  [a?.seats ?? '—', a?.department_total_cents ?? '—', a?.revenue_cents ?? '—'].forEach(value=>tr.insertCell().textContent=value);
  tr.insertCell().append(badge(row.status));
  return tr;
}

function isolationRow(item) {
  const tr = element('tr');
  tr.append(...[item.line,item.record,item.case,item.reason].map(value=>element('td',value)));
  return tr;
}

export function snapshot(report, selected, stage) {
  const stats = report.intake;
  document.querySelector('[data-metric="input"]').textContent = stats.input;
  document.querySelector('[data-metric="accepted"]').textContent = stats.accepted;
  document.querySelector('[data-metric="isolated"]').textContent = stats.rejected;
  document.querySelector('[data-metric="cases"]').textContent = report.cases?.length ?? '—';
  const table = document.querySelector('#rows');
  table.replaceChildren();

  let columns;
  let rows;
  if (stage === 'intake') {
    columns = ['源行', '记录键', '业务分组', '原因码'];
    rows = stats.isolation.map(isolationRow);
    if (!rows.length) {
      const empty = element('tr');
      empty.insertCell().textContent = '当前文件没有隔离行';
      rows = [empty];
    }
  } else if (report.mode === 'allocation') {
    columns = allocHeaders;
    rows = (report.cases || []).map(row => allocationRow(row, selected));
  } else {
    columns = headers;
    rows = (report.cases || []).map(row => bridgeRow(row, selected));
  }
  const head = element('tr');
  head.append(...columns.map(title => element('th', title, {scope:'col'})));
  table.createTHead().append(head);
  const body = table.createTBody();
  body.append(...rows);

  const picked = report.cases?.find(row=>row.case===selected);
  document.querySelector('#detail-title').textContent = picked ? `分组 ${picked.case}` : '采信摘要';
  let shown;
  if (report.mode === 'allocation') {
    shown = picked
      ? (picked.allocation ?? {原因: picked.status, 参与记录: picked.issues ?? []})
      : stats.reasons;
  } else {
    shown = picked ? picked.measure?.evidence ?? picked.prep?.details ?? {原因:picked.status} : stats.reasons;
  }
  document.querySelector('#detail').textContent = pretty(shown);
  if (report.balance) {
    const b = report.balance;
    document.querySelector('#counts').textContent = report.mode === 'allocation'
      ? `行数 ${b.accounted}/${b.input} · ${b.ready} 份合同通过 · 对账差 ${b.reconcile_delta_cents ?? 0} 分`
      : `行数 ${b.accounted}/${b.input} · ${b.ready} 组通过`;
  } else {
    document.querySelector('#counts').textContent = `采信 ${stats.accepted} 行 · 隔离 ${stats.rejected} 行`;
  }
}

export function history(items, active) {
  const target = document.querySelector('#history');
  target.replaceChildren();
  for (const run of items) {
    const button = element('button', run.id.slice(0,10), {'data-run':run.id,'aria-pressed':String(run.id===active),type:'button'});
    const item = element('li');
    item.append(button, badge(run.status));
    target.append(item);
  }
  if (!items.length) target.append(element('li','尚无执行批次'));
}
