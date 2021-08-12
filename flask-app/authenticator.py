
from pymongo import MongoClient
import re
import hashlib
import random
import string
import uuid

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Authenticator:

    def __init__(self, driver):
        self.driver = driver

    def _get_verification_code(self):
        """
        Return a random 6-character code
        """
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    def _send_verification_code(self, receiver_email, code):
        """
        Send a verification email to the user that signed up with the given email using smtplib
        """

        # Login to the uoftalk gmail account
        smtp_server = "smtp.gmail.com"
        sender_email = "uoftalk.verify@gmail.com" 
        password = "removed_for_privacy"
        
        # Create the email body
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "UofTalk Registration Verification Code"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        body = f"""
    Hello!
                    
    Your email had been used to sign-up for UofTalk.
    Please find the verfication code below and enter it in the registration page.

    Verification Code: {code}

    If you did not intend to register, please disregard this email.

    Thanks!
    UofTalk : Boundless Connections 
                """
    
        part2 = MIMEText(body)
        msg.attach(part2)

        # Send the email
        s = smtplib.SMTP_SSL('smtp.gmail.com')
        s.login(sender_email, password)
        s.sendmail(sender_email, receiver_email, msg.as_string())
        s.quit()

    def _get_hash(self, password):
        """
        return the hashed the password using a sophisticated injective algorithm
        """
        mixed_string = ""
        for i in range(len(password)):
            mixed_string += (password[i] + password[len(password) - 1 - i])

        dk = hashlib.pbkdf2_hmac('sha1', bytes(mixed_string, encoding='utf8'), b'betamanwazhere', 100000)
        return dk.hex()


    def send_password_update_email(self, receiver_email):
          # Login to the uoftalk gmail account
        smtp_server = "smtp.gmail.com"
        sender_email = "uoftalk.verify@gmail.com" 
        password = "removed_for_privacy"
        
        # Create the email body
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "UofTalk Password Changed"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        body = f"""
    Hello!
                    
    Your password has been changed.

    If you did not intend to change your password, please reply to this email immediately. 

    Regards,
    UofTalk : Boundless Connections 
                """
    
        part2 = MIMEText(body)
        msg.attach(part2)

        # Send the email
        s = smtplib.SMTP_SSL('smtp.gmail.com')
        s.login(sender_email, password)
        s.sendmail(sender_email, receiver_email, msg.as_string())
        s.quit()

    def register(self, email_id, username, password):
        """
        Register the user with the given email and password

        Return codes:
            - 1 Email is in use
            - 2 Email is not UofT email
            - 3 Password too short
            - 4 Username is in use
            - Otherwise returns the user's cookie
        """

        # Check the password length
        if len(password) < 8:
            return 3

        # Check if the email is a uoft email
        if re.match(r".*@mail.utoronto\.ca", email_id) is None:
            return 2

        # Check if username is not in use
        if self.driver.find_one('users', {'username': username}):
            return 4

        # Generate the hashed password and the verification code
        hashed_password = self._get_hash(password)
        code = self._get_verification_code()

        # Generate a random UUID for the user's cookie
        cookie = uuid.uuid4().hex

        # Create JSON database entry for the user
        entry = {
            "cookie": cookie, 
            "email_id": email_id,
            "password": hashed_password,
            "verification_code": code,
            "verified": False,
            "logged_in": False
        }

        if self.driver.find_one('auth', {"email_id": email_id}) is None:
            # Insert the user to the authentication table
            self.driver.insert_one('auth', entry)

            # Create a new user entry
            preferences = {
                "music": [-1,-1,-1,-1],
                "movie": [-1,-1,-1,-1],
                "game": [-1,-1,-1,-1],
                "humor": [-1,-1,-1,-1, -1, -1],
                "overall": [-1,-1,-1,-1, -1,-1,-1,-1, -1,-1,-1,-1, -1,-1,-1,-1, -1, -1]
            }

            cluster_association = {}
            for label in ['music', 'game', 'humor', 'movie', 'overall']:
                cluster_association[label] = {}        
                for k in [3, 9, 15]:
                    cluster_association[label][str(k)] = -1

            new_user_entry = {
                'user_id': uuid.uuid4().hex,
                'email': email_id,
                'username': username,
                'preferences': preferences,
                'cluster_association': cluster_association,
                'cluster_granularity' : 9,
                'finished_survey' : {"quest": False, "meme": False},
                'bio': "",
                'blocklist' : []
            }

            # Add this user to the users collection
            self.driver.insert_one('users', new_user_entry)

            self._send_verification_code(email_id, code)
        else:
            # The email the user provided is already in use
            print("Email id is already in use")
            return 1

        return cookie

    def authenticate(self, email_id, password):
        """
        Return codes:
            - 0 User is valid
            - 1 User is valid, but they did not verify their email
            - 2 Invalid login
        """
        # Query the database to see if the email and password tuple exists
        user = self.driver.find_one('auth', {"email_id": email_id, "password": self._get_hash(password)})

        if user is not None:
            if user['verified']:
                return 0
            else:
                return 1
        return 2

    def update_password(self, email, new_password):
        """
        Return codes:
            - 0 Password too short
            - 1 Password updated
        """

        if len(new_password) < 8:
            return 0

        # Hash the password
        hashed_password = self._get_hash(new_password)
        self.driver.update_one("auth", {"email_id": email}, {"$set": {"password": hashed_password}})
        return 1


    def check_verification_code(self, email, code):
        """
        Returns true if the entered code is correct
        """

        # Check if the entered code is the same as the one stored in the database for this user
        if self.driver.find_one('auth', {"email_id": email, "verification_code": code}) is not None:
            self.driver.update_one('auth', {"email_id": email}, 
                                    {"$set": {"verified": True}})
            return True
        return False

    def resend_verification_code(self, email):
        """
        Generate a new verification code and send it to the given email
        """
        new_code = self._get_verification_code()
        self.driver.update_one('auth', {"email_id": email}, 
                                    {"$set": {"verification_code": new_code}})
        self._send_verification_code(email, new_code)

    def set_user_login_status(self, email, status):
        """
        Set the login status of the user with the given email
        """
        self.driver.update_one('auth', {"email_id": email}, 
                                    {"$set": {"logged_in": status}})

    def get_user_login_status(self, email):
        """
        Get the login status of the user with the given email
        Returns None if user does not exist
        """
        user = self.driver.find_one('auth', {"email_id": email})
        if user:
            return user['logged_in']