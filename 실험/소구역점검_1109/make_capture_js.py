"""samples.json으로 국토정보맵 영상 캡처용 Playwright 코드를 20곳씩 나눠 만든다."""
import json
import os

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\소구역점검_1109"
samples = json.load(open(os.path.join(HERE, "samples.json"), encoding="utf-8"))["samples"]
TEMPLATE = r"""async (page) => {
  const items = __ITEMS__;
  const dir = __DIR__;
  await page.setViewportSize({ width: 800, height: 740 });
  await page.evaluate(() => {
    const m = document.getElementById('div_map');
    for (let x = 10; x < 800; x += 40) for (let y = 5; y < 740; y += 40) {
      for (const el of document.elementsFromPoint(x, y)) {
        if (el === document.body || el === document.documentElement || el.contains(m) || m.contains(el)) continue;
        let top = el;
        while (top.parentElement && !top.parentElement.contains(m)) top = top.parentElement;
        top.style.display = 'none';
      }
    }
    fnBaseLayer('TMS Layer_2013');
    map.updateSize();
    if (window.__sampleLayer) map.removeLayer(window.__sampleLayer);
    window.__sampleLayer = new ol.layer.Vector({ source: new ol.source.Vector(), zIndex: 9999 });
    map.addLayer(window.__sampleLayer);
  });
  const log = [];
  for (const s of items) {
    const ok = await page.evaluate(async (s) => {
      const src = window.__sampleLayer.getSource();
      src.clear();
      for (const ln of s.lines) {
        const f = new ol.Feature(new ol.geom.LineString(ln));
        f.setStyle(new ol.style.Style({ stroke: new ol.style.Stroke({ color: 'rgba(255,240,0,0.95)', width: 2, lineDash: [8, 8] }) }));
        src.addFeature(f);
      }
      const p = new ol.Feature(new ol.geom.Point([s.x, s.y]));
      p.setStyle(new ol.style.Style({ image: new ol.style.Circle({ radius: 14, stroke: new ol.style.Stroke({ color: 'rgba(255,60,60,1)', width: 2 }) }) }));
      src.addFeature(p);
      const v = map.getView();
      v.setCenter([s.x, s.y]);
      v.setZoom(s.type === '보행로' ? 12 : 13);
      return await new Promise(res => { let done = false; map.once('rendercomplete', () => { done = true; res(true); }); map.render(); setTimeout(() => { if (!done) res(false); }, 12000); });
    }, s);
    await page.waitForTimeout(300);
    await page.screenshot({ path: dir + '\\' + s.id + '.jpg', type: 'jpeg', quality: 80 });
    log.push(s.id + (ok ? '' : ':시간초과'));
  }
  return log.join(' ');
}
"""
keys = ["id", "type", "x", "y", "lines"]


def slim(s):
    """표시용 선을 1m 단위로 줄이고 꼭짓점을 솎아 코드 크기를 줄인다."""
    t = {k: s[k] for k in keys}
    t["lines"] = [[[round(a), round(b)] for a, b in (ln[::4] + ln[-1:])] for ln in s["lines"]]
    return t


for b in range(0, len(samples), 20):
    items = [slim(s) for s in samples[b:b + 20]]
    code = TEMPLATE.replace("__ITEMS__", json.dumps(items, ensure_ascii=False, separators=(",", ":"))).replace("__DIR__", json.dumps(os.path.join(HERE, "영상"), ensure_ascii=False))
    path = os.path.join(HERE, f"capture_{b // 20 + 1}.js")
    open(path, "w", encoding="utf-8").write(code)
    print(path, len(items))
