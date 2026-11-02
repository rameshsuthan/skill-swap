const { chromium } = require('../frontend/node_modules/@playwright/test');
const path = require('node:path');
(async()=>{const browser=await chromium.launch();try{const page=await browser.newPage({deviceScaleFactor:2});for(const name of ['system-architecture','agent-workflow','approval-sequence']){const file=path.resolve('docs/submission/diagrams',name+'.svg');await page.goto('file://'+file);await page.locator('svg').screenshot({path:file.replace('.svg','.png')});}}finally{await browser.close()}})();
