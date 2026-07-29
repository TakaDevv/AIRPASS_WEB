import random
from datetime import datetime, timedelta

from models import db, User, Stadium, Event, Seat, Ticket, Parking, Notification
from utils import generate_ticket_code, generate_qr_code

SECTIONS = ["A", "B", "C", "D"]

STADIUMS_DATA = [
    {"name": "Stade Olympique 5 Juillet", "city": "Alger", "capacity": 60000},
    {"name": "Stade Mustapha Tchaker", "city": "Blida", "capacity": 25000},
    {"name": "Stade Miloud Hadefi", "city": "Oran", "capacity": 40000},
]

EVENTS_DATA = [
    "USM Alger vs MC Alger",
    "CR Belouizdad vs ES Setif",
    "JS Kabylie vs USM Bel Abbes",
    "MC Oran vs ASO Chlef",
    "Algerie vs Nigeria",
    "Algerie vs Cameroun",
    "CR Belouizdad vs Union Sportive Monastirienne",
    "Finale Coupe d'Algerie",
]

FIRST_NAMES = ["Yacine", "Amine", "Sofiane", "Riyad", "Nadia", "Amina", "Sarah", "Karim",
               "Walid", "Djamel", "Lina", "Meriem", "Bilal", "Hicham", "Farid", "Nassim",
               "Imene", "Rania", "Adel", "Oussama"]
LAST_NAMES = ["Benali", "Boudiaf", "Cherif", "Djaballah", "Haddad", "Kaci", "Larbi",
              "Mansouri", "Nacer", "Ouahab", "Rahmani", "Saidi", "Tazi", "Yahiaoui",
              "Ziani", "Bouazza", "Cherfi", "Djilali", "Ferhat", "Guerroudj"]


def seed_database():
    """Peuple la base avec des donnees de demonstration realistes."""
    if User.query.first():
        return  # deja peuplee

    # --- Admin ---
    admin = User(fullname="Administrateur Airpass", email="admin@airpass.dz",
                 phone="0550000000", role="admin")
    admin.set_password("admin123")
    db.session.add(admin)

    # --- Stades ---
    stadiums = []
    for s in STADIUMS_DATA:
        stadium = Stadium(name=s["name"], city=s["city"], capacity=s["capacity"],
                           image="stadium_default.jpg")
        db.session.add(stadium)
        stadiums.append(stadium)
    db.session.flush()

    # --- Evenements ---
    events = []
    for i, title in enumerate(EVENTS_DATA):
        event_date = datetime.utcnow() + timedelta(days=random.randint(3, 60))
        event = Event(
            title=title,
            stadium_id=stadiums[i % len(stadiums)].id,
            date=event_date,
            image="event_default.jpg",
            description=(f"Match officiel « {title} » comptant pour la saison en cours. "
                          "Ambiance garantie, places limitees, reservez des maintenant."),
            base_price=random.choice([1200.0, 1500.0, 2000.0, 3000.0]),
        )
        db.session.add(event)
        events.append(event)
    db.session.flush()

    # --- Places (500 par evenement) ---
    for event in events:
        seats_per_section = 500 // len(SECTIONS)
        for section in SECTIONS:
            rows = 25
            per_row = seats_per_section // rows
            for r in range(1, rows + 1):
                for n in range(1, per_row + 1):
                    price = event.base_price + (50.0 if section in ("A", "B") else 0.0)
                    seat = Seat(event_id=event.id, section=section, row=str(r),
                                number=n, status="disponible", price=price)
                    db.session.add(seat)
    db.session.flush()

    # --- Utilisateurs (20) ---
    users = []
    for i in range(20):
        fullname = f"{FIRST_NAMES[i]} {LAST_NAMES[i]}"
        email = f"{FIRST_NAMES[i].lower()}.{LAST_NAMES[i].lower()}@example.com"
        user = User(fullname=fullname, email=email,
                    phone=f"05{random.randint(10000000, 99999999)}", role="user")
        user.set_password("password123")
        db.session.add(user)
        users.append(user)
    db.session.flush()

    # --- Billets (100) avec parking + QR code ---
    created_tickets = 0
    attempts = 0
    while created_tickets < 100 and attempts < 2000:
        attempts += 1
        event = random.choice(events)
        available_seat = Seat.query.filter_by(event_id=event.id, status="disponible").first()
        if not available_seat:
            continue

        user = random.choice(users)
        available_seat.status = "reserve"

        code = generate_ticket_code()
        qr_filename = generate_qr_code(code)

        ticket = Ticket(user_id=user.id, event_id=event.id, seat_id=available_seat.id,
                         qr_code=qr_filename, status="valide", code=code,
                         purchase_date=datetime.utcnow() - timedelta(days=random.randint(0, 20)))
        db.session.add(ticket)
        db.session.flush()

        parking_zone = random.choice(["A", "B", "C"])
        parking = Parking(ticket_id=ticket.id,
                           parking_number=f"Parking {parking_zone}-{random.randint(1, 99)}",
                           status="reserve")
        db.session.add(parking)

        notif1 = Notification(user_id=user.id,
                               message=f"Votre reservation pour « {event.title} » est confirmee.")
        notif2 = Notification(user_id=user.id,
                               message=f"Votre place {available_seat.label} est reservee.")
        db.session.add(notif1)
        db.session.add(notif2)

        created_tickets += 1

    db.session.commit()
    print(f"[AIRPASS] Donnees de demonstration creees : "
          f"{len(stadiums)} stades, {len(events)} evenements, "
          f"{len(users)} utilisateurs, {created_tickets} billets.")
