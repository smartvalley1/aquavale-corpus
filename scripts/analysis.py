"""First analyses on the corpus: (1) inferring absence from consumption vs. detecting internal leaks,
(2) reconnaissance-value distribution of network links and work orders, (3) corpus inventory, (4) Figure 1.

Usage: AQV_OUT=. python3 scripts/analysis.py
"""
import os, glob, json
import numpy as np, pandas as pd
D = os.environ.get('AQV_OUT', '.')

cons = pd.read_csv(f'{D}/data/consumption_hourly.csv', parse_dates=['hour'])
gt = pd.read_csv(f'{D}/analysis/_household_ground_truth_HIDDEN.csv').fillna('')
cons['day'] = cons.hour.dt.date; cons['h'] = cons.hour.dt.hour
day = cons.groupby(['customer_id', 'day']).litres_x10.sum().reset_index()
day['away_pred'] = day.litres_x10 < .1 * day.groupby('customer_id').litres_x10.transform('median')
truth = set()
for _, r in gt[gt.absence_days > 0].iterrows():
    s = pd.Timestamp(r.absence_start)
    truth |= {(r.customer_id, (s + pd.Timedelta(days=k)).date()) for k in range(int(r.absence_days))}
day['away_true'] = [(a, g) in truth for a, g in zip(day.customer_id, day.day)]
tp = (day.away_pred & day.away_true).sum(); fp = (day.away_pred & ~day.away_true).sum(); fn = (~day.away_pred & day.away_true).sum()
hh_pred, hh_true = set(day[day.away_pred].customer_id), set(gt[gt.absence_days > 0].customer_id)
night = cons[cons.h.between(2, 4)].groupby('customer_id').litres_x10.min()
leak_pred, leak_true = set(night[night > .5].index), set(gt[gt.household_type == 'internal_leak'].customer_id)
r1 = dict(day_level_absence_precision=round(tp / (tp + fp), 3), day_level_absence_recall=round(tp / (tp + fn), 3),
          households_with_absence=len(hh_true), households_found=len(hh_pred & hh_true), false_alarm_households=len(hh_pred - hh_true),
          leak_households=len(leak_true), leaks_found=len(leak_pred & leak_true), leak_false_alarms=len(leak_pred - leak_true))
links = pd.read_csv(f'{D}/data/network_links.csv'); wo = pd.read_csv(f'{D}/data/fault_work_orders.csv')
r2 = dict(link_recon_distribution=links.recon_value.value_counts().to_dict(), work_order_recon_distribution=wo.recon_value.value_counts().to_dict(),
          work_orders=len(wo), mean_leak_duration_days=round(float((pd.to_datetime(wo.repaired) - pd.to_datetime(wo.start)).dt.days.mean()), 1))
inv = [dict(file=os.path.basename(p), rows=sum(1 for _ in open(p)) - 1, columns=pd.read_csv(p, nrows=5).shape[1]) for p in sorted(glob.glob(f'{D}/data/*.csv'))]
for p in sorted(glob.glob(f'{D}/documents/*.md')):
    t = open(p).read(); inv.append(dict(file=os.path.basename(p), rows=t.count('\n'), columns='D' + (t.split('(D')[1][0] if '(D' in t else '?')))
pd.DataFrame(inv).to_csv(f'{D}/analysis/corpus_inventory.csv', index=False)
res = dict(consumption=r1, network=r2)
json.dump(res, open(f'{D}/analysis/first_results.json', 'w'), indent=1, default=int)
print(json.dumps(res, indent=1, default=int))

# Figure 1
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.dates as md
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#9a9893', 'axes.labelcolor': '#3d3c38', 'xtick.color': '#6b6a65', 'ytick.color': '#6b6a65'})
hid = gt[(gt.absence_days >= 7) & (gt.household_type == 'family')].customer_id.iloc[0]
d = cons[cons.customer_id == hid].set_index('hour').litres_x10.resample('D').sum() * 10
r = gt[gt.customer_id == hid].iloc[0]; s = pd.Timestamp(r.absence_start); e = s + pd.Timedelta(days=int(r.absence_days))
fig, ax = plt.subplots(1, 2, figsize=(9, 3.2), gridspec_kw={'width_ratios': [1.5, 1]})
a = ax[0]; a.axvspan(s, e, color='#f0efec', zorder=0); a.plot(d.index, d.values, color='#2a78d6', lw=2)
a.text(s + (e - s) / 2, d.max() * .92, 'away from home\n(inferable)', ha='center', va='top', color='#3d3c38', fontsize=8)
a.set_title('(a) Daily consumption of a fictional household', loc='left', fontsize=9.5, color='#1f1e1b'); a.set_ylabel('litres / day')
a.grid(axis='y', color='#e6e4df', lw=.6); a.tick_params(axis='x', labelsize=7.5); a.set_ylim(0); a.xaxis.set_major_formatter(md.DateFormatter('%d %b'))
b = ax[1]; x = np.arange(2); left = np.zeros(2)
for l, c in zip(['low', 'medium', 'high'], ['#86b6ef', '#3987e5', '#1c5cab']):
    v = np.array([(links.recon_value == l).mean(), (wo.recon_value == l).mean()]) * 100
    b.barh(x, v, left=left, color=c, edgecolor='white', lw=2, height=.55, label=l)
    for i in range(2):
        if v[i] > 8: b.text(left[i] + v[i] / 2, x[i], f'{v[i]:.0f}%', ha='center', va='center', color='white' if l != 'low' else '#1f1e1b', fontsize=8)
    left += v
b.set_yticks(x, [f'All links\n(n={len(links)})', f'Work orders\n(n={len(wo)})']); b.set_xlim(0, 100); b.set_xlabel('percent')
b.set_title('(b) Reconnaissance value', loc='left', fontsize=9.5, color='#1f1e1b')
b.legend(frameon=False, ncol=3, loc='lower center', bbox_to_anchor=(.45, -.45), fontsize=8)
plt.tight_layout(); plt.savefig(f'{D}/analysis/figure1_sample_data.png', dpi=200, bbox_inches='tight')
