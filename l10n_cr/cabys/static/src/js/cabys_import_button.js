odoo.define('cabys.cabys_import_button', function (require) {

    "use strict";
    
    var core = require('web.core');
    
    var ListController = require('web.ListController');
    
        ListController.include({
    
            renderButtons: function($node) {
    
            this._super.apply(this, arguments);
    
                if (this.$buttons) {
    
                    let cabys_import_button = this.$buttons.find('.oe_cabys_import_button');
    
                    cabys_import_button && cabys_import_button.click(this.proxy('cabys_import_button')) ;
    
                }
    
            },
    
            cabys_import_button: function () {
    
                console.log('yay importing cabys catalog');
                var self = this;
                var state = self.model.get(self.handle, {raw: true});
                var context = state.getContext();

                self.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'cabys.catalog.import.wizard',
                    target: 'new',
                    views: [[false, 'form']],
                    context: context,
                });
       
            }
    
        });
    
    })