frappe.pages['embedded'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Sales and Purchase Report',
		single_column: true
	});
}