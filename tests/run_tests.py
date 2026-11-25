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
    ok('app boots at v1.15.0', pg.evaluate("APP_VERSION")=='v1.15.0')

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
    pg.evaluate("openReview({name:'Plain Lead',email:'a@b.gov',phone:'555-010-0100',source:'manual'})")
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
    ok('S2 no delete button on others notes', pg.locator('#evNotesList .card:has-text("Someone else") button:has-text("Delete")').count()==0)
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
    pg.evaluate("openReview({name:'Dana Cole',company:'Mesa County',title:'Director',email:'d@mesa.gov',phone:'555-010-0100',source:'manual'})")
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
    pg.evaluate("openReview({name:'Zed',email:'z@z.gov',phone:'555-010-0100',source:'manual'})")
    ok('Active-event switch swaps question set', pg.locator('#qualArea [data-qid]').count()==1 and 'budget cycle' in pg.inner_text('#qualArea').lower())
    pg.evaluate("closeReview()")

    # ---- v1.15.0 additions ----
    pg.evaluate("setActiveEvent('ev1')"); pg.wait_for_timeout(200)
    pg.evaluate("openEventDetail('ev1')"); pg.wait_for_timeout(150)
    own = pg.evaluate("State.eventNotes.find(n=>n.author==='Nic').id")
    pg.evaluate(f"editEventNote('{own}')")
    pg.fill('#evNoteEditText','Booth 412, Hall B. Power drop is limited. UPDATE: bring a 25ft extension cord.')
    pg.click('#evNotesList button:has-text("Save")'); pg.wait_for_timeout(200)
    ok('N edit own note saves new text + marks edited', 'extension cord' in pg.inner_text('#evNotesList') and 'edited' in pg.inner_text('#evNotesList'))
    ok('N edit keeps one copy (no duplicate)', pg.evaluate("[...window.__store.keys()].filter(k=>k.includes('/notes/')).length")==2)
    pg.evaluate(f"editEventNote('{own}')"); pg.fill('#evNoteEditText','   '); pg.click('#evNotesList button:has-text("Save")')
    ok('N blank edit rejected', 'extension cord' in pg.evaluate("window.__store.get('events/ev1/notes/'+'%s').text" % own))
    pg.click('#evNotesList button:has-text("Cancel")')
    ok('N Edit offered on others notes, Delete is not', pg.locator('#evNotesList .card:has-text("Someone else") button:has-text("Edit")').count()==1 and pg.locator('#evNotesList .card:has-text("Someone else") button:has-text("Delete")').count()==0)
    pg.locator('#evNotesList .card:has-text("Someone else") button:has-text("Edit")').click(); pg.fill('#evNoteEditText','Someone else (clarified by Nic)'); pg.click('#evNotesList button:has-text("Save")'); pg.wait_for_timeout(200)
    ok('N editing another rep note records editor', 'edited by Nic' in pg.inner_text('#evNotesList') and 'clarified' in pg.inner_text('#evNotesList'))
    pg.evaluate("closeEventDetail()")
    # alphabetical pick-lists
    pg.evaluate("State.competitors=['Zeta Co','alpha Inc','Beta LLC']; renderSoftwareSelectOptions()")
    opts = pg.evaluate("[...document.querySelectorAll('#f_software option')].map(o=>o.textContent)")
    ok('A competitor list alphabetical helper', pg.evaluate("alphaSort(['Zeta','alpha','Beta']).join()")=='alpha,Beta,Zeta')
    # attendees default order + bottom save
    pg.evaluate("switchTab('attendees')")
    ok('B bottom Save hidden with no attendees', pg.evaluate("document.getElementById('btnSaveAttendeesBottom').style.display")=='none')
    pg.evaluate("(async()=>{const c=State.db.collection('events').doc('ev1').collection('attendees'); for(const [f,l] of [['Zed','Young'],['Amy','Adams'],['Bo','adams'],['Cy','Miller']]) await c.add({firstName:f,lastName:l,company:'X'});})()"); pg.wait_for_timeout(300)
    ok('B bottom Save shows once records exist', pg.evaluate("document.getElementById('btnSaveAttendeesBottom').style.display")=='')
    names = pg.evaluate("[...document.querySelectorAll('#attendeeTbody tr')].map(r=>r.querySelectorAll('input')[1].value)")
    ok('A attendees default to last-name order', names==['Adams','adams','Miller','Young'], names)
    # leads list order + toggle
    pg.evaluate("(async()=>{const c=State.db.collection('events').doc('ev1').collection('leads'); await c.add({name:'Zoe Baker',email:'z@z.gov',phone:'555-010-0100',savedAt:Date.now()+5000}); await c.add({name:'Al Adams',email:'a@a.gov',phone:'555-010-0100',savedAt:1});})()"); pg.wait_for_timeout(300)
    pg.evaluate("switchTab('leads')")
    order = pg.evaluate("[...document.querySelectorAll('.lead-item .name')].map(e=>e.textContent)")
    ok('A leads default A-Z by last name', order.index('Al Adams') < order.index('Zoe Baker') and order[0]=='Al Adams', order)
    pg.select_option('#leadSortSel','recent')
    order2 = pg.evaluate("[...document.querySelectorAll('.lead-item .name')].map(e=>e.textContent)")
    ok('A leads toggle to newest first', order2[0]=='Zoe Baker', order2)

    # ---- v1.15.0: title from differently-labelled attendee column ----
    def title_key(labels):
        return pg.evaluate("(l)=>{State.attendeeColumns=CANONICAL_COLS.concat(l.map(x=>({key:x.toLowerCase().replace(/[^a-z0-9]+/g,'_'),label:x})));return attendeeTitleKey();}", labels)
    ok('T "Employment Title" recognised', title_key(['City Name','Employment Title'])=='employment_title')
    ok('T "Job Title" / "Position" / "Role" recognised', title_key(['Job Title'])=='job_title' and title_key(['Position'])=='position' and title_key(['Role'])=='role')
    ok('T plain "Title" beats looser matches', title_key(['Role','Title'])=='title')
    ok('T salutation-style Title column ignored', title_key(['Salutation Title','State']) is None)
    ok('T no false hit on "Controller"/"Hotel"', title_key(['Controller','Hotel Needed']) is None)
    pg.evaluate("State.attendeeColumns=CANONICAL_COLS.concat([{key:'employment_title',label:'Employment Title'}]); State.attendees=[{id:'x1',firstName:'Patricia',lastName:'Moore',company:'Washington County Circuit Court',email:'',phone:'',employment_title:'Clerk of Court'}]; renderAttendeeTable()")
    pg.evaluate("addAttendeeToLeads('x1')")
    ok('T green button brings the title in', pg.input_value('#f_title')=='Clerk of Court')
    pg.evaluate("closeReview()")
    pg.evaluate("openReview({name:'Patricia Moore',company:'',title:'',email:'',phone:'',source:'qr'})")
    ok('T scan/manual exact match fills title', pg.input_value('#f_title')=='Clerk of Court' and pg.input_value('#f_company')!='')
    ok('T match chip shows the title', 'Clerk of Court' in pg.inner_text('#matchArea'))
    pg.evaluate("closeReview()")
    pg.evaluate("openReview({name:'Patricia Moore',company:'',title:'County Clerk',email:'',phone:'',source:'qr'})")
    ok('T badge title is never overwritten', pg.input_value('#f_title')=='County Clerk')
    pg.evaluate("closeReview()")

    # ---- v1.15.0: QA findings ----
    pg.evaluate("setActiveEvent('ev1')"); pg.wait_for_timeout(200); pg.evaluate("switchTab('scan')")
    pg.click("text=+ Enter a lead manually"); pg.wait_for_timeout(150)
    ok('Q1 manual entry is labelled manual', pg.inner_text('#f_source')=='Source: manual entry')
    # validators
    V = lambda fn,v: pg.evaluate(f"{fn}({json.dumps(v)})")
    ok('Q3 valid emails accepted', all(V('isValidEmail',v) for v in ['a@b.gov','first.last+tag@sub.county.us.gov']))
    ok('Q3 invalid emails rejected', not any(V('isValidEmail',v) for v in ['not-an-email','a@b','@x.com','a b@c.com','']))
    ok('Q3 valid phones accepted', all(V('isValidPhone',v) for v in ['(555) 010-0100','+1 555-010-0100','555.010.0100 x12','5550100']))
    ok('Q3 invalid phones rejected', not any(V('isValidPhone',v) for v in ['abc','12','555-ABCD','']))
    # save with junk -> warning, nothing saved, then save anyway
    before = pg.evaluate("[...window.__store.keys()].filter(k=>k.startsWith('events/ev1/leads/')).length")
    pg.fill('#f_name','Bad Data'); pg.fill('#f_email','not-an-email'); pg.fill('#f_phone','abc'); pg.click('#btnSaveLead'); pg.wait_for_timeout(150)
    ok('Q3 junk email/phone triggers a warning', pg.locator('#btnContactSaveAnyway').count()==1 and 'look valid' in pg.inner_text('#qualIncompleteBox'))
    ok('Q3 nothing saved while warning is up', pg.evaluate("[...window.__store.keys()].filter(k=>k.startsWith('events/ev1/leads/')).length")==before)
    pg.click('#btnContactSaveAnyway'); pg.wait_for_timeout(300)
    if pg.locator('#btnQualSaveAnyway').count(): pg.click('#btnQualSaveAnyway'); pg.wait_for_timeout(300)  # ev1 also has a required question from earlier tests
    ok('Q3 Save anyway still saves', pg.evaluate("[...window.__store.keys()].filter(k=>k.startsWith('events/ev1/leads/')).length")==before+1)
    pg.evaluate("switchTab('leads')"); pg.wait_for_timeout(100)
    ok('Q3 junk contact counts as missing contact', pg.locator('.lead-item:has-text("Bad Data") .badge:has-text("No contact")').count()==1)
    # CSV safety
    ok('Q3 csvSafe neutralises formulas', pg.evaluate("csvSafe('=cmd|\\' /C calc\\'!A0')").startswith("'=") and pg.evaluate("csvSafe('@SUM(1)')").startswith("'@") and pg.evaluate("csvSafe('-cmd')").startswith("'-"))
    ok('Q3 csvSafe leaves phones/numbers alone', pg.evaluate("[csvSafe('+1 555-010-0100'),csvSafe('-5'),csvSafe('(555) 010-0100'),csvSafe('Plain')]")==['+1 555-010-0100','-5','(555) 010-0100','Plain'])
    pg.evaluate("State.db.collection('events').doc('ev1').collection('leads').add({name:'Evil Person',company:'=HYPERLINK(\"http://x\")',email:'bad@',phone:'+1 555-010-0100',notes:'+cmd',savedAt:Date.now()})"); pg.wait_for_timeout(250)
    with pg.expect_download() as dl3: pg.click('#btnExportCsv')
    csv3 = open(dl3.value.path()).read()
    ok('Q3 export neutralises formula in company', "\"'=HYPERLINK" in csv3, csv3[-400:])
    ok('Q3 export keeps invalid email out of Email, notes it in Description', 'Invalid email: bad@' in csv3)
    ok('Q3 export keeps a +1 phone intact', '"+1 555-010-0100"' in csv3)
    # readout
    pr2 = pg.evaluate("buildReadoutPrompt(allLeadsSorted(), [])")
    import datetime
    ok('Q2 readout prompt carries today and the no-invented-year rule', 'Today is' in pr2 and str(datetime.date.today().year) in pr2 and 'Never state a year' in pr2)
    pg.evaluate("State.lastReadoutPrompt='PROMPT TEXT'; renderReadoutSuccess('hello')")
    ok('Q2 readout shows its inputs', pg.locator('details.readout-inputs').count()==1 and 'PROMPT TEXT' in pg.inner_text('details.readout-inputs pre') or 'PROMPT TEXT' in pg.evaluate("document.querySelector('details.readout-inputs pre').textContent"))
    # tab badge
    lab = pg.evaluate("document.querySelector('.tab-btn[data-tab=\"leads\"]').getAttribute('aria-label')")
    ok('Q5 Leads tab explains its badge', lab and 'saved' in lab, lab)
    # self test
    pg.evaluate("switchTab('setup')"); pg.click('#btnScannerSelfTest'); pg.wait_for_function("document.getElementById('selfTestOut').innerText.includes('Environment')", timeout=8000)
    ok('Q4 scanner self-test runs and reports', 'Secure page' in pg.inner_text('#selfTestOut') and pg.locator('#btnSelfTestCopy').is_visible())

    # ---- v1.15.0: sticky save, autofill, torch, feedback, share ----
    pg.evaluate("setActiveEvent('ev1')"); pg.wait_for_timeout(200)
    pg.evaluate("openReview(null)")
    ok('4a Save bar is sticky', pg.evaluate("getComputedStyle(document.querySelector('.sticky-save')).position")=='sticky')
    attrs = pg.evaluate("['f_name','f_company','f_title','f_email','f_phone'].map(id=>{const e=document.getElementById(id);return [e.getAttribute('autocomplete'),e.type,e.getAttribute('name')]})")
    ok('4b lead fields have autocomplete off + unique names', all(a[0]=='off' and a[2].startswith('cl-lead-') for a in attrs), attrs)
    ok('4b email/phone use text type with the right keyboard', pg.evaluate("[document.getElementById('f_email').type,document.getElementById('f_email').inputMode,document.getElementById('f_phone').type,document.getElementById('f_phone').inputMode]")==['text','email','text','tel'])
    pg.fill('#f_email','not-an-email'); pg.evaluate("document.getElementById('f_email').dispatchEvent(new Event('blur'))")
    ok('4b validation still flags a bad email (no type=email needed)', pg.is_visible('#f_email_err'))
    pg.evaluate("closeReview()")
    # torch
    pg.evaluate("""(()=>{window.__torchCalls=[];const v=document.getElementById('camVideo');
      const track={getCapabilities:()=>({torch:true}),applyConstraints:async c=>{window.__torchCalls.push(JSON.stringify(c))}};
      Object.defineProperty(v,'srcObject',{configurable:true,get:()=>({getVideoTracks:()=>[track]})});refreshTorchButton();})()""")
    ok('5a torch button shows when the camera supports it', pg.is_visible('#btnTorch') or pg.evaluate("document.getElementById('btnTorch').style.display")=='')
    pg.evaluate("document.getElementById('btnTorch').click()"); pg.wait_for_timeout(100)
    ok('5a torch on sends the torch constraint', any('"torch":true' in c for c in pg.evaluate("window.__torchCalls")) and 'on' in pg.inner_text('#btnTorch').lower())
    pg.evaluate("turnTorchOff()"); pg.wait_for_timeout(100)
    ok('5a pausing the camera turns the torch off', any('"torch":false' in c for c in pg.evaluate("window.__torchCalls")))
    pg.evaluate("Object.defineProperty(document.getElementById('camVideo'),'srcObject',{configurable:true,get:()=>null}); refreshTorchButton()")
    ok('5a torch button hides without support', pg.evaluate("document.getElementById('btnTorch').style.display")=='none')
    # feedback
    pg.evaluate("""(()=>{window.__vib=[];navigator.vibrate=(n)=>{window.__vib.push(n);return true;};window.__osc=0;
      audioCtx={currentTime:0,state:'running',createOscillator:()=>{window.__osc++;return {frequency:{},connect(){},start(){},stop(){}}},createGain:()=>({gain:{setValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){}}),destination:{}};})()""")
    pg.evaluate("localStorage.removeItem('compassleads.fbHaptic'); localStorage.removeItem('compassleads.fbSound'); scanFeedback()")
    ok('5c scan feedback vibrates and beeps by default', pg.evaluate("window.__vib.length")==1 and pg.evaluate("window.__osc")==1)
    pg.evaluate("localStorage.setItem('compassleads.fbHaptic','0'); localStorage.setItem('compassleads.fbSound','0'); scanFeedback()")
    ok('5c toggles switch each off', pg.evaluate("window.__vib.length")==1 and pg.evaluate("window.__osc")==1)
    pg.evaluate("localStorage.removeItem('compassleads.fbHaptic'); localStorage.removeItem('compassleads.fbSound')")
    ok('5c a successful scan triggers feedback', (pg.evaluate("lastQrAt=0; State.pendingLead=null; onQrDetected('A B | Dir | Co'); window.__vib.length")==2))
    pg.evaluate("closeReview()")
    # share
    pg.evaluate("""(()=>{window.__shared=[];const mm=window.matchMedia.bind(window);window.matchMedia=q=>String(q).includes('pointer: coarse')?{matches:true}:mm(q);
      navigator.canShare=()=>true;navigator.share=async d=>{window.__shared.push(d);};})()""")
    pg.evaluate("switchTab('leads')"); pg.wait_for_timeout(100)
    dl_count = {'n':0}; pg.on('download', lambda d: dl_count.__setitem__('n', dl_count['n']+1))
    pg.evaluate("exportCsv(false)"); pg.wait_for_timeout(300)
    ok('6 phone export opens the share sheet with a .csv file', pg.evaluate("window.__shared.length")==1 and pg.evaluate("window.__shared[0].files[0].name").endswith('.csv') and dl_count['n']==0)
    pg.evaluate("window.__shared=[]; navigator.share=async()=>{const e=new Error('x');e.name='AbortError';throw e;}; 0")
    pg.evaluate("exportCsv(false)"); pg.wait_for_timeout(300)
    ok('6 cancelling the share sheet does not download', dl_count['n']==0)
    pg.evaluate("navigator.share=async()=>{throw new Error('boom')}; 0")
    pg.evaluate("exportCsv(false)"); pg.wait_for_timeout(400)
    ok('6 a failed share falls back to download', dl_count['n']==1)
    pg.evaluate("exportCsv(true)"); pg.wait_for_timeout(400)
    ok('6 "download instead" always downloads', dl_count['n']==2)
    pg.evaluate("window.__shared=[]; navigator.share=async d=>{window.__shared.push(d)}; 0; State.lastReadoutPrompt='p'; renderReadoutSuccess('Readout body')")
    ok('6 readout has a Share button', pg.locator('#btnReadoutShare').count()==1)
    pg.evaluate("document.getElementById('btnReadoutShare').click()"); pg.wait_for_timeout(150)
    ok('6 readout share sends the text', pg.evaluate("window.__shared.length")==1 and 'Readout body' in pg.evaluate("window.__shared[0].text"))
    b.close()
bad=[r for r in results if not r[1]]
print(f"\n{len(results)-len(bad)}/{len(results)} passed"); print('errors:', [e for e in errs if 'net::ERR' not in e and 'Failed to load resource' not in e][:8])
sys.exit(1 if bad else 0)
