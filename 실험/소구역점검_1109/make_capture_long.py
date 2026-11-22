"""1km 이상 독립 보행 묶음 전수 캡처용 Playwright 코드를 만든다. 묶음 전체가 들어오게 맞춘다."""
import json
import os

HERE = r"C:\Users\seungjun\Documents\claude_code\논문\정보기술학회\실험\소구역점검_1109"
items = json.load(open(os.path.join(HERE, "long_groups.json"), encoding="utf-8"))
TEMPLATE = r"""async (page) => {
  const items = __ITEMS__;
  const dir = __DIR__;
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
      const v = map.getView();
      v.fit(src.getExtent(), { size: map.getSize(), padding: [60, 60, 60, 60], maxZoom: 12 });
      if (Math.round(v.getZoom()) === 11) v.setZoom(10);  // 줌 11에는 이 지역 영상이 없다
      return await new Promise(res => { let done = false; map.once('rendercomplete', () => { done = true; res(true); }); map.render(); setTimeout(() => { if (!done) res(false); }, 12000); });
    }, s);
    await page.waitForTimeout(300);
    await page.screenshot({ path: dir + '\\' + s.id + '.jpg', type: 'jpeg', quality: 80 });
    log.push(s.id + (ok ? '' : ':시간초과'));
  }
  return log.join(' ');
}
"""
AGAIN = {"L04", "L05", "L06", "L07", "L08", "L09", "L13", "L15", "L18", "L19", "L20", "L21", "L22", "L23", "L24", "L26", "L27", "L28"}
slim = [{"id": s["id"], "lines": s["lines"]} for s in items if s["id"] in AGAIN]
code = TEMPLATE.replace("__ITEMS__", json.dumps(slim, separators=(",", ":"))).replace("__DIR__", json.dumps(os.path.join(HERE, "영상"), ensure_ascii=False))
open(os.path.join(HERE, "capture_long.js"), "w", encoding="utf-8").write(code)
print(len(slim), round(len(code) / 1024), "KB")
