frappe.pages['sales-analysis'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Sales Analysis',
		single_column: true
	});
}