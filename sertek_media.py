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
    _defaults={}
    _description="sertek media module"
    _columns={
              "cost":fields.float("Cost"),
              }

class account_invoice(osv.osv):
    _inherit="account.invoice"
    _defaults={}
    _description="sertek media module"
    
    def _cal_cost(self,cr,uid,ids,cost,args,context=None):
        res={}
        id=tuple(self.pool.get('account.invoice.line').search(cr,uid,[('invoice_id','in',ids)]))
        #print " select order_line_id from sale_order_line_invoice_rel where invoice_id in %s" %(id)
        if id:
            cr.execute('''
             select sum(sl.cost) from sale_order_line_invoice_rel as rel join sale_order_line as sl on rel.order_line_id = sl.id  where rel.invoice_id in %s 
             ''',(id,))
        
        result = cr.fetchall()
        for i in ids:
            if result:
                res[i]=result[0][0]
        #print"===============",res[ids]["cost"][0][0]
        
        return res
        #for i in cr.fetchall():
        #print"================",i
        
            
        
          #  for i in self.browse(cr,uid,ids):
           #     print "=======",i.invoice_line
            #    ids=map(int,i.invoice_line or [])
             #   print ids
               
            #res["cost"]=100
            #print"resssssssssssssssssss",res
        #return {"value":res}
        
    def _cal_profit(self,cr,uid,ids,profit,args,context=None):
        res={}
        for i in self.browse(cr,uid,ids):
            profit=i.amount_untaxed-i.cost
            #res["profit"]=profit
        for j in ids:
            res[j]=profit
        return res
    
    def _cal_mony_paid(self,cr,uid,ids,money_paid,args,context=None):
        res={}
        obj=self.pool.get("account.voucher")
        current_period=obj._get_period(cr, uid, context=context)
        credit_total=0.0
        for i in self.browse(cr,uid,ids):
#             id=map(int,i.payment_ids or [])
#             print"+++++++++++++++++++",i.period_id.id
#             period=i.period_id.id
            for j in i.payment_ids:
                if j.period_id.id == current_period:
                    credit_total = credit_total + j.credit
            res.update({i.id:credit_total})  
            credit_total = 0.0
        return res 
    
    def _cal_bonus(self,cr,uid,ids,bonus_cost,args,context=None):
        res={}
        obj_invoice=self.browse(cr,uid,ids)
        for j in obj_invoice:
            customer=map(int,j.partner_id or [])
            userss=map(int,j.user_id or [])
            #userss=j.user_id 
        for k in customer: 
            customer_obj=self.pool.get("res.partner").browse(cr,uid,k)
        customer_bonus=customer_obj.default_bonus
        for l in  userss: 
            user_obj=self.pool.get("res.users").browse(cr,uid,l)
        user_bonus=user_obj.bonus
        if customer_bonus > user_bonus:
            bonus=customer_bonus
        else:
             bonus=user_bonus
        for i in ids:
             res[i]=bonus
        return res
         
   
    _columns={
              "cost":fields.function(_cal_cost,type='float',string="Cost"),
              "profit":fields.function(_cal_profit,type="float",string="Profit"),
              "money_paid":fields.function(_cal_mony_paid,type="float",string="Money paid in that periods"),
              "bonus_cost":fields.function(_cal_bonus,type="float",string="cost_bonus(%)"),
              }
    
    
    

  
    

