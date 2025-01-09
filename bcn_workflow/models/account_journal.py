from odoo import fields, models, api, _

class CustomAccountJournal(models.Model):
    _inherit = "account.journal"

    
    


    @api.depends('company_id')
    def _compute_l10n_latam_company_use_documents(self):
        for rec in self:
            rec.l10n_latam_company_use_documents = rec.company_id._localization_use_documents()

    @api.onchange('company_id', 'type')
    def _onchange_company(self):
        self.l10n_latam_use_documents = self.type in ['sale', 'purchase'] and \
            self.l10n_latam_company_use_documents

    @api.onchange('type', 'l10n_latam_use_documents')
    def _onchange_type(self):
        res = super()._onchange_type()
        if self.l10n_latam_use_documents:
            self.refund_sequence = False
        return res
    
    @api.constrains('l10n_latam_use_documents')
    def check_use_document(self):
        for rec in self:
            if rec.env['account.move'].search([('journal_id', '=', rec.id), ('posted_before', '=', True)], limit=1):
                pass