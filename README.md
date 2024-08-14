# Bus Reservation System

## Overview
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Bus Reservation system is a comprehensive web application which is designed to facilitate easy and efficient ticket booking and management. It aims to streamline the entire process of viewing available buses, booking bus tickets and handling customer information. It solves the problem of manual booking of tickets which can lead to errors. It can be accessed by anyone at any place so that passengers need not visit the location to inquire about bus details and schedules.

 ## Features
a) <b>Admin Panel:</b> Administrators have access to a dedicated dashboard where they can manage bus schedules and monitor bookings. The admin panel also allows for adding new buses, routes and updating bus information.
 
b) <b>User Registration and Authentication:</b> Users can create an account, log in securely and manage their profile. The user data is stored into database and used whenever user is logged in.
 
c) <b>Bus search and availability:</b> Users can search for buses based on the source, destination and travel date.

d) <b>Book and Cancel ticket:</b> User is listed with available buses in the requested schedule and user can book tickets in any of the buses based on available seats. Before the journey date, user can also cancel the ticket.

e) <b>Booking history:</b> User can also view all the bookings made by him/her and their details upto date.

## Technologies Used
* <b>Frontend:</b> HTML, CSS, JavaScript

* <b>Backend:</b> Django framework

* <b>Database:</b> SQLite for data storage and management

## Installation
1.  Clone the repository:
   
                    git clone https://github.com/sarathvadavalli/bus_reservation_system.git
2. Navigate to the project directory and install dependencies:

                   cd bus-reservation-system
                   pip install -r requirements.txt
3. Set up the database
   
                    python manage.py migrate
4. Run the developement server:
   
                    python manage.py runserver

## Future Enhancements
- Integration with a payment gateway to make secure online payments for ticket bookings.
- Integration with SMS API for booking notifications.
- Mobile app version for easier access of the application.
