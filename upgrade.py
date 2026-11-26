from datetime import datetime, timedelta
import json, urllib.request, urllib.parse, urllib.error, re
from flask import Response

def install(app, engine, query, rows, auth, fail):
 from flask import request, session, jsonify
 import os, secrets
 def provider(params):
  key=os.getenv('SERPAPI_KEY','').strip()
  label='Flight' if params.get('engine')=='google_flights' else 'Hotel'
  if not key: raise ValueError('Live pricing is not configured: missing SERPAPI_KEY')
  params.update(api_key=key,currency='INR',hl='en',gl='in')
  try:
   with urllib.request.urlopen('https://serpapi.com/search.json?'+urllib.parse.urlencode(params),timeout=25) as r: data=json.load(r)
  except urllib.error.HTTPError as e:
   app.logger.warning('%s provider HTTP status %s',label,e.code)
   if e.code in (401,403): raise ValueError(label+' provider authentication failed; check API key')
   if e.code==429: raise ValueError(label+' provider rate limit or quota reached')
   if e.code==400: raise ValueError(label+' provider rejected search parameters; check airport codes and dates')
   raise ValueError(label+' provider returned HTTP '+str(e.code))
  except (urllib.error.URLError,TimeoutError,OSError,ValueError):
   app.logger.warning('%s provider connection or response failed',label)
   raise ValueError(label+' provider unavailable; try again later')
  if data.get('error'):
   app.logger.warning('%s provider returned an error response',label)
   raise ValueError(label+' provider could not complete this search; check search inputs and SerpApi dashboard')
  return data
 @app.post('/api/live')
 @auth()
 def live():
  d=request.get_json() or {}
  try:
   start=datetime.strptime(d['date'],'%Y-%m-%d').date(); nights=int(d['nights']); people=int(d['people']); origin=d['origin'].upper().strip(); dest=d['destination'].upper().strip(); city=d['city'].strip()
   if start<datetime.now().date() or not 1<=nights<=30 or not 1<=people<=6 or not re.fullmatch('[A-Z]{3}',origin) or not re.fullmatch('[A-Z]{3}',dest) or origin==dest or not 1<=len(city)<=80: raise ValueError('Check dates, airport codes and travellers')
   end=start+timedelta(days=nights)
   f=provider(dict(engine='google_flights',departure_id=origin,arrival_id=dest,outbound_date=str(start),type=2,adults=people))
   h=provider(dict(engine='google_hotels',q='Hotels in '+city,check_in_date=str(start),check_out_date=str(end),adults=people))
   flights=[]; hotels=[]
   for x in (f.get('best_flights',[])+f.get('other_flights',[]))[:12]:
    if isinstance(x.get('price'),(int,float)) and x['price']>0:
     flights.append(dict(name=' / '.join(y.get('airline','Flight')+' '+y.get('flight_number','') for y in x.get('flights',[])),price=round(x['price']),details=str(x.get('total_duration','?'))+' min'))
   for x in h.get('properties',[])[:20]:
    p=x.get('total_rate',{}).get('extracted_lowest'); rate=x.get('rate_per_night',{}).get('extracted_lowest')
    if not isinstance(p,(int,float)) and isinstance(rate,(int,float)): p=rate*nights
    if isinstance(p,(int,float)) and p>0: hotels.append(dict(name=x.get('name','Hotel'),price=round(p),details=str(x.get('overall_rating','Unrated'))+' rating'))
   if not flights: return fail('No priced flights found for these airports and date',404)
   if not hotels: return fail('No priced hotels found for this city and stay',404)
   qid=secrets.token_hex(16); payload=dict(flights=flights,hotels=hotels,date=str(start),nights=nights,people=people,origin=origin,destination=dest,city=city)
   with engine.begin() as c: query(c,'INSERT INTO live_quotes VALUES (:id,:u,:p,:e)',id=qid,u=session['uid'],p=json.dumps(payload),e=int(datetime.now().timestamp())+900)
   return jsonify(id=qid,**payload)
  except (ValueError,KeyError,TypeError) as e: return fail(str(e))
 @app.post('/api/live/checkout')
 @auth()
 def checkout():
  d=request.get_json() or {}
  with engine.begin() as c:
   r=query(c,'SELECT * FROM live_quotes WHERE id=:id AND user_id=:u',id=d.get('id'),u=session['uid']).mappings().first()
   if not r or r['expires']<datetime.now().timestamp(): return fail('Quote expired; search again',409)
   try:
    p=json.loads(r['payload']); fi=int(d['flight']); hi=int(d['hotel']); assert 0<=fi<len(p['flights']) and 0<=hi<len(p['hotels']); f=p['flights'][fi]; h=p['hotels'][hi]
   except (ValueError,TypeError,KeyError,AssertionError): return fail('Select valid options')
   if not query(c,'DELETE FROM live_quotes WHERE id=:id',id=r['id']).rowcount: return fail('Quote already used',409)
   bid='TM-'+secrets.token_hex(5).upper(); total=f['price']+h['price']+199
   payload=dict(**p,flight=f,hotel=h,fee=199,total=total); payload.pop('flights'); payload.pop('hotels')
   query(c,'INSERT INTO live_trips VALUES (:id,:u,:p,:t,:s)',id=bid,u=session['uid'],p=json.dumps(payload),t=total,s='demo_paid')
  return jsonify(id=bid,total=total)
 @app.get('/api/profile')
 @auth()
 def profile():
  with engine.connect() as c:
   u=dict(query(c,'SELECT name,email,role FROM users WHERE id=:u',u=session['uid']).mappings().one()); trips=rows(query(c,'SELECT * FROM live_trips WHERE user_id=:u',u=session['uid'])); payments=rows(query(c,'SELECT p.* FROM payments p JOIN bookings b ON b.id=p.booking_id WHERE b.user_id=:u',u=session['uid']))
  for t in trips: t['payload']=json.loads(t['payload'])
  return jsonify(user=u,trips=trips,payments=payments)
 @app.post('/api/live/<bid>/cancel')
 @auth()
 def cancel_live(bid):
  with engine.begin() as c:
   if not query(c,"UPDATE live_trips SET status='demo_refunded' WHERE id=:id AND user_id=:u AND status='demo_paid'",id=bid,u=session['uid']).rowcount: return fail('Reservation not found',404)
  return jsonify(ok=True)
 @app.get('/api/invoice/<bid>')
 @auth()
 def invoice(bid):
  with engine.connect() as c:
   r=query(c,'SELECT * FROM live_trips WHERE id=:id AND user_id=:u',id=bid,u=session['uid']).mappings().first()
   if not r: r=query(c,'SELECT b.*,s.name,p.status AS payment_status FROM bookings b JOIN services s ON s.id=b.service_id JOIN payments p ON p.booking_id=b.id WHERE b.id=:id AND b.user_id=:u',id=bid,u=session['uid']).mappings().first()
   if not r: return fail('Not found',404)
   body='TRAVELMADI — DEMO INVOICE (not a tax invoice)\n'+ '\n'.join(f'{k}: {v}' for k,v in dict(r).items() if k not in ('user_id','payload'))
   if 'payload' in r: body+='\n'+json.dumps(json.loads(r['payload']),indent=2,ensure_ascii=False)
  return Response(body,mimetype='text/plain',headers={'Content-Disposition':f'attachment; filename="{bid}.txt"'})
