from datetime import datetime, timedelta
import time
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import Buses, Schedule, Book, Profile, SeatInventory
from django.db.models import F
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import IntegrityError, connection
from django.core.cache import cache
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone


def home(request):
    context = {'STATIC_VERSION': settings.STATIC_VERSION}
    return render(request, 'home.html', context)

def displaybus(request, schedule_id):
    try:
        schedule = Schedule.objects.select_related('bus').get(schedule_id=schedule_id)
        schedule.id = schedule.bus.bus_id
    except Schedule.DoesNotExist:
        return render(request, 'error.html', {'message': 'Bus not found'})
    
    return render(request, 'displaybus.html', {'bus': schedule})


@login_required(login_url='signin')
def viewprofile(request):
    if request.method == 'POST':
        user_r = request.user
        username_r = request.POST.get('username', '').strip()
        first_name_r = request.POST.get('first_name', '').strip()
        last_name_r = request.POST.get('last_name', '').strip()
        email_r = request.POST.get('email', '').strip()
        phno_r = request.POST.get('phno', '').strip()
        posted_data = {
            'username': username_r,
            'first_name': first_name_r,
            'last_name': last_name_r,
            'email': email_r,
            'phno': phno_r,
        }
        
        if (user_r.username != username_r and User.objects.filter(username=username_r).exists()):
            return render(request, 'profile.html', {
                'data': posted_data,
                'profile_error': "Sorry! the entered username already exists.",
                'edit_profile_open': True,
            })

        user_r.username = username_r
        user_r.first_name = first_name_r
        user_r.last_name = last_name_r
        user_r.email = email_r
        user_r.save()

        profile, created = Profile.objects.get_or_create(user=user_r)
        if profile:
            profile.phno = phno_r
            profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect(viewprofile)

    user_id = request.user.id
    cur = connection.cursor()

    try:
        cur.callproc('get_user_profile', [user_id])
        res = cur.fetchone()

        col = []
        for desc in cur.description:
            col.append(desc[0])

        dic = dict(zip(col,res))
        return render(request, 'profile.html', {'data': dic})
    except Exception as e:
        return redirect('home')


@login_required(login_url='signin')
def findbus(request):
    context = {}
    if request.method == 'POST':
        source = request.POST.get('source')
        destination = request.POST.get('destination')
        date_str = request.POST.get('date')
        
        if date_str is None or date_str == '':
           return render(request, 'error.html', {'message': 'Date is required'})
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return render(request, 'error.html', {'message': 'Invalid date format'})

                
        cache_key = f'bus_search_{source}_{destination}_{date_str}'
        scheduled_buses = cache.get(cache_key)
        if scheduled_buses is None:
            scheduled_buses = list(
                Schedule.objects.select_related('bus').filter(
                    source=source,
                    dest=destination,
                    arrival_datetime__date=date,
                ).annotate(
                    bus_name=F('bus__bus_name'),
                    price=F('bus__price'),
                ).values(
                    'schedule_id', 'bus_name', 'source', 'dest',
                    'arrival_datetime', 'departure_datetime', 'price',
                )
            )
            cache.set(cache_key, scheduled_buses, timeout=1800)
        else:
            print("Serving from the cache..")

        if scheduled_buses:
            remaining_by_schedule = dict(
                Schedule.objects.filter(
                    schedule_id__in=[bus['schedule_id'] for bus in scheduled_buses]
                ).values_list('schedule_id', 'rem')
            )
            for bus in scheduled_buses:
                bus['rem'] = remaining_by_schedule.get(bus['schedule_id'])
     
            return render(request, 'list.html', {'buses': scheduled_buses})
        else:
            context['error'] = "No available Bus Schedule for entered Route and Date"
            return render(request, 'findbus.html', context)
    
    return render(request, 'findbus.html')


@login_required(login_url='signin')
def refresh_schedule_seats(request, schedule_id):
    schedule = get_object_or_404(Schedule, schedule_id=schedule_id)
    return JsonResponse({'remaining_seats': schedule.rem})


@login_required(login_url='signin')
def bookings(request):
    context = {}
    if request.method == 'POST':
        sch_id = request.POST.get('schedule_id')
        seats_r = int(request.POST.get('no_seats'))
        schedule = Schedule.objects.select_related('bus').get(schedule_id=sch_id)
        bus = schedule.bus
        user = request.user
        try:
            with transaction.atomic():
                seats = (
                    SeatInventory.objects
                    .select_for_update(skip_locked=True)
                    .filter(schedule=schedule, status="AVAILABLE")
                    .order_by("seat_no")[:seats_r]
                )

                if len(seats) < seats_r:
                    return render(request, 'findbus.html', {
                        "error": "Sorry select fewer number of seats"
                    })

                selected_seats = [seat.seat_no for seat in seats]
                selected_seats_str = ', '.join(selected_seats)

                price_r = seats_r * bus.price
                booking = Book.objects.create(
                    user=user,
                    schedule=schedule,
                    nos=seats_r,
                    seats=selected_seats_str,
                    price=price_r,
                    time=datetime.now(),
                    status='BOOKED'
                )

                for seat in seats:
                    seat.status = 'BOOKED'
                    seat.save()

                schedule.rem = schedule.rem - seats_r
                schedule.save()

            return render(request, 'booking.html', {
                'book': booking,
                'bus': schedule,
                'seats': selected_seats
            })

        except IntegrityError:
            return render(request, 'findbus.html', {
                "error": "Some seats were just booked by another user. Please try again."
            })
        except Exception as e:
            print(e)
            return render(request, 'findbus.html', {
                "error": e
            })
        
    else:
        return render(request, 'findbus.html')


@login_required(login_url='signin')
def cancellings(request):
    context = {}
    if request.method == 'POST':
        id_r = request.POST.get('booking_id')
        try:
            book = Book.objects.select_related('schedule').get(
                bookid=id_r,
                user=request.user,
            )
        except Book.DoesNotExist:
            context['error'] = "Sorry You have not booked that bus"
            return render(request, 'error.html', context)

        if book.status.upper() in ('C', 'CANCELLED'):
            context['error'] = "Sorry, you have already cancelled that booking"
            return render(request, 'error.html', context)

        schedule = book.schedule
        departure_datetime = schedule.departure_datetime
        now = timezone.now()
        if now >= departure_datetime:
            context['error'] = "Journey already completed"
            return render(request, 'error.html', context)
        if now >= departure_datetime - timedelta(hours=6):
            context['error'] = "Sorry, the booking can't be cancelled"
            return render(request, 'error.html', context)

        with transaction.atomic():
            seats = book.seats
            selected_seats = seats.split(', ')
            (SeatInventory.objects
                .filter(schedule=book.schedule, seat_no__in=selected_seats)
                .update(status = 'AVAILABLE'))

            schedule.rem += int(book.nos)
            schedule.save(update_fields=['rem'])
            book.status = 'CANCELLED'
            book.nos = 0
            book.save(update_fields=['status', 'nos'])

            messages.success(request, "Booked Bus has been cancelled successfully. Your amount will be refunded within 2-3 days.")
            return redirect(seebookings)
    else:
        return render(request, 'findbus.html')


@login_required(login_url='signin')
def seebookings(request):
    context = {}
    user = request.user
    name_r = user.username
    book_list = list(
        Book.objects.filter(user=request.user).select_related('schedule__bus')
    )

    if not book_list:
        return render(request, 'findbus.html', {"error": "Sorry no buses booked"})

    data = []
    for book in book_list:
        s = book.schedule
        book.schedule_id = s.schedule_id
        book.bus_name = s.bus.bus_name
        book.source = s.source
        book.dest = s.dest
        book.arrival_datetime = s.arrival_datetime
        book.departure_datetime = s.departure_datetime

        data.append({
            'bookid': book.bookid,
            'status': book.status,
            'bus_name': book.bus_name,
            'source': s.source,
            'dest': s.dest,
            'departure_datetime': s.departure_datetime,
            'arrival_datetime': s.arrival_datetime,
        })

    context = {
        'book_list': book_list,
        'book_list_json': data, 
        'name': request.user.username,
    }
    return render(request, 'booklist.html', context)


def signup(request):
    context = {}
    if request.method == 'POST':
        username_r = request.POST.get('username')
        first_name_r = request.POST.get('first_name')
        last_name_r = request.POST.get('last_name')
        email_r = request.POST.get('email')
        password_r = request.POST.get('password')
        phno_r = request.POST.get('phno')
 
        try:
            user = User.objects.create_user(
                    username=username_r, 
                    email=email_r, 
                    password=password_r,
                    first_name=first_name_r, 
                    last_name=last_name_r, 
                )
        except IntegrityError:
            context["error"] = "Username already exists"
            return render(request, 'signup.html', context)
        if user:
            Profile.objects.create(user=user, phno=phno_r)
            return render(request, 'thank.html')
        else: 
            context["error"] = "Provide valid credentials"
            return render(request, 'signup.html', context)
    
    return render(request, 'signup.html', context)


def signin(request):
    context = {}
    if request.method == 'POST':
        username_r = request.POST.get('username')
        password_r = request.POST.get('password')
        user = authenticate(request, username=username_r, password=password_r)
        if user:
            login(request, user)
            context["user"] = user.username
            context["id"] = request.user.id
            return render(request, 'success.html', context)
        else:
            context["error"] = "Invalid Username or Password"
            return render(request, 'signin.html', context)
    else:
        context["error"] = ""
        return render(request, 'signin.html', context)


def signout(request):
    context = {}
    logout(request)
    context['error'] = "You have been logged out"
    return render(request, 'bye.html', context)
