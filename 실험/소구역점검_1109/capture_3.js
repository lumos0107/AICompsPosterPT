async (page) => {
  const items = [{"id":"R01","type":"도로","x":906868.25,"y":1497139.52,"lines":[[[906868,1497169],[906867,1497146],[906868,1497139]]]},{"id":"R02","type":"도로","x":904788.67,"y":1497341.99,"lines":[[[904743,1497234],[904742,1497222],[904734,1497210],[904733,1497203],[904736,1497198],[904741,1497192],[904778,1497168],[904785,1497165],[904789,1497165],[904817,1497184],[904825,1497191],[904839,1497198],[904842,1497202],[904845,1497214],[904839,1497234],[904827,1497253],[904823,1497268],[904823,1497297],[904813,1497299],[904797,1497297],[904780,1497323],[904777,1497328],[904790,1497349],[904788,1497362],[904787,1497382],[904787,1497382]]]},{"id":"R03","type":"도로","x":912667.53,"y":1497784.23,"lines":[[[912651,1497756],[912668,1497785],[912668,1497787]]]},{"id":"R04","type":"도로","x":913948.49,"y":1497160.94,"lines":[[[913929,1497135],[913948,1497159],[913953,1497176],[913956,1497180]]]},{"id":"R05","type":"도로","x":913303.9,"y":1503000.9,"lines":[[[913320,1503037],[913318,1503014],[913315,1503004],[913304,1503001],[913289,1502998],[913289,1502998]]]},{"id":"R06","type":"도로","x":904403.55,"y":1498270.09,"lines":[[[904403,1498276],[904407,1498252],[904431,1498228],[904442,1498202],[904442,1498202]]]},{"id":"R07","type":"도로","x":905298.76,"y":1497598.26,"lines":[[[905296,1497598],[905343,1497597],[905369,1497596]]]},{"id":"R08","type":"도로","x":905663.09,"y":1497651.5,"lines":[[[905654,1497652],[905670,1497651]]]},{"id":"R09","type":"도로","x":909764.47,"y":1498395.07,"lines":[[[909767,1498395],[909752,1498396]]]},{"id":"R10","type":"도로","x":911247.72,"y":1498120.7,"lines":[[[911257,1498102],[911244,1498122]]]},{"id":"R11","type":"도로","x":907972.83,"y":1502216.67,"lines":[[[907973,1502214],[907972,1502223]]]},{"id":"R12","type":"도로","x":910494.11,"y":1502727.14,"lines":[[[910493,1502747],[910494,1502726]]]},{"id":"R13","type":"도로","x":911896.07,"y":1497196.07,"lines":[[[911898,1497178],[911895,1497204],[911892,1497227]]]},{"id":"R14","type":"도로","x":914272.81,"y":1502590.41,"lines":[[[914276,1502586],[914273,1502591]]]},{"id":"R15","type":"도로","x":912676.54,"y":1499632.88,"lines":[[[912632,1499629],[912734,1499630],[912781,1499619],[912847,1499625],[912872,1499631],[912914,1499603],[912914,1499603]]]},{"id":"R16","type":"도로","x":906185.86,"y":1497996.67,"lines":[[[906142,1497989],[906214,1497999]]]},{"id":"R17","type":"도로","x":909520.7,"y":1500952.59,"lines":[[[909515,1500950],[909522,1500953]]]},{"id":"R18","type":"도로","x":903664.09,"y":1499775.11,"lines":[[[903668,1499782],[903664,1499775]]]},{"id":"R19","type":"도로","x":909843.67,"y":1502993.55,"lines":[[[909849,1503001],[909825,1502965]]]},{"id":"R20","type":"도로","x":905375.65,"y":1499939.32,"lines":[[[905376,1499939],[905378,1499941]]]}];
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
