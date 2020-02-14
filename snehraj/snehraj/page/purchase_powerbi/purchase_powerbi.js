frappe.pages['purchase-powerbi'].on_page_load = function(wrapper) {
     	new analysis(wrapper);
}

analysis = Class.extend({
	init: function(wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Purchase Analytics',
			single_column: true
		});
		this.make();
	},
	make: function() {
		var a='https://app.powerbi.com/view?r=eyJrIjoiN2U0MjBmMGQtN2Y4OS00YmMxLTg2MzktZDBhMjk5MTUzNWRjIiwidCI6ImJjNzY3ZWI5LWUwNmYtNDg3MC1iMTY1LTVlZDg4MmFmOWUwNyJ9';
		$(frappe.render_template("purchase-powerbi", this)).appendTo(this.page.main);
		$(document).ready(function() {
    			$('#myiFrame').attr('src', a);
		});
	}
})