import requests
from requests.auth import HTTPBasicAuth
from frappe.utils import get_datetime,getdate
import frappe
import secrets
import string
import re
import random
from frappe.utils import random_string

def generate_random_password(length=12):
	"""Generate a random password."""
	characters = string.ascii_letters + string.digits + string.punctuation
	return ''.join(random.choice(characters) for _ in range(length))

def login_credential_scheduler():
	API_KEY = 'RaNanZK6GnxVWpfi1bK5A8PryzXKpU'
	DOMAIN = 'apprendiseu.talentlms.com'
	users_list_endpoint = f'https://{DOMAIN}/api/v1/users'

	# Fetch participants
	participants = frappe.get_all('Participant', fields=['name', 'email'])

	for participant in participants:
		try:
			email = participant.get('email')
			if not email:
				frappe.log_error(f"Participant {participant['name']} has no email.", "TalentLMS User Check")
				continue

			# Fetch user data from TalentLMS
			response = requests.get(
				users_list_endpoint,
				auth=HTTPBasicAuth(API_KEY, ''),
				params={"email": email},
				headers={"Content-Type": "application/json"}
			)
			response.raise_for_status()  # Raise error for bad status
			users = response.json()

			if not users:
				frappe.log_error(f"No TalentLMS users found for email {email}.", "TalentLMS User Check")
				continue

			user_data = users[0] if isinstance(users, list) else users
			user_id = user_data.get('id')
			courses = user_data.get('courses', [])

			participant_doc = frappe.get_doc('Participant', participant['name'])
			for online_entry in participant_doc.get('online', []):
				for course in courses:
					if online_entry.get('course_id') == course.get('id'):
						frappe.log_error(f"Matching course found for participant {participant['name']}: {course['id']}")
						online_entry.progress_status = course.get('completion_status_formatted')
						online_entry.date_begin = getdate(course.get('enrolled_on'))
						if course.get('completed_on'):
							online_entry.date_end = getdate(course.get('completed_on'))
						else:
							online_entry.date_end = None  # Ensure it's blank
						
					   
						# You might want to update something here if needed
			participant_doc.save()

		except requests.RequestException as e:
			frappe.log_error(f"Request error for email {email}", "TalentLMS API Error")
		except Exception as e:
			frappe.log_error(f"Unexpected error for participant {participant['name']}: ", "TalentLMS Scheduler")

def login_credential(doc, method=None):
	"""
	Function to check if a user exists in TalentLMS and update document data.
	"""
	# Constants

	# API_KEY = 'RaNanZK6GnxVWpfi1bK5A8PryzXKpU'
	# DOMAIN = 'apprendiseu.talentlms.com'
	CONF = frappe.get_doc("Talent LMS Settings")
	API_KEY = frappe.utils.password.get_decrypted_password("Talent LMS Settings", CONF.name, "api_key")
	DOMAIN = CONF.domain
	if not API_KEY:
		frappe.log_error(f"API KEY not found for document {doc.name}", 'Talent LMS Settings')
		return {"status": "error", "message": "API KEY not found"}
	if not DOMAIN:
		frappe.log_error(f"DOMAIN not found for document {doc.name}", 'Talent LMS Settings')
		return {"status": "error", "message": "DOMAIN not found"}
	if not doc.email:
		frappe.log_error(f"No email found for document {doc.name}", 'TalentLMS User Check')
		return {"status": "error", "message": "No email provided"}

	email = doc.email
	users_list_endpoint = f'https://{DOMAIN}/api/v1/users'

	try:
		# API Request to TalentLMS
		response = requests.get(
			users_list_endpoint,
			auth=HTTPBasicAuth(API_KEY, ''),
			params={"email": email},
			headers={"Content-Type": "application/json"}
		)
		response.raise_for_status()
		users = response.json()

		if not users:
			frappe.log_error(f"User {email} not found in TalentLMS.", 'TalentLMS User Check')
			return {"status": "not_found", "message": f"User with email {email} not found in TalentLMS."}

		# Extract user data
		user_data = users[0] if isinstance(users, list) else users
		user_id = user_data.get('id')
		courses = user_data.get('courses', [])

		if not user_id:
			frappe.log_error(f"No user ID found for email {email}.", 'TalentLMS User Check')
			return {"status": "error", "message": "No user ID in response"}

		# Generate random password
		random_password = generate_random_password()

		# Process courses
		for course in courses:
			course_id = course.get('id', 'Unknown Course')
			existing_row = next(
				(row for row in (doc.get("online") or []) if row.user_id == user_id and row.course_id == course_id),
				None
			)

			for offer in doc.offer_list:
				try:
					product_bundle = frappe.get_doc('Product Bundle', offer.offer)
				except frappe.DoesNotExistError:
					frappe.log_error(f"Product Bundle {offer.offer} not found.")
					continue

				for bundle_item in product_bundle.items:
					try:
						item = frappe.get_doc('Item', {"item_code": bundle_item.item_code})
					except frappe.DoesNotExistError:
						frappe.log_error(f"Item {bundle_item.item_code} not found.")
						continue

					if item.item_group == 'Online':
						if existing_row:
							existing_row.online_course = item.name
						else:
							doc.append("online", {
								"user_id": user_id,
                                "date_begin" :getdate(course.get('enrolled_on')),
                                "progress_status" : course.get('completion_status_formatted'),
								"initial__pw": random_password,
								"online_course": item.name,
                                'booking_id' : offer.booking_id,
								"course_id": course_id,
								"date_required_to_complete": getdate(offer.start_date)
							})

						frappe.log_error(f"Processed course {course_id} for user {user_id}.{offer.start_date}", 'TalentLMS User Check')

		return {"status": "success", "user": user_data}

	except requests.exceptions.RequestException as e:
		frappe.log_error(f"Error during TalentLMS API call: ", 'TalentLMS User Check')
		return {"status": "error", "message": "API request failed"}

    
        



# def online_manually(doc, method=None):
#     if not doc.edoobox_creation:
#         for offer in doc.offer_list:
#             product_bundle = None
#             item = None

#             # Try to get Product Bundle first
#             try:
#                 product_bundle = frappe.get_doc('Product Bundle', offer.offer)
#             except frappe.DoesNotExistError:
#                 pass  # If it doesn't exist, move on to check for an Item

#             # If no Product Bundle, try getting it as an Item
#             if not product_bundle:
#                 try:
#                     item = frappe.get_doc('Item', offer.offer)
#                 except frappe.DoesNotExistError:
#                     frappe.log_error(
#                         f"Neither Product Bundle nor Item found for {offer.offer} in document {doc.name}.",
#                         'Online Manually Check'
#                     )
#                     continue

#             # If it's a Product Bundle, process its items
#             if product_bundle:
#                 for bundle_item in product_bundle.items:
#                     try:
#                         item = frappe.get_doc('Item', bundle_item.item_code)
#                     except frappe.DoesNotExistError:
#                         frappe.log_error(
#                             f"Item {bundle_item.item_code} not found in Product Bundle {offer.offer}.",
#                             'Online Manually Check'
#                         )
#                         continue

#                     if item.item_group == 'Online':
#                         add_online_course(doc, item, offer)

#             # If it's a standalone Item, process it directly
#             elif item and item.item_group == 'Online':
#                 add_online_course(doc, item, offer)

#     return {"status": "success"}

        

    

# def add_online_course(doc, item, offer):
#     """Helper function to add an online course entry."""
#     existing_row = next((row for row in doc.online if row.online_course == item.name), None)

#     if not existing_row:
#         doc.append("online", {
#             "initial__pw": generate_random_password(),
#             "online_course": item.name,
#             "date_required_to_complete": getdate(offer.start_date),
#         })

#     frappe.log_error(
#         f"Processed course {getattr(offer, 'course_id', 'Unknown')} for user {getattr(offer, 'user_id', 'Unknown')} in document {doc.name}.",
#         'TalentLMS User Check'
#     )









# import frappe
# import requests
# from requests.auth import HTTPBasicAuth
# from frappe.utils import getdate

# def login_credential(doc, method=None):
#     """Fetch user data from TalentLMS and process online courses manually."""
    
#     API_KEY = 'RaNanZK6GnxVWpfi1bK5A8PryzXKpU'  # Secure API key retrieval
#     DOMAIN = 'apprendiseu.talentlms.com'

#     if not API_KEY:
#         frappe.log_error("TalentLMS API key not found in configuration.", "TalentLMS User Check")
#         return {"status": "error", "message": "API key not configured"}

#     if not doc.email:
#         frappe.log_error(f"No email found for document {doc.name}", "TalentLMS User Check")
#         return {"status": "error", "message": "No email provided"}

#     email = doc.email
#     users_list_endpoint = f"https://{DOMAIN}/api/v1/user/email:{email}"

#     response = requests.get(
#         users_list_endpoint,
#         auth=HTTPBasicAuth(API_KEY, ''),
#         headers={"Content-Type": "application/json"}
#     )

#     # Handle cases where the user is NOT found (404)
#     if response.status_code != 404:
#         frappe.log_error(f"User {email} not found in TalentLMS. Adding only item names.", "TalentLMS User Check")
#         for offer in doc.offer_list:
#             process_offer_courses(doc, offer, None, None, [])  # No user_id, no courses
#         return {"status": "not_found", "message": f"User with email {email} not found. Only item names added."}

#     # If the response is NOT 404, check for other errors
#     if response.status_code == 200:
#         frappe.log_error(f"TalentLMS API error: {response.status_code} - {response.text}", "TalentLMS User Check")
#         return {"status": "error", "message": f"TalentLMS API error: {response.status_code}"}

#     # User found, process their data
#     user_data = response.json()

#     # Generate a random password (Always needed)
#     random_password = generate_random_password()
    
#     user_id = user_data.get('id')
#     courses = user_data.get('courses', [])

#     for offer in doc.offer_list:
#         process_offer_courses(doc, offer, user_id, random_password, courses)

#     return {"status": "success", "user": user_data}

# def process_offer_courses(doc, offer, user_id, random_password, courses):
#     """Process courses from offers and append to online table."""
    
#     item_doc = None
#     product_bundle = None

#     if frappe.db.exists('Product Bundle', offer.offer):
#         product_bundle = frappe.get_doc('Product Bundle', offer.offer)
    
#     if not product_bundle and frappe.db.exists('Item', offer.offer):
#         item_doc = frappe.get_doc('Item', offer.offer)

#     if not product_bundle and not item_doc:
#         frappe.log_error(f"Neither Product Bundle nor Item found for {offer.offer} in document {doc.name}.", "TalentLMS User Check")
#         return

#     items_to_process = product_bundle.items if product_bundle else [item_doc]

#     for bundle_item in items_to_process:
#         item_code = bundle_item.item_code if product_bundle else bundle_item.name

#         # Fetch item only if product_bundle exists
#         item = frappe.get_doc('Item', item_code) if product_bundle else item_doc

#         if item.item_group == "Online":
#             existing_row = next((row for row in doc.online if row.online_course == item.name), None)
#             if not existing_row:
#                 doc.append("online", {
#                     "user_id": user_id,  # Will be None if user not found
#                     "initial__pw": random_password if user_id else None,  # Only set password if user exists
#                     "online_course": item.name,
#                     "booking_id": offer.booking_id,
#                     "course_id": next((c.get("id") for c in courses if c.get("id")), None) if user_id else None,
#                     "date_required_to_complete": getdate(offer.start_date)
#                 })
    
#     frappe.log_error(f"Processed courses for user {user_id if user_id else 'Pending User'} in document {doc.name}.", "TalentLMS User Check")



