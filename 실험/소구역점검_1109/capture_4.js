async (page) => {
  const items = [{"id":"R21","type":"도로","x":910415.45,"y":1500364.48,"lines":[[[910413,1500363],[910421,1500369]]]},{"id":"R22","type":"도로","x":910825.4,"y":1474265.25,"lines":[[[910825,1474253],[910825,1474266],[910827,1474279]]]},{"id":"R23","type":"도로","x":910015.22,"y":1475603.25,"lines":[[[910011,1475605],[910015,1475603]]]},{"id":"R24","type":"도로","x":910179.05,"y":1475074.96,"lines":[[[910140,1475074],[910138,1475065],[910140,1475060],[910189,1475079],[910200,1475085],[910210,1475091],[910221,1475098]]]},{"id":"R25","type":"도로","x":913919.03,"y":1473063.52,"lines":[[[913915,1473060],[913923,1473065],[913923,1473065]]]},{"id":"R26","type":"도로","x":913162.9,"y":1474895.06,"lines":[[[913195,1474888],[913162,1474895]]]},{"id":"R27","type":"도로","x":915362.14,"y":1475289.87,"lines":[[[915383,1475289],[915363,1475290],[915356,1475291]]]},{"id":"R28","type":"도로","x":913640.23,"y":1475168.04,"lines":[[[913633,1475148],[913640,1475167],[913632,1475191],[913625,1475197],[913617,1475209],[913615,1475213]]]},{"id":"R29","type":"도로","x":911495.02,"y":1474047.81,"lines":[[[911349,1474097],[911378,1474097],[911417,1474096],[911441,1474092],[911475,1474063],[911524,1474035],[911571,1474024],[911606,1474010],[911611,1474010]]]},{"id":"R30","type":"도로","x":910258.25,"y":1474340.53,"lines":[[[910252,1474341],[910262,1474342],[910266,1474345],[910269,1474348],[910269,1474349]]]},{"id":"R31","type":"도로","x":912832.22,"y":1472880.3,"lines":[[[912820,1472881],[912844,1472863],[912866,1472855]]]},{"id":"R32","type":"도로","x":914127.6,"y":1474404.86,"lines":[[[914130,1474410],[914114,1474387],[914110,1474381]]]},{"id":"R33","type":"도로","x":910882.13,"y":1475661.97,"lines":[[[910870,1475554],[910890,1475651],[910886,1475660],[910871,1475668],[910849,1475684],[910832,1475710],[910837,1475743]]]},{"id":"R34","type":"도로","x":910635.14,"y":1474136.37,"lines":[[[910635,1474133],[910642,1474159]]]},{"id":"R35","type":"도로","x":913011.29,"y":1474095.52,"lines":[[[913029,1474280],[913027,1474237],[913023,1474207],[913021,1474165],[913020,1474133],[913017,1474110],[913002,1474073],[912997,1474060]]]},{"id":"R36","type":"도로","x":912868.62,"y":1472656.67,"lines":[[[912846,1472563],[912869,1472660],[912869,1472660]]]},{"id":"R37","type":"도로","x":913147.88,"y":1474029.88,"lines":[[[913149,1474057],[913147,1473999]]]},{"id":"R38","type":"도로","x":912819.34,"y":1472997.16,"lines":[[[912828,1472999],[912809,1472995]]]},{"id":"R39","type":"도로","x":911925.08,"y":1475147.43,"lines":[[[911922,1475147],[911927,1475147]]]}];
  const dir = "C:\\Users\\seungjun\\Documents\\claude_code\\논문\\정보기술학회\\실험\\소구역점검_1109\\영상";
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
