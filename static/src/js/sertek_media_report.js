openerp.sertek_media_report = function(instance) {
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;
    var module = instance.point_of_sale;
    var round_di = instance.web.round_decimals;
    var round_pr = instance.web.round_precision;

    instance.web.ListView.Groups = instance.web.ListView.Groups.extend({
        render: function (post_render) {
            var self = this;
            var $el = $('<tbody>');
            this.elements = [$el[0]];
            console.log(this.datagroup);
            this.datagroup.list(
                _(this.view.visible_columns).chain()
                    .filter(function (column) { return column.tag === 'field';})
                    .pluck('name').value(),
                function (groups) {
                    // page count is irrelevant on grouped page, replace by limit
                	self.view.$pager.find('.oe_pager_group').hide();
                    self.view.$pager.find('.oe_list_pager_state').text(self.view._limit ? self.view._limit : '∞');
                    var info = {}
                    var period_id = []
                    _.each(groups,function(group_info){
                    	if (group_info.grouped_on == 'user_id'){
                    		info[group_info.domain[0][2]] = group_info.domain[1][2]
                    	}else if (group_info.grouped_on == 'period_id'){
                    		period_id.push(group_info.value[0])
                    	}
                    });
                    if (period_id.length > 0){
                		var model = new instance.web.Model('account.invoice');
                    	model.call('fetch_previous_period_total',{
                    		'period_id':period_id,
                    	}).done(function(result){
                    		for(i=0;i<groups.length;i++){
                    			groups[i].previous_total =  result[groups[i].value[0]]
                    		} 
                			$el[0].appendChild(
                                self.render_groups(groups));
                                if (post_render) { post_render(); }                		
                    	})                		                    	
                    }
                    else if (Object.keys(info).length != 0){
                		var model = new instance.web.Model('account.invoice');
                    	model.call('fetch_previous_period',{
                    		'groups':info,
                    	}).done(function(result){
                    		for(i=0;i<groups.length;i++){
                    			groups[i].previous_total =  result[groups[i].domain[0][2]]
                    		} 
                			$el[0].appendChild(
                                self.render_groups(groups));
                                if (post_render) { post_render(); }                		
                    	})                		
                	}else{
                		$el[0].appendChild(
                                self.render_groups(groups));
                                if (post_render) { post_render(); }                		                		
                	}
                }, function (dataset) {
                    self.render_dataset(dataset).then(function (list) {
                        self.children[null] = list;
                        self.elements =
                            [list.$current.replaceAll($el)[0]];
                        self.setup_resequence_rows(list, dataset);
                    }).always(function() {
                        if (post_render) { post_render(); }
                    });
                });
            return $el;
        },
    	
		render_groups:function(datagroups){
			var self = this;
	        var placeholder = this.make_fragment();
	        _(datagroups).each(function (group) {
	        	if (self.children[group.value]) {
	                self.records.proxy(group.value).reset();
	                delete self.children[group.value];
	            }
	            var child = self.children[group.value] = new (self.view.options.GroupsType)(self.view, {
	                records: self.records.proxy(group.value),
	                options: self.options,
	                columns: self.columns
	            });
	            self.bind_child_events(child);
	            child.datagroup = group;
	            var $row = child.$row = $('<tr class="oe_group_header">');
	            if (group.openable && group.length) {
	                $row.click(function (e) {
	                    if (!$row.data('open')) {
	                        $row.data('open', true)
	                            .find('span.ui-icon')
	                                .removeClass('ui-icon-triangle-1-e')
	                                .addClass('ui-icon-triangle-1-s');
	                        child.open(self.point_insertion(e.currentTarget));
	                    } else {
	                        $row.removeData('open')
	                            .find('span.ui-icon')
	                                .removeClass('ui-icon-triangle-1-s')
	                                .addClass('ui-icon-triangle-1-e');
	                        child.close();
	                        // force recompute the selection as closing group reset properties
	                        var selection = self.get_selection();
	                        $(self).trigger('selected', [selection.ids, this.records]);
	                    }
	                });
	            }
	            placeholder.appendChild($row[0]);
	            var $group_column = $('<th class="oe_list_group_name">').appendTo($row);
	            // Don't fill this if group_by_no_leaf but no group_by
	            if (group.grouped_on) {
	                var row_data = {};
	                row_data[group.grouped_on] = group;
	                var group_label = _t("Undefined");
	                var group_column = _(self.columns).detect(function (column) {
	                    return column.id === group.grouped_on; });
	                if (group_column) {
	                    try {
	                        group_label = group_column.format(row_data, {
	                            value_if_empty: _t("Undefined"),
	                            process_modifiers: false
	                        });
	                    } catch (e) {
	                        group_label = _.str.escapeHTML(row_data[group_column.id].value);
	                    }
	                } else {
	                    group_label = group.value;
	                    if (group_label instanceof Array) {
	                        group_label = group_label[1];
	                    }
	                    if (group_label === false) {
	                        group_label = _t('Undefined');
	                    }
	                    group_label = _.str.escapeHTML(group_label);
	                }
	                    
	                // group_label is html-clean (through format or explicit
	                // escaping if format failed), can inject straight into HTML
	                $group_column.html(_.str.sprintf(_t("%s (%d)"),
	                    group_label, group.length));

	                if (group.length && group.openable) {
	                    // Make openable if not terminal group & group_by_no_leaf
	                    $group_column.prepend('<span class="ui-icon ui-icon-triangle-1-e" style="float: left;">');
	                } else {
	                    // Kinda-ugly hack: jquery-ui has no "empty" icon, so set
	                    // wonky background position to ensure nothing is displayed
	                    // there but the rest of the behavior is ui-icon's
	                    $group_column.prepend('<span class="ui-icon" style="float: left; background-position: 150px 150px">');
	                }
	            }
	            self.indent($group_column, group.level);
	            if (self.options.selectable) {
	                $row.append('<td>');
	            }
	            _(self.columns).chain()
	                .filter(function (column) { return column.invisible !== '1'; })
	                .each(function (column) {
                    	if (group.grouped_on == 'period_id' && column.id == "comision_employee"){
             			   var r = {};
	                        r[column.id] = {value: 0.15 * parseFloat(group.previous_total) + parseFloat(group.aggregates[column.id])};
	                        $('<td class="oe_number">')
                           .html(column.format(r, {process_modifiers: false}))
                           .appendTo($row);	                    		
                    	}	                	
	                	else if(column.id == "comision_employee" && group.grouped_on == 'user_id'){
	                			   var r = {};
			                        r[column.id] = {value: 0.15 * parseFloat(group.previous_total) + parseFloat(group.aggregates[column.id])};
			                        $('<td class="oe_number">')
		                            .html(column.format(r, {process_modifiers: false}))
		                            .appendTo($row);	                    		
	                	}	 
	                	else if (column.meta) {
	                        // do not do anything
	                    } else if (column.id in group.aggregates) {
	                        var r = {};
	                        r[column.id] = {value: group.aggregates[column.id]};
	                        $('<td class="oe_number">')
	                            .html(column.format(r, {process_modifiers: false}))
	                            .appendTo($row);
	                    }else {
	                        $row.append('<td>');
	                    }
	                });
	            if (self.options.deletable) {
	                $row.append('<td class="oe_list_group_pagination">');
	            }
	            if (group.grouped_on == 'user_id'){
	            	var $row_child  = $("<tr></tr>");
	            	for (i = 0 ; i < 8 ;i++){
	            		$row_child.append($("<td></td>"));
	            	}
	            	if (group.previous_total != undefined){
		            	$row_child.append($("<td align = 'right' class = 'oe_readonly' >Previous Period Payments</td>"))
		            	$row_child.append($("<td style = 'border-right:2px solid;border-left:2px solid;border-bottom:2px solid;border-top:2px solid' class = 'oe_list_field_cell oe_list_field_float oe_number  oe_readonly'  ><font color='green'>"+group.previous_total+"</font></td>" ))
		            	$row_child.append($("<td align = 'right' class = 'oe_readonly' >Commision(15%)</td>"))
		            	comision  = 0.15 * group.previous_total ;
		            	$row_child.append($("<td style = 'border-right:2px solid;border-left:2px solid;border-bottom:2px solid;border-top:2px solid' class = 'oe_list_field_cell oe_list_field_float oe_number  oe_readonly'  ><font color='green'>"+comision+"</font></td>" ))
		            	placeholder.appendChild($row_child[0]);	            	            		
	            	}
	            }	            
	        });
	        return placeholder;
		},
    });
};