/** Record the real local app. Requires an isolated, seeded server on port 8000.
 * Audio preparation and final encoding are handled by render_demo.py.
 * Does not mock providers or alter production databases. */
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {chromium, expect} = require('../frontend/node_modules/@playwright/test');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'storage/demo-video');
const scenes = JSON.parse(fs.readFileSync(path.join(out, 'scenes.json')));
(async () => {
 const browser = await chromium.launch({headless:true});
 const context = await browser.newContext({viewport:{width:1440,height:1080},recordVideo:{dir:out,size:{width:1440,height:1080}},timezoneId:'America/Chicago'});
 const page = await context.newPage();
 const started = Date.now();
 const timeline=[];
 async function caption(text) {
  await page.evaluate(text=>{
   let el=document.getElementById('video-caption');
   if(!el){el=document.createElement('div');el.id='video-caption';el.style.cssText='position:fixed;bottom:0;left:0;right:0;z-index:999999;background:#102a26f5;color:white;padding:22px 70px;font:23px/1.5 system-ui;text-align:center;border-top:3px solid #7dcca8;pointer-events:none;min-height:78px;display:flex;align-items:center;justify-content:center;';document.body.appendChild(el);document.body.style.paddingBottom='160px';}
   el.textContent=text;
  },text);
 }
 async function speak(id){const s=scenes.find(s=>s.id===id);await caption(s.text);timeline.push({...s,start:(Date.now()-started)/1000});await page.waitForTimeout((s.duration+0.6)*1000);}
 async function show(selector){await page.locator(selector).first().evaluate(e=>e.scrollIntoView({block:'center',behavior:'smooth'}));await page.waitForTimeout(700);}
 try {
  await page.goto('http://127.0.0.1:8000');
  await expect(page.getByRole('button',{name:'Find my exchange',exact:true})).toBeEnabled();
  await speak('intro');await speak('fiction');await speak('maya');
  await page.getByRole('button',{name:'Find my exchange',exact:true}).click();
  await speak('search');
  await expect(page.getByRole('button',{name:'Approve & save proposal'})).toBeEnabled({timeout:120000});
  const rid=await page.evaluate(()=>localStorage.getItem('skillswap-run'));
  await speak('circle');
  await show('.workspace');await speak('times');
  await page.getByText('Behind the exchange',{exact:true}).click();
  await show('.activity-content');await speak('agents');
  await show('.activity-row:has-text("pinecone / search-records")');await speak('pinecone');
  await show('.activity-row:has-text("validate_and_schedule")');await speak('validation');
  await page.getByText('Behind the exchange',{exact:true}).click();
  await show('.workspace');await speak('change');
  execFileSync(path.join(root,'.venv/bin/python'),[path.join(root,'scripts/demo_scenario.py'),'remove-nina-window'],{cwd:root,env:{...process.env,SKILLSWAP_DOMAIN_DB:path.join(root,'storage/video-domain.sqlite')},stdio:'pipe'});
  await page.getByRole('button',{name:'Approve & save proposal'}).click();
  await expect(page.getByText('Availability changed. Please review again.',{exact:true})).toBeVisible({timeout:30000});
  await expect(page.getByRole('button',{name:'Approve & save proposal'})).toBeEnabled({timeout:30000});
  await speak('stale');await speak('consent');
  await page.getByRole('button',{name:'Approve & save proposal'}).click();
  await expect(page.getByRole('heading',{name:'Proposal saved'})).toBeVisible({timeout:30000});
  await speak('saved');
  await page.reload();
  await expect(page.getByRole('heading',{name:'Proposal saved'})).toBeVisible({timeout:30000});
  await speak('recovery');
  const dl=page.waitForEvent('download');await page.getByRole('link',{name:'Download proposal'}).click();await(await dl).saveAs(path.join(out,'proposal.json'));
  await speak('export');
  await show('.memory-panel');await speak('memory');await speak('memorycontrol');
  await show('.provider-strip');await speak('services');
  await page.evaluate(()=>window.scrollTo({top:0,behavior:'smooth'}));await page.waitForTimeout(800);await speak('ending');
  const run=await(await page.request.get('http://127.0.0.1:8000/api/runs/'+rid)).json();
  const events=await(await page.request.get('http://127.0.0.1:8000/api/runs/'+rid+'/events')).json();
  if(!run.result||run.discovery?.source!=='semantic')throw Error('Expected saved live semantic proposal');
  fs.writeFileSync(path.join(out,'evidence.json'),JSON.stringify({run_id:rid,status:run.status,discovery:run.discovery,servers:[...new Set(events.map(e=>e.server))],model_calls:run.model_calls},null,2));
  fs.writeFileSync(path.join(out,'timeline.json'),JSON.stringify(timeline,null,2));
  await page.screenshot({path:path.join(out,'ending.png')});
 } finally {await context.close();fs.writeFileSync(path.join(out,'video-path.txt'),await page.video().path());await browser.close();}
})().catch(e=>{console.error(e.message);process.exit(1)});
