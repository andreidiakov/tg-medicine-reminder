import pyrebase
import os

FIREBASE_API_TOKEN = os.environ.get("FIREBASE_API_TOKEN")
FIREBASE_DB = os.environ.get("FIREBASE_DB")

config = {
  "apiKey": FIREBASE_API_TOKEN,
  "authDomain": "medical-reminder-bot.firebaseapp.com",
  "databaseURL": FIREBASE_DB,
  "storageBucket": "medical-reminder-bot.appspot.com"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

def add_user(user):
    db.child("users").child(user['ID']).set(user)

def delete_user(ID):
    db.child("users").child(ID).remove()

def add_medicine(user_ID, medicine):
    db.child("users").child(user_ID).child("medicines").child(medicine['name']).set(medicine)

def update_medicine(user_ID, medicine, field, value):
    db.child("users").child(user_ID).child("medicines").child(medicine).child(field).set(value)

def delete_medicine(ID, medicine):
    db.child("users").child(ID).child("medicines").child(medicine).remove()

def load_users():
    all_users = db.child("users").get()
    return all_users

def add_reminder(reminder):
    db.child("reminders").child(reminder['ID']).set(reminder)

def delete_reminder(ID):
    db.child("reminders").child(ID).remove() 

def load_reminders():
    all_reminders = db.child("reminders").get()
    return all_reminders
