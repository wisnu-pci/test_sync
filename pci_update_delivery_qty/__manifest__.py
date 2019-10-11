{
    'name': 'PCI - Update Delivery Qty & Scheduler',
    'version': '11.0.2.7',
    'depends': ['sale_management', 'hr', 'product', 'timesheet_invoiceable'],
    'author': 'Port Cities Ltd',
    'summary': 'Update Delivery Qty in the SO line based on Invoiceable Timesheet',
    'description': """
        V.1.0 \n
        the delivered qty to be updated automatically based on time spent\n
        author : Aziz and Rian \n
        - create new wizard 'update.delivered.qty.sale' with one field Date (date_select) and button "Update Delivered Qty"\n
        - create new field employee on sale.order.line to be added on form view and tree view\n
        author : Endy\n
        v.1.1.0\n
        - Add button to update quantity product, add automation to update quantity weekly and create invoice\n
        - Add Field Date From (date_from) in page Other Information. Create default for Date to in wizard set tolast Sunday.\n
        - Update Compute function to update delivered qty in range Date From to Date To. if Date From is Empty Date From will set to first date the timesheet inputed for current analytic account.\n
        v.2.0.1\n
        - Create invoice automated after update the Delivered Qty and set Date Invoice same as Date To in Wizard.\n
        - Create scheduled action to run automatically in Monday Midnight\n
        - Add new boolean field "Auto Invoice" in object account.analytic.account and make condition to check field Auto Invoice then do automatically create invoice if the field s True\n
        author : Wisnu and Ugi\n
        v.2.2\n
        - migrate to odoo10\n
        v.2.3\n
        - improvement the module to handle archived employee, and editable price unit\n
        author : Wisnu
        v.2.4\n
        - migrate to odoo11
        author : Syarifudin\n
        v.2.5.1\n
        - add timesheet report wizard in sale order to print excel timesheet report\n
        author : Rofi S.A\n
        v.2.5.2\n
        - Improvement in code\n
        - Pylint improvement\n
        - Revome unnecessary log and commented print\n
        author : WS
        v.2.6\n
        - Improve update delivery qty with section\n
        author : Reynaldi Yosfino
        v.2.7\n
        - Improve update delivery qty with section\n
        author : WS
    
    """,

    'website': 'https://www.portcities.net',
    'category': 'sales',
    'sequence': 1,
    'data': [
        'data/cron_auto_update_delivery_qty.xml',
        'wizard/report_timesheet_wizard_view.xml',
        'wizard/update_delivery_qty_sale_view.xml',
        'views/sale_order_view.xml',
        'views/employee_view.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
