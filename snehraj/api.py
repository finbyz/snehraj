from __future__ import unicode_literals
import frappe, erpnext
from frappe import _, db
from frappe.utils import flt, cint, get_url_to_form, nowdate, cstr, fmt_money, get_fullname, getdate
from frappe.model.mapper import get_mapped_doc
from erpnext.utilities.product import get_price
from frappe.contacts.doctype.address.address import get_address_display, get_default_address
from frappe.contacts.doctype.contact.contact import get_contact_details, get_default_contact
from erpnext.stock.doctype.item.item import Item, get_item_defaults
from frappe.desk.reportview import get_match_cond, get_filters_cond
import json


@frappe.whitelist()
def get_party_details(party=None, party_type="Customer", ignore_permissions=False):

	if not party:
		return {}

	if not db.exists(party_type, party):
		frappe.throw(_("{0}: {1} does not exists").format(party_type, party))

	return _get_party_details(party, party_type, ignore_permissions)

def _get_party_details(party=None, party_type="Customer", ignore_permissions=False):

	out = frappe._dict({
		party_type.lower(): party
	})

	party = out[party_type.lower()]

	if not ignore_permissions and not frappe.has_permission(party_type, "read", party):
		frappe.throw(_("Not permitted for {0}").format(party), frappe.PermissionError)

	party = frappe.get_doc(party_type, party)
	
	set_address_details(out, party, party_type)
	set_contact_details(out, party, party_type)
	set_other_values(out, party, party_type)

	if party_type == 'Lead':
		out.organisation = party.company_name
	elif party_type == 'Customer':
		out.organisation = party.customer_name

	return out

def set_address_details(out, party, party_type):
	billing_address_field = "customer_address" if party_type == "Lead" \
		else party_type.lower() + "_address"
	out[billing_address_field] = get_default_address(party_type, party.name)
	
	out.address_display = get_address_display(out[billing_address_field])

def set_contact_details(out, party, party_type):
	out.contact_person = get_default_contact(party_type, party.name)

	if not out.contact_person:
		out.update({
			"contact_person": None,
			"contact_display": None,
			"contact_email": None,
			"contact_mobile": None,
			"contact_phone": None,
			"contact_designation": None,
			"contact_department": None
		})
	else:
		out.update(get_contact_details(out.contact_person))

def set_other_values(out, party, party_type):
	# copy
	if party_type=="Customer":
		to_copy = ["customer_name", "customer_group", "territory", "language"]
	else:
		to_copy = ["supplier_name", "supplier_type", "language"]
	for f in to_copy:
		out[f] = party.get(f)

@frappe.whitelist()
def item_override_before_rename(self, method, *args, **kwargs):
	Item.before_rename = item_before_rename

def item_before_rename(self, old_name, new_name, merge=False):
	if self.item_name == old_name:
		frappe.db.set_value("Item", old_name, "item_name", old_name)

	if merge:
		# Validate properties before merging
		if not frappe.db.exists("Item", new_name):
			frappe.throw(_("Item {0} does not exist").format(new_name))

		field_list = ["stock_uom", "is_stock_item", "has_serial_no", "has_batch_no"]
		new_properties = [cstr(d) for d in frappe.db.get_value("Item", new_name, field_list)]
		if new_properties != [cstr(self.get(fld)) for fld in field_list]:
			frappe.throw(_("To merge, following properties must be same for both items")
                                + ": \n" + ", ".join([self.meta.get_label(fld) for fld in field_list]))

@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	def postprocess(source, target):
		target.append('items', {
			'item_code': source.product_name,
			'item_name': source.product_name,
			'base_cost' : source.per_unit_price
			})

	doclist = get_mapped_doc("Outward Sample" , source_name,{
		"Outward Sample":{
			"doctype" : "Quotation",
			"field_map":{
				"link_to" : "quotation_to",
				"party" : "customer",
				"date" : "transaction_date" ,
			},
		}
	},target_doc, postprocess)

	return doclist

@frappe.whitelist()
def get_new_sales_order():
	return frappe.db.sql("""
		SELECT 
			`tabSales Order`.name, `tabSales Order`.retailer, `tabSales Order`.transaction_date as transaction_date
		FROM
			`tabSales Order`
		""", as_dict=1)

@frappe.whitelist()
def so_validate(self, method):
	if self._action == 'submit' and not self.override_pricing_rule:
		discount_validation(self)

@frappe.whitelist()
def so_before_save(self, method):
	get_pricing_rule_discount(self)

def get_pricing_rule_discount(self):
	from erpnext.accounts.doctype.pricing_rule.utils import get_pricing_rules, filter_pricing_rules
	from erpnext.stock.get_item_details import process_args

	parent_dict = {}

	for fieldname in self.meta.get_valid_columns():
		parent_dict[fieldname] = self.get(fieldname)

	parent_dict.update({"document_type": "Sales Order Item"})

	for item in self.get("items"):
		if not item.original_discount:
			if item.get("item_code"):
				args = parent_dict.copy()
				args.update(item.as_dict())

				args["doctype"] = self.doctype
				args["name"] = self.name

				if not args.get("transaction_date"):
					args["transaction_date"] = args.get("posting_date")

				if self.get("is_subcontracted"):
					args["is_subcontracted"] = self.is_subcontracted

			args = process_args(args)

			pricing_rules = get_pricing_rules(args)
			pricing_rule = filter_pricing_rules(args, pricing_rules)

			if pricing_rule:
				item.original_discount = pricing_rule.discount_percentage

def discount_validation(self):
	for item in self.get("items"):
		if item.discount_percentage > item.original_discount:
			so_link = get_url_to_form(self.doctype, self.name)

			recipients = ['aalapsheth@snehraj.com', 'pathiksheth@snehraj.com']
			subject = "Apporve Discount for SO - {}".format(self.name)
			message = "Please Apporve Sales Order - <b><a href='{so_link}'>{name}</a></b> of {customer} for discount - Modified By: {modified_by}".format(
				so_link=so_link, name=self.name, customer=self.customer, modified_by=self.modified_by)

			frappe.enqueue(frappe.sendmail, recipients=recipients, subject = subject, message = message)
			frappe.throw(_("Discount Percentage can not be greater than {0} in row {1}".format(item.original_discount, item.idx)))

@frappe.whitelist()
def so_on_submit(self, method):
	return
	# send_so_mail(self)

def send_so_mail(self):
	if self.sales_person == "Bijal Shah":
		attachments = []
		recipients = ['bijal.shah@snehraj.com']
		subject = "Sales Order: {} submitted".format(self.name)
		message = "Dear Bijal Shah,<br><br>Sales Order {name} is submitted by {modified_by} for customer {customer} with Total Amount of {amount}.".format(
			name=frappe.bold(self.name),
			modified_by=get_fullname(self.modified_by),
			customer=self.customer,
			amount=fmt_money(self.rounded_total, 2, self.currency))

		try:
			attachments.append(frappe.attach_print('Sales Order', self.name, print_format="Sales Order With Rate", print_letterhead=True))
		except:
			pass

		frappe.sendmail(recipients=recipients,
			subject=subject,
			message=message,
			attachments=attachments)

@frappe.whitelist()
def dn_on_update_after_submit(self, method):
	if cint(self.send_message):
		send_message(self)

def send_message(self):
	from frappe.core.doctype.sms_settings.sms_settings import send_sms

	if not self.lr_no:
		frappe.msgprint(_("Please update LR No and then try sending sms"))
		self.send_message = 0
		self.save()
		frappe.db.commit()
		return
		
	if not self.contact_mobile:
		frappe.msgprint(_("No mobile number found, so message not sent"))
		return

	message = """Snehraj Notebook Industries 
		{customer} {city_name} 
		Challan Number: {name} 
		LR Number: {lr_no} """.format(
			customer = self.customer,
			city_name = self.city_name or '',
			name = self.name,
			lr_no = self.lr_no)

	numbers = self.contact_mobile.split(",")

	send_sms(numbers, message)

@frappe.whitelist()
def dn_on_submit(self, method):
	update_sales_invoice(self)

@frappe.whitelist()
def dn_before_cancel(self, method):
	update_sales_invoice(self)

def update_sales_invoice(self):
	for row in self.items:
		if row.against_sales_invoice and row.si_detail:
			if self._action == 'submit':
				delivery_note = self.name
				dn_detail = row.name

			elif self._action == 'cancel':
				delivery_note = ''
				dn_detail = ''

			frappe.db.sql("""update `tabSales Invoice Item` 
				set dn_detail = %s, delivery_note = %s 
				where name = %s """, (dn_detail, delivery_note, row.si_detail))

@frappe.whitelist()
def insert_item_details(doc_details, item_details):
	from six import string_types

	if isinstance(doc_details, string_types):
		doc_details = json.loads(doc_details)

	doc = frappe.get_doc(doc_details)
	
	item_details = frappe._dict(json.loads(item_details))
	item_details.pop('name')
	item_details.pop('idx')

	to_remove = []
	for row in doc.items:
		if row.item_code == item_details.item_code:
			to_remove.append(row)

	[doc.remove(row) for row in to_remove]

	for row in doc.get('paper_roll_detail'):
		detail = item_details.copy()
		detail.qty = row.qty
		detail.received_qty = row.qty
		detail.stock_qty = row.qty
		detail.amount = flt(row.qty * detail.rate) * doc.conversion_rate
		detail.base_amount = flt(row.qty * detail.rate)
		detail.base_net_amount = flt(row.qty * detail.rate)
		detail.net_amount = flt(row.qty * detail.rate) * doc.conversion_rate
		detail.roll_no = row.roll_no
		
		doc.append('items', detail)


	for idx, row in enumerate(doc.get('items')):
		row.idx = idx + 1

	doc.set('paper_roll_detail', [])

	if doc.is_new():
		doc.insert()
	else:
		doc.save()

	return doc.as_dict()

@frappe.whitelist()
def get_batch_qty(filters):
	filters = json.loads(filters)
	
	args = {
		'item_code': filters.get("item_code"),
		'warehouse': filters.get("warehouse"),
		'batch_no': filters.get("batch_no"),
	}

	data = frappe.db.sql("""select round(sum(sle.actual_qty),2)
				from `tabStock Ledger Entry` sle
				    INNER JOIN `tabBatch` batch on sle.batch_no = batch.name
				where
					sle.item_code = %(item_code)s
					and sle.warehouse = %(warehouse)s
					and sle.batch_no = %(batch_no)s
					and batch.docstatus < 2 and sle.is_cancelled = 0
				group by batch_no having sum(sle.actual_qty) > 0
				order by batch.expiry_date, sle.batch_no desc""", args)

	if data:
		return flt(data[0][0])
	else:
		return 0

@frappe.whitelist()
def bom_before_save(self, method):
	self.total_labor_cost = self.labor_cost * self.quantity
	self.total_cost = self.raw_material_cost + self.total_labor_cost - self.scrap_material_cost 
	per_unit_price = flt(self.total_cost) / flt(self.quantity)

	if self.per_unit_price != per_unit_price:
		self.per_unit_price  = per_unit_price

@frappe.whitelist()
def get_transfer_items(work_order, items):
	from erpnext.stock.doctype.batch.batch import get_batch_qty

	if isinstance(items, basestring):
		items = json.loads(items)

	se_data = frappe.get_list("Stock Entry", 
		filters={
			"purpose": "Material Transfer for Manufacture",
			"work_order": work_order,
			"docstatus": 1
		})

	items_list = []

	for se in se_data:
		doc = frappe.get_doc("Stock Entry", se.name)
		items_list += [row for row in doc.items if get_batch_qty(batch_no=row.batch_no, warehouse=row.t_warehouse, item_code=row.item_code)]

	items_list += items[-1:]

	return items_list

@frappe.whitelist()
def lcv_validate(self, method):
	if self._action == "submit":
		create_lcv_jv(self)

def create_lcv_jv(self):
	for row in self.get('taxes'):
		account_type = frappe.db.get_value("Account", row.credit_account, 'account_type')

		if account_type in ["Payable", "Receivable"] and not row.party:
			frappe.throw(_("Party Type and Party is required for Receivable / Payable account {0} in Row # {1}".format(row.credit_account, row.idx)))

		jv = frappe.new_doc("Journal Entry")
		jv.voucher_type = "Journal Entry"
		jv.posting_date = nowdate()

		jv.append('accounts',{
			'account': row.expense_account,
			'debit_in_account_currency': row.amount
		})

		jv.append('accounts',{
			'account': row.credit_account,
			'credit_in_account_currency': row.amount,
			'party_type': cstr(row.party_type),
			'party': cstr(row.party),
		})

		jv.cheque_no = row.reference_no
		jv.cheque_date = row.posting_date or nowdate()
		jv.user_remarks = row.remarks

		jv.save()
		jv.submit()

		row.db_set('journal_entry_ref', jv.name)

	else:
		frappe.db.commit()

@frappe.whitelist()
def lcv_on_cancel(self, method):
	cancel_lcv_jv(self)

def cancel_lcv_jv(self):
	for row in self.get('taxes'):
		if row.journal_entry_ref:
			jv = frappe.get_doc("Journal Entry", row.journal_entry_ref)
			jv.cancel()
			row.db_set('journal_entry_ref', '')
	else:
		frappe.db.commit()
		
@frappe.whitelist()
def docs_before_naming(self, method):
	from erpnext.accounts.utils import get_fiscal_year

	date = self.get("transaction_date") or self.get("posting_date") or getdate()

	fy = get_fiscal_year(date)[0]
	fiscal = frappe.db.get_value("Fiscal Year", fy, 'fiscal')

	if fiscal:
		self.fiscal = fiscal
	else:
		fy_years = fy.split("-")
		fiscal = fy_years[0][2:] + '-' + fy_years[1][2:]
		self.fiscal = fiscal

# @frappe.whitelist()
# def docperm():
# 	doc = frappe.new_doc("DocPerm")
# 	doc.read = 1
# 	doc.write = 1
# 	doc.create = 1
# 	doc.delete = 1
# 	doc.idx = 2
# 	doc.parent = "Role"
# 	doc.role = "Local Admin"
# 	doc.parentfield = 'permissions'
# 	doc.parenttype = "DocType"
# 	doc.db_insert()

@frappe.whitelist()
def pi_before_save(self,method):
	update_item_detail(self)
	
def update_item_detail(self):
	item_dict = frappe._dict()
	
	for row in self.items:
		item_dict.setdefault(row.item_code, [0, 0])
		item_dict[row.item_code][0] += row.qty
		item_dict[row.item_code][1] += 1
	
	self.set('item_details', [])

	for key, values in item_dict.items():
		self.append('item_details',{
			'item_code': key,
			'qty': values[0],
			'no_of_packages': values[1],
		})

@frappe.whitelist()
def get_item_details(pi):
	doc = frappe.get_doc("Purchase Invoice",pi)
	item_dict = frappe._dict()
	
	for row in doc.items:
		item_dict.setdefault(row.item_code, [0, 0])
		item_dict[row.item_code][0] += row.qty
		item_dict[row.item_code][1] += 1
		
	doc.set('item_details', [])
	
	for key, values in item_dict.items():
		doc.append('item_details',{
			'item_code': key,
			'qty': values[0],
			'no_of_packages': values[1],
		})
	
	frappe.db.commit()

@frappe.whitelist()
def job_card_validate(self, method):
	if self.is_new() and not self.amended_from:
		get_wo_raw_materials(self)

@frappe.whitelist()
def job_card_on_submit(self, method):
	make_se_for_job_card(self)

@frappe.whitelist()
def job_card_on_cancel(self, method):
	cancel_jc_stock_entry(self)

def get_wo_raw_materials(self):
	wo = frappe.get_doc("Work Order", self.work_order)

	self.set('required_items', [])

	for row in wo.required_items:
		self.append("required_items", {
			'item_code': row.item_code,
			'item_name': row.item_name,
			'description': row.description,
			'uom': cstr(frappe.db.get_value("BOM Item", {'item_code': row.item_code}, 'uom')),
			'source_warehouse': row.source_warehouse,
		})

def make_se_for_job_card(self):
	def get_stock_entry_doc(source_name, target_doc=None):
		def set_missing_values(source, target):
			target.stock_entry_type = "Manufacture"
			target.purpose = "Manufacture"
			target.from_bom = 1
			target.naming_series = "STE-.fiscal.-"
			target.fg_completed_qty = source.get('for_quantity', 0) - source.get('transferred_qty', 0)
			
			production_item, to_warehouse = frappe.db.get_value("Work Order", source.work_order, ['production_item','fg_warehouse'])
			item = get_item_defaults(production_item, source.company)
			
			target.add_to_stock_entry_detail({
				production_item: {
					"to_warehouse": to_warehouse,
					"from_warehouse": "",
					"qty": target.fg_completed_qty,
					"item_name": item.item_name,
					"description": item.description,
					"stock_uom": item.stock_uom,
					"expense_account": item.get("expense_account"),
					"cost_center": item.get("buying_cost_center"),
				}
			})

			#target.calculate_rate_and_amount()
			target.set_missing_values()

		doclist = get_mapped_doc("Job Card", source_name, {
			"Job Card": {
				"doctype": "Stock Entry",
				"field_map": {
					"for_quantity": "fg_completed_qty"
				},
			},
			"Job Card Required Item": {
				"doctype": "Stock Entry Detail",
				"field_map": {
					"source_warehouse": "s_warehouse",
					"uom": "stock_uom",
					"batch_no": "batch_no"
				},
				"field_no_map":[
					'conversion_factor'
				]
			}
		}, target_doc, set_missing_values)

		return doclist

	doc = get_stock_entry_doc(self.name)
	doc.job_card = ''
	#doc.get_stock_and_rate()
	
	try:
		doc.save(ignore_permissions=True)
		doc.submit()
	except Exception as e:
		frappe.throw(str(e))

	self.db_set('stock_entry', doc.name)
	
def cancel_jc_stock_entry(self):
	if self.stock_entry:
		doc = frappe.get_doc("Stock Entry", self.stock_entry)
		doc.cancel()
		self.db_set('stock_entry', '')

@frappe.whitelist()
def make_stock_entry(work_order_id, purpose, qty=None):
	# from erpnext.stock.doctype.stock_entry.stock_entry import get_additional_costs
	print("chalyu ho chalyu")
	work_order = frappe.get_doc("Work Order", work_order_id)
	if not frappe.db.get_value("Warehouse", work_order.wip_warehouse, "is_group") \
			and not work_order.skip_transfer:
		wip_warehouse = work_order.wip_warehouse
	else:
		wip_warehouse = None

	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = purpose
	stock_entry.work_order = work_order_id
	stock_entry.company = work_order.company
	stock_entry.from_bom = 1
	stock_entry.bom_no = work_order.bom_no
	stock_entry.use_multi_level_bom = work_order.use_multi_level_bom
	stock_entry.fg_completed_qty = qty or (flt(work_order.qty) - flt(work_order.produced_qty))
	if work_order.bom_no:
		stock_entry.inspection_required = frappe.db.get_value('BOM',
			work_order.bom_no, 'inspection_required')

	if purpose=="Material Transfer for Manufacture":
		stock_entry.to_warehouse = wip_warehouse
		stock_entry.project = work_order.project
	else:
		stock_entry.from_warehouse = wip_warehouse
		stock_entry.to_warehouse = work_order.fg_warehouse
		stock_entry.project = work_order.project
		# if purpose=="Manufacture":
		# 	additional_costs = get_additional_costs(work_order, fg_qty=stock_entry.fg_completed_qty)
		# 	stock_entry.set("additional_costs", additional_costs)
	stock_entry.set_stock_entry_type()
	stock_entry.get_items()

	job_cards = frappe.get_list("Job Card", {'work_order': work_order_id, 'docstatus': 1})

	if job_cards:
		job_card_items = []
		last_item = stock_entry.items[-1].as_dict()
		source_items = stock_entry.items[:-1]

		idx = 1

		for d in source_items:
			for job in job_cards:
				data = frappe.db.sql("""
					select source_warehouse, batch_no, qty
					from `tabJob Card Required Item`
					where parent = %s and item_code = %s """, values=(job.name, d.item_code), as_dict=1)[0] or []

				if data:
					row = d.as_dict()
					row.s_warehouse = data.source_warehouse
					row.batch_no = data.batch_no
					row.qty = data.qty
					row.transfer_qty = data.qty
					row.amount = flt(row.rate) * flt(data.qty)
					row.idx = idx
					job_card_items.append(frappe._dict(row))

					idx += 1

		last_item.idx = idx
		job_card_items.append(frappe._dict(last_item))
		stock_entry.set('items', [])
		stock_entry.extend('items', job_card_items[:])
		stock_entry.calculate_rate_and_amount(raise_error_if_no_rate=False)

	return stock_entry.as_dict()
	
def fiscal_before_save(self,method):
	start_date = str(self.year_start_date)
	end_date = str(self.year_end_date)

	fiscal = start_date.split("-")[0][2:] + end_date.split("-")[0][2:]
	self.fiscal = fiscal