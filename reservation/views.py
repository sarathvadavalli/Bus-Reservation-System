from datetime import datetime
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Bus, Book, UserProfile
from django.db.models import F
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings

def home(request):
    context = {'STATIC_VERSION': settings.STATIC_VERSION}
    return render(request, 'home.html', context)

def deleteAll(request):
    Bus.objects.update(rem = F('capacity'))
    return HttpResponse('All records deleted')


@login_required(login_url='signin')
def viewprofile(request):
    user_r = request.user
    userprofile = UserProfile.objects.get(user=user_r)
    phno_r = userprofile.phno
    return render(request, 'profile.html', {'user': user_r, 'phno': phno_r})


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

        buses = Bus.objects.filter(
            source=source,
            dest=destination,
            date=date
        )
        if buses:
            return render(request, 'list.html', {'buses': buses})
        else:
            #context['data'] = request.POST
            context['error'] = "No available Bus Schedule for entered Route and Date"
            return render(request, 'findbus.html', context)
    
    return render(request, 'findbus.html')


@login_required(login_url='signin')
def bookings(request):
    context = {}
    if request.method == 'POST':
        id_r = request.POST.get('bus_id')
        seats_r = int(request.POST.get('no_seats'))
        bus = Bus.objects.get(bus_id=id_r)
        if bus:
            if bus.rem > seats_r:
                userid_r = request.user.id
                name_r = bus.bus_name
                src_r = bus.source 
                dest_r = bus.dest
                price_r = seats_r * bus.price
                date_r = bus.date
                time_r = bus.time
                rem_r = bus.rem - seats_r
                Bus.objects.filter(bus_id=id_r).update(rem=rem_r)
             
                book = Book.objects.create(userid=userid_r, bus_name=name_r, 
                                           src=src_r, dest=dest_r, date=date_r, time=time_r,
                                           nos=seats_r, price=price_r, 
                                           status='BOOKED')
                print('------------book id-----------', book.id)
                return render(request, 'bookings.html', {'book': book, 'bus': bus})
            else:
                context["error"] = "Sorry select fewer number of seats"
                return render(request, 'findbus.html', context)

    else:
        return render(request, 'findbus.html')


@login_required(login_url='signin')
def cancellings(request):
    context = {}
    if request.method == 'POST':
        id_r = request.POST.get('bus_id')
    
        try:
            book = Book.objects.get(id=id_r)
            bus = Bus.objects.get(bus_name=book.bus_name)
            rem_r = bus.rem + book.nos
            Bus.objects.filter(bus_name=book.bus_name).update(rem=rem_r)
            #nos_r = book.nos - seats_r
            Book.objects.filter(id=id_r).update(status='CANCELLED')
            Book.objects.filter(id=id_r).update(nos=0)
            messages.success(request, "Booked Bus has been cancelled successfully.")
            return redirect(seebookings)
        except Book.DoesNotExist:
            context["error"] = "Sorry You have not booked that bus"
            return render(request, 'error.html', context)
    else:
        return render(request, 'findbus.html')


@login_required(login_url='signin')
def seebookings(request):
    context = {}
    id_r = request.user.id
    name_r = request.user.username
    print(name_r)
    book_list = Book.objects.filter(userid=id_r)
    if book_list:
        return render(request, 'booklist.html', {'book_list': book_list, 'name': name_r})
    else:
        context["error"] = "Sorry no buses booked"
        return render(request, 'findbus.html', context)


def signup(request):
    context = {}
    if request.method == 'POST':
        name_r = request.POST.get('name')
        email_r = request.POST.get('email')
        password_r = request.POST.get('password')
        phno_r = request.POST.get('phno')

        user = User.objects.create_user(name_r, email_r, password_r)
        if user:
            userprofile = UserProfile.objects.create(user=user, phno=phno_r)
            print("Phone no: ",userprofile.phno)
            return render(request, 'thank.html')
        else: 
            context["error"] = "Provide valid credentials"
            return render(request, 'signup.html', context)
    
    return render(request, 'signup.html', context)


def signin(request):
    context = {}
    if request.method == 'POST':
        name_r = request.POST.get('name')
        password_r = request.POST.get('password')
        user = authenticate(request, username=name_r, password=password_r)
        if user:
            login(request, user)
            context["user"] = name_r
            context["id"] = request.user.id
            return render(request, 'success.html', context)
        else:
            context["error"] = "Invalid Username or Password"
            return render(request, 'signin.html', context)
    else:
        context["error"] = "You are not logged in"
        return render(request, 'signin.html', context)


def signout(request):
    context = {}
    logout(request)
    context['error'] = "You have been logged out"
    return render(request, 'bye.html', context)
