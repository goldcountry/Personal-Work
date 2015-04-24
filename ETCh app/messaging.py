import datetime
import json
from google.appengine.api import datastore_types
from google.appengine.ext import db
import webapp2
from webapp2_extras import security
import cgi
import urllib
import wsgiref.handlers

"""
How the server will work:

Users:
	Each user will be stored in the appengine datastore as a class User.
	Each user will have a user ID, a list of friend ID's, and a list
	 of unread messages (which is always empty while the user is 
	 offline). They'll also have a "message waiting" boolean value.
	When we get to doing the encryption side of things, this may grow.

Messaging:
	When a user sends a message, the client sends an HTTP POST message
	to the server.
"""



message_delimiter = "\n"


# this is how we will store user data in the datastore
# the unread messages themselves are stored in their own model in the datastore
# to get an individual user from a userID, do a GQL query as follows:
#   user = db.GqlQuery("SELECT * FROM User WHERE userID IS :1", username)

class User(db.Model):
	userID = db.StringProperty()
	friends = db.StringListProperty()
	unread_messages = db.IntegerProperty()
	sent_messages = db.IntegerProperty()
	password_hash = db.StringProperty()
	sent_freqs = db.StringListProperty()
	received_freqs = db.StringListProperty()
	freqs_accepted = db.StringListProperty()

	def set_password(self, raw_password):
		self.password_hash = security.generate_password_hash(raw_password)

	def attempt_login(self, raw_password):
		return security.check_password_hash(raw_password, self.password_hash)

class FriendRequest(db.Model):
	sender = db.StringProperty()
	receiver = db.StringProperty()
	senderKey = db.StringProperty()
	receiverKey = db.StringProperty()


class AddUser(webapp2.RequestHandler):
	# POSTs to this URL should be in the form of:
	#   {user: "username", pass: "password"}
	def post(self):
		new_username = self.request.get('user')
		new_userpass = self.request.get('pass')
		user_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", new_username)
		if user_gql.get() is not None:
			self.response.write("username already taken")
		else:
			user = User()
			user.userID = new_username
			user.set_password(new_userpass)
			user.friends = []
			user.unread_messages = 0
			user.sent_messages = 0
			user.sent_freqs = []
			user.received_freqs = []
			user.friend_requests_accepted = []
			user.put()
			self.response.write("user created successfully")

class WaitingMessage(db.Model):
	
	# this is how each unread message is stored in the datastore.
	# after a message is claimed, it will be deleted from the datastore.
	# for an individual user to find their unread messages, do a GQL query as follows:
	# 	messages = db.GqlQuery("SELECT * FROM WaitingMessage WHERE recipient = user.userID")

	sender = db.StringProperty()
	recipient = db.StringProperty()
	message = db.StringProperty()
	time_sent = db.StringProperty()

def messageToDict(message):
	messageDict = {}
	messageDict["from"] = message.sender
	messageDict["body"] = message.message
	messageDict["time_sent"] = message.time_sent
	return messageDict

def userMessageReceived(sendername, recipname):

	# make a datastore query to get the correct user
	# update that user's information
	# put that updated user back to the datastore
	recipient_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", recipname)
	recipient = recipient_gql.get()
	if recipient is not None:
		recipient.unread_messages += 1
		recipient.put()
		sender_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", sendername)
		sender = sender_gql.get()
		if sender is not None:
			sender.sent_messages += 1
			sender.put()

class SendFriendRequest(webapp2.RequestHandler):
	# Posts here should be in the form of:
	#   {user: "username", pass: "password", friend: "new friend's username", pub_key: "your public key"}
	# When you try to friend someone, it puts your name into their pending requests.
	# then, when they friend you, it removes that name and adds each other
	#  into your respective friend lists.
	def post(self):
		username = self.request.get('user')
		raw_pass = self.request.get('pass')
		friendname = self.request.get('friend')
		user_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", username)
		friend_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", friendname)
		user = user_gql.get()
		friend = friend_gql.get()
		if user is None:
			self.response.write("no such user")
			
		elif friend is None:
			self.response.write('no such friend')
			
		elif user.attempt_login(raw_pass):
			if username not in friend.sent_freqs:
				friend.received_freqs.append(username)
				user.sent_freqs.append(friendname)
				request = FriendRequest()
				request.sender = user.userID
				request.receiver = friend.userID
				request.senderKey = self.request.get("pub_key")
				request.put()
				user.put()
				friend.put()
				self.response.write(friendname)
			else:
				request_gql = db.GqlQuery("SELECT * FROM FriendRequest WHERE sender = :1 AND receiver = :2", friendname, username)
				request = request_gql.get()
				request.receiverKey = self.request.get("pub_key")
				if username in friend.sent_freqs: friend.sent_freqs.remove(username)
				friend.freqs_accepted.append(username)
				if friendname in user.received_freqs: user.received_freqs.remove(friendname)
				friend.put()
				user.put()
				request.put()
				self.response.write(friendname)

		else:
			self.response.write("validation incorrect")

class CheckIncomingFriendRequests(webapp2.RequestHandler):

	# Should be in the form of:
	#   {user: "username" pass: "password"}
	def post(self):
		username = self.request.get("user")
		raw_pass = self.request.get("pass")
		user_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", username)
		user = user_gql.get()
		if user is None:
			self.response.write("no such user")
		elif user.attempt_login(raw_pass):
			# Should send back users who have requested you
			responseDict = {}
			num = 0
			for requester in user.received_freqs:
				requestDict = {}
				request_gql = db.GqlQuery("SELECT * FROM FriendRequest WHERE receiver = :1", username)
				request = request_gql.get()
				if request != None:
					requestDict['sender'] = request.sender
					requestDict['pub_key'] = request.senderKey
					responseDict[num] = requestDict
					num += 1
				else: break
			user.received_freqs = []
			user.put()
			self.response.write(json.dumps(responseDict))

		else:
			self.response.write("validation incorrect")


# {user: "username", pass: "password", friend: "the user whose request we are accepting", pub_key:"public key"}
class AcceptFriendRequest(webapp2.RequestHandler):
	def post(self):
		username = self.request.get("user")
		raw_pass = self.request.get("pass")
		friendname = self.request.get("friend")
		user_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", username)
		user = user_gql.get()
		friend_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", friendname)
		friend = friend_gql.get()
		if user is None:
			self.response.write("no such user")
		elif friend is None:
			self.response.write("no such friend")
		elif user.attempt_login(raw_pass):
			request_gql = db.GqlQuery("SELECT * FROM FriendRequest WHERE sender = :1 AND receiver = :2", friendname, username)
			request = request_gql.get()
			request.receiverKey = self.request.get("pub_key")
			
			if username in friend.sent_freqs: friend.sent_freqs.remove(username)
			friend.freqs_accepted.append(username)
			if friendname in user.received_freqs: user.received_freqs.remove(friendname)
			friend.put()
			user.put()
			request.put()
			self.response.write(friendname)

		else:
			self.response.write("validation incorrect")

def acceptFreq():
	pass


def sendFreq():
	pass

# {user: "username", pass: "password"}
class CheckAcceptedFriendRequests(webapp2.RequestHandler):
	def post(self):
		username = self.request.get("user")
		raw_pass = self.request.get("pass")
		user_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", username)
		user = user_gql.get()
		if user is None:
			self.response.write("no such user")
		elif user.attempt_login(raw_pass):
			responseDict = {}
			num = 0
			for accepter in user.freqs_accepted:
				requestDict = {}
				request_gql = db.GqlQuery("SELECT * FROM FriendRequest WHERE sender = :1 AND receiver = :2", username, accepter)
				request = request_gql.get()
				requestDict['friend'] = accepter
				requestDict['pub_key'] = request.receiverKey
				responseDict[num] = requestDict
				num += 1
				request.delete()
			user.freqs_accepted = []
			user.put()
			self.response.write(json.dumps(responseDict))
		else:
			self.response.write("validation incorrect")

# Login attempts should be in the form of:
#   {user: "username" pass: "password"}
# Naturally, the password will need to be encrypted before being sent, 
#  to protect from MITM attacks, but we'll figure that part out later

class LoginUser(webapp2.RequestHandler):
	def post(self):
		username = self.request.get("user")
		raw_pass = self.request.get("pass")
		user_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", username)
		user = user_gql.get()
		if user is None:
			self.response.write("no such user")
		elif user.attempt_login(raw_pass):
			self.response.write("login success")
		else:
			self.response.write("login failure")



# Will delete all user data: the user profile, and all inbound messages.
# Since the user will need to authenticate in order to delete, these
#  requests should be in the form of:
#   {user: "username", pass: "password"}
# Naturally, the password will need to be encrypted before being sent, 
#  to protect from MITM attacks, but we'll figure that part out later

class DeleteUser(webapp2.RequestHandler):
	def post(self):
		username = self.request.get('user')
		raw_pass = self.request.get('pass')
		user_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", username)
		user = user_gql.get()
		if user.attempt_login(raw_pass):
			user.delete()
			messages = db.GqlQuery("SELECT * FROM WaitingMessage WHERE recipient = :1", username)
			for message in messages: message.delete()
			self.response.write("user successfully deleted")
		else:
			self.response.write("invalid verification")

# sent messages should be in the form of a JSON object as follows:
# {time_sent: "timestamp", body: "ciphertext", from: "sender ID, to: "recipient ID", pass: "sender password"}
# Naturally, the password will need to be encrypted before being sent, 
#  to protect from MITM attacks, but we'll figure that part out later
# get the recipient
# update the recipient's unread messages number
# store the message in the datastore
# respond saying that the message was successfully delivered to the server ???

class MessageReceived(webapp2.RequestHandler):
	def post(self):
		# get the values from the post
		sender_name = self.request.get('from')
		recipient_name = self.request.get('to')
		message_text = self.request.get('body')
		time_stamp = self.request.get('time_sent')
		sender_pass = self.request.get('pass')
		user_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", sender_name)
		user = user_gql.get()
		if user is not None:
			if user.attempt_login(sender_pass):
				# update the sender and recipient's data fields
				userMessageReceived(sender_name, recipient_name)

				# make and store a new message
				new_message = WaitingMessage()
				new_message.sender = sender_name
				new_message.recipient = recipient_name
				new_message.message = message_text
				new_message.time_sent = time_stamp
				new_message.put()
				self.response.write("message logged")
			else:
				self.response.write("validation incorrect")


# CheckMessage queries should be in the form:
#   {user="username", pass="password"}
class CheckMessages(webapp2.RequestHandler):
	def post(self):
		username = self.request.get('user')
		user_gql = db.GqlQuery("SELECT * FROM User WHERE userID = :1", username)
		user = user_gql.get()
		if user is None:
			self.response.write("no such user")
		elif(user.unread_messages > 0):
			messages = makeMessageString(user)
			self.response.write(messages)
		else:
			self.response.write("No New Messages")

def makeMessageString(user):
	messages = db.GqlQuery("SELECT * FROM WaitingMessage WHERE recipient = :1 ORDER BY time_sent DESC", user.userID)
	response = {}
	key = 0
	for message in messages:
		json_message = messageToDict(message) 
		response[key] = json_message
		message.delete()
		key += 1
	user.unread_messages = 0
	return json.dumps(response)

# included for testing. Will not be a part of the final version
class GetAllUsernames(webapp2.RequestHandler):
	def post(self):
		users = db.GqlQuery("SELECT * FROM User")
		for user in users:
			self.response.write(user.userID + "\n")


app = webapp2.WSGIApplication([
	('/users/new', AddUser),
	('/users/login', LoginUser),
	('/users/delete', DeleteUser),
	('/send_message', MessageReceived),
	('/check_messages', CheckMessages),
	('/users/send_friend_request', SendFriendRequest),
	('/users/accept_friend_request', AcceptFriendRequest),
	('/users/check_friends', CheckIncomingFriendRequests),
	('/users/check_accepts', CheckAcceptedFriendRequests),
	('/users/getall/names', GetAllUsernames)
])


def main():
	app.run()

if __name__ == "__main__":
	main()

