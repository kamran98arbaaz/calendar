from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Booking, Hall, User
from wtforms import StringField, TextAreaField, SelectField, SubmitField, DateField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from datetime import datetime, date, timezone, timedelta
import calendar
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

main = Blueprint('main', __name__)

# Define IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

class BookingForm(FlaskForm):
    client_name = StringField('Client Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    time_slot = SelectField('Time Slot', choices=[('day', 'Day'), ('night', 'Night')], validators=[DataRequired()])
    submit = SubmitField('Book')

@main.route('/')
def index():
    halls = Hall.query.all()
    # Booking counter logic
    ar_garden = Hall.query.filter_by(name='AR Garden').first()
    diamond_palace = Hall.query.filter_by(name='Diamond Palace').first()
    ar_count = Booking.query.filter_by(hall_id=ar_garden.id if ar_garden else 0).count() if ar_garden else 0
    diamond_count = Booking.query.filter_by(hall_id=diamond_palace.id if diamond_palace else 0).count() if diamond_palace else 0
    return render_template('index.html', halls=halls, ar_count=ar_count, diamond_count=diamond_count)

@main.route('/hall/<int:hall_id>')
def hall(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    today = datetime.now(IST).date()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    cal = calendar.monthcalendar(year, month)
    # Calculate start and end dates for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    all_bookings = Booking.query.filter(Booking.hall_id == hall_id, Booking.date >= start_date, Booking.date < end_date).all()
    booking_dict = {(str(b.date), b.time_slot): b for b in all_bookings}
    month_name = calendar.month_name[month]
    total = len(all_bookings)
    confirmed = sum(1 for b in all_bookings if b.status == 'confirmed')
    pending = sum(1 for b in all_bookings if b.status == 'pending')
    day = sum(1 for b in all_bookings if b.time_slot == 'day')
    night = sum(1 for b in all_bookings if b.time_slot == 'night')
    return render_template('hall.html', hall=hall, cal=cal, year=year, month=month, month_name=month_name, booking_dict=booking_dict, total=total, confirmed=confirmed, pending=pending, day=day, night=night)

@main.route('/book/<int:hall_id>/<int:year>/<int:month>/<int:day>', methods=['GET', 'POST'])
@login_required
def book(hall_id, year, month, day):
    hall = Hall.query.get_or_404(hall_id)
    selected_date = date(year, month, day)
    form = BookingForm()
    if request.method == 'GET':
        slot = request.args.get('slot')
        if slot:
            form.time_slot.data = slot
    if form.validate_on_submit():
        # Check if slot is available
        existing = Booking.query.filter_by(hall_id=hall_id, date=selected_date, time_slot=form.time_slot.data).first()
        if existing:
            flash('This slot is already booked')
            return redirect(url_for('main.hall', hall_id=hall_id))
        bid = Booking.generate_bid()
        booking = Booking(
            bid=bid,
            hall_id=hall_id,
            date=selected_date,
            time_slot=form.time_slot.data,
            client_name=form.client_name.data,
            phone=form.phone.data,
            address=form.address.data,
            user_id=current_user.id,
            created_at=datetime.now(IST)
        )
        db.session.add(booking)
        db.session.commit()
        flash('Booking created successfully')
        return redirect(url_for('main.booking_detail', booking_id=booking.id))
    return render_template('book.html', form=form, hall=hall, date=selected_date)

@main.route('/booking/<int:booking_id>')
@login_required
def booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('main.index'))
    return render_template('booking_detail.html', booking=booking)

@main.route('/edit_booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('main.index'))
    form = BookingForm(obj=booking)
    if form.validate_on_submit():
        booking.client_name = form.client_name.data
        booking.phone = form.phone.data
        booking.address = form.address.data
        db.session.commit()
        flash('Booking updated')
        return redirect(url_for('main.booking_detail', booking_id=booking.id))
    return render_template('edit_booking.html', form=form, booking=booking)

@main.route('/confirm_booking/<int:booking_id>', methods=['POST'])
@login_required
def confirm_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('main.index'))
    booking.status = 'confirmed'
    booking.confirmed_at = datetime.now(IST)
    db.session.commit()
    flash('Booking confirmed')
    return redirect(url_for('main.booking_detail', booking_id=booking.id))

@main.route('/delete_booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        password = request.form.get('password')
        if not current_user.check_password(password):
            flash('Invalid password')
            return redirect(url_for('main.delete_booking', booking_id=booking_id))
        db.session.delete(booking)
        db.session.commit()
        flash('Booking deleted')
        return redirect(url_for('main.index'))
    return render_template('delete_booking.html', booking=booking)


@main.route('/hall/<int:hall_id>/bookings/total')
@login_required
def hall_bookings_total(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    today = datetime.now(IST).date()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    bookings = Booking.query.filter(Booking.hall_id == hall_id, Booking.date >= start_date, Booking.date < end_date).all()
    return render_template('booking_list.html', hall=hall, bookings=bookings, title='Total Bookings', year=year, month=month)

@main.route('/hall/<int:hall_id>/bookings/confirmed')
@login_required
def hall_bookings_confirmed(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    today = datetime.now(IST).date()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    bookings = Booking.query.filter(Booking.hall_id == hall_id, Booking.status == 'confirmed', Booking.date >= start_date, Booking.date < end_date).all()
    return render_template('booking_list.html', hall=hall, bookings=bookings, title='Confirmed Bookings', year=year, month=month)

@main.route('/hall/<int:hall_id>/bookings/pending')
@login_required
def hall_bookings_pending(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    today = datetime.now(IST).date()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    bookings = Booking.query.filter(Booking.hall_id == hall_id, Booking.status == 'pending', Booking.date >= start_date, Booking.date < end_date).all()
    return render_template('booking_list.html', hall=hall, bookings=bookings, title='Pending Bookings', year=year, month=month)

@main.route('/hall/<int:hall_id>/bookings/day')
@login_required
def hall_bookings_day(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    today = datetime.now(IST).date()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    bookings = Booking.query.filter(Booking.hall_id == hall_id, Booking.time_slot == 'day', Booking.date >= start_date, Booking.date < end_date).all()
    return render_template('booking_list.html', hall=hall, bookings=bookings, title='Day Bookings', year=year, month=month)

@main.route('/hall/<int:hall_id>/bookings/night')
@login_required
def hall_bookings_night(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    today = datetime.now(IST).date()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    bookings = Booking.query.filter(Booking.hall_id == hall_id, Booking.time_slot == 'night', Booking.date >= start_date, Booking.date < end_date).all()
    return render_template('booking_list.html', hall=hall, bookings=bookings, title='Night Bookings', year=year, month=month)

@main.route('/print_receipt/<int:booking_id>')
@login_required
def print_receipt(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('main.index'))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, fontSize=18)
    normal_style = styles['Normal']

    elements = []

    # Title
    elements.append(Paragraph("Wedding Hall Booking Receipt", title_style))
    elements.append(Spacer(1, 12))

    # Booking Details
    data = [
        ['BID:', booking.bid],
        ['Hall:', booking.hall.name],
        ['Date:', booking.date.strftime('%d %b %Y')],
        ['Time Slot:', booking.time_slot.title()],
        ['Client Name:', booking.client_name],
        ['Phone:', booking.phone],
        ['Address:', booking.address],
        ['Status:', booking.status.title()],
        ['Booked on:', booking.created_at.strftime('%d %b %Y at %I:%M %p')],
    ]
    if booking.confirmed_at:
        data.append(['Confirmed on:', booking.confirmed_at.strftime('%d %b %Y at %I:%M %p')])

    table = Table(data, colWidths=[100, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    from flask import send_file
    return send_file(buffer, as_attachment=True, download_name=f'receipt_{booking.bid}.pdf', mimetype='application/pdf')

@main.route('/export_csv')
@login_required
def export_csv():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('main.index'))

    import csv
    from io import StringIO

    si = StringIO()
    writer = csv.writer(si)

    # Write header
    writer.writerow(['BID', 'Hall', 'Date', 'Time Slot', 'Client Name', 'Phone', 'Address', 'Status', 'Booked On', 'Confirmed On'])

    # Write data
    bookings = Booking.query.all()
    for booking in bookings:
        writer.writerow([
            booking.bid,
            booking.hall.name,
            booking.date.strftime('%d %b %Y'),
            booking.time_slot.title(),
            booking.client_name,
            booking.phone,
            booking.address,
            booking.status.title(),
            booking.created_at.strftime('%d %b %Y %H:%M') if booking.created_at else '',
            booking.confirmed_at.strftime('%d %b %Y %H:%M') if booking.confirmed_at else ''
        ])

    output = si.getvalue()
    si.close()

    from flask import Response
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=client_bookings.csv'}
    )

@main.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        query = request.form.get('query')
        bookings = Booking.query.filter(
            (Booking.bid.contains(query)) |
            (Booking.client_name.contains(query)) |
            (Booking.phone.contains(query))
        ).all()
        return render_template('search_results.html', bookings=bookings, query=query)
    return render_template('search.html')