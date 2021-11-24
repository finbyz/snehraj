# -*- coding: utf-8 -*-
# Copyright (c) 2019, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, get_url_to_form
from erpnext.accounts.utils import get_fiscal_year
from erpnext.stock.get_item_details import get_item_details

import json

class JobworkReceipt(Document):
	def before_naming(self):
		fy = get_fiscal_year(self.get("posting_date"))[0]
		fiscal = frappe.db.get_value("Fiscal Year", fy, 'fiscal')
		if fiscal:
			self.fiscal = fiscal
		else:
			fy_years = fy.split("-")
			fiscal = fy_years[0][2:] + '-' + fy_years[1][2:]
			self.fiscal = fiscal

	def validate(self):
		self.validate_items()
		self.calculate_total()

	def validate_items(self):
		if not self.get('items'):
			frappe.throw(_("Items Table is Mandatory!"))

	def calculate_total(self):
		self.total_qty = sum([flt(row.qty) for row in self.items])
		self.total_amount = sum([flt(row.basic_amount) for row in self.items])

	@frappe.whitelist()
	def insert_item_details(self):

		if not self.item:
			frappe.throw(_("Please select item first."))

		elif not self.get('paper_roll_detail'):
			frappe.throw(_("Please add Paper Roll Detials."))

		total_qty = sum(list(map(lambda d: flt(d.qty, 3) ,self.paper_roll_detail)))

		if total_qty != flt(self.total_quantity):
			frappe.throw(_("The sum of quantity {} does not match with total quantity {}.".format(total_qty, self.total_quantity)))

		if len(self.paper_roll_detail) != cint(self.no_of_rolls):
			frappe.throw(_("The number of rolls should not be less or greater than {}.".format(self.no_of_rolls)))

		args = {
			'item_code': self.item,
			'warehouse': self.warehouse,
			'customer': self.customer,
			'update_stock': 0,
			'conversion_rate': 1,
			'company': self.company,
			'transaction_date': self.posting_date,
			'ignore_pricing_rule': 1,
			'doctype': self.doctype,
			'qty': self.total_quantity or 1,
			'conversion_factor': 1,
		}

		item_details = get_item_details(args)

		for row in self.paper_roll_detail:
			item = frappe._dict()
			item.item_code = self.item
			item.item_name = item_details.item_name
			item.description = item_details.description
			item.image = item_details.image
			item.qty = row.qty
			item.stock_qty = item_details.stock_qty
			item.transfer_qty = item_details.stock_qty
			item.basic_rate = item_details.rate or self.rate
			item.basic_amount = flt(row.qty * item.basic_rate)
			item.uom = item_details.uom
			item.conversion_factor = item_details.conversion_factor
			item.stock_uom = item_details.stock_uom
			item.t_warehouse = self.warehouse
			item.roll_no = row.roll_no

			self.append('items', item)
		
		self.set('paper_roll_detail', [])
		self.item = ''
		self.rate = 0.0
		self.total_quantity = 0.0
		self.no_of_rolls = 0

		self.calculate_total()

	def on_submit(self):
		self.create_stock_entry()

	def on_cancel(self):
		self.cancel_stock_entry()

	def create_stock_entry(self):
		se = frappe.new_doc("Stock Entry")
		se.naming_series = "STE-.fiscal.-"
		se.stock_entry_type = "Material Receipt"
		se.purpose = "Material Receipt"
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time
		se.company = self.company
		se.set_posting_time = self.set_posting_time
		se.to_warehouse = self.warehouse
		se.fiscal = self.fiscal

		for row in self.items:
			se.append("items",{
				'item_code': row.item_code,
				't_warehouse': row.t_warehouse,
				'qty': row.qty,
				'basic_rate': row.basic_rate,
				'uom': row.uom,
				'conversion_factor': row.conversion_factor,
			})

		for row in self.additional_costs:
			se.append('additional_costs', {
				'posting_date': row.posting_date,
				'expense_account': row.expense_account,
				'credit_account': row.credit_account,
				'description': row.description,
				'amount': row.amount,
			})

		try:
			se.save()
			se.submit()
		except:
			frappe.db.rollback()
			frappe.throw(_("Error creating Stock Entry"), title="Error")
		else:
			self.update_batch_no(se)
			self.db_set('stock_entry', se.name)
			url = get_url_to_form("Stock Entry", se.name)
			frappe.msgprint("Stock Entry - <a href='{url}'>{doc}</a> created of Material Receipt.".format(url=url, doc=frappe.bold(se.name)))
			frappe.db.commit()

	def update_batch_no(self, se):
		for row, d in zip(self.items, se.items):
			if row.idx == d.idx:
				row.db_set('batch_no', d.batch_no)

	def cancel_stock_entry(self):
		if self.stock_entry:
			se = frappe.get_doc("Stock Entry",self.stock_entry)
			se.cancel()
			frappe.db.commit()
			self.db_set('stock_entry','')
			url = get_url_to_form("Stock Entry", se.name)
			frappe.msgprint("Stock Entry - <a href='{url}'>{doc}</a> cancelled!".format(url=url, doc=frappe.bold(se.name)))
