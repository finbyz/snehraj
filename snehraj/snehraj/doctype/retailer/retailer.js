// Copyright (c) 2018, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Retailer", {
	onload: function(frm){
		if(frappe.route_options.distributor){
			frm.set_value('distributor', frappe.route_options.distributor);
			frappe.route_options = null;
		}
	},

	onload_post_render: function(frm){
		cur_frm.set_query("distributor", function() {
			return {
				query: "erpnext.controllers.queries.customer_query",
				filters: {
					"customer_group": "Distributor"
				}
			};
		});
	},

	refresh: function(frm){
		frappe.dynamic_link = { doc: frm.doc, fieldname: 'name', doctype: 'Retailer' }

		if (frm.doc.__islocal) {
			hide_field(['address_html','contact_html']);
			frappe.contacts.clear_address_and_contact(frm);
		}
		else {
			unhide_field(['address_html','contact_html']);
			frappe.contacts.render_address_and_contact(frm);
		}
	}

});