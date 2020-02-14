# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "snehraj"
app_title = "Snehraj"
app_publisher = "Finbyz Tech Pvt Ltd"
app_description = "Custom App For Snehraj"
app_icon = "octicon octicon-book"
app_color = "Orange"
app_email = "info@finbyz.com"
app_license = "GPL 3.0"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/snehraj/css/snehraj.css"
# app_include_js = [
# 	"assets/js/summernote.min.js",
# 	"assets/js/comment_desk.min.js",
# 	"assets/js/editor.min.js",
# 	"assets/js/timeline.min.js"
# ]

# app_include_css = [
# 	"assets/css/snehraj.min.css",
# 	# "assets/css/summernote.min.css"
# ]
# app_include_js = "/assets/snehraj/js/snehraj.js"

# include js, css files in header of web template
# web_include_css = "/assets/snehraj/css/snehraj.css"
# web_include_js = "/assets/snehraj/js/snehraj.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "snehraj.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "snehraj.install.before_install"
# after_install = "snehraj.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "snehraj.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

override_whitelisted_methods = {
	"frappe.core.page.permission_manager.permission_manager.get_roles_and_doctypes": "snehraj.permission.get_roles_and_doctypes",
	"frappe.core.page.permission_manager.permission_manager.get_permissions": "snehraj.permission.get_permissions",
	"frappe.core.page.permission_manager.permission_manager.add": "snehraj.permission.add",
	"frappe.core.page.permission_manager.permission_manager.update": "snehraj.permission.update",
	"frappe.core.page.permission_manager.permission_manager.remove": "snehraj.permission.remove",
	"frappe.core.page.permission_manager.permission_manager.reset": "snehraj.permission.reset",
	"frappe.core.page.permission_manager.permission_manager.get_users_with_role": "snehraj.permission.get_users_with_role",
	"frappe.core.page.permission_manager.permission_manager.get_standard_permissions": "snehraj.permission.get_standard_permissions",
	"frappe.utils.print_format.download_multi_pdf": "snehraj.print_format.download_multi_pdf",
	# "erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry": "snehraj.api.make_stock_entry",
}

doc_events = {
	"Sales Order": {
		"validate": "snehraj.api.so_validate",
		"before_save": "snehraj.api.so_before_save",
		"on_submit": "snehraj.api.so_on_submit",
	},
	"Delivery Note": {
		"on_submit": "snehraj.api.dn_on_submit",
		"before_cancel": "snehraj.api.dn_before_cancel",
		"on_update_after_submit": "snehraj.api.dn_on_update_after_submit",
	},
	"Batch": {
		'before_naming': "snehraj.batch_valuation.override_batch_autoname",
	},
	"Purchase Receipt": {
		"validate": "snehraj.batch_valuation.pr_validate",
		"on_cancel": "snehraj.batch_valuation.pr_on_cancel",
	},
	"Purchase Invoice": {
		"validate": "snehraj.batch_valuation.pi_validate",
		"on_cancel": "snehraj.batch_valuation.pi_on_cancel",
		"before_save": "snehraj.api.pi_before_save"
	},
	"Stock Entry": {
		"validate": "snehraj.batch_valuation.stock_entry_validate",
		"on_submit": "snehraj.batch_valuation.stock_entry_on_submit",
		"on_cancel": "snehraj.batch_valuation.stock_entry_on_cancel",
	},
	"Landed Cost Voucher": {
		"validate": [
			"snehraj.batch_valuation.lcv_validate",
			"snehraj.api.lcv_validate",
		],
		"on_submit": "snehraj.batch_valuation.lcv_on_submit",
		"on_cancel": [
			"snehraj.batch_valuation.lcv_on_cancel",
			"snehraj.api.lcv_on_cancel",
		],
	},
	"BOM":{
		"before_save":"snehraj.api.bom_before_save"
	},
	("Sales Invoice", "Purchase Invoice", "Payment Request", "Payment Entry", "Journal Entry", "Material Request", "Purchase Order", "Work Order", "Production Plan", "Stock Entry", "Quotation", "Sales Order", "Delivery Note", "Purchase Receipt", "Packing Slip"): {
		"before_naming": "snehraj.api.docs_before_naming",
	},
	"Job Card": {
		"validate": "snehraj.api.job_card_validate",
		"on_submit": "snehraj.api.job_card_on_submit",
		"on_cancel": "snehraj.api.job_card_on_cancel",
	},
}



# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"snehraj.tasks.all"
# 	],
# 	"daily": [
# 		"snehraj.tasks.daily"
# 	],
# 	"hourly": [
# 		"snehraj.tasks.hourly"
# 	],
# 	"weekly": [
# 		"snehraj.tasks.weekly"
# 	]
# 	"monthly": [
# 		"snehraj.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "snehraj.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "snehraj.event.get_events"
# }
