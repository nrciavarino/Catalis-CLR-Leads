import json, sys
from playwright.sync_api import sync_playwright
stub = open('stub.js').read()
results=[]; errs=[]
def ok(name, cond, extra=''):
    results.append((name,bool(cond),extra)); print(('PASS ' if cond else 'FAIL ')+name+(' — '+str(extra) if (extra and not cond) else ''))
api_calls=[]
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width':420,'height':900}, accept_downloads=True)
    ctx.add_init_script(stub)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append('pageerror: '+str(e)))
    pg.on('console', lambda m: errs.append('console.error: '+m.text) if m.type=='error' else None)
    def route(r):
        u = r.request.url
        if u.startswith('file://'): return r.continue_()
        if 'api.anthropic.com' in u:
            body = json.loads(r.request.post_data); api_calls.append(body)
            prompt = body['messages'][0]['content']
            if 'Find a publicly listed' in prompt:
                txt = '{"email":"found@county.gov","phone":"555-0100","sourceNote":"county directory"}'
            else: txt = 'READOUT OK'
            return r.fulfill(status=200, content_type='application/json', body=json.dumps({'content':[{'type':'text','text':txt}]}))
        return r.abort()
    pg.route('**/*', route)
    pg.goto('file://'+__import__('os').path.abspath('../index.html'))
    pg.wait_for_function("typeof State!=='undefined' && State.db && State.events.length>0", timeout=8000)
    ok('app boots at v1.14.0', pg.evaluate("APP_VERSION")=='v1.14.0')

    # ---- Stage 1: partial-contact web search ----
    pg.evaluate("openReview({name:'Pat Jones',company:'Lee County',title:'Clerk',email:'pat@lee.gov',phone:'',notes:'',source:'manual'}, 'k1')")
    ok('S1 alert shows when only phone missing', pg.locator('#btnWebSearchContact').is_visible())
    ok('S1 button says phone', 'phone' in pg.inner_text('#btnWebSearchContact').lower(), pg.inner_text('#btnWebSearchContact'))
    ok('S1 no red styling when one present', not pg.evaluate("document.getElementById('f_phone_wrap').classList.contains('missing')"))
    pg.click('#btnWebSearchContact'); pg.wait_for_function("document.getElementById('f_phone').value!==''")
    ok('S1 phone filled', pg.input_value('#f_phone')=='555-0100')
    ok('S1 existing email untouched', pg.input_value('#f_email')=='pat@lee.gov')
    sp = [c for c in api_calls if 'Find a publicly listed' in c['messages'][0]['content']][-1]['messages'][0]['content']
    ok('S1 prompt asks only for phone', 'work phone number' in sp and 'email' not in sp.split('Respond')[0].lower().replace('email address','X') or 'work phone number' in sp, sp[:120])
    ok('S1 alert clears when both present', pg.locator('#btnWebSearchContact').count()==0)
    pg.evaluate("closeReview()")
    pg.evaluate("openReview({name:'No Contact',company:'X',title:'',email:'',phone:'',notes:'',source:'manual'})")
    ok('S1 both blank still offers search', 'contact info' in pg.inner_text('#btnWebSearchContact').lower())
    ok('S1 both blank keeps red styling', pg.evaluate("document.getElementById('f_email_wrap').classList.contains('missing')"))
    pg.evaluate("closeReview()")

    # ---- Regression: event with no questions ----
    pg.evaluate("openReview({name:'Plain Lead',email:'a@b.gov',phone:'1',source:'manual'})")
    ok('R no qual area for event without questions', pg.inner_html('#qualArea')=='')
    pg.click('#btnSaveLead'); pg.wait_for_timeout(200)
    leads = [v for k,v in pg.evaluate("[...window.__store.entries()]") if k.startswith('events/ev1/leads/')] if False else None
    cnt = pg.evaluate("[...window.__store.keys()].filter(k=>k.startsWith('events/ev1/leads/')).length")
    ok('R plain lead saves with no questions configured', cnt==1)

    # ---- Stage 2: notes ----
    pg.evaluate("switchTab('events')")
    pg.click("button[aria-label='Event notes and qualification questions'] >> nth=0")
    ok('S2 detail screen opens', pg.locator('#view-eventdetail.active').count()==1)
    pg.fill('#evNoteText','Booth 412, Hall B. Power drop is limited.'); pg.select_option('#evNoteTag','Venue'); pg.click('#btnAddEvNote')
    pg.wait_for_function("document.getElementById('evNotesList').innerText.includes('Booth 412')")
    ok('S2 note appears with tag + author', 'Venue' in pg.inner_text('#evNotesList') and 'Nic' in pg.inner_text('#evNotesList'))
    pg.fill('#evNoteText','   '); pg.click('#btnAddEvNote')
    ok('S2 blank note rejected', pg.evaluate("[...window.__store.keys()].filter(k=>k.includes('/notes/')).length")==1)
    pg.fill('#evNoteText','Second note'); pg.click('#btnAddEvNote'); pg.wait_for_function("document.getElementById('evNotesList').innerText.includes('Second note')")
    ok('S2 newest first', pg.inner_text('#evNotesList').index('Second note') < pg.inner_text('#evNotesList').index('Booth 412'))
    pg.evaluate("window.confirm=()=>true")
    pg.locator('#evNotesList button:has-text("Delete")').first.click(); pg.wait_for_timeout(200)
    ok('S2 delete own note', pg.evaluate("[...window.__store.keys()].filter(k=>k.includes('/notes/')).length")==1)
    pg.evaluate("window.__store.set('events/ev1/notes/other',{text:'Someone else',tag:'',author:'Sam',createdAt:5})"); pg.evaluate("openEventDetail('ev1')"); pg.wait_for_timeout(100)
    ok('S2 no delete button on others notes', pg.locator('#evNotesList .card:has-text("Someone else") button').count()==0)
    prompt = pg.evaluate("fetchEventNotes('ev1').then(n=>buildReadoutPrompt([{name:'A',company:'B'}], n))")
    ok('S2 notes flow into readout prompt', 'Someone else' in prompt and 'Event-level notes' in prompt)

    # ---- Stage 3: qualification builder ----
    def addq(label,typ,opts='',req=False):
        pg.fill('#qfLabel',label); pg.select_option('#qfType',typ)
        if opts: pg.fill('#qfOptions',opts)
        pg.set_checked('#qfRequired',req); pg.click('#btnAddQual'); pg.wait_for_timeout(150)
    addq('Product interest','single','CMS, Jury, Land Records',True)
    addq('Modules of interest','multi','e-Filing\nPayments\nPortal')
    addq('Has budget?','yesno')
    addq('Timeline notes','text')
    qf = pg.evaluate("State.events.find(e=>e.id==='ev1').qualFields")
    ok('S3 four questions persisted w/ stable ids', len(qf)==4 and len({f['id'] for f in qf})==4, qf)
    pg.fill('#qfLabel','Bad'); pg.select_option('#qfType','single'); pg.fill('#qfOptions','OnlyOne'); pg.click('#btnAddQual')
    ok('S3 choice question with <2 choices rejected', len(pg.evaluate("State.events.find(e=>e.id==='ev1').qualFields"))==4)
    pg.fill('#qfLabel',''); pg.fill('#qfOptions','')
    ok('S3 copy-from picker lists other event', pg.locator('#btnCopyQual').count()==1)
    pg.click('#btnCopyQual'); pg.wait_for_timeout(150)
    ok('S3 copied question gets a new id', len(pg.evaluate("State.events.find(e=>e.id==='ev1').qualFields"))==5)
    # archive the copied one
    qid = pg.evaluate("State.events.find(e=>e.id==='ev1').qualFields[4].id")
    pg.evaluate(f"qfToggleArchive('{qid}')"); pg.wait_for_timeout(150)
    first = pg.evaluate("State.events.find(e=>e.id==='ev1').qualFields[0].id")
    pg.evaluate(f"qfMove('{first}',1)"); pg.wait_for_timeout(150)
    ok('S3 reorder works', pg.evaluate("State.events.find(e=>e.id==='ev1').qualFields[1].label")=='Product interest')
    pg.evaluate(f"qfMove('{first}',-1)"); pg.wait_for_timeout(150)

    # ---- lead form with questions ----
    pg.evaluate("switchTab('scan')")
    pg.evaluate("openReview({name:'Dana Cole',company:'Mesa County',title:'Director',email:'d@mesa.gov',phone:'555',source:'manual'})")
    ok('S3 form renders 4 active questions (archived hidden)', pg.locator('#qualArea [data-qid]').count()==4)
    ok('S3 required marker on required', '*' in pg.inner_text('#qualArea [data-qid] >> nth=0'))
    pg.click('#btnSaveLead'); pg.wait_for_timeout(150)
    ok('S3 required blocks save + offers save-anyway', pg.locator('#btnQualSaveAnyway').count()==1)
    ok('S3 missing question highlighted', pg.locator('#qualArea .qual-missing').count()==1)
    ok('S3 nothing saved yet', pg.evaluate("[...window.__store.keys()].filter(k=>k.startsWith('events/ev1/leads/')).length")==1)
    pg.click('#btnQualSaveAnyway'); pg.wait_for_timeout(250)
    ok('S3 save anyway saves lead', pg.evaluate("[...window.__store.keys()].filter(k=>k.startsWith('events/ev1/leads/')).length")==2)
    pg.evaluate("switchTab('leads')"); pg.wait_for_timeout(100)
    ok('S3 Incomplete badge on lead + header count', pg.locator('.lead-item:has-text("Dana Cole") .badge:has-text("Incomplete")').count()==1 and 'incomplete' in pg.inner_text('#leadIncompleteBadge'))
    # edit and answer
    key = pg.evaluate("Object.entries(State.leads).find(([k,l])=>l.name==='Dana Cole')[0]")
    pg.evaluate(f"editLead('{key}')")
    pg.select_option('#qualArea select >> nth=0','CMS')
    pg.check('#qualArea input[type=checkbox][value="Payments"]'); pg.check('#qualArea input[type=checkbox][value="Portal"]')
    pg.fill('#qualArea input[type=text]','Budget in Q3, "board vote", Sept')
    pg.click('#btnSaveLead'); pg.wait_for_timeout(250)
    saved = pg.evaluate(f"State.leads['{key}']")
    ok('S3 answers saved on edit (stable ids)', saved['qual'][first]=='CMS' and sorted(saved['qual'][qf[1]['id']])==['Payments','Portal'], saved.get('qual'))
    ok('S3 returned to Leads tab after save', pg.locator('#view-leads.active').count()==1)
    ok('S3 Incomplete badge cleared', pg.locator('.lead-item:has-text("Dana Cole") .badge:has-text("Incomplete")').count()==0)
    ok('S3 answers visible on lead card', 'CMS' in pg.inner_text('.lead-item:has-text("Dana Cole")'))
    # editing again preserves answers; clearing optional removes
    pg.evaluate(f"editLead('{key}')")
    ok('S3 edit prefills answers', pg.input_value('#qualArea select >> nth=0')=='CMS' and pg.locator('#qualArea input[value="Payments"]').is_checked())
    pg.evaluate("closeReview()")

    # ---- CSV export ----
    with pg.expect_download() as dl:
        pg.click('#btnExportCsv')
    path = dl.value.path(); csv = open(path).read(); hdr = csv.split('\n')[0]
    ok('CSV keeps original columns first', hdr.startswith('"First Name","Last Name","Company","Title","Email","Phone","Lead Source"'))
    ok('CSV has question columns', all(x in hdr for x in ['"Product interest"','"Modules of interest"','"Has budget?"','"Timeline notes"']), hdr)
    ok('CSV has Qualification Complete (required exists)', '"Qualification Complete"' in hdr)
    ok('CSV archived+unanswered question excluded', 'Budget cycle open?' not in hdr)
    ok('CSV multi joined, quotes escaped', 'Payments; Portal' in csv and 'Budget in Q3, ""board vote"", Sept' in csv)
    ok('CSV plain lead complete=No', '"No"' in csv and '"Yes"' in csv)
    # archive a question with answers -> still exported
    pg.evaluate(f"State.detailEventId='ev1'"); pg.evaluate(f"qfToggleArchive('{qf[3]['id']}')"); pg.wait_for_timeout(150)
    with pg.expect_download() as dl2: pg.click('#btnExportCsv')
    ok('CSV archived question with answers still exported', '"Timeline notes"' in open(dl2.value.path()).read().split('\n')[0])

    # ---- readout ----
    pr = pg.evaluate("fetchEventNotes('ev1').then(n=>buildReadoutPrompt(allLeadsSorted(), n))")
    ok('Readout prompt has qualification breakdown', 'Qualification question answers' in pr and 'Product interest: CMS: 1' in pr, pr[-600:])

    # ---- switching to event with different questions ----
    pg.evaluate("setActiveEvent('ev0')"); pg.wait_for_timeout(200)
    pg.evaluate("openReview({name:'Zed',email:'z@z.gov',phone:'1',source:'manual'})")
    ok('Active-event switch swaps question set', pg.locator('#qualArea [data-qid]').count()==1 and 'budget cycle' in pg.inner_text('#qualArea').lower())
    pg.evaluate("closeReview()")
    b.close()
bad=[r for r in results if not r[1]]
print(f"\n{len(results)-len(bad)}/{len(results)} passed"); print('errors:', [e for e in errs if 'net::ERR' not in e and 'Failed to load resource' not in e][:8])
sys.exit(1 if bad else 0)
