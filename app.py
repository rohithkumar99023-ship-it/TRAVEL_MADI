import os, secrets
from datetime import date
from functools import wraps
from flask import Flask, request, session, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
app=Flask(__name__, template_folder=".")
app.secret_key=os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE')=='1')
url=os.getenv('DATABASE_URL','sqlite:///travelmadi.db').replace('postgres://','postgresql+psycopg://',1)
if url.startswith('postgresql://'): url=url.replace('postgresql://','postgresql+psycopg://',1)
engine=create_engine(url,pool_pre_ping=True)
def query(conn,s,**p): return conn.execute(text(s),p)
def rows(r): return [dict(x) for x in r.mappings()]
def init():
 with engine.begin() as c:
  for s in open(os.path.join(os.path.dirname(__file__),'schema.sql')).read().split(';'):
   if s.strip(): c.execute(text(s))
  if not query(c,'SELECT id FROM services LIMIT 1').first():
   for kind,name,origin,dest,price,capacity in [('Flights','IndiGo 6E 214','Bengaluru','Delhi',5499,30),('Flights','Air India AI 804','Bengaluru','Mumbai',4899,24),('Hotels','The Imperial Retreat','Goa','Goa',6999,12),('Hotels','The Royal Palace','Jaipur','Jaipur',8999,10),('Trains','Shatabdi Express','Bengaluru','Chennai',1299,40),('Buses','Luxury Volvo','Bengaluru','Goa',1499,30),('Cabs','Executive Sedan','Bengaluru','Mysuru',2999,8),('Packages','Maldives Escape','Bengaluru','Maldives',45999,10),('Packages','Kashmir Retreat','Delhi','Srinagar',24999,15)]:
    query(c,'INSERT INTO services VALUES (:id,:kind,:name,:origin,:dest,:price,:capacity,1)',id=secrets.token_hex(8),kind=kind,name=name,origin=origin,dest=dest,price=price,capacity=capacity)
  for dest,name,price in [('Dubai','Marina Grand Hotel',11999),('Singapore','Bayview Retreat',13999),('Mumbai','Harbour Signature Hotel',7999),('Kochi','Backwater Heritage Resort',6499)]:
   sid='hotel-'+dest.lower()
   query(c,'INSERT INTO services VALUES (:id,:k,:n,:o,:d,:p,:c,1) ON CONFLICT DO NOTHING',id=sid,k='Hotels',n=name,o=dest,d=dest,p=price,c=15)
  # Stable, clearly simulated catalog; existing reservations remain intact.
  for i,(k,n,o,d,p,cap) in enumerate([["Flights","Skyline Air · Economy · 07:30","Bengaluru","Delhi",3499,24],["Flights","Vista Airways · Economy · 18:20","Bengaluru","Delhi",4299,16],["Trains","Intercity Express · AC Chair Car · 06:10","Bengaluru","Delhi",699,40],["Trains","Night Express · AC 3 Tier · 21:15","Bengaluru","Delhi",1099,0],["Buses","Premium Volvo AC Sleeper · 22:00","Bengaluru","Delhi",899,28],["Buses","Express AC Seater · 08:00","Bengaluru","Delhi",599,12],["Flights","Skyline Air · Economy · 07:30","Bengaluru","Mumbai",3672,24],["Flights","Vista Airways · Economy · 18:20","Bengaluru","Mumbai",4472,16],["Trains","Intercity Express · AC Chair Car · 06:10","Bengaluru","Mumbai",872,40],["Trains","Night Express · AC 3 Tier · 21:15","Bengaluru","Mumbai",1272,0],["Buses","Premium Volvo AC Sleeper · 22:00","Bengaluru","Mumbai",1072,28],["Buses","Express AC Seater · 08:00","Bengaluru","Mumbai",772,12],["Flights","Skyline Air · Economy · 07:30","Bengaluru","Goa",3845,24],["Flights","Vista Airways · Economy · 18:20","Bengaluru","Goa",4645,16],["Trains","Intercity Express · AC Chair Car · 06:10","Bengaluru","Goa",1045,40],["Trains","Night Express · AC 3 Tier · 21:15","Bengaluru","Goa",1445,0],["Buses","Premium Volvo AC Sleeper · 22:00","Bengaluru","Goa",1245,28],["Buses","Express AC Seater · 08:00","Bengaluru","Goa",945,12],["Flights","Skyline Air · Economy · 07:30","Bengaluru","Chennai",4018,24],["Flights","Vista Airways · Economy · 18:20","Bengaluru","Chennai",4818,16],["Trains","Intercity Express · AC Chair Car · 06:10","Bengaluru","Chennai",1218,40],["Trains","Night Express · AC 3 Tier · 21:15","Bengaluru","Chennai",1618,0],["Buses","Premium Volvo AC Sleeper · 22:00","Bengaluru","Chennai",1418,28],["Buses","Express AC Seater · 08:00","Bengaluru","Chennai",1118,12],["Flights","Skyline Air · Economy · 07:30","Bengaluru","Hyderabad",4191,24],["Flights","Vista Airways · Economy · 18:20","Bengaluru","Hyderabad",4991,16],["Trains","Intercity Express · AC Chair Car · 06:10","Bengaluru","Hyderabad",1391,40],["Trains","Night Express · AC 3 Tier · 21:15","Bengaluru","Hyderabad",1791,0],["Buses","Premium Volvo AC Sleeper · 22:00","Bengaluru","Hyderabad",1591,28],["Buses","Express AC Seater · 08:00","Bengaluru","Hyderabad",1291,12],["Flights","Skyline Air · Economy · 07:30","Bengaluru","Kochi",4364,24],["Flights","Vista Airways · Economy · 18:20","Bengaluru","Kochi",5164,16],["Trains","Intercity Express · AC Chair Car · 06:10","Bengaluru","Kochi",1564,40],["Trains","Night Express · AC 3 Tier · 21:15","Bengaluru","Kochi",1964,0],["Buses","Premium Volvo AC Sleeper · 22:00","Bengaluru","Kochi",1764,28],["Buses","Express AC Seater · 08:00","Bengaluru","Kochi",1464,12],["Flights","Skyline Air · Economy · 07:30","Delhi","Mumbai",4537,24],["Flights","Vista Airways · Economy · 18:20","Delhi","Mumbai",5337,16],["Trains","Intercity Express · AC Chair Car · 06:10","Delhi","Mumbai",1737,40],["Trains","Night Express · AC 3 Tier · 21:15","Delhi","Mumbai",2137,0],["Buses","Premium Volvo AC Sleeper · 22:00","Delhi","Mumbai",1937,28],["Buses","Express AC Seater · 08:00","Delhi","Mumbai",1637,12],["Flights","Skyline Air · Economy · 07:30","Mumbai","Goa",3510,24],["Flights","Vista Airways · Economy · 18:20","Mumbai","Goa",4310,16],["Trains","Intercity Express · AC Chair Car · 06:10","Mumbai","Goa",710,40],["Trains","Night Express · AC 3 Tier · 21:15","Mumbai","Goa",1110,0],["Buses","Premium Volvo AC Sleeper · 22:00","Mumbai","Goa",910,28],["Buses","Express AC Seater · 08:00","Mumbai","Goa",610,12],["Flights","Skyline Air · Economy · 07:30","Delhi","Jaipur",3683,24],["Flights","Vista Airways · Economy · 18:20","Delhi","Jaipur",4483,16],["Trains","Intercity Express · AC Chair Car · 06:10","Delhi","Jaipur",883,40],["Trains","Night Express · AC 3 Tier · 21:15","Delhi","Jaipur",1283,0],["Buses","Premium Volvo AC Sleeper · 22:00","Delhi","Jaipur",1083,28],["Buses","Express AC Seater · 08:00","Delhi","Jaipur",783,12],["Flights","Skyline Air · Economy · 07:30","Chennai","Hyderabad",3856,24],["Flights","Vista Airways · Economy · 18:20","Chennai","Hyderabad",4656,16],["Trains","Intercity Express · AC Chair Car · 06:10","Chennai","Hyderabad",1056,40],["Trains","Night Express · AC 3 Tier · 21:15","Chennai","Hyderabad",1456,0],["Buses","Premium Volvo AC Sleeper · 22:00","Chennai","Hyderabad",1256,28],["Buses","Express AC Seater · 08:00","Chennai","Hyderabad",956,12],["Trains","Intercity Express · AC Chair Car · 06:10","Bengaluru","Mysuru",1229,40],["Trains","Night Express · AC 3 Tier · 21:15","Bengaluru","Mysuru",1629,0],["Buses","Premium Volvo AC Sleeper · 22:00","Bengaluru","Mysuru",1429,28],["Buses","Express AC Seater · 08:00","Bengaluru","Mysuru",1129,12],["Hotels","Signature City Retreat · Deluxe room","Goa","Goa",2299,12],["Hotels","Grand Horizon Resort · Breakfast included","Goa","Goa",4599,8],["Packages","Goa Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Goa",9999,12],["Hotels","Signature City Retreat · Deluxe room","Jaipur","Jaipur",2579,12],["Hotels","Grand Horizon Resort · Breakfast included","Jaipur","Jaipur",4939,8],["Packages","Jaipur Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Jaipur",12099,12],["Hotels","Signature City Retreat · Deluxe room","Kochi","Kochi",2859,12],["Hotels","Grand Horizon Resort · Breakfast included","Kochi","Kochi",5279,8],["Packages","Kochi Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Kochi",14199,12],["Hotels","Signature City Retreat · Deluxe room","Mumbai","Mumbai",3139,12],["Hotels","Grand Horizon Resort · Breakfast included","Mumbai","Mumbai",5619,8],["Packages","Mumbai Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Mumbai",16299,12],["Hotels","Signature City Retreat · Deluxe room","Delhi","Delhi",3419,12],["Hotels","Grand Horizon Resort · Breakfast included","Delhi","Delhi",5959,8],["Packages","Delhi Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Delhi",18399,12],["Hotels","Signature City Retreat · Deluxe room","Chennai","Chennai",3699,12],["Hotels","Grand Horizon Resort · Breakfast included","Chennai","Chennai",6299,8],["Packages","Chennai Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Chennai",20499,12],["Hotels","Signature City Retreat · Deluxe room","Mysuru","Mysuru",3979,12],["Hotels","Grand Horizon Resort · Breakfast included","Mysuru","Mysuru",6639,8],["Packages","Mysuru Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Mysuru",22599,12],["Hotels","Signature City Retreat · Deluxe room","Hyderabad","Hyderabad",4259,12],["Hotels","Grand Horizon Resort · Breakfast included","Hyderabad","Hyderabad",6979,8],["Packages","Hyderabad Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Hyderabad",24699,12],["Hotels","Signature City Retreat · Deluxe room","Manali","Manali",4539,12],["Hotels","Grand Horizon Resort · Breakfast included","Manali","Manali",7319,8],["Packages","Manali Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Manali",26799,12],["Hotels","Signature City Retreat · Deluxe room","Ooty","Ooty",4819,12],["Hotels","Grand Horizon Resort · Breakfast included","Ooty","Ooty",7659,8],["Packages","Ooty Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Ooty",28899,12],["Hotels","Signature City Retreat · Deluxe room","Dubai","Dubai",5099,12],["Hotels","Grand Horizon Resort · Breakfast included","Dubai","Dubai",7999,8],["Packages","Dubai Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Dubai",30999,12],["Hotels","Signature City Retreat · Deluxe room","Singapore","Singapore",5379,12],["Hotels","Grand Horizon Resort · Breakfast included","Singapore","Singapore",8339,8],["Packages","Singapore Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Singapore",33099,12],["Hotels","Signature City Retreat · Deluxe room","Maldives","Maldives",5659,12],["Hotels","Grand Horizon Resort · Breakfast included","Maldives","Maldives",8679,8],["Packages","Maldives Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Maldives",35199,12],["Hotels","Signature City Retreat · Deluxe room","Kashmir","Kashmir",5939,12],["Hotels","Grand Horizon Resort · Breakfast included","Kashmir","Kashmir",9019,8],["Packages","Kashmir Escape · 4 days / 3 nights · Stay + transfers + sightseeing","Bengaluru","Kashmir",37299,12]]):
   query(c,'INSERT INTO services VALUES (:id,:k,:n,:o,:d,:p,:cap,:active) ON CONFLICT DO NOTHING',id='demo-v2-'+str(i),k=k,n=n,o=o,d=d,p=p,cap=max(cap,1),active=1)
  email=os.getenv('ADMIN_EMAIL','').lower(); password=os.getenv('ADMIN_PASSWORD','')
  if email and len(password)>=10 and not query(c,'SELECT id FROM users WHERE email=:e',e=email).first():
   query(c,'INSERT INTO users VALUES (:id,:n,:e,:p,:r)',id=secrets.token_hex(8),n='Administrator',e=email,p=generate_password_hash(password),r='admin')
@app.cli.command('init-db')
def init_cmd(): init(); print('Database initialized')
def fail(msg,status=400): return jsonify(error=msg),status
def auth(admin=False):
 def deco(fn):
  @wraps(fn)
  def wrap(*a,**kw):
   if not session.get('uid'): return fail('Please sign in',401)
   if admin and session.get('role')!='admin': return fail('Forbidden',403)
   return fn(*a,**kw)
  return wrap
 return deco
@app.before_request
def csrf():
 if request.method in ('POST','PATCH','DELETE') and (not session.get('csrf') or request.headers.get('X-CSRF-Token')!=session['csrf']): return fail('Invalid CSRF token',403)
@app.get('/')
def home(): return render_template('index.html')
@app.get('/api/session')
def state():
 session.setdefault('csrf',secrets.token_hex(24)); return jsonify(csrf=session['csrf'],user=session.get('name'),role=session.get('role'))
@app.post('/api/register')
def register():
 d=request.get_json() or {}; n=str(d.get('name','')).strip(); e=str(d.get('email','')).strip().lower(); p=str(d.get('password',''))
 if not n or len(n)>100 or '@' not in e or len(e)>254 or not 8<=len(p)<=128: return fail('Enter valid details and a password of 8–128 characters')
 try:
  with engine.begin() as c: query(c,'INSERT INTO users VALUES (:id,:n,:e,:p,:r)',id=secrets.token_hex(8),n=n,e=e,p=generate_password_hash(p),r='customer')
 except IntegrityError: return fail('Email already registered',409)
 return jsonify(ok=True),201
@app.post('/api/login')
def login():
 d=request.get_json() or {}
 with engine.connect() as c: u=query(c,'SELECT * FROM users WHERE email=:e',e=str(d.get('email','')).strip().lower()).mappings().first()
 if not u or not check_password_hash(u['password'],str(d.get('password',''))): return fail('Invalid credentials',401)
 session.clear(); session.update(uid=u['id'],name=u['name'],role=u['role'],csrf=secrets.token_hex(24)); return state()
@app.post('/api/logout')
def logout(): session.clear(); return state()
@app.get('/api/services')
def services():
 with engine.connect() as c: return jsonify(rows(query(c,'SELECT * FROM services WHERE active=1 ORDER BY kind,price')))
@app.get('/api/availability')
def availability():
 with engine.connect() as c:
  r=query(c,"SELECT s.capacity-COALESCE(SUM(b.quantity),0) AS available FROM services s LEFT JOIN bookings b ON b.service_id=s.id AND b.travel_date=:d AND b.status='confirmed' WHERE s.id=:id AND s.active=1 GROUP BY s.capacity",d=request.args.get('date',''),id=request.args.get('id','')).scalar()
 return jsonify(available=r or 0)
@app.post('/api/bookings')
@auth()
def book():
 d=request.get_json() or {}
 try:
  qty=int(d['quantity']); day=date.fromisoformat(d['date']); assert 1<=qty<=10 and day>=date.today()
 except (KeyError,ValueError,TypeError,AssertionError): return fail('Invalid date or quantity')
 passenger=str(d.get('passenger','')).strip()
 if not passenger or len(passenger)>150: return fail('Enter passenger name')
 with engine.begin() as c:
  # Lock inventory row before checking capacity, serializing concurrent bookings.
  query(c,'UPDATE services SET capacity=capacity WHERE id=:id',id=d.get('id'))
  s=query(c,'SELECT * FROM services WHERE id=:id AND active=1',id=d.get('id')).mappings().first()
  if not s: return fail('Service unavailable',404)
  used=query(c,"SELECT COALESCE(SUM(quantity),0) FROM bookings WHERE service_id=:id AND travel_date=:d AND status='confirmed'",id=s['id'],d=day.isoformat()).scalar()
  if used+qty>s['capacity']: return fail('Not enough availability',409)
  bid='TM-'+secrets.token_hex(5).upper(); total=s['price']*qty
  query(c,'INSERT INTO bookings VALUES (:id,:u,:s,:d,:q,:p,:t,:status)',id=bid,u=session['uid'],s=s['id'],d=day.isoformat(),q=qty,p=passenger,t=total,status='confirmed')
  query(c,'INSERT INTO payments VALUES (:id,:b,:a,:s)',id=secrets.token_hex(8),b=bid,a=total,s='demo_paid')
 return jsonify(id=bid,total=total),201
@app.get('/api/bookings')
@auth()
def bookings():
 with engine.connect() as c: return jsonify(rows(query(c,'SELECT b.*,s.name,s.kind,s.origin,s.destination FROM bookings b JOIN services s ON s.id=b.service_id WHERE b.user_id=:u ORDER BY b.travel_date',u=session['uid'])))
@app.post('/api/bookings/<bid>/cancel')
@auth()
def cancel(bid):
 with engine.begin() as c:
  r=query(c,"UPDATE bookings SET status='cancelled' WHERE id=:id AND user_id=:u AND status='confirmed'",id=bid,u=session['uid'])
  if not r.rowcount: return fail('Booking not found or already cancelled',404)
  query(c,"UPDATE payments SET status='demo_refunded' WHERE booking_id=:id",id=bid)
 return jsonify(ok=True)
@app.get('/api/admin')
@auth(True)
def admin():
 with engine.connect() as c: return jsonify(users=rows(query(c,'SELECT id,name,email,role FROM users')),bookings=rows(query(c,'SELECT b.*,s.name FROM bookings b JOIN services s ON s.id=b.service_id')),services=rows(query(c,'SELECT * FROM services')))
@app.post('/api/admin/services')
@auth(True)
def add():
 d=request.get_json() or {}
 try:
  p=int(d['price']); cap=int(d['capacity']); assert p>0 and cap>0 and d['kind'] in ['Flights','Hotels','Trains','Buses','Cabs','Packages']; assert all(str(d[k]).strip() for k in ['name','origin','destination'])
 except (KeyError,ValueError,TypeError,AssertionError): return fail('Invalid service')
 with engine.begin() as c: query(c,'INSERT INTO services VALUES (:id,:k,:n,:o,:d,:p,:c,1)',id=secrets.token_hex(8),k=d['kind'],n=d['name'],o=d['origin'],d=d['destination'],p=p,c=cap)
 return jsonify(ok=True),201
@app.patch('/api/admin/services/<sid>')
@auth(True)
def edit(sid):
 d=request.get_json() or {}
 try: p=int(d['price']); assert p>0; active=int(bool(d['active']))
 except (KeyError,ValueError,TypeError,AssertionError): return fail('Invalid update')
 with engine.begin() as c:
  if not query(c,'UPDATE services SET price=:p,active=:a WHERE id=:id',p=p,a=active,id=sid).rowcount: return fail('Not found',404)
 return jsonify(ok=True)
@app.get('/api/wishlist')
@auth()
def wishlist():
 with engine.connect() as c: return jsonify(rows(query(c,'SELECT s.* FROM services s JOIN wishlist w ON w.service_id=s.id WHERE w.user_id=:u',u=session['uid'])))
@app.post('/api/wishlist/<sid>')
@auth()
def toggle_wishlist(sid):
 with engine.begin() as c:
  if not query(c,'SELECT id FROM services WHERE id=:id',id=sid).first(): return fail('Service not found',404)
  r=query(c,'DELETE FROM wishlist WHERE user_id=:u AND service_id=:s',u=session['uid'],s=sid)
  if r.rowcount: return jsonify(saved=False)
  query(c,'INSERT INTO wishlist (user_id,service_id) VALUES (:u,:s) ON CONFLICT DO NOTHING',u=session['uid'],s=sid)
 return jsonify(saved=True)
@app.get('/api/destinations/saved')
@auth()
def saved_destinations():
 with engine.connect() as c: return jsonify([r[0] for r in query(c,'SELECT destination FROM saved_destinations WHERE user_id=:u',u=session['uid'])])
@app.post('/api/destinations/saved/<name>')
@auth()
def save_destination(name):
 if name not in ('Goa','Dubai','Singapore','Jaipur','Mumbai','Kochi'): return fail('Unknown destination',404)
 with engine.begin() as c:
  r=query(c,'DELETE FROM saved_destinations WHERE user_id=:u AND destination=:d',u=session['uid'],d=name)
  if r.rowcount: return jsonify(saved=False)
  query(c,'INSERT INTO saved_destinations VALUES (:u,:d) ON CONFLICT DO NOTHING',u=session['uid'],d=name)
 return jsonify(saved=True)
from upgrade import install
install(app,engine,query,rows,auth,fail)
if __name__=='__main__': init(); app.run(debug=False)
