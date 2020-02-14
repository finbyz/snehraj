frappe.pages['retail-analysis'].on_page_load = function(wrapper) {
     	new analysis(wrapper);
}

analysis = Class.extend({
	init: function(wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Sales Analysis (Retail)',
			single_column: true
		});
		this.make();
	},
	make: function() {
		var a='https://app.powerbi.com/view?r=eyJrIjoiYmRhZTc3MzUtNjljNy00NmQwLThkOTYtZmMwMmM4OTFjY2QzIiwidCI6ImJjNzY3ZWI5LWUwNmYtNDg3MC1iMTY1LTVlZDg4MmFmOWUwNyJ9';
		$(frappe.render_template("retail", this)).appendTo(this.page.main);
		$(document).ready(function() {
    			$('#myiFrame').attr('src', a);
		});
	}
})
