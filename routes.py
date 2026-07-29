# -*- coding: utf-8 -*-
from functools import wraps
from datetime import datetime

from flask import (Blueprint, render_template, redirect, url_for, request,
                    session, flash, send_from_directory, abort)

from models import db, User, Stadium, Event, Seat, Ticket, Parking, Notification
from forms import RegisterForm, LoginForm, ProfileForm, StadiumForm, EventForm, SeatForm
from utils import generate_ticket_code, generate_qr_code, generate_ticket_pdf
from config import Config

main_bp = Blueprint("main", __name__)


# ----------------------------------------------------------------------
# Décorateurs d'authentification
# ----------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Veuillez vous connecter pour accéder à cette page.", "warning")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Veuillez vous connecter.", "warning")
            return redirect(url_for("main.login"))
        if session.get("role") != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)


@main_bp.app_context_processor
def inject_globals():
    user = current_user()
    unread_count = 0
    if user:
        unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return dict(current_user=user, unread_notifications=unread_count)


# ----------------------------------------------------------------------
# Pages publiques
# ----------------------------------------------------------------------
@main_bp.route("/")
def index():
    query = request.args.get("q", "").strip()
    events_query = Event.query.order_by(Event.date.asc())
    if query:
        events_query = events_query.filter(Event.title.ilike(f"%{query}%"))
    events = events_query.limit(8).all()
    upcoming = Event.query.filter(Event.date >= datetime.utcnow()).order_by(Event.date.asc()).limit(4).all()
    stadiums = Stadium.query.all()
    return render_template("index.html", events=events, stadiums=stadiums, upcoming=upcoming, query=query)


@main_bp.route("/events/<int:event_id>")
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template("event_detail.html", event=event)


# ----------------------------------------------------------------------
# Authentification
# ----------------------------------------------------------------------
@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing:
            flash("Un compte existe déjà avec cet email.", "danger")
        else:
            user = User(fullname=form.fullname.data.strip(),
                        email=form.email.data.lower().strip(),
                        phone=form.phone.data.strip() if form.phone.data else None,
                        role="user")
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Compte créé avec succès. Vous pouvez vous connecter.", "success")
            return redirect(url_for("main.login"))
    return render_template("register.html", form=form)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            session["user_id"] = user.id
            session["role"] = user.role
            session["fullname"] = user.fullname
            flash(f"Bienvenue, {user.fullname} !", "success")
            if user.is_admin:
                return redirect(url_for("main.admin_dashboard"))
            return redirect(url_for("main.dashboard"))
        flash("Email ou mot de passe incorrect.", "danger")
    return render_template("login.html", form=form)


@main_bp.route("/logout")
def logout():
    session.clear()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("main.index"))


# ----------------------------------------------------------------------
# Espace utilisateur
# ----------------------------------------------------------------------
@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    tickets = Ticket.query.filter_by(user_id=user.id).order_by(Ticket.purchase_date.desc()).limit(5).all()
    notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(5).all()
    upcoming_events = Event.query.filter(Event.date >= datetime.utcnow()).order_by(Event.date.asc()).limit(4).all()
    return render_template("dashboard.html", tickets=tickets, notifications=notifications, upcoming_events=upcoming_events)


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    form = ProfileForm(obj=user)
    if form.validate_on_submit():
        user.fullname = form.fullname.data.strip()
        user.phone = form.phone.data.strip() if form.phone.data else None
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        session["fullname"] = user.fullname
        flash("Profil mis à jour avec succès.", "success")
        return redirect(url_for("main.profile"))
    return render_template("profile.html", form=form, user=user)


# ----------------------------------------------------------------------
# Réservation (choix de siège + paiement simulé)
# ----------------------------------------------------------------------
@main_bp.route("/booking/<int:event_id>", methods=["GET"])
@login_required
def booking(event_id):
    event = Event.query.get_or_404(event_id)
    selected_seat_id = request.args.get("seat", type=int)
    selected_seat = None
    if selected_seat_id:
        selected_seat = Seat.query.filter_by(id=selected_seat_id, event_id=event_id).first()
        if not selected_seat or selected_seat.status != "disponible":
            flash("Cette place n'est plus disponible, veuillez en choisir une autre.", "warning")
            return redirect(url_for("main.booking", event_id=event_id))

    seats = Seat.query.filter_by(event_id=event_id).order_by(Seat.section, Seat.row, Seat.number).all()
    sections = {}
    for s in seats:
        sections.setdefault(s.section, []).append(s)

    return render_template("booking.html", event=event, sections=sections, selected_seat=selected_seat)


@main_bp.route("/booking/<int:event_id>/pay", methods=["POST"])
@login_required
def booking_pay(event_id):
    event = Event.query.get_or_404(event_id)
    seat_id = request.form.get("seat_id", type=int)
    seat = Seat.query.filter_by(id=seat_id, event_id=event_id).first()

    if not seat or seat.status != "disponible":
        flash("Cette place n'est plus disponible.", "danger")
        return redirect(url_for("main.booking", event_id=event_id))

    user = current_user()

    # --- Paiement simulé : clic sur "Payer" = réservation validée ---
    seat.status = "reserve"

    code = generate_ticket_code()
    qr_filename = generate_qr_code(code)

    ticket = Ticket(user_id=user.id, event_id=event.id, seat_id=seat.id,
                     qr_code=qr_filename, status="valide", code=code)
    db.session.add(ticket)
    db.session.flush()

    # --- Parking automatique ---
    import random
    zone = random.choice(["A", "B", "C"])
    parking = Parking(ticket_id=ticket.id, parking_number=f"Parking {zone}-{random.randint(1, 99)}",
                       status="reserve")
    db.session.add(parking)

    # --- Notifications ---
    db.session.add(Notification(user_id=user.id,
                                 message=f"Votre réservation pour « {event.title} » est confirmée."))
    db.session.add(Notification(user_id=user.id,
                                 message=f"Votre place {seat.label} est réservée."))
    db.session.add(Notification(user_id=user.id,
                                 message=f"Une place de {parking.parking_number} vous a été attribuée."))

    db.session.commit()

    flash("Paiement effectué avec succès ! Votre billet est prêt.", "success")
    return redirect(url_for("main.ticket_detail", ticket_id=ticket.id))


# ----------------------------------------------------------------------
# Mes billets
# ----------------------------------------------------------------------
@main_bp.route("/tickets")
@login_required
def tickets():
    user = current_user()
    user_tickets = Ticket.query.filter_by(user_id=user.id).order_by(Ticket.purchase_date.desc()).all()
    return render_template("tickets.html", tickets=user_tickets)


@main_bp.route("/tickets/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    user = current_user()
    if ticket.user_id != user.id and not user.is_admin:
        abort(403)
    return render_template("ticket_detail.html", ticket=ticket)


@main_bp.route("/tickets/<int:ticket_id>/download")
@login_required
def ticket_download(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    user = current_user()
    if ticket.user_id != user.id and not user.is_admin:
        abort(403)

    filename = generate_ticket_pdf(ticket, ticket.user, ticket.event, ticket.event.stadium, ticket.seat, ticket.parking)
    return send_from_directory(Config.TICKETS_PDF_FOLDER, filename, as_attachment=True)


@main_bp.route("/tickets/<int:ticket_id>/verify-identity", methods=["POST"])
@login_required
def verify_identity(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    user = current_user()
    if ticket.user_id != user.id:
        abort(403)
    flash("Identité vérifiée avec succès (Face ID simulé).", "success")
    return redirect(url_for("main.ticket_detail", ticket_id=ticket.id))


@main_bp.route("/tickets/<int:ticket_id>/scan-nfc", methods=["POST"])
@login_required
def scan_nfc(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    user = current_user()
    if ticket.user_id != user.id and not user.is_admin:
        abort(403)

    if ticket.status == "utilise":
        flash("Ce billet a déjà été scanné et validé à l'entrée.", "info")
    else:
        ticket.status = "utilise"
        db.session.add(Notification(user_id=ticket.user_id,
                                     message=f"Billet {ticket.code} validé à l'entrée du stade."))
        db.session.commit()
        flash("Billet validé avec succès (NFC simulé). Accès autorisé.", "success")
    return redirect(url_for("main.ticket_detail", ticket_id=ticket.id))


# ----------------------------------------------------------------------
# Notifications
# ----------------------------------------------------------------------
@main_bp.route("/notifications")
@login_required
def notifications():
    user = current_user()
    user_notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    for n in user_notifications:
        n.is_read = True
    db.session.commit()
    return render_template("notifications.html", notifications=user_notifications)


# ----------------------------------------------------------------------
# Chatbot (simulé)
# ----------------------------------------------------------------------
@main_bp.route("/chatbot")
@login_required
def chatbot():
    return render_template("chatbot.html")


# ----------------------------------------------------------------------
# Administration
# ----------------------------------------------------------------------
@main_bp.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "users": User.query.filter_by(role="user").count(),
        "tickets": Ticket.query.count(),
        "events": Event.query.count(),
        "available_seats": Seat.query.filter_by(status="disponible").count(),
    }
    recent_tickets = Ticket.query.order_by(Ticket.purchase_date.desc()).limit(6).all()
    return render_template("admin/dashboard.html", stats=stats, recent_tickets=recent_tickets)


@main_bp.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@main_bp.route("/admin/users/<int:user_id>/toggle-role", methods=["POST"])
@admin_required
def admin_toggle_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session.get("user_id"):
        flash("Vous ne pouvez pas modifier votre propre rôle.", "warning")
    else:
        user.role = "admin" if user.role == "user" else "user"
        db.session.commit()
        flash(f"Rôle de {user.fullname} mis à jour.", "success")
    return redirect(url_for("main.admin_users"))


@main_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session.get("user_id"):
        flash("Vous ne pouvez pas supprimer votre propre compte.", "warning")
    else:
        db.session.delete(user)
        db.session.commit()
        flash("Utilisateur supprimé.", "success")
    return redirect(url_for("main.admin_users"))


# --- Stades (CRUD) ---
@main_bp.route("/admin/stadiums", methods=["GET", "POST"])
@admin_required
def admin_stadiums():
    form = StadiumForm()
    if form.validate_on_submit():
        stadium = Stadium(name=form.name.data.strip(), city=form.city.data.strip(),
                           capacity=form.capacity.data)
        db.session.add(stadium)
        db.session.commit()
        flash("Stade ajouté avec succès.", "success")
        return redirect(url_for("main.admin_stadiums"))
    stadiums = Stadium.query.all()
    return render_template("admin/stadiums.html", form=form, stadiums=stadiums)


@main_bp.route("/admin/stadiums/<int:stadium_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_stadium(stadium_id):
    stadium = Stadium.query.get_or_404(stadium_id)
    form = StadiumForm(obj=stadium)
    if form.validate_on_submit():
        stadium.name = form.name.data.strip()
        stadium.city = form.city.data.strip()
        stadium.capacity = form.capacity.data
        db.session.commit()
        flash("Stade mis à jour.", "success")
        return redirect(url_for("main.admin_stadiums"))
    return render_template("admin/stadium_edit.html", form=form, stadium=stadium)


@main_bp.route("/admin/stadiums/<int:stadium_id>/delete", methods=["POST"])
@admin_required
def admin_delete_stadium(stadium_id):
    stadium = Stadium.query.get_or_404(stadium_id)
    db.session.delete(stadium)
    db.session.commit()
    flash("Stade supprimé.", "success")
    return redirect(url_for("main.admin_stadiums"))


# --- Événements (CRUD) ---
@main_bp.route("/admin/events", methods=["GET", "POST"])
@admin_required
def admin_events():
    form = EventForm()
    form.stadium_id.choices = [(s.id, s.name) for s in Stadium.query.all()]
    if form.validate_on_submit():
        try:
            event_date = datetime.strptime(form.date.data.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Format de date invalide. Utilisez AAAA-MM-JJ HH:MM.", "danger")
            return redirect(url_for("main.admin_events"))

        event = Event(title=form.title.data.strip(), stadium_id=form.stadium_id.data,
                      date=event_date, description=form.description.data,
                      base_price=form.base_price.data)
        db.session.add(event)
        db.session.commit()
        flash("Événement créé avec succès.", "success")
        return redirect(url_for("main.admin_events"))

    events = Event.query.order_by(Event.date.asc()).all()
    return render_template("admin/events.html", form=form, events=events)


@main_bp.route("/admin/events/<int:event_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = EventForm(obj=event)
    form.stadium_id.choices = [(s.id, s.name) for s in Stadium.query.all()]
    if request.method == "GET":
        form.date.data = event.date.strftime("%Y-%m-%d %H:%M")

    if form.validate_on_submit():
        try:
            event_date = datetime.strptime(form.date.data.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Format de date invalide. Utilisez AAAA-MM-JJ HH:MM.", "danger")
            return redirect(url_for("main.admin_edit_event", event_id=event.id))

        event.title = form.title.data.strip()
        event.stadium_id = form.stadium_id.data
        event.date = event_date
        event.description = form.description.data
        event.base_price = form.base_price.data
        db.session.commit()
        flash("Événement mis à jour.", "success")
        return redirect(url_for("main.admin_events"))

    return render_template("admin/event_edit.html", form=form, event=event)


@main_bp.route("/admin/events/<int:event_id>/delete", methods=["POST"])
@admin_required
def admin_delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Événement supprimé.", "success")
    return redirect(url_for("main.admin_events"))


# --- Places (CRUD par événement) ---
@main_bp.route("/admin/events/<int:event_id>/seats", methods=["GET", "POST"])
@admin_required
def admin_seats(event_id):
    event = Event.query.get_or_404(event_id)
    form = SeatForm()
    if form.validate_on_submit():
        seat = Seat(event_id=event.id, section=form.section.data.strip().upper(),
                    row=form.row.data.strip(), number=form.number.data,
                    price=form.price.data, status=form.status.data)
        db.session.add(seat)
        db.session.commit()
        flash("Place ajoutée.", "success")
        return redirect(url_for("main.admin_seats", event_id=event.id))

    seats = Seat.query.filter_by(event_id=event.id).order_by(Seat.section, Seat.row, Seat.number).all()
    return render_template("admin/seats.html", form=form, event=event, seats=seats)


@main_bp.route("/admin/seats/<int:seat_id>/delete", methods=["POST"])
@admin_required
def admin_delete_seat(seat_id):
    seat = Seat.query.get_or_404(seat_id)
    event_id = seat.event_id
    if seat.status == "reserve":
        flash("Impossible de supprimer une place déjà réservée.", "warning")
    else:
        db.session.delete(seat)
        db.session.commit()
        flash("Place supprimée.", "success")
    return redirect(url_for("main.admin_seats", event_id=event_id))


@main_bp.route("/admin/seats/<int:seat_id>/toggle-status", methods=["POST"])
@admin_required
def admin_toggle_seat(seat_id):
    seat = Seat.query.get_or_404(seat_id)
    if seat.ticket:
        flash("Cette place est déjà liée à un billet vendu.", "warning")
    else:
        seat.status = "reserve" if seat.status == "disponible" else "disponible"
        db.session.commit()
        flash("Statut de la place mis à jour.", "success")
    return redirect(url_for("main.admin_seats", event_id=seat.event_id))


# --- Billets vendus / Parking (lecture) ---
@main_bp.route("/admin/tickets")
@admin_required
def admin_tickets():
    all_tickets = Ticket.query.order_by(Ticket.purchase_date.desc()).all()
    return render_template("admin/tickets.html", tickets=all_tickets)


@main_bp.route("/admin/parking")
@admin_required
def admin_parking():
    all_parking = Parking.query.join(Ticket).order_by(Ticket.purchase_date.desc()).all()
    return render_template("admin/parking.html", parkings=all_parking)


# ----------------------------------------------------------------------
# Erreurs
# ----------------------------------------------------------------------
@main_bp.app_errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403


@main_bp.app_errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404
