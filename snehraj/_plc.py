# -*- coding: utf-8 -*-

"""
	Endpoints:

	Request Type 	: POST
	Endpoint 		: https://erp.snehraj.com/api/method/snehraj.plc.ping

1) 	Request Type 	: POST
	Endpoint 		: https://erp.snehraj.com/api/method/snehraj.plc.get_wo_details

2) 	Request Type 	: POST
	Endpoint 		: https://erp.snehraj.com/api/method/snehraj.plc.create_job_card

3) 	Request Type 	: POST
	Endpoint 		: https://erp.snehraj.com/api/method/snehraj.plc.get_paper_roll_details

4) 	Request Type 	: POST
	Endpoint 		: https://erp.snehraj.com/api/method/snehraj.plc.start_job

5) 	Request Type 	: POST
	Endpoint 		: https://erp.snehraj.com/api/method/snehraj.plc.stop_job

6) 	Request Type 	: POST
	Endpoint 		: https://erp.snehraj.com/api/method/snehraj.plc.complete_job

7) 	Request Type 	: POST
	Endpoint 		: https://erp.snehraj.com/api/method/snehraj.plc.update_job

8) 	Request Type 	: POST
	Endpoint 		: https://erp.snehraj.com/api/method/snehraj.plc.update_machine_power

"""

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, now_datetime, cstr, nowdate
from frappe.utils.dateutils import parse_date
from erpnext.stock.doctype.batch.batch import get_batch_qty
from werkzeug.wrappers import Response
import json
import re

success_message = "SUCCESS"
error_message = "@FAIL$"

api_key = "7187cedb5c5e445"
api_secret_key = "def9d8271a69434"

# user = "pathiksheth@snehraj.com"
user = "Administrator"


def validate_request(data, data_size=1):
	if data[0] != "@":
		return False

	elif data[-1] != "$":
		return False

	elif len(data[1:-1].split('|')) != data_size:
		return False

	return True

# use_regex = kwargs.get('use_regex', 0)
# if not use_regex:
# 	separator = "*"
# 	list_items = data[list_field].split(separator)

# else:
# 	pattern = r"(?:[a-zA-Z0-9 -]+:\(.*?)\)"
# 	list_items = re.findall(pattern, data[list_field])

# if use_regex:
# 	item_code = d[0]
# 	values = d[1].replace("(","").replace(")","").split(',')
# 	data_dict[item_code] = tuple(values)

def parse_data(data, fields, **kwargs):
	data_list = data[1:-1].split('|')
	data = frappe._dict()

	for field, value in zip(fields, data_list):
		data[field] = value

	if kwargs.get('child'):
		child = kwargs.get('child')

		child_field = child['child_field']
		keys = child['keys']
		separator = child['separator']

		list_items = data[child_field].split(separator)
		items = []

		for list_item in list_items:
			data_dict = frappe._dict()
			item_list = list_item.split(':')
			
			if len(item_list) == len(keys):
				for key, value in zip(keys, item_list):
					data_dict[key] = value

				items.append(data_dict)

		data[child_field] = items

	return data

def publish(message):
	frappe.publish_realtime("msgprint", message=str(message), user="Administrator")

def get_timestamp():
	return now_datetime().strftime("%Y-%m-%d %H:%M:%S").split(" ")

def get_endpoint(method):
	return "https://erp.snehraj.com/api/method/snehraj.plc." + method

def log(args):
	has_error = 0
	error = None

	if args.get('has_error'):
		has_error = 1
		error = args.get('error')

	endpoint = get_endpoint(args.method)

	frappe.get_doc(dict(
		doctype= "PLC Log",
		title= args.method,
		endpoint= endpoint,
		request_data= args.request_data,
		response_data= args.response_data,
		has_error= has_error,
		error= error,
		timestamp = now_datetime()
	)).insert(ignore_permissions=True)

@frappe.whitelist()
def ping():
	return Response("@" + success_message + "$")

# 1 - Done
@frappe.whitelist()
def get_wo_details():
	"""
	Request Type - POST

	Request to Server: 
		@Work-order|Machine-ID$
	
	Response to Device: 
		@ SUCCESS | Machine-ID | Work-order | item_to_Manufacture | Qty_to_Manufacture | Roll Size | GSM | CUT | *Item_code | Required qty | count |Attribute:Attribute_value | Attribute:Attribute_value | Attribute:Attribute_value | . . . . . . . . . . | Attribute:Attribute_value |*Item_code | Required qty | count |Attribute:Attribute_value | Attribute:Attribute_value | Attribute:Attribute_value | . . . . . . . . . . Attribute:Attribute_value | Date | Time$
	"""
	args = frappe._dict()
	args.method = "get_wo_details"
	request_data = frappe.request.data
	args.request_data = request_data

	if not validate_request(request_data, data_size=2):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Invalid Request!"
		log(args)
		return Response(error_message)

	fields = ['work_order', 'workstation']
	data = parse_data(request_data, fields)
	
	if not frappe.db.exists("Work Order", data.work_order):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Work Order {} does not exists!".format(data.work_order)
		log(args)
		return Response(error_message)

	if frappe.db.get_value("Work Order", data.work_order, 'workstation') != data.workstation:
		args.response_data = error_message
		args.has_error = 1
		args.error = "Workstation {} does not match with Work Order's Workstation!".format(data.workstation)
		log(args)
		return Response(error_message)

	doc = frappe.get_doc("Work Order", data.work_order)

	response = [success_message, doc.workstation, doc.name, doc.production_item, cstr(doc.qty), cstr(doc.roll_size), cstr(doc.gsm), cstr(doc.cut)]

	for row in doc.required_items:
		response.append("*" + row.item_code)
		item = frappe.get_doc("Item", row.item_code)

		response.append(str(len(item.get('attributes'))))

		for d in item.get('attributes'):
			response.append(d.attribute + ":" + d.attribute_value)

	response.extend(get_timestamp())

	response = "@" + "|".join(response) + "$"
	args.response_data = response
	log(args)

	return Response(response)

# 2 - Done
@frappe.whitelist()
def create_job_card():
	"""
	Creates Job Card for specific Work Order

	Request Type - POST
	
	Request to Server:
		@work_order|Machine-ID$

	Response to Device: 
		@SUCCESS|Job_Card_Number|Date|time$

	"""
	args = frappe._dict()
	args.method = "create_job_card"
	request_data = frappe.request.data
	args.request_data = request_data

	if not validate_request(request_data, data_size=2):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Invalid Request!"
		log(args)
		return Response(error_message)

	fields = ['work_order', 'workstation']
	data = parse_data(request_data, fields)

	if not frappe.db.exists("Work Order", data.work_order) or \
		frappe.db.get_value("Work Order", data.work_order, 'workstation') != data.workstation or \
		frappe.db.get_value("Work Order", data.work_order, 'status') == "Completed":
		
		args.response_data = error_message
		args.has_error = 1
		args.error = "Invalid Data!"
		log(args)
		return Response(error_message)

	doc = frappe.new_doc("Job Card")
	
	workstation, wip_warehouse = frappe.db.get_value("Work Order", data.work_order, ('workstation', 'wip_warehouse'))

	doc.update({
		'work_order': data.work_order,
		'workstation': workstation,
		'operation': "Section",
		'wip_warehouse': wip_warehouse,
		'posting_date': nowdate(),
	})

	try:
		doc.save()
	except Exception as e:
		args.response_data = error_message
		args.has_error = 1
		args.error = frappe.get_traceback()
		log(args)
		return Response(error_message)
	else:
		response = "@" + "|".join([success_message, doc.name] + get_timestamp()) + "$"
		args.response_data = response
		log(args)
		return Response(response)

# 3 - Done
@frappe.whitelist()
def get_paper_roll_details():
	"""
	Returns raw materials list of Job Card for finishing it.

	Request Type - POST

	Request to Server: 
		@ Job-card | item-code | Batch-No | Roll-No | Weight $ 
	Response to Device: 
		@ SUCCESS | Batch-No | Roll-No | Weight | Date | Time$
	"""

	args = frappe._dict()
	args.method = "get_paper_roll_details"
	request_data = frappe.request.data
	args.request_data = request_data

	if not validate_request(request_data, data_size=5):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Invalid Request!"
		log(args)
		return Response(error_message)

	fields = ['job_card', 'item_code', 'batch_no', 'roll_no', 'qty']
	data = parse_data(request_data, fields)

	try:
		row, source_warehouse = frappe.db.get_value("Job Card Required Item", 
			{'parent': data.job_card, 'item_code': data.item_code}, ['name', 'source_warehouse'])

	except Exception as e:
		args.response_data = error_message
		args.has_error = 1
		args.error = frappe.get_traceback()
		log(args)
		return Response(error_message)

	if data.batch_no != "0":
		if not frappe.db.exists("Batch", data.batch_no):
			args.response_data = error_message
			args.has_error = 1
			args.error = "Batch No {} does not exists!".format(data.batch_no)
			log(args)
			return Response(error_message)

		roll_no = cstr(frappe.db.get_value("Batch", data.batch_no, 'roll_no'))
		qty = get_batch_qty(data.batch_no, source_warehouse, data.item_code)

		if not qty:
			args.response_data = error_message
			args.has_error = 1
			args.error = "No quantity in Batch!"
			log(args)
			return Response(error_message)

		frappe.db.set_value("Job Card Required Item", row, 'batch_no', data.batch_no)
		frappe.db.commit()

		response = "@" + "|".join([success_message, data.batch_no, roll_no, str(qty)] + get_timestamp()) + "$"
		args.response_data = response
		log(args)
		return Response(response)

	elif data.roll_no != "0":
		batches = frappe.get_list("Batch", filters={'roll_no': data.roll_no, 'item': data.item_code})

		if not batches:
			args.response_data = error_message
			args.has_error = 1
			args.error = "No matching batch found!"
			log(args)
			return Response(error_message)

		batch_nos = []
		for batch in batches:
			qty = get_batch_qty(batch.name, source_warehouse, data.item_code)

			if qty:
				batch_nos.append([batch.name, data.roll_no, str(qty)])

		if not batch_nos:
			args.response_data = error_message
			args.has_error = 1
			args.error = "No matching batch found!"
			log(args)
			return Response(error_message)

		batch_len = str(len(batch_nos))
		batch_nos = "|".join([batch for d in batch_nos for batch in d])

		response = "@" + "|".join([success_message, batch_len, batch_nos] + get_timestamp()) + "$"
		args.response_data = response
		log(args)
		return Response(response)

	elif data.qty != "0":
		batches = get_batch_qty(item_code=data.item_code, warehouse=source_warehouse)

		batch_nos = []
		for batch in batches:
			if flt(data.qty) == flt(batch.qty):
				roll_no = cstr(frappe.db.get_value("Batch", batch.batch_no, "roll_no"))
				batch_nos.append([batch.batch_no, roll_no, str(data.qty)])

		if not batch_nos:
			args.response_data = error_message
			args.has_error = 1
			args.error = "No matching batch found!"
			log(args)
			return Response(error_message)

		batch_len = str(len(batch_nos))
		batch_nos = "|".join([batch for d in batch_nos for batch in d])

		response = "@" + "|".join([success_message, batch_len, batch_nos] + get_timestamp()) + "$"
		args.response_data = response
		log(args)
		return Response(response)

	else:
		args.response_data = error_message
		args.has_error = 1
		args.error = "Invalid Data!"
		log(args)
		return Response(error_message)

# 4 - Done
@frappe.whitelist()
def start_job():
	"""
	Starts Job for specific Job Card

	Request Type - POST

	Request to Server:
		@job_card$

	Response to Device:
		@SUCCESS$ or @FAIL$
	"""

	args = frappe._dict()
	args.method = "start_job"
	request_data = frappe.request.data
	args.request_data = request_data

	if not validate_request(request_data, data_size=1):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Invalid Request!"
		log(args)
		return Response(error_message)

	fields = ['job_card']
	data = parse_data(request_data, fields)

	if not frappe.db.exists("Job Card", data.job_card):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Job Card {} does not exists!".format(data.job_card)
		log(args)
		return Response(error_message)

	started_time = now_datetime()

	doc = frappe.get_doc("Job Card", data.job_card)
	doc.append('time_logs', {
		'from_time': started_time,
		'completed_qty': 0.0,
	})
	doc.job_started = 1
	doc.started_time = started_time

	try:
		doc.save()
	except Exception as e:
		args.response_data = error_message
		args.has_error = 1
		args.error = frappe.get_traceback()
		log(args)
		return Response(error_message)
	else:
		response = "@"+ success_message + "$"
		args.response_data = response
		log(args)
		return Response(response)

# 5 - Done
@frappe.whitelist()
def stop_job():
	"""
	Pause Job for specific Job Card

	Request Type - POST

	Request from Server:
		@job_card|Paper-count | bunch-count | section-count | Machine-RPM$

	Response to Device:
		@SUCCESS$ or @FAIL$
	"""

	args = frappe._dict()
	args.method = "stop_job"
	request_data = frappe.request.data
	args.request_data = request_data

	if not validate_request(request_data, data_size=5):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Invalid Request!"
		log(args)
		return Response(error_message)

	fields = ['job_card', 'paper_count', 'bunch', 'section', 'efficiency']
	data = parse_data(request_data, fields)

	if not frappe.db.exists("Job Card", data.job_card):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Job Card {} does not exists!".format(data.job_card)
		log(args)
		return Response(error_message)

	completed_time = now_datetime()
	
	doc = frappe.get_doc("Job Card", data.job_card)
	
	for d in doc.get("time_logs"):
		if d.from_time and not d.get('to_time'):
			d.to_time = completed_time
			d.paper_count = cint(data.paper_count)
			d.bunch = cint(data.bunch)
			d.section = cint(data.section)
			d.efficiency = flt(data.efficiency)

			doc.job_started = 0
			doc.started_time = ''
			break
	else:
		args.response_data = error_message
		args.has_error = 1
		args.error = "Job Card {} already stopped!".format(data.job_card)
		log(args)
		return Response(error_message)

	try:
		doc.save()
	except Exception as e:
		args.response_data = error_message
		args.has_error = 1
		args.error = frappe.get_traceback()
		log(args)
		return Response(error_message)
	else:
		response = "@"+ success_message + "$"
		args.response_data = response
		log(args)
		return Response(response)

# 6 - Done
@frappe.whitelist()
def complete_job():
	"""
	Finishes Job for specific Job Card and Create Stock Entry

	Request Type - POST

	Request from Server:
		@ job-card | item-code : Qty : partially_used [0 or 1] * item-code: Qty * : partially_used [0 or 1] ... | section-count $
	
	Response to Device:
		@SUCCESS | total_produced_qty | status $ or @FAIL$
	"""

	args = frappe._dict()
	args.method = "complete_job"
	request_data = frappe.request.data
	args.request_data = request_data

	if not validate_request(request_data, data_size=3):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Invalid Request!"
		# log(args)
		return Response(error_message)

	fields = ['job_card', 'required_items', 'section']
	data = parse_data(request_data, fields, child={
		'child_field': 'required_items',
		'keys': ['item_code', 'qty', 'partially_used'],
		'separator': "*",
	})

	if not frappe.db.exists("Job Card", data.job_card):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Job Card {} does not exists!".format(data.job_card)
		# log(args)
		return Response(error_message)

	doc = frappe.get_doc("Job Card", data.job_card)

	for row in doc.required_items:
		for d in data.required_items:
			if row.item_code == d.item_code:
				if not d.partially_used and row.batch_no:
					batch_qty = get_batch_qty(row.batch_no, row.source_warehouse, row.item_code)
					row.qty = batch_qty
					row.calculated_qty = flt(d.qty)

				else:
					row.qty = row.calculated_qty = flt(d.qty)

				break

	doc.for_quantity = flt(data.section)
	doc.time_logs[-1].completed_qty = flt(data.section)
	
	try:
		doc.save()
		# doc.submit()
	except Exception as e:
		args.response_data = error_message
		args.has_error = 1
		args.error = frappe.get_traceback()
		# log(args)
		return Response(error_message)
	else:
		status, produced_qty = frappe.db.get_value("Work Order", doc.work_order, ['status', 'produced_qty'])
		response = "@" + "|".join([success_message, str(produced_qty), status]) + "$"
		args.response_data = response
		# log(args)
		return Response(response)

# 7 - Done
@frappe.whitelist()
def update_job():
	"""
	Pause Job for specific Job Card

	Request Type - POST

	Request from Server:
		@job_card|Paper-count | bunch-count | section-count | Machine-RPM$

	Response to Device:
		@SUCCESS$ or @FAIL$
	"""

	args = frappe._dict()
	args.method = "update_job"
	request_data = frappe.request.data
	args.request_data = request_data

	if not validate_request(request_data, data_size=5):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Invalid Request!"
		log(args)
		return Response(error_message)

	fields = ['job_card', 'paper_count', 'bunch', 'section', 'efficiency']
	data = parse_data(request_data, fields)

	if not frappe.db.exists("Job Card", data.job_card):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Job Card {} does not exists!".format(data.job_card)
		log(args)
		return Response(error_message)

	timestamp = now_datetime()
	
	doc = frappe.get_doc("Job Card", data.job_card)

	last_row = doc.time_logs[-1]
	last_row.to_time = timestamp
	last_row.paper_count = cint(data.paper_count)
	last_row.bunch = cint(data.bunch)
	last_row.section = cint(data.section)
	last_row.efficiency = flt(data.efficiency)

	doc.append('time_logs', {
		'from_time': timestamp,
		'completed_qty': 0.0,
	})

	try:
		doc.save()
	except Exception as e:
		args.response_data = error_message
		args.has_error = 1
		args.error = frappe.get_traceback()
		log(args)
		return Response(error_message)
	else:
		response = "@"+ success_message + "$"
		args.response_data = response
		log(args)
		return Response(response)

# 8 - Done
@frappe.whitelist()
def update_machine_power():
	"""
	Updates Workstation Power (KWt) in Energy Consumption DocType

	Request Type - POST

	Request from Server:
		@ Machine-ID | KWh $

	Response to Device:
		@SUCCESS$ or @FAIL$
	"""

	args = frappe._dict()
	args.method = "update_machine_power"
	request_data = frappe.request.data
	args.request_data = request_data

	if not validate_request(request_data, data_size=2):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Invalid Request!"
		log(args)
		return Response(error_message)

	fields = ['workstation', 'power']
	data = parse_data(request_data, fields)

	if not frappe.db.exists("Workstation", data.workstation):
		args.response_data = error_message
		args.has_error = 1
		args.error = "Workstation {} does not exists!".format(data.workstation)
		log(args)
		return Response(error_message)

	doc = frappe.new_doc("Energy Consumption")
	doc.workstation = data.workstation
	doc.power = flt(data.power)
	try:
		doc.insert(ignore_permissions=True)
	except Exception as e:
		args.response_data = error_message
		args.has_error = 1
		args.error = frappe.get_traceback()
		log(args)
		return Response(error_message)
	else:
		response = "@"+ success_message + "$"
		args.response_data = response
		log(args)
		return Response(response)
