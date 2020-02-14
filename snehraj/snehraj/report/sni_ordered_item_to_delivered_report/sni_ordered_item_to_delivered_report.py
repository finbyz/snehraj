# Copyright (c) 2013, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe import _, msgprint

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		_("Sales Order") + ":Link/Sales Order:120",
		_("Customer") + ":Link/Customer:120",
		_("Distributor Name") + ":Data:150",
		_("Date") + ":Date:100",
		_("City") + ":Data:100",
		_("Retailer Name") + ":Link/Retailer:100",
		_("Product Name") + ":Link/Item:120",
		_("MRP") + ":Float:80",
		_("Qty") + ":Float:60",
		_("Qty UOM") + ":Data:60",
		_("Delivered Qty") + ":Float:100",
		_("Qty to Deliver") + ":Float:100",
		_("Available Qty") + ":Float:100",
		_("Projected Qty") + ":Float:100",
		_("Item Delivery Date") + ":Date:100"					
	]

def get_data(filters):
	conditions = ''

	if filters.get('date_range'):
		conditions += " and so.delivery_date between '%s' and '%s' " % (filters.date_range[0], filters.date_range[1])

	data = frappe.db.sql("""
		SELECT 
		 so.name as "Sales Order",
		 so.customer as "Customer",
		 so.customer_name as "Distributor Name",
		 so.transaction_date as "Date",
		 a.city as "City",
	 	 so.retailer as "Retailer Name",
		 soi.item_code as "Product Name",
		 soi.price_per_piece as "MRP",
		 soi.qty as "Qty",
		 soi.uom as "Qty UOM",
		 soi.delivered_qty as "Delivered Qty",
		 (soi.qty - ifnull(soi.delivered_qty, 0)) as "Qty to Deliver",
		 bin.actual_qty as "Available Qty",
		 bin.projected_qty as "Projected Qty",
		 soi.delivery_date as "Item Delivery Date"
		from
		 `tabSales Order` as so JOIN `tabSales Order Item` as soi
		 LEFT JOIN `tabBin` as bin ON (bin.item_code = soi.item_code
		 and bin.warehouse = soi.warehouse) LEFT JOIN `tabAddress` as a ON (a.name = so.retailer_address_name)
		where
		 soi.parent = so.name
		 and so.docstatus = 1
		 and so.status not in ("Stopped", "Closed")
		 and ifnull(soi.delivered_qty,0) < ifnull(soi.qty,0)
		 {conditions}
		order by so.transaction_date asc
		""".format(conditions = conditions))
	
	return data
