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









def login_credential(doc, method=None):
    """
    Function to check if a user exists in TalentLMS and log the response.
    """
    # Constants
    API_KEY = 'RaNanZK6GnxVWpfi1bK5A8PryzXKpU'
    DOMAIN = 'apprendiseu.talentlms.com'

    if not doc.email:
        frappe.log_error(f"No email found for document {doc.name}", 'TalentLMS User Check')
        return {"status": "error", "message": "No email provided"}

    email = doc.email  # Use the provided email from doc
    users_list_endpoint = f'https://{DOMAIN}/api/v1/users'

    try:
        # Make a GET request to check if the user exists
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

        frappe.log_error(f"User {email} found in TalentLMS.", 'TalentLMS User Check')

        # Standardize user data handling
        user_data = users[0] if isinstance(users, list) else users
        user_id = user_data.get('id')
        courses = user_data.get('courses', [])

        if not user_id:
            frappe.log_error(f"No user ID found for email {email}.", 'TalentLMS User Check')
            return {"status": "error", "message": "No user ID in response"}

        # Generate a random password
        random_password = generate_random_password()
        frappe.log_error(f"Generated Password: {random_password}")

        # Handle each course ID individually
        for course in courses:
            course_id = course.get('id', 'Unknown Course')

            # Check if an entry for the user already exists in the child table
            existing_row = next(
                (row for row in (doc.get("online") or []) if row.user_id == user_id and row.course_id == course_id),
                None
            )
            
            for i in doc.offer_list:
                product_bundle = frappe.get_doc('Product Bundle', i.offer)
                for bundle_item in product_bundle.items:
                    practical_items_test = frappe.get_doc('Item', {"Item_code": bundle_item.item_code})
                    frappe.log_error(practical_items_test)
                    if practical_items_test.item_group == 'Online':
                        if existing_row:
                            existing_row.online_course = practical_items_test.name  # Update existing row
                        else:
                            doc.append("online", {
                                "user_id": user_id,
                                # 'customer': doc.institution_invoice,
                                "initial__pw": random_password,
                                "online_course": practical_items_test.name,
                                "course_id": course_id
                            })

            frappe.log_error(f"Processed course ID {course_id} for user_id {user_id}.", 'TalentLMS User Check')

        return {"status": "success", "user": user_data}

    except requests.exceptions.RequestException as e:
        error_message = f"Error while checking TalentLMS user: {e}"
        frappe.log_error('TalentLMS User Check', error_message)
        return {"status": "error", "message": "Request failed"}


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
                        online_entry.date_end= getdate(course.get('completed_on'))
                        
                        # You might want to update something here if needed
            participant_doc.save()

        except requests.RequestException as e:
            frappe.log_error(f"Request error for email {email}", "TalentLMS API Error")
        except Exception as e:
            frappe.log_error(f"Unexpected error for participant {participant['name']}: {str(e)}", "TalentLMS Scheduler")
