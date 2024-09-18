import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd


# Database connection
def create_connection():
    try:
        con = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="rental_cars"
        )
        if con.is_connected():
            return con
    except Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
        return None

# Functions to interact with the database
def add_car(con, car_id, brand, rent):
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO cars (car_id, brand, rent, available) VALUES (%s, %s, %s, 'y')", (car_id, brand, rent))
        con.commit()
        st.success("Car inserted successfully!")
    except Error as e:
        st.error(f"Error: {e}")

def delete_car(con, car_id):
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM cars WHERE car_id = %s AND available = 'y'", (car_id,))
        con.commit()
        st.success("Car deleted successfully!")
    except Error as e:
        st.error(f"Error: {e}")

def get_available_cars(con):
    try:
        cur = con.cursor()
        cur.execute("SELECT car_id, brand, rent FROM cars WHERE available = 'y'")
        rows = cur.fetchall()
        return rows
    except Error as e:
        st.error(f"Error: {e}")
        return []

def book_car(con, car_id, name, email, startdate):
    try:
        cur = con.cursor()
        cur.execute("SELECT user_name FROM users WHERE fname = %s AND email = %s", (name, email))
        user_name = cur.fetchone()[0]
        cur.execute("SELECT brand FROM cars WHERE car_id = %s", (car_id,))
        car_name = cur.fetchone()[0]
        cur.execute("INSERT INTO manages (car_id, username, carname, startdate) VALUES (%s, %s, %s, %s)", (car_id, user_name, car_name, startdate))
        cur.execute("UPDATE cars SET available = 'n' WHERE car_id = %s", (car_id,))
        con.commit()
        st.success("Car booked successfully!")
    except Error as e:
        st.error(f"Error: {e}")

def return_car(con, car_id, username):
    try:
        cur = con.cursor()
        cur.execute("UPDATE cars SET available = 'y' WHERE car_id = %s", (car_id,))
        cur.execute("DELETE FROM manages WHERE car_id = %s AND username = %s", (car_id, username))
        con.commit()
        st.success("Car returned successfully!")
    except Error as e:
        st.error(f"Error: {e}")

def validate_login(con, username, password):
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
        admin = cur.fetchone()
        if admin:
            return True, "admin"
        cur.execute("SELECT * FROM users WHERE user_name = %s AND password = %s", (username, password))
        user = cur.fetchone()
        if user:
            return True, "user"
        return False, None
    except Error as e:
        st.error(f"Error: {e}")
        return False, None

def add_user(con, user_name, password, fname, lname, email, phone):
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO users (user_name, password, fname, lname, email, phoneno) VALUES (%s, %s, %s, %s, %s, %s)", 
                    (user_name, password, fname, lname, email, phone))
        con.commit()
        st.success("User registered successfully!")
    except Error as e:
        st.error(f"Error: {e}")

# Streamlit app
def main():
    st.title("CAR RENTAL SYSTEM")

    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    if 'signup_mode' not in st.session_state:
        st.session_state.signup_mode = False

    # Create a database connection
    con = create_connection()

    if con:
        if not st.session_state.logged_in:
            if not st.session_state.signup_mode:
                username = st.text_input("Username")
                password = st.text_input("Password", type='password')

                if st.button("Login"):
                    logged_in, user_type = validate_login(con, username, password)
                    if logged_in:
                        st.session_state.logged_in = True
                        st.session_state.user_type = user_type
                        st.success(f"Login successful! Welcome {username}")
                    else:
                        st.error("Invalid username or password")

                if st.button("Sign Up"):
                    st.session_state.signup_mode = True
            else:
                st.subheader("Sign Up")
                user_name = st.text_input("User Name", key="signup_user_name")
                password = st.text_input("Password", type='password', key="signup_password")
                fname = st.text_input("First Name", key="signup_fname")
                lname = st.text_input("Last Name", key="signup_lname")
                email = st.text_input("Email", key="signup_email")
                phone = st.text_input("Phone Number", key="signup_phone")
                
                if st.button("Register", key="signup_register"):
                    add_user(con, user_name, password, fname, lname, email, phone)
                    st.session_state.signup_mode = False
                
                if st.button("Back to Login", key="back_to_login"):
                    st.session_state.signup_mode = False

        else:
            # Create a logout button
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.user_type = None

            # Menu
            menu = ["Add Car", "Delete Car", "View Available Cars", "Book Car", "Return Car"]
            choice = st.sidebar.selectbox("Menu", menu, key="menu_selectbox")

            if choice == "Add Car" and st.session_state.user_type == "admin":
                st.subheader("Add Car")
                car_id = st.text_input("Car ID", key="add_car_id")
                brand = st.text_input("Brand", key="add_car_brand")
                rent = st.number_input("Rent", min_value=0, step=1, key="add_car_rent")
                if st.button("Add Car", key="add_car_button"):
                    add_car(con, car_id, brand, rent)

            elif choice == "Delete Car" and st.session_state.user_type == "admin":
                st.subheader("Delete Car")
                car_id = st.text_input("Car ID", key="delete_car_id")
                if st.button("Delete Car", key="delete_car_button"):
                    delete_car(con, car_id)

            elif choice == "View Available Cars":
                st.subheader("Available Cars")
                available_cars = get_available_cars(con)
                if available_cars:
                    df = pd.DataFrame(available_cars, columns=["Car ID", "Brand", "Rent"])
                    st.table(df)

            elif choice == "Book Car" and st.session_state.user_type == "user":
                st.subheader("Book Car")
                car_id = st.text_input("Car ID", key="book_car_id")
                name = st.text_input("FName [as mentioned while registering] ", key="book_car_name")
                email = st.text_input("Email [as mentioned while registering]", key="book_car_email")
                startdate = st.date_input("Start Date", key="book_car_startdate")
                if st.button("Book Car", key="book_car_button"):
                    book_car(con, car_id, name, email, startdate)

            elif choice == "Return Car" and st.session_state.user_type == "user":
                st.subheader("Return Car")
                car_id = st.text_input("Car ID", key="return_car_id")
                username = st.text_input("Username [as mentioned while registering]", key="return_car_username")
                if st.button("Return Car", key="return_car_button"):
                    return_car(con, car_id, username)

            if st.session_state.user_type == "user" and (choice == "Add Car" or choice == "Delete Car"):
                st.error("Only admins can perform this action")

if __name__ == '__main__':
    main()
