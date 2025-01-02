from odoo import api, fields, models, _, Command, SUPERUSER_ID, modules, tools
from odoo.exceptions import UserError
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.payment"

    amount_company_currency = fields.Monetary(
        string='Amount on Company Currency',
        compute='_compute_amount_company_currency',
        currency_field='company_currency_id',
    )
    
    @api.depends('amount', 'other_currency', 'amount_company_currency', 'to_pay_move_line_ids')
    def _compute_exchange_rate(self):
        for rec in self:
            if rec.other_currency:
                _logger.info('Compute exchange_rate')
                if rec.state != 'posted' and len(rec.to_pay_move_line_ids) > 0:
                    _logger.info('Found ')
                    first_move_line = rec.to_pay_move_line_ids[0]
                    if first_move_line.move_id.l10n_ar_currency_rate:
                        rec.exchange_rate = first_move_line.move_id.l10n_ar_currency_rate
                        _logger.info(rec.exchange_rate)
                    else:
                        rec.exchange_rate = rec.amount and (
                            rec.amount_company_currency / rec.amount) or 0.0
                
                else:
                    if rec.matched_move_line_ids:
                        first_move_line = rec.matched_move_line_ids[0] if rec.matched_move_line_ids else False
                        if first_move_line.move_id.l10n_ar_currency_rate:
                            rec.exchange_rate = first_move_line.move_id.l10n_ar_currency_rate
                            _logger.info(rec.exchange_rate)
                        else:
                            rec.exchange_rate = rec.amount and (
                                rec.amount_company_currency / rec.amount) or 0.0
                    else:
                        rec.exchange_rate = rec.amount and (
                                rec.amount_company_currency / rec.amount) or 0.0
            else:
                rec.exchange_rate = 0.0
                
    @api.depends('amount', 'other_currency', 'force_amount_company_currency','exchange_rate')
    def _compute_amount_company_currency(self):
        """
        * Si las monedas son iguales devuelve 1
        * si no, si hay force_amount_company_currency, devuelve ese valor
        * sino, devuelve el amount convertido a la moneda de la cia
        """
        for rec in self:
            _logger.info('Compute _compute_amount_company_currency')
            amount_company_currency = rec.amount
            if not rec.other_currency:
                _logger.info('Entered first')
                amount_company_currency = rec.amount
            else:
                amount_company_currency = rec.amount * rec.exchange_rate
                _logger.info(f'Entered third: {rec.amount},{rec.exchange_rate}')
            _logger.info(amount_company_currency)
            rec.amount_company_currency = amount_company_currency

    @api.depends('amount_company_currency','exchange_rate')
    def _compute_amount_from_dollar(self):
        for rec in self:
            rec.amount = rec.amount_company_currency * rec.exchange_rate