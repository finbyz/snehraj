// Copyright (c) 2016, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["SNI Ordered Item to Delivered Report"] = {
	"filters": [
		{
			"fieldname": "date_range",
			"fieldtype": "DateRange",
			"label": __("Delivery Date Range"),
			"default": [frappe.datetime.add_days(frappe.datetime.nowdate(), -30), frappe.datetime.nowdate()] 
		}
	]
}
