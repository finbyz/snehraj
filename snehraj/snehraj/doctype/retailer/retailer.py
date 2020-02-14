# -*- coding: utf-8 -*-
# Copyright (c) 2018, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.contacts.address_and_contact import load_address_and_contact, delete_contact_and_address


class Retailer(Document):

	def validate(self):
		self.flags.is_new_doc = self.is_new()

	def onload(self):
		"""Load address and contacts in `__onload`"""
		load_address_and_contact(self)

	def on_trash(self):
		delete_contact_and_address('Retailer', self.name)

def customer_group_filter(doctype, txt, searchfield, start, page_len, filters):
        return frappe.db.sql("""select customer_name, customer_group from `tabCustomer`
                            where customer_group = '%s'""" % filters.get('customer_group'))