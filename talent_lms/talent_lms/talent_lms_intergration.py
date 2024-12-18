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







# def login_credential(doc, method=None):
#     """Check if a user exists by email in TalentLMS and update their password if inactive."""
   

#     API_KEY = 'RaNanZK6GnxVWpfi1bK5A8PryzXKpU'
#     DOMAIN = 'apprendiseu.talentlms.com'
    
#     if not doc.email:
#         frappe.log_error(f"No email found for document {doc.name}", 'TalentLMS User Check')
#         return None
    
#     email = doc.email  # Fetch email dynamically from `doc`
#     users_list_endpoint = f'https://{DOMAIN}/api/v1/users'
    
#     try:
#         response = requests.get(
#             users_list_endpoint,
#             auth=HTTPBasicAuth(API_KEY, ''),
#             params={"email": email},
#             headers={"Content-Type": "application/json"}
#         )
#         response.raise_for_status()
        
#         # Parse response JSON
#         users = response.json()
        
#         if users:
#             # Log the found user information
#             frappe.log(f"Users found for email {email}")

#             # Process the first user (if applicable)
#             user = users[0] if isinstance(users, list) else users
#             user_id = user.get('id')
#             user_status = user.get('status', 'Unknown')
#             courses = user.get('courses', [])

#             frappe.log(f"User ID: {user_id}, Status: {user_status}")
#             random_password = generate_random_password()
#             frappe.log_error(random_password)
            
#             # Ensure we append to the 'online' field rather than overwrite it
#             online_data = doc.get('online') or []
#             unique_entries = {entry.get('user_id') + entry.get('date_begin'): entry for entry in online_data}

#             # Loop through the courses and process them
#             if courses:
#                 for course in courses:
#                     course_name = course.get('name', 'Unknown Course')
#                     uid  = course.get('id', 'Unknown Course')
#                     # role_n = course.get('role', 'Unknown Course')
#                     # s = course.get('completion_status')

#                     # completed_on = course.get('completed_on')
#                     # enrolled_on = course.get('enrolled_on')
                    
#                     # Initialize date_str and d_c
#                     # date_str = None
#                     # d_c = None
                    
#                     # if enrolled_on:
#                     #     datetime_obj = getdate(enrolled_on)
#                     #     date_str = datetime_obj.strftime("%Y/%m/%d") if datetime_obj else None
                    
#                     # if completed_on:
#                     #     completed_on_d = getdate(completed_on)
#                     #     d_c = completed_on_d.strftime("%Y/%m/%d") if completed_on_d else None
                    
#                     frappe.log_error(f"Processing course: {course_name}, Date: {date_str}, Completed On: {d_c}")
                    
#                     # Check if the entry already exists in `online_data` (based on user_id and date_begin)
#                     entry_key = f"{user_id}{date_str}"
#                     if entry_key not in unique_entries:
#                         # Add a single dictionary with user_id, role_n (initial__pw), date_begin, and progress_status
#                         online_data.append({
#                             "user_id": user_id,
#                             "initial__pw": random_password,
#                             # 'date_begin': date_str,
#                             # 'ate_end' : d_c,
#                             # 'progress_status': s,
#                             'course_id' : uid
#                         })
#                         unique_entries[entry_key] = {
#                             "user_id": user_id,
#                             "initial__pw": random_password,
#                             # 'date_begin': (date_str),
#                             # 'date_end' : (d_c),
#                             'progress_status': s,
#                             'course_id' : uid
#                         }
#                         frappe.log_error(f"Added new course entry for User ID: {user_id}, Course: {course_name}", 'TalentLMS User Check')
#                     else:
#                         frappe.log_error(f"Duplicate entry found for User ID: {user_id} on {date_str}", 'TalentLMS User Check')
#             else:
#                 frappe.log_error(f"No courses found for User ID: {user_id}", level='DEBUG')
            
#             # Update `doc.online` with accumulated data
#             doc.set('online', list(unique_entries.values()))
            
#             return user  # Return the first user object
#         else:
#             frappe.log_error(f"No users found with email: {email}", 'TalentLMS User Check')
#             return None
    
#     except requests.exceptions.RequestException as e:
#         # Log any request exception
#         frappe.log_error(f"Request Exception: {str(e)}", 'TalentLMS API Error')
#         return None


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

    email =doc.email  # Use the provided email from doc
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

        # Fetch practical item names
        item_name_EN = frappe.db.get_value('Item', {'item_group': 'Online', 'custom_language': 'EN'}, 'name')
        item_name_DE = frappe.db.get_value('Item', {'item_group': 'Online', 'custom_language': 'DE'}, 'name')

        item_name = item_name_EN
        for i in doc.offer_list:
            if i.language == 'German':
                item_name = item_name_DE
                break

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

        # Prepare a comma-separated list of course IDs
        course_ids = []
        for course in courses:
            course_id = course.get('id', 'Unknown Course')
            course_ids.append(course_id)

        course_ids_str = ", ".join(course_ids)

        # Check if an entry for the user already exists in the child table
        existing_row = next((row for row in (doc.get("online") or []) if row.user_id == user_id), None)

        if existing_row:
            existing_row.course_id = course_ids_str
        else:
            doc.append("online", {
                "user_id": user_id,
                'customer': doc.institution_invoice,
                "initial__pw": random_password,
                "online_course": item_name,
                "course_id": course_ids_str
            })

        frappe.log_error(f"Added or updated entries for user_id {user_id}.", 'TalentLMS User Check')
        return {"status": "success", "user": user_data}

    except requests.exceptions.RequestException as e:
        error_message = f"Error while checking TalentLMS user:"
        frappe.log_error(error_message, 'TalentLMS User Check')
        return {"status": "error", "message": "Request failed"}
 
        

   





def login_credential_scheduler():
    import frappe
    from frappe.utils import getdate
    import requests
    from requests.auth import HTTPBasicAuth

    API_KEY = 'RaNanZK6GnxVWpfi1bK5A8PryzXKpU'
    DOMAIN = 'apprendiseu.talentlms.com'
    users_list_endpoint = f'https://{DOMAIN}/api/v1/users'

    # Fetch participants
    participants = frappe.get_all(
        'Participants',
        filters={'status': 'Draft'},
        fields=['name', 'email']
    )

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
            response.raise_for_status()
            users = response.json()

            if not users:
                frappe.log_error(f"No TalentLMS users found for email {email}.", "TalentLMS User Check")
                continue

            user_data = users[0] if isinstance(users, list) else users
            user_id = user_data.get('id')
            courses = user_data.get('courses', [])

            # Fetch and update the full participant document
            participant_doc = frappe.get_doc('Participants', participant['name'])
            latest_enrollment_date = None
            latest_course_status = None
            latest_course_id = None

            for online_entry in participant_doc.get('online', []):
                matched = False
                course_ids = [cid.strip() for cid in online_entry.get('course_id', '').split(',')]
                for course_id in course_ids:
                    for course in courses:
                        if str(course.get('id')) == course_id:
                            matched = True
                            online_entry.progress_status = course.get('completion_status_formatted')
                            online_entry.date_begin = getdate(course.get('enrolled_on'))

                            # Only set date_end if completed_on is not None
                            if course.get('completed_on'):
                                online_entry.date_end = getdate(course.get('completed_on'))
                            else:
                                online_entry.date_end = None  # Ensure it's blank

                            enrolled_on = course.get('enrolled_on')
                            if enrolled_on:
                                enrollment_date = getdate(enrolled_on)
                                if not latest_enrollment_date or enrollment_date > latest_enrollment_date:
                                    latest_enrollment_date = enrollment_date
                                    latest_course_status = course.get('completion_status_formatted')
                                    latest_course_id = course_id
                            break
                    if matched:
                        break

                if not matched:
                    frappe.log_error(
                        f"No match for Course IDs {online_entry.get('course_id')} for participant {participant['name']}.",
                        "Course ID Mismatch"
                    )

            # Update additional fields
            if latest_enrollment_date:
                participant_doc.latest_enrollment_date = latest_enrollment_date
            if latest_course_status:
                participant_doc.latest_course_status = latest_course_status
            if latest_course_id:
                participant_doc.latest_course_id = latest_course_id

            # Save the participant document
            participant_doc.save(ignore_permissions=True)
            frappe.db.commit()

        except Exception as e:
            frappe.log_error(f"Error for participant {participant.get('name', 'unknown')} with email {email}: ",
                             'TalentLMS User Check')
            continue

    return {"status": "success", "message": "Process completed successfully"}
