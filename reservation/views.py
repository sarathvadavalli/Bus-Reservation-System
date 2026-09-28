from datetime import datetime, timedelta
import time
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import Buses, Schedule1, Book, Seat, Profile
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
        schedule = Schedule1.objects.select_related('bus').get(schedule_id=schedule_id)
        schedule.id = schedule.bus.bus_id
    except Schedule1.DoesNotExist:
        return render(request, 'error.html', {'message': 'Bus not found'})
    
    return render(request, 'displaybus.html', {'bus': schedule})


def deleteAll(request):
    user = User.objects.get(username="hai")  
    user.delete()
    return HttpResponse('Record deleted..')
    #Bus.objects.update(rem = F('capacity'))
    #return HttpResponse('All records deleted')


@login_required(login_url='signin')
# def viewprofile(request):
#     user_r = request.user
#     userprofile = Profile.objects.get(user=user_r)
#     phno_r = userprofile.phno
#     return render(request, 'profile.html', {'user': user_r, 'phno': phno_r})

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
    cur.callproc('get_user_profile', [user_id])
    res = cur.fetchone()

    col = []
    for desc in cur.description:
        col.append(desc[0])

    dic = dict(zip(col,res))
    return render(request, 'profile.html', {'data': dic})


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

                
        # cache_key = f'bus_{source}_{destination}_{date}'
        # cached_data = cache.get(cache_key)

        print("Fetching from database")
        scheduled_buses = Schedule1.objects.select_related('bus').filter(
            source=source,
            dest=destination,
            date=date
        )
        if scheduled_buses:
        #     print(list(scheduled_buses))
            # i = 1
            # for schedule in scheduled_buses:
            #     bus = schedule.bus_id
            #     schedule.id = i
            #     i += 1
            #     schedule.bus_name = bus.bus_name
            #     schedule.price = bus.price
            # cache.set(cache_key, response_data, timeout=300)
            return render(request, 'list.html', {'buses': scheduled_buses})
        else:
            #context['data'] = request.POST
            response_data = {'Message': "No available Bus Schedule for entered Route and Date"}
            # cache.set(cache_key, response_data, timeout=400)
            context['error'] = "No available Bus Schedule for entered Route and Date"
            return render(request, 'findbus.html', context)
    
    return render(request, 'findbus.html')


@login_required(login_url='signin')
def bookings(request):
    context = {}
    if request.method == 'POST':
        sch_id = request.POST.get('schedule_id')
        seats_r = int(request.POST.get('no_seats'))
        schedule = Schedule1.objects.select_related('bus').get(schedule_id=sch_id)
        bus = schedule.bus
        user = request.user
        try:
            with transaction.atomic():
                # Step 1: Get already booked seats
                booked_seats = set(
                    Seat.objects
                    .filter(schedule_id=schedule)
                    .values_list('seat_no', flat=True) 
                )

                # Step 2: Generate all seats
                all_seats = [f"A{i}" for i in range(1, bus.capacity + 1)]

                # Step 3: Find available seats
                available_seats = [
                    seat for seat in all_seats
                    if seat not in booked_seats
                ]

                print(available_seats)

                if len(available_seats) < seats_r:
                    return render(request, 'findbus.html', {
                        "error": "Sorry select fewer number of seats"
                    })

                # Step 4: Select seats
                selected_seats = available_seats[:seats_r]

                print(selected_seats)

                time.sleep(5)

                # Step 5: Create booking
                price_r = seats_r * bus.price
                booking = Book.objects.create(
                    user=user,
                    schedule=schedule,
                    nos=seats_r,
                    price=price_r,
                    time=datetime.now(),
                    status='BOOKED'
                )

                # Step 6: Insert seat rows
                for seat in selected_seats:
                    Seat.objects.create(
                        book_id=booking,
                        schedule_id=schedule,
                        seat_no=seat
                    )

                # (Optional) update rem for display only
                schedule.rem = schedule.rem - seats_r
                schedule.save()

            return render(request, 'bookings.html', {
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
        departure_datetime = timezone.make_aware(
            datetime.combine(schedule.date, schedule.departure_time),
            timezone.get_current_timezone(),
        )
        now = timezone.now()
        if now >= departure_datetime:
            context['error'] = "Journey already completed"
            return render(request, 'error.html', context)
        if now >= departure_datetime - timedelta(hours=6):
            context['error'] = "Sorry, the booking can't be cancelled"
            return render(request, 'error.html', context)

        with transaction.atomic():
            schedule.rem += int(book.nos)
            schedule.save(update_fields=['rem'])
            Seat.objects.filter(book_id=book).delete()
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
        book.date = s.date
        book.arrival_time = s.arrival_time
        book.departure_time = s.departure_time

        data.append({
            'bookid': book.bookid,
            'status': book.status,
            'bus_name': book.bus_name,
            'source': s.source,
            'dest': s.dest,
            'date': s.date,
            'departure_time': s.departure_time,
            'arrival_time': s.arrival_time,
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
