from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(30))
    role = db.Column(db.String(20), default="user")  # user / admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tickets = db.relationship("Ticket", backref="user", lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    @property
    def is_admin(self):
        return self.role == "admin"


class Stadium(db.Model):
    __tablename__ = "stadiums"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255), default="stadium_default.jpg")

    events = db.relationship("Event", backref="stadium", lazy=True, cascade="all, delete-orphan")


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    stadium_id = db.Column(db.Integer, db.ForeignKey("stadiums.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    image = db.Column(db.String(255), default="event_default.jpg")
    description = db.Column(db.Text)
    base_price = db.Column(db.Float, default=1500.0)

    seats = db.relationship("Seat", backref="event", lazy=True, cascade="all, delete-orphan")
    tickets = db.relationship("Ticket", backref="event", lazy=True, cascade="all, delete-orphan")

    @property
    def available_seats_count(self):
        return Seat.query.filter_by(event_id=self.id, status="disponible").count()

    @property
    def total_seats_count(self):
        return Seat.query.filter_by(event_id=self.id).count()


class Seat(db.Model):
    __tablename__ = "seats"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    section = db.Column(db.String(20), nullable=False)
    row = db.Column(db.String(10), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="disponible")  # disponible / reserve
    price = db.Column(db.Float, nullable=False)

    ticket = db.relationship("Ticket", backref="seat", uselist=False)

    @property
    def label(self):
        return f"{self.section}-{self.row}{self.number}"


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey("seats.id"), nullable=False, unique=True)
    qr_code = db.Column(db.String(255))
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="valide")  # valide / utilise / annule
    code = db.Column(db.String(64), unique=True)

    parking = db.relationship("Parking", backref="ticket", uselist=False, cascade="all, delete-orphan")


class Parking(db.Model):
    __tablename__ = "parking"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False, unique=True)
    parking_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="reserve")  # reserve / utilise


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
