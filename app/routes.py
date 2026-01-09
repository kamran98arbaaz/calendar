from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Booking, Hall, User, IST, current_ist, current_utc
from wtforms import StringField, TextAreaField, SelectField, SubmitField, DateField, FloatField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from datetime import date, timezone
import calendar
from sqlalchemy import func
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

main = Blueprint('main', __name__)

class BookingForm(FlaskForm):
    client_name = StringField('Client Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    time_slot = SelectField('Time Slot', choices=[('day', 'Day'), ('night', 'Night')], validators=[DataRequired()])
    advance_paid = FloatField('Advance Paid', default=0.0)
    balance = FloatField('Balance', default=0.0)
    total = FloatField('Total', default=0.0)
    submit = SubmitField('Book')

@main.route('/')
def index():
    halls = Hall.query.all()
    hall_dict = {h.name: h for h in halls}
    ar_garden = hall_dict.get('AR Garden')
    diamond_palace = hall_dict.get('Diamond Palace')

    # Get year and month from params, default to current
    today = current_ist().date()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)

    # Booking counter logic for selected month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # Optimized count query
    booking_counts = db.session.query(Booking.hall_id, func.count(Booking.id)).filter(Booking.date >= start_date, Booking.date < end_date).group_by(Booking.hall_id).all()
    count_dict = {hid: cnt for hid, cnt in booking_counts}
    ar_count = count_dict.get(ar_garden.id if ar_garden else 0, 0)
    diamond_count = count_dict.get(diamond_palace.id if diamond_palace else 0, 0)
    total_count = ar_count + diamond_count

    # Upcoming bookings for each hall - optimized
    hall_ids = [h.id for h in halls if h]
    upcoming = db.session.query(Booking).filter(Booking.date >= today, Booking.hall_id.in_(hall_ids)).order_by(Booking.date).limit(4).all()
    upcoming_ar = [b for b in upcoming if ar_garden and b.hall_id == ar_garden.id][:2]
    upcoming_diamond = [b for b in upcoming if diamond_palace and b.hall_id == diamond_palace.id][:2]

    # Bookings for mini calendar - optimized
    start_of_month = date(year, month, 1)
    end_of_month = date(year if month < 12 else year + 1, month % 12 + 1, 1)
    booking_dates_query = db.session.query(Booking.date).filter(Booking.date >= start_of_month, Booking.date < end_of_month).distinct().all()
    booking_dates = {d[0] for d in booking_dates_query}

    # Calculate prev and next
    prev_month = month - 1 if month > 1 else 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    return render_template('index.html', halls=halls, ar_count=ar_count, diamond_count=diamond_count, total_count=total_count, upcoming_ar=upcoming_ar, upcoming_diamond=upcoming_diamond, today=today, calendar=calendar, date=date, Booking=Booking, booking_dates=booking_dates, year=year, month=month, prev_year=prev_year, prev_month=prev_month, next_year=next_year, next_month=next_month, ar_garden=ar_garden, diamond_palace=diamond_palace)

@main.route('/hall/<int:hall_id>')
def hall(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    today = current_ist().date()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    cal = calendar.monthcalendar(year, month)
    # Calculate start and end dates for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    all_bookings = Booking.query.filter(Booking.hall_id == hall_id, Booking.date >= start_date, Booking.date < end_date).with_entities(Booking.id, Booking.date, Booking.time_slot).all()
    booking_dict = {(str(b.date), b.time_slot): b for b in all_bookings}
    month_name = calendar.month_name[month]
    total = Booking.query.filter(Booking.hall_id == hall_id, Booking.date >= start_date, Booking.date < end_date).count()
    confirmed = Booking.query.filter(Booking.hall_id == hall_id, Booking.date >= start_date, Booking.date < end_date, Booking.status == 'confirmed').count()
    pending = Booking.query.filter(Booking.hall_id == hall_id, Booking.date >= start_date, Booking.date < end_date, Booking.status == 'pending').count()
    day = Booking.query.filter(Booking.hall_id == hall_id, Booking.date >= start_date, Booking.date < end_date, Booking.time_slot == 'day').count()
    night = Booking.query.filter(Booking.hall_id == hall_id, Booking.date >= start_date, Booking.date < end_date, Booking.time_slot == 'night').count()
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
            created_at=current_utc(),
            advance_paid=form.advance_paid.data,
            balance=form.balance.data,
            total=form.total.data
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
    if current_user.role not in ['user', 'admin']:
        flash('Access denied')
        return redirect(url_for('main.index'))
    return render_template('booking_detail.html', booking=booking)

@main.route('/edit_booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if current_user.role not in ['user', 'admin']:
        flash('Access denied')
        return redirect(url_for('main.index'))
    form = BookingForm(obj=booking)
    if form.validate_on_submit():
        booking.client_name = form.client_name.data
        booking.phone = form.phone.data
        booking.address = form.address.data
        booking.advance_paid = form.advance_paid.data
        booking.balance = form.balance.data
        booking.total = form.total.data
        db.session.commit()
        flash('Booking updated')
        return redirect(url_for('main.booking_detail', booking_id=booking.id))
    return render_template('edit_booking.html', form=form, booking=booking)

@main.route('/confirm_booking/<int:booking_id>', methods=['POST'])
@login_required
def confirm_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if current_user.role not in ['user', 'admin']:
        flash('Access denied')
        return redirect(url_for('main.index'))
    booking.status = 'confirmed'
    booking.confirmed_at = current_utc()
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
    today = current_ist().date()
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
    today = current_ist().date()
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
    today = current_ist().date()
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
    today = current_ist().date()
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
    today = current_ist().date()
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
    if current_user.role not in ['user', 'admin']:
        flash('Access denied')
        return redirect(url_for('main.index'))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, bottomMargin=30, leftMargin=30, rightMargin=30)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, fontSize=18, fontName='Helvetica-Bold')

    elements = []

    # Convert timestamps to IST
    created_at_ist = booking.created_at.replace(tzinfo=timezone.utc).astimezone(IST) if booking.created_at.tzinfo is None else booking.created_at.astimezone(IST)
    confirmed_at_ist = None
    if booking.confirmed_at:
        confirmed_at_ist = booking.confirmed_at.replace(tzinfo=timezone.utc).astimezone(IST) if booking.confirmed_at.tzinfo is None else booking.confirmed_at.astimezone(IST)

    # Function to create booking details table
    def create_booking_table():
        data = [
            ['Booking Details', ''],
            ['BID:', booking.bid],
            ['Hall:', booking.hall.name],
            ['Date:', booking.date.strftime('%d %b %Y')],
            ['Time Slot:', booking.time_slot.title()],
            ['Client Name:', booking.client_name],
            ['Phone:', booking.phone],
            ['Address:', booking.address],
            ['Status:', booking.status.title()],
            ['Booked on:', created_at_ist.strftime('%d %b %Y at %I:%M %p')],
        ]
        if confirmed_at_ist:
            data.append(['Confirmed on:', confirmed_at_ist.strftime('%d %b %Y at %I:%M %p')])

        style_commands = [
            ('SPAN', (0, 0), (1, 0)),  # Merge header row
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),  # Header row
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 10),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),  # Center the merged header
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),  # Bold BID
            # Highlight Hall
            ('BACKGROUND', (0, 2), (-1, 2), colors.lightgrey),
            ('FONTNAME', (0, 2), (1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (1, 2), 10),
            # Highlight Date
            ('BACKGROUND', (0, 3), (-1, 3), colors.lightgrey),
            ('FONTNAME', (0, 3), (1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 3), (1, 3), 10),
        ]

        table = Table(data, colWidths=[120, 300])
        table.setStyle(TableStyle(style_commands))
        return table

    # Function to create payment table
    def create_payment_table():
        payment_data = [
            ['Payment Information', ''],
            ['Total:', f'{booking.total or 0:.2f}'],
            ['Advance Paid:', f'{booking.advance_paid or 0:.2f}'],
            ['Balance:', f'{booking.balance or 0:.2f}'],
        ]
        payment_table = Table(payment_data, colWidths=[120, 300])
        payment_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),  # Merge header row
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),  # Header row
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 10),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),  # Center the merged header
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),  # Bold the amount column
        ]))
        return payment_table

    # Company Copy
    elements.append(create_booking_table())
    elements.append(Spacer(1, 10))
    elements.append(create_payment_table())
    elements.append(Spacer(1, 15))

    # Line break
    line_table = Table([['']], colWidths=[420])
    line_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 15))

    # Customer Copy
    elements.append(create_booking_table())
    elements.append(Spacer(1, 10))
    elements.append(create_payment_table())

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
        created_at_ist = booking.created_at.replace(tzinfo=timezone.utc).astimezone(IST) if booking.created_at and booking.created_at.tzinfo is None else (booking.created_at.astimezone(IST) if booking.created_at else None)
        confirmed_at_ist = booking.confirmed_at.replace(tzinfo=timezone.utc).astimezone(IST) if booking.confirmed_at and booking.confirmed_at.tzinfo is None else (booking.confirmed_at.astimezone(IST) if booking.confirmed_at else None)
        writer.writerow([
            booking.bid,
            booking.hall.name,
            booking.date.strftime('%d %b %Y'),
            booking.time_slot.title(),
            booking.client_name,
            booking.phone,
            booking.address,
            booking.status.title(),
            created_at_ist.strftime('%d %b %Y %H:%M') if created_at_ist else '',
            confirmed_at_ist.strftime('%d %b %Y %H:%M') if confirmed_at_ist else ''
        ])

    output = si.getvalue()
    si.close()

    from flask import Response
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=client_bookings.csv'}
    )

@main.route('/date/<int:year>/<int:month>/<int:day>')
@login_required
def date_bookings(year, month, day):
    selected_date = date(year, month, day)
    bookings = Booking.query.filter(Booking.date == selected_date).order_by(Booking.hall_id, Booking.time_slot).all()
    return render_template('booking_list.html', bookings=bookings, title=f'Bookings for {selected_date.strftime("%d %b %Y")}', year=year, month=month, hall=None)

@main.route('/monthly/total/<int:year>/<int:month>')
@login_required
def monthly_bookings_total(year, month):
    start_date = date(year, month, 1)
    end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    bookings = Booking.query.filter(Booking.date >= start_date, Booking.date < end_date).order_by(Booking.date, Booking.hall_id, Booking.time_slot).all()
    title = f'Total Bookings for {start_date.strftime("%B %Y")}'
    return render_template('booking_list.html', bookings=bookings, title=title, year=year, month=month, hall=None)

@main.route('/monthly/hall/<int:hall_id>/<int:year>/<int:month>')
@login_required
def monthly_hall_bookings(hall_id, year, month):
    hall = Hall.query.get_or_404(hall_id)
    start_date = date(year, month, 1)
    end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    bookings = Booking.query.filter(Booking.hall_id == hall_id, Booking.date >= start_date, Booking.date < end_date).order_by(Booking.date, Booking.time_slot).all()
    title = f'{hall.name} Bookings for {start_date.strftime("%B %Y")}'
    return render_template('booking_list.html', bookings=bookings, title=title, year=year, month=month, hall=hall)

@main.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        query = request.form.get('query').strip()
        # Check if query is "Month Year"
        parts = query.split()
        if len(parts) == 2:
            month_str, year_str = parts
            try:
                year = int(year_str)
                month = next((i for i, name in enumerate(calendar.month_name) if name and name.lower() == month_str.lower()), None)
                if month:
                    # Valid month year
                    start_date = date(year, month, 1)
                    end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
                    bookings = Booking.query.filter(Booking.date >= start_date, Booking.date < end_date).order_by(Booking.date, Booking.hall_id, Booking.time_slot).all()
                    title = f'Bookings for {month_str} {year}'
                    return render_template('booking_list.html', bookings=bookings, title=title, year=year, month=month, hall=None)
            except ValueError:
                pass
        # Normal search
        bookings = Booking.query.filter(
            (Booking.bid.ilike(f'%{query}%')) |
            (Booking.client_name.ilike(f'%{query}%')) |
            (Booking.phone.ilike(f'%{query}%'))
        ).all()
        return render_template('search_results.html', bookings=bookings, query=query)
    return render_template('search.html')