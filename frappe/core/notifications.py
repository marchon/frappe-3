# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe

def get_notification_config():
	return {
		"for_doctype": {
			"Error Log": {"seen": 0},
			"Communication": {"status": "Open", "communication_type": "Communication"},
			"ToDo": "frappe.core.notifications.get_things_todo",
			"Event": "frappe.core.notifications.get_todays_events",
			"Error Snapshot": {"seen": 0, "parent_error_snapshot": None},
		},
		"for_other": {
			"Likes": "frappe.core.notifications.get_unseen_likes",
			"Chat": "frappe.core.notifications.get_unread_messages",
			"Email": "frappe.core.notifications.get_unread_emails",
		}
	}

def get_things_todo(as_list=False):
	"""Returns a count of incomplete todos"""
	data = frappe.get_list("ToDo",
		fields=["name", "description"] if as_list else "count(*)",
		filters=[["ToDo", "status", "=", "Open"]],
		or_filters=[["ToDo", "owner", "=", frappe.session.user],
			["ToDo", "assigned_by", "=", frappe.session.user]],
		as_list=True)

	if as_list:
		return data
	else:
		return data[0][0]

def get_todays_events(as_list=False):
	"""Returns a count of todays events in calendar"""
	from frappe.desk.doctype.event.event import get_events
	from frappe.utils import nowdate
	today = nowdate()
	events = get_events(today, today)
	return events if as_list else len(events)

def get_unread_messages():
	"returns unread (docstatus-0 messages for a user)"
	return frappe.db.sql("""\
		SELECT count(*)
		FROM `tabCommunication`
		WHERE communication_type in ('Chat', 'Notification')
		AND reference_doctype = 'User'
		AND reference_name = %s
		and modified >= DATE_SUB(NOW(),INTERVAL 1 YEAR)
		AND seen=0
		""", (frappe.session.user,))[0][0]

def get_unseen_likes():
	"""Returns count of unseen likes"""
	return frappe.db.sql("""select count(*) from `tabCommunication`
		where
			communication_type='Comment'
			and modified >= DATE_SUB(NOW(),INTERVAL 1 YEAR)
			and comment_type='Like'
			and owner is not null and owner!=%(user)s
			and reference_owner=%(user)s
			and seen=0""", {"user": frappe.session.user})[0][0]

def get_unread_emails():
	"returns unread emails for a user"

	return frappe.db.sql("""\
		SELECT count(*)
		FROM `tabCommunication`
		WHERE communication_type='Communication'
		AND communication_medium="Email"
		AND email_status not in ("Spam", "Trash")
		AND email_account in (
			SELECT distinct email_account from `tabUser Email` WHERE parent=%(user)s
		)
		AND modified >= DATE_SUB(NOW(),INTERVAL 1 YEAR)
		AND seen=0
		""", {"user": frappe.session.user})[0][0]