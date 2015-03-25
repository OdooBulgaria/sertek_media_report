from openerp.osv import osv,fields,orm

class res_partner(osv.osv):
    _inherit="res.partner"
    _defaults={}
    _description="sertek media module"
    _columns={
              "default_bonus":fields.float("Default Bonus %"),
              }


class res_user(osv.osv):
    _inherit="res.users"
    _defaults={}
    _description="one field in users"
    _columns={
              "bonus":fields.float("Bonus %"),
              }

class sale_order_line(osv.osv):
    _inherit="sale.order.line"
    _defaults={
               'final_cost':10.0,
               }
    _description="sertek media module"
    _columns={
              "final_cost":fields.float("Final Unit Cost"),
              }

class account_invoice(osv.osv):
    _inherit="account.invoice"
    _defaults={}
    _description="sertek media module"
    def fetch_previous_period_total(self,cr,uid,period_id,context=None):
        result = {}
        for group in period_id:
            if group:
                cr.execute('''
                select id,date_start from account_period 
                where date_start < (select date_start from account_period where id = %s) and  special = false  order by date_start desc limit 1 
                ''' % (group))
                period = cr.fetchall()
                if period:
                    cr.execute('''
                    select sum(b.credit) as credit from account_move_reconcile as a 
                    left join account_move_line as b on a.id = b.reconcile_id or b.reconcile_partial_id = a.id 
                    where a.id in (select account_move_reconcile.id as reconcile from account_invoice 
                    left join account_move on account_invoice.move_id = account_move.id 
                    left join account_move_line on account_move.id = account_move_line.move_id 
                    left join account_move_reconcile on account_move_line.reconcile_id = account_move_reconcile.id 
                    or account_move_line.reconcile_partial_id = account_move_reconcile.id 
                    where account_invoice.period_id = %s and account_move_reconcile.id is not null) 
                    and b.period_id = %s
                    ''' %(period[0][0],group))
                    total = cr.fetchone();
                    result.update({group:total[0] or 0})
        return result
            
    def fetch_previous_period(self,cr,uid,groups,context=None):
        result = {}
        for group in groups:
            try:
                cr.execute('''
                select id,date_start from account_period 
                where date_start < (select date_start from account_period where id = %s) and  special = false  order by date_start desc limit 1 
                ''' % (groups.get(group,False)))
                period = cr.fetchall()
                if period:
                    cr.execute('''
                    select sum(b.credit) as credit from account_move_reconcile as a 
                    left join account_move_line as b on a.id = b.reconcile_id or b.reconcile_partial_id = a.id 
                    where a.id in (select account_move_reconcile.id as reconcile from account_invoice 
                    left join account_move on account_invoice.move_id = account_move.id 
                    left join account_move_line on account_move.id = account_move_line.move_id 
                    left join account_move_reconcile on account_move_line.reconcile_id = account_move_reconcile.id 
                    or account_move_line.reconcile_partial_id = account_move_reconcile.id 
                    where account_invoice.period_id = %s and account_move_reconcile.id is not null and account_invoice.user_id = %s) 
                    and b.period_id = %s
                    ''' %(period[0][0],int(group),groups.get(group,False)))
                    total = cr.fetchone();
                    result.update({group:total[0] or 0})
            except:
                return {}
        return result
    
    def _cal_cost(self,cr,uid,ids,final_cost,args,context=None):
        res={}
        id=tuple(self.pool.get('account.invoice.line').search(cr,uid,[('invoice_id','in',ids)]))
        #print " select order_line_id from sale_order_line_invoice_rel where invoice_id in %s" %(id)
        if id:
            cr.execute('''
             select sum(sl.final_cost) from sale_order_line_invoice_rel as rel join sale_order_line as sl on rel.order_line_id = sl.id  where rel.invoice_id in %s 
             ''',(id,))
        result = cr.fetchall()
        for i in ids:
            if result:
                res[i]=result[0][0]
        return res
        
    def _compute_comision(self,cr,uid,ids,field,args,context=None):
        res = {}
        for i in self.browse(cr,uid,ids,context):
            total = 0
            cr.execute('''
            select bonus_cost from account_invoice where id = %s
            '''%(i.id))
            bonus_cost = cr.fetchone()[0] or 0.00
            total = ((i.money_paid - i.amount_total + i.profit) * bonus_cost)/100
            res[i.id] = total
        return res
    
    def _cal_profit(self,cr,uid,ids,profit,args,context=None):
        res={}
        for i in self.browse(cr,uid,ids):
            profit = 0
            profit=i.amount_untaxed-i.final_cost
            res[i.id] = profit
#         for j in ids:
#             res[j]=profit
        return res
    
    def _cal_mony_paid(self,cr,uid,ids,money_paid,args,context=None):
        res={}
        obj=self.pool.get("account.voucher")
        current_period=obj._get_period(cr, uid, context=context)
        credit_total=0.0
        for i in self.browse(cr,uid,ids):
            for j in i.payment_ids:
                if j.period_id.id == current_period:
                    credit_total = credit_total + j.credit
            res.update({i.id:credit_total})  
            credit_total = 0.0
        return res 
    
    def _cal_bonus(self,cr,uid,ids,bonus_cost,args,context=None):
        res={}
        for i in self.browse(cr,uid,ids,context):
            if i.partner_id and i.partner_id.default_bonus > 0:
                res[i.id] = i.partner_id.default_bonus
            elif i.user_id and i.user_id.bonus > 0:
                res[i.id] = i.user_id.bonus
            else:
                res[i.id] = 0
#         for j in obj_invoice:
#             customer=map(int,j.partner_id or [])
#             userss=map(int,j.user_id or [])
#         for k in customer: 
#             customer_obj=self.pool.get("res.partner").browse(cr,uid,k)
#         customer_bonus=customer_obj.default_bonus
#         for l in  userss: 
#             user_obj=self.pool.get("res.users").browse(cr,uid,l)
#         user_bonus=user_obj.bonus
#         if customer_bonus > user_bonus:
#             bonus=customer_bonus
#         else:
#              bonus=user_bonus
#         for i in ids:
#              res[i]=bonus
        return res
    
    def _get_users(self, cr, uid, ids, context=None):
        result = []
        for id in ids:
            cr.execute('''select id from account_invoice where user_id = %s and type = 'out_invoice' 
            ''' %(id))
            invoice = cr.fetchall()
            for i in invoice:
                result.append(i[0])
        return result

    
    def _get_partner(self, cr, uid, ids, context=None):
        result = []
        for id in ids:
            cr.execute('''select id from account_invoice where partner_id = %s and type = 'out_invoice' 
            ''' %(id))
            invoice = cr.fetchall()
            for i in invoice:
                result.append(i[0])
        return result

    def _get_invoice(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()
   
    _columns={
              "final_cost":fields.function(_cal_cost,type='float',string="Cost of Invoice"),
              "profit":fields.function(_cal_profit,type="float",string="Profit"),
              "money_paid":fields.function(_cal_mony_paid,type="float",string="Money paid in that period"),
              "bonus_cost":fields.function(_cal_bonus,type="float",string="Bonus (%)",
               store={
                    'res.partner': (_get_partner, ['default_bonus'], 0),
                    'res.users': (_get_users,['bonus'], 0)
                }),
              "comision_employee":fields.function(_compute_comision,type = 'float',string = "Employee Commision",
                   store={
                        'res.partner': (_get_partner, ['default_bonus'], 10),
                        'res.users': (_get_users,['bonus'], 10),
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 10),
                       'account.invoice.line': (_get_invoice, ['price_unit', 'invoice_line_tax_id', 'discount', 'quantity'], 10),
                    }),
              }
    
    
    

  
    

