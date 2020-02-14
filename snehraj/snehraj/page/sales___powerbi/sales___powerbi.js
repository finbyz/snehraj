frappe.pages['sales-powerbi'].on_page_load = function(wrapper) {
     	new analysis(wrapper);
}

analysis = Class.extend({
	init: function(wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Sales Analysis',
			single_column: true
		});
		this.make();
	},
	make: function() {
		var a='https://app.powerbi.com/view?r=eyJrIjoiMmQ2N2QyZjgtYmVjZi00YWRjLWFlZWEtNTBmZjRhMzYzMjI2IiwidCI6ImJjNzY3ZWI5LWUwNmYtNDg3MC1iMTY1LTVlZDg4MmFmOWUwNyJ9';
		$(frappe.render_template("sales-powerbi", this)).appendTo(this.page.main);
		$(document).ready(function() {
    			$('#myiFrame').attr('src', a);
		});
	}
})