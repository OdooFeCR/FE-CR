# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import logging
import email
import base64
import pathlib

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

from lxml import etree
from datetime import datetime
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, pycompat
from odoo.tests.common import Form
from . import api_import_mail

_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 10
MAIL_TIMEOUT = 60


class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    def fetch_mail(self):
        _logger.info("Test from ir.cron")
        res_companies_ids = self.env['res.company'].sudo().search([])
        for res_company_id in res_companies_ids:
            if res_company_id.import_bill_automatic:
                additionnal_context = {
                    'fetchmail_cron_running': True
                }
                MailThread = self.env['mail.thread']
                server = res_company_id.import_bill_mail_server_id
                additionnal_context['fetchmail_server_id'] = server.id
                additionnal_context['server_type'] = server.server_type
                # Buscar el mail, leer correos --- importar factura ...
                _logger.info('Start checking for new emails on %s server %s', server.server_type, server.name)
                count, failed = 0, 0
                imap_server = None
                if server.server_type == 'imap':
                    try:
                        imap_server = server.connect()
                        imap_server.select(mailbox=res_company_id.import_bill_folder_import or 'INBOX')
                        result, data = imap_server.search(None, '(UNSEEN)')
                        if not data[0]:
                            _logger.info("Empty Folder (Stop Execute)")
                            return
                        for num in data[0].split():
                            result, data = imap_server.fetch(num, '(RFC822)')
                            imap_server.store(num, '-FLAGS', '\\Seen')
                            message = data[0][1]
                            try:
                                # To leave the mail in the state in which they were.
                                if isinstance(message, xmlrpclib.Binary):
                                    message = bytes(message.data)
                                if isinstance(message, str):
                                    message = message.encode('utf-8')
                                # extract = getattr(email, 'message_from_bytes', email.message_from_string)
                                # msg_txt = extract(message)
                                # parse the message, verify we are not in a loop by checking message_id is not
                                # duplicated

                                message = email.message_from_bytes(message, policy=email.policy.SMTP)

                                # parse the message, verify we are not in a loop by checking message_id is not duplicated
                                msg = MailThread.message_parse(message, save_original=False)

                                # msg = MailThread.with_context(**additionnal_context).message_parse(msg_txt,
                                #                                                                    save_original=False)
                                # Fixing --> Save Original : False --> No store Content On Odoo
                                _logger.info("------ Process Message --------")
                                _logger.info("Subject : %s " % msg.get('subject', ''))
                                _logger.info("From: %s " % msg.get('from', ''))
                                _logger.info("To: %s " % msg.get('to', ''))
                                result = self.create_invoice_with_attamecth(msg, res_company_id)
                                if result and not isinstance(result, bool):
                                    if not server.original:
                                        _logger.info("Deleting Mail")
                                        imap_server.store(num, '+FLAGS', '\\Deleted')
                                    _logger.info("Invoice created correctly %s", str(result))
                                elif result:
                                    if not server.original:
                                        _logger.info("Deleting Mail")
                                        imap_server.store(num, '+FLAGS', '\\Deleted')
                                    _logger.info("Repeated Invoice")
                                else:
                                    _logger.info("Ignore email")
                            except Exception as e:
                                _logger.info('Failed to process mail from %s server %s. Exception (%s)', server.server_type,
                                             server.name, str(e),
                                             exc_info=True)
                                failed += 1
                            imap_server.store(num, '+FLAGS', '\\Seen')
                            self._cr.commit()
                            count += 1
                            _logger.info("------ End Process Message -------")
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count,
                                     server.server_type, server.name, (count - failed), failed)
                    except Exception as e:
                        _logger.info("General failure when trying to fetch mail from %s server %s. Exception (%s)",
                                     server.server_type,
                                     server.name, str(e), exc_info=True)
                    finally:
                        if imap_server:
                            _logger.info("Finally Execute -> Close Imap Server")

                            try:
                                # Buscar registros en account.move creados sin razon
                                moves_to_delete = self.env['account.move'].search([
                                    ('partner_id', '=', False),
                                    ('ref', '=', False),
                                    ('state', '=', 'draft'),
                                    ('move_type', '=', 'in_invoice'),
                                    ('line_ids', '=', False),  # Asegurarse de que no haya líneas
                                ])
                                _logger.info('Se encontraron {0} documentos creados erroneamente, se procedera eliminar'.format(len(moves_to_delete)))

                                # Eliminar los registros encontrados
                                moves_to_delete.unlink()
                            except Exception as e:
                                _logger.info("Ocurrio un error eliminando las facturas creadas erroneamente, se eliminaran en la siguiente pasada.")


                            imap_server.close()
                            imap_server.logout()
                    server.write({'date': fields.Datetime.now()})
                else:
                    _logger.info("Only Support for IMAP Server")
                    server.write({'date': fields.Datetime.now()})
                    return super(FetchmailServer, self).fetch_mail()

    @staticmethod
    def is_xml_file_in_attachment(attach):
        file_name = attach.fname or 'item.ignore'
        if pathlib.Path(file_name.upper()).suffix == '.XML':
            return True
        return False

    def get_bill_exist_or_false(self, invoice_xml):
        namespaces = invoice_xml.nsmap
        inv_xmlns = namespaces.pop(None)
        namespaces['inv'] = inv_xmlns
        electronic_number = invoice_xml.xpath("inv:Clave", namespaces=namespaces)[0].text
        domain = [('number_electronic', '=', electronic_number)]
        return self.env['account.move'].search(domain, limit=1)

    def create_ir_attachment_invoice(self, invoice, attach, mimetype):
        content = attach.content
        if isinstance(attach.content,  str):
            content = attach.content.encode('utf-8')
        ir_attachment = self.env['ir.attachment'].create({
            'name': attach.fname,
            'type': 'binary',
            'datas': base64.b64encode(content),
            'store_fname': attach.fname,
            'res_model': 'account.move',
            'res_id': invoice.id,
            'mimetype': mimetype
        })

        return ir_attachment

    def create_invoice_with_attamecth(self, msg, company_id):
        for attach in msg.get('attachments'):
            if self.is_xml_file_in_attachment(attach):
                try:
                    #Este funciona par bytes y str
                    attachencode = base64.encodebytes(attach.content) if isinstance(attach.content, bytes) else base64.encodebytes(attach.content.encode('utf-8'))
                    
                    invoice_xml = etree.fromstring(base64.b64decode(attachencode))
                    document_type = re.search(
                        'FacturaElectronica|NotaCreditoElectronica|'
                        'NotaDebitoElectronica|TiqueteElectronico|MensajeHacienda',
                        invoice_xml.tag).group(0)
                    
                    # if document_type == 'TiqueteElectronico' or document_type == 'NotaDebitoElectronica':
                    if document_type == 'TiqueteElectronico':
                        _logger.info("Este es un Tiquete Electronico no son válidas para impuestos.")
                        continue
                        # continue
                    # Check Exist
                    exist_invoice = self.get_bill_exist_or_false(invoice_xml)

                    if document_type == 'MensajeHacienda':
                        if exist_invoice:
                            attachment_id = self.create_ir_attachment_invoice(exist_invoice, attach,
                                                                                  'application/xml')
                            exist_invoice.message_post(attachment_ids=[attachment_id.id])
                            # exist_invoice.has_ack = True
                            _logger.info('Documento ya registrado previamente.')
                            return exist_invoice
                        continue
                    if document_type == 'FacturaElectronica' and exist_invoice:
                        _logger.info("Its duplicate Invoice (%s), Deleting Mail" % exist_invoice.ref)
                        return True
                    if document_type == 'NotaCreditoElectronica' and exist_invoice:
                        _logger.info("Its duplicate Invoice (%s), Deleting Mail" % exist_invoice.ref)
                        return True
                    # If not is ACK is Invoice
                    if document_type == 'FacturaElectronica' or document_type == 'NotaDebitoElectronica':
                        type_invoice = 'in_invoice'
                    elif document_type == 'NotaCreditoElectronica':
                        type_invoice = 'in_refund'
                    else:
                        _logger.info("The electronic receipt is unknown, it will simply be ignored")

                    self = self.with_context(default_journal_id=company_id.import_bill_journal_id.id,
                                             default_move_type='in_invoice', move_type=type_invoice, journal_type='purchase', default_payment_methods_id=1)
                    invoice_form = Form(self.env['account.move'].with_context(default_payment_methods_id=1), view='account.view_move_form')

                    print('invoice_form: ', invoice_form)
                    invoice_form._values['payment_methods_id'] = 1
                    invoice_form._values['move_type'] = type_invoice or 'in_invoice'

                    invoice = invoice_form.save()
                    print('invoice: ', invoice)
                    invoice.fname_xml_supplier_approval = attach.fname

                    content_supplier_approval = attach.content
                    if isinstance(attach.content,  str):
                        content_supplier_approval = attach.content.encode('utf-8')
                    invoice.xml_supplier_approval = base64.encodebytes(content_supplier_approval)
                    api_import_mail.load_xml_data_from_mail(invoice, True, company_id.import_bill_account_id,
                                                            company_id.import_bill_product_id,
                                                            company_id.import_bill_account_analytic_id)

                    if invoice:
                        attachment_id = self.create_ir_attachment_invoice(invoice, attach, 'application/xml')
                        list_attachment = [attachment_id.id]
                        # Searching PDF
                        for attach in msg.get('attachments'):
                            file_name = attach.fname or 'item.ignore'
                            if pathlib.Path(file_name.upper()).suffix == '.XML':
                                content_invoice_xml = attach.content
                                if isinstance(attach.content,  str):
                                    content_invoice_xml = attach.content.encode('utf-8')
                                attachencode = base64.encodebytes(content_invoice_xml)
                                invoice_xml = etree.fromstring(base64.b64decode(attachencode))
                                if re.search('MensajeHacienda', invoice_xml.tag):
                                    list_attachment.append(
                                        self.create_ir_attachment_invoice(invoice, attach, 'application/xml').id)
                            if pathlib.Path(file_name.upper()).suffix == '.PDF':
                                list_attachment.append(
                                    self.create_ir_attachment_invoice(invoice, attach, 'application/pdf').id)

                        invoice.message_post(attachment_ids=list_attachment)
                        return invoice
                    else:
                        False

                except Exception as e:
                    _logger.info("This XML file is not XML-compliant. Error: %s", e)
                    continue
        return False
