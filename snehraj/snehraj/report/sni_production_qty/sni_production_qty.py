# Copyright (c) 2013, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, today, cstr

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		_("Item Name") + "::140",
		_("Item Group") + ":Link/Item Group:100",
		_("Brand") + ":Link/Brand:100",
		_("Warehouse") + ":Link/Warehouse:120",\
		_("Ordered Qty (Stock UOM)") + ":Float:140",
		_("No of Pieces") + ":Float:80",
		_("No of Boxes") + ":Float:80",
		_("Current Stock") + ":Float:100",
		_("Production Qty") + ":Float:100",
		_("Qty to be Produced") + ":Float:120",
	]

def get_data(filters):
	bin_list = get_bin_list(filters)
	item_map = get_item_map(filters.get("item_code"))
	warehouse_company = {}
	data = []

	for bin in bin_list:
		item = item_map.get(bin.item_code)

		if not item:
			# likely an item that has reached its end of life
			continue

		# item = item_map.setdefault(bin.item_code, get_item(bin.item_code))
		company = warehouse_company.setdefault(bin.warehouse,
			frappe.db.get_value("Warehouse", bin.warehouse, "company"))

		if filters.brand and filters.brand != item.brand:
			continue

		elif filters.company and filters.company != company:
			continue

		no_cf = get_conversion_factor(item.name, 'Nos')

		no_of_piece = 0
		if no_cf:
			no_of_piece = bin.reserved_qty / flt(no_cf)

		box_cf = get_conversion_factor(item.name, 'Box')

		no_of_box = 0
		if box_cf:
			no_of_box = bin.reserved_qty / flt(box_cf)

		if bin.reserved_qty == 0:
			qty_to_produce = 0
		else:
			qty_to_produce = bin.reserved_qty - bin.actual_qty - bin.planned_qty

			if qty_to_produce < 0:
				qty_to_produce = 0

		data.append([item.item_name, item.item_group, item.brand, bin.warehouse,
			bin.reserved_qty, no_of_piece, no_of_box, bin.actual_qty, bin.planned_qty, qty_to_produce])

	return data

def get_bin_list(filters):
	conditions = []

	if filters.range:
		conditions.append("bin.creation BETWEEN '{0}' AND '{1}'".format(filters.range[0], filters.range[1]))

	if filters.item_code:
		conditions.append("item_code = '%s' "%filters.item_code)
		
	if filters.warehouse:
		warehouse_details = frappe.db.get_value("Warehouse", filters.warehouse, ["lft", "rgt"], as_dict=1)

		if warehouse_details:
			conditions.append(" exists (select name from `tabWarehouse` wh \
				where wh.lft >= %s and wh.rgt <= %s and bin.warehouse = wh.name)"%(warehouse_details.lft,
				warehouse_details.rgt))

	bin_list = frappe.db.sql("""select item_code, warehouse, actual_qty, planned_qty, ordered_qty, reserved_qty
		from tabBin bin {conditions} order by item_code, warehouse""".format(
			conditions=" where " + " and ".join(conditions) if conditions else ""), as_dict=1)

	return bin_list

def get_item_map(item_code):
	"""Optimization: get only the item doc"""

	condition = ""
	if item_code:
		condition = 'and item_code = "{0}"'.format(frappe.db.escape(item_code, percent=False))

	items = frappe.db.sql("""select * from `tabItem` item
		where is_stock_item = 1
		and disabled=0
		{condition}
		and (end_of_life > %(today)s or end_of_life is null or end_of_life='0000-00-00')
		and exists (select name from `tabBin` bin where bin.item_code=item.name)"""\
		.format(condition=condition), {"today": today()}, as_dict=True)

	item_map = frappe._dict()
	for item in items:
		item_map[item.name] = item

	return item_map

def get_conversion_factor(item, uom):
	conversion_factor = frappe.db.sql("""select uom.conversion_factor 
		from `tabUOM Conversion Detail` uom join `tabItem` item on (uom.parent = item.name)
		where uom.parent = %(item)s and uom.uom = %(uom)s""", {'item': item, 'uom': uom})

	if conversion_factor:
		return conversion_factor[0][0]

	return False
