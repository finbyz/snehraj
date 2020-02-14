// Copyright (c) 2019, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Jobwork Receipt', {
	refresh: function(frm) {
		if(frm.doc.docstatus==0) {
			if(!frm.doc.posting_date) {
				frm.set_value('posting_date', frappe.datetime.nowdate());
			}
			if(!frm.doc.posting_time) {
				frm.set_value('posting_time', frappe.datetime.now_time());
			}
			frm.trigger('set_posting_date_and_time_read_only');
		}
	},

	set_posting_time: function(frm){
		frm.trigger('set_posting_date_and_time_read_only');
	},

	set_posting_date_and_time_read_only: function(frm){
		if(frm.doc.docstatus == 0 && frm.doc.set_posting_time) {
			frm.set_df_property('posting_date', 'read_only', 0);
			frm.set_df_property('posting_time', 'read_only', 0);
		} else {
			frm.set_df_property('posting_date', 'read_only', 1);
			frm.set_df_property('posting_time', 'read_only', 1);
		}
	},
	calculate_total_additional_costs: function(frm) {
		const total_additional_costs = frappe.utils.sum(
			(frm.doc.additional_costs || []).map(function(c) { return flt(c.amount); })
		);

		frm.set_value("total_additional_costs",
			flt(total_additional_costs, precision("total_additional_costs")));
	},
	insert_item_details: function(frm) {
		frm.call({
			method: 'insert_item_details',
			doc: frm.doc,
			callback: function(r){
				console.log(r);
				if(!r.exc){
					cur_frm.refresh_field('items');
				}
			}
		})
	},
});

frappe.ui.form.on('Jobwork Receipt Item', {
	item_code: function(frm, cdt, cdn){
		const item = locals[cdt][cdn];

		if(!frm.doc.customer){
			frappe.msgprint(__("Please specify: Customer."));
			return
		}

		if(item.item_code){
			return frappe.call({
				method: "erpnext.stock.get_item_details.get_item_details",
				child: item,
				args: {
					doc: frm.doc,
					args: {
						item_code: item.item_code,
						warehouse: item.warehouse,
						customer: frm.doc.customer,
						update_stock: 0,
						conversion_rate: 1,
						company: frm.doc.company,
						transaction_date: frm.doc.posting_date,
						ignore_pricing_rule: 1,
						doctype: frm.doc.doctype,
						name: frm.doc.name,
						qty: item.qty || 1,
						stock_qty: item.stock_qty,
						conversion_factor: item.conversion_factor,
						uom : item.uom,
						stock_uom: item.stock_uom,
						child_docname: item.name,
					}
				},
				callback: function(r) {
					if(!r.exc) {
						frappe.model.set_value(cdt, cdn, 'item_name', r.message.item_name);
						frappe.model.set_value(cdt, cdn, 'description', r.message.description);
						frappe.model.set_value(cdt, cdn, 'image', r.message.image);
						frappe.model.set_value(cdt, cdn, 'qty', r.message.qty);
						frappe.model.set_value(cdt, cdn, 'basic_rate', r.message.rate);
						frappe.model.set_value(cdt, cdn, 'uom', r.message.uom);
						frappe.model.set_value(cdt, cdn, 'conversion_factor', r.message.conversion_factor);
						frappe.model.set_value(cdt, cdn, 'stock_uom', r.message.stock_uom);
						frappe.model.set_value(cdt, cdn, 'transfer_qty', r.message.stock_qty);
					}
				}
			});
		}
	},

	basic_rate: function(frm, cdt, cdn){
		let item = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, 'basic_amount', flt(item.basic_rate * item.qty));
	},

	qty: function(frm, cdt, cdn){
		let item = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, 'basic_amount', flt(item.basic_rate * item.qty));
	},
});

frappe.ui.form.on('Landed Cost Taxes and Charges', {
	amount: function(frm) {
		frm.events.calculate_total_additional_costs(frm);
	}
});
