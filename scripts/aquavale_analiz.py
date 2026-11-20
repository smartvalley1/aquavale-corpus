"""Örnek veri üzerinde ilk analizler: (1) tüketimden evde bulunma çıkarımı vs kaçak tespiti,
(2) şebeke keşif değeri dağılımı ve iş emirlerinde yüksek değerli varlık oranı, (3) derlem envanteri."""
import pandas as pd, numpy as np, json, glob, os
import os; D = os.environ.get('AQV_OUT', '.')
tk = pd.read_csv(f'{D}/veri/tuketim_saatlik.csv', parse_dates=['saat'])
gt = pd.read_csv(f'{D}/analiz/_hane_gercegi_GIZLI.csv').fillna('')
tk['gun'] = tk.saat.dt.date; tk['h'] = tk.saat.dt.hour
day = tk.groupby(['abone_no', 'gun']).litre_x10.sum().reset_index()
med = day.groupby('abone_no').litre_x10.transform('median')
day['yok_tahmin'] = day.litre_x10 < .1 * med
# gerçek yokluk günleri
start = pd.Timestamp('2026-09-01').date()
truth = set()
for _, r in gt[gt.yokluk_gunleri > 0].iterrows():
    s = pd.Timestamp(r.yokluk_baslangic)
    for k in range(int(r.yokluk_gunleri)): truth.add((r.abone_no, (s + pd.Timedelta(days=k)).date()))
day['yok_gercek'] = [(a, g) in truth for a, g in zip(day.abone_no, day.gun)]
tp = (day.yok_tahmin & day.yok_gercek).sum(); fp = (day.yok_tahmin & ~day.yok_gercek).sum(); fn = (~day.yok_tahmin & day.yok_gercek).sum()
hh_pred = set(day[day.yok_tahmin].abone_no); hh_true = set(gt[gt.yokluk_gunleri > 0].abone_no)
# gece minimum debisi → iç tesisat kaçağı (meşru amaç)
night = tk[tk.h.between(2, 4)].groupby('abone_no').litre_x10.min()
leak_pred = set(night[night > .5].index); leak_true = set(gt[gt.hane_turu == 'tesisat_kacagi'].abone_no)
# sabah ilk kullanım saati (rutin çıkarımı)
wake = tk[(tk.h.between(4, 11)) & (tk.litre_x10 > tk.groupby('abone_no').litre_x10.transform('median'))].groupby(['abone_no', 'gun']).h.min()
wake_sd = wake.groupby('abone_no').std().median()
r1 = dict(gun_duzeyi_yokluk_kesinlik=round(tp / (tp + fp), 3), gun_duzeyi_yokluk_duyarlilik=round(tp / (tp + fn), 3),
          yokluk_yasayan_hane=len(hh_true), dogru_bulunan_hane=len(hh_pred & hh_true), yanlis_alarm_hane=len(hh_pred - hh_true),
          kacak_hane=len(leak_true), kacak_dogru=len(leak_pred & leak_true), kacak_yanlis=len(leak_pred - leak_true),
          uyanma_saati_std_medyan=round(float(wake_sd), 2))
# (2) şebeke
hat = pd.read_csv(f'{D}/veri/sebeke_hatlar.csv'); ie = pd.read_csv(f'{D}/veri/ariza_is_emirleri.csv')
r2 = dict(hat_kesif_dagilimi=hat.kesif_degeri.value_counts().to_dict(),
          is_emri_kesif_dagilimi=ie.kesif_degeri.value_counts().to_dict(),
          is_emri_sayisi=len(ie), ortalama_sizinti_suresi_gun=round(float((pd.to_datetime(ie.onarim) - pd.to_datetime(ie.baslangic)).dt.days.mean()), 1))
# (3) envanter
inv = []
for p in sorted(glob.glob(f'{D}/veri/*.csv')):
    df = pd.read_csv(p, nrows=None if 'tuketim' not in p else 5)
    inv.append(dict(dosya=os.path.basename(p), satir=sum(1 for _ in open(p)) - 1, sutun=df.shape[1]))
for p in sorted(glob.glob(f'{D}/belgeler/*.md')):
    t = open(p).read(); lv = t.split('(D')[1][0] if '(D' in t else '?'
    inv.append(dict(dosya=os.path.basename(p), satir=t.count('\n'), sutun=f'D{lv}'))
pd.DataFrame(inv).to_csv(f'{D}/analiz/derlem_envanteri.csv', index=False)
json.dump(dict(tuketim=r1, sebeke=r2), open(f'{D}/analiz/ilk_bulgular.json', 'w'), ensure_ascii=False, indent=1, default=int)
print(json.dumps(dict(tuketim=r1, sebeke=r2), ensure_ascii=False, indent=1, default=int))
