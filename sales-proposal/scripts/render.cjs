#!/usr/bin/env node
/* Rend la proposition HTML en PDF (une page par diapo), enregistre une image par page
   et refuse un contenu qui déborde d'une diapo.

     node scripts/render.cjs chemin/proposition.html

   Sorties, à côté du HTML : <nom>.pdf et pages/pNN.png.
   Playwright est requis. S'il n'est pas installé ici, indiquer un module existant :
     PLAYWRIGHT_MODULE=/chemin/vers/node_modules/playwright
   et, si besoin, un navigateur précis : CHROME_PATH=/chemin/vers/chrome */
const path = require('path');
const fs = require('fs');

function chargerPlaywright() {
  const pistes = [process.env.PLAYWRIGHT_MODULE, 'playwright', 'playwright-core'].filter(Boolean);
  for (const p of pistes) {
    try { return require(p); } catch (e) { /* piste suivante */ }
  }
  console.error('Playwright introuvable. Installez-le (npm i playwright && npx playwright install chromium)\n' +
    'ou indiquez un module existant avec PLAYWRIGHT_MODULE=/chemin/node_modules/playwright.');
  process.exit(3);
}

(async () => {
  const source = process.argv[2];
  if (!source || !fs.existsSync(source)) { console.error('usage : node render.cjs proposition.html'); process.exit(3); }
  const abs = path.resolve(source);
  const dossier = path.dirname(abs);
  const nom = path.basename(abs, '.html');
  const { chromium } = chargerPlaywright();
  const options = process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {};
  let nav;
  try {
    nav = await chromium.launch(options);
  } catch (e) {
    console.error('Navigateur introuvable pour cette version de Playwright.\n' +
      'Lancez « npx playwright install chromium » dans le dossier de Playwright,\n' +
      'ou indiquez un Chrome existant avec CHROME_PATH=/chemin/vers/chrome.\n' + String(e.message || e).split('\n')[0]);
    process.exit(3);
  }
  const page = await nav.newPage();
  await page.goto('file://' + abs);
  await page.evaluate(() => document.fonts.ready);
  const taille = await page.evaluate(() => {
    const s = document.querySelector('.slide').getBoundingClientRect();
    return { w: Math.round(s.width), h: Math.round(s.height) };
  });
  await page.setViewportSize({ width: taille.w, height: taille.h });

  const rapport = await page.evaluate(() => [...document.querySelectorAll('.slide')].map((s, i) => {
    const haut = s.getBoundingClientRect().top;
    const pied = s.querySelector('.foot');
    const limite = pied ? pied.getBoundingClientRect().top - haut - 8 : s.getBoundingClientRect().height - 40;
    let bas = 0, large = 0;
    for (const el of s.querySelectorAll(':scope > *:not(.foot)')) {
      const r = el.getBoundingClientRect();
      bas = Math.max(bas, r.bottom - haut);
      large = Math.max(large, el.scrollWidth - el.clientWidth);
    }
    const images = [...s.querySelectorAll('img')].filter(im => !im.complete || im.naturalWidth === 0).length;
    return { page: i + 1, cle: s.dataset.cle || '', bas: Math.round(bas), limite: Math.round(limite), deborde: bas > limite || large > 2, images_cassees: images };
  }));

  await page.pdf({ path: path.join(dossier, nom + '.pdf'), width: taille.w + 'px', height: taille.h + 'px', printBackground: true, preferCSSPageSize: true });
  const pages = path.join(dossier, 'pages');
  fs.mkdirSync(pages, { recursive: true });
  const diapos = await page.$$('.slide');
  for (let i = 0; i < diapos.length; i++) {
    await diapos[i].screenshot({ path: path.join(pages, 'p' + String(i + 1).padStart(2, '0') + '.png') });
  }
  await nav.close();

  const octets = fs.readFileSync(path.join(dossier, nom + '.pdf')).toString('latin1');
  const pagesPdf = (octets.match(/\/Type\s*\/Page(?![s])/g) || []).length;
  const fautes = rapport.filter(r => r.deborde || r.images_cassees);
  if (pagesPdf !== rapport.length) {
    console.error('Le PDF compte ' + pagesPdf + ' pages pour ' + rapport.length + ' diapos : une diapo se répand sur deux pages.');
    fautes.push({ page: 0, cle: 'pdf' });
  }
  console.log(path.join(dossier, nom + '.pdf') + ' · ' + rapport.length + ' pages · images dans ' + pages);
  for (const r of fautes.filter(f => f.page)) {
    console.error('PAGE ' + r.page + ' (' + r.cle + ') : ' +
      (r.deborde ? 'le contenu déborde (' + r.bas + ' px pour ' + r.limite + ' px disponibles). ' : '') +
      (r.images_cassees ? r.images_cassees + ' image(s) introuvable(s).' : ''));
  }
  process.exit(fautes.length ? 2 : 0);
})();
