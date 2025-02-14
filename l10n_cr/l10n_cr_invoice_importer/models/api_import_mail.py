import logging
_logger = logging.getLogger(__name__)

import re
import base64
import logging

from odoo import _
from odoo.exceptions import UserError

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree


_logger = logging.getLogger(__name__)


def get_tipo_documento_from_xml(node_xml):
    if node_xml == 'FacturaElectronica':
        return 'FE'
    elif node_xml == 'NotaCreditoElectronica':
        return  'NC'
    elif node_xml == 'NotaDebitoElectronica':
        return 'ND'
    elif node_xml == 'TiqueteElectronico':
        return 'TE'
    return ''


def load_xml_data_from_mail(invoice, load_lines, account_id, product_id=False, analytic_account_id=False):
    try:
        invoice_xml = etree.fromstring(base64.b64decode(invoice.xml_supplier_approval))
        document_type = re.search('FacturaElectronica|NotaCreditoElectronica|NotaDebitoElectronica|TiqueteElectronico',
                                  invoice_xml.tag).group(0)

        if document_type == 'TiqueteElectronico':
            raise UserError(_("This is a Electronic Ticket only a Electronic Bill are valid for taxes"))

    except Exception as e:
        invoice.unlink()
        raise UserError(_("This XML does not comply with the necessary structure to be processed. Error: %s") % e)

    namespaces = invoice_xml.nsmap
    inv_xmlns = namespaces.pop(None)
    namespaces['inv'] = inv_xmlns

    invoice.consecutive_number_receiver = invoice_xml.xpath("inv:NumeroConsecutivo", namespaces=namespaces)[0].text

    invoice.ref = invoice_xml.xpath("inv:NumeroConsecutivo", namespaces=namespaces)[0].text
    invoice.sequence = invoice_xml.xpath("inv:NumeroConsecutivo", namespaces=namespaces)[0].text

    invoice.number_electronic = invoice_xml.xpath("inv:Clave", namespaces=namespaces)[0].text
    # invoice.name = invoice_xml.xpath("inv:Clave", namespaces=namespaces)[0].text
    activity_node = invoice_xml.xpath("inv:CodigoActividad", namespaces=namespaces)
    activity = False
    if activity_node:
        activity_id = activity_node[0].text
        activity = invoice.env['economic.activity'].with_context(active_test=False).search([('code', '=', activity_id)],
                                                                                           limit=1)
    else:
        activity_id = False
    #Flag Invoice load from email
    #invoice.from_mail = True
    invoice.economic_activity_id = activity
    invoice.date_issuance = invoice_xml.xpath("inv:FechaEmision", namespaces=namespaces)[0].text
    invoice.invoice_date = invoice.date_issuance
    invoice.tipo_documento = get_tipo_documento_from_xml(document_type)

    if invoice.tipo_documento == 'TE':
        invoice.unlink()
        raise UserError(_("No se aceptan Tiquete Electronico") % e)

    emisor = invoice_xml.xpath("inv:Emisor/inv:Identificacion/inv:Numero", namespaces=namespaces)[0].text
    try:
        receptor = invoice_xml.xpath("inv:Receptor/inv:Identificacion/inv:Numero", namespaces=namespaces)[0].text
    except Exception as e:
        invoice.unlink()
        raise UserError('The receptor info not was founded in XML. Please check the email in the inbox.') 

    if receptor != invoice.company_id.vat:
        #Deleted Invoice and stop Process
        invoice.unlink()
        raise UserError('The receptor in the XML does not correspond to the current company ' +
                        receptor + '. Please check the email in the inbox.') 

    currency_node = invoice_xml.xpath("inv:ResumenFactura/inv:CodigoTipoMoneda/inv:CodigoMoneda", namespaces=namespaces)

    if currency_node:
        invoice.currency_id = invoice.env['res.currency'].search([('name', '=', currency_node[0].text)], limit=1).id
    else:
        invoice.currency_id = invoice.env['res.currency'].search([('name', '=', 'CRC')], limit=1).id

    partner = invoice.env['res.partner'].search([('vat', '=', emisor),
                                                 '|',
                                                 ('company_id', '=', invoice.company_id.id),
                                                 ('company_id', '=', False)],
                                                limit=1)

    if partner:
        invoice.partner_id = partner
    else:
        #Try Create Partner...
        try:
            nombre_emisor = invoice_xml.xpath("inv:Emisor/inv:Nombre", namespaces=namespaces)[0].text
            type_emisor = invoice_xml.xpath("inv:Emisor/inv:Identificacion/inv:Tipo", namespaces=namespaces)[0].text
            type = invoice.env['identification.type'].search([('code', '=', type_emisor)], limit=1)
        except Exception as e:
            invoice.unlink()
            raise UserError("There isn't necessary info for create Partner. Please check the email in the inbox.")

        vals = {
            'name': nombre_emisor,
            'company_id': invoice.company_id.id,
            'identification_id': type.id,
            'vat': emisor,
            'active': True,
            'is_company': True,
            'type': 'contact',
            'activity_id': activity.id
        }
        try:
            email_emisor  = invoice_xml.xpath("inv:Emisor/inv:CorreoElectronico", namespaces=namespaces)[0].text
            vals['email'] = email_emisor
        except Exception as e:
            _logger.info("There isn't complementary info, error ({0}), but the invoicy will be created".format(e))
            pass
        try:
            phone_emisor = invoice_xml.xpath("inv:Emisor/inv:Telefono/inv:NumTelefono", namespaces=namespaces)[0].text
            vals['phone'] = phone_emisor
        except Exception as e:
            _logger.info("There isn't complementary info, error ({0}), but the invoicy will be created".format(e))
            pass
        try:
            payment_emisor = invoice_xml.xpath("inv:MedioPago", namespaces=namespaces)[0].text
            payment = invoice.env['payment.methods'].search([('sequence', '=', payment_emisor)], limit=1)
            vals['payment_methods_id'] = payment.id
        except Exception as e:
            _logger.info("There isn't complementary info, error ({0}), but the invoicy will be created".format(e))
            pass
        partner = invoice.env['res.partner'].sudo().create(vals)
        invoice.partner_id = partner
        invoice.message_post(
            body='The provider does not exist; it has been created automatically, please fill in the details of this provider before validating the bill.')
        _logger.info('The provider does not exist; it has been created automatically, please fill in the details of this provider before validating the bill.')


    if not invoice.partner_id.economic_activities_ids:
        invoice.partner_id.action_get_economic_activities()

    # invoice.account_id = partner.property_account_payable_id
    # invoice.payment_term_id = partner.property_supplier_payment_term_id

    payment_method_node = invoice_xml.xpath("inv:MedioPago", namespaces=namespaces)
    if payment_method_node:
        invoice.payment_methods_id = invoice.env['payment.methods'].sudo().search(
            [('sequence', '=', payment_method_node[0].text)], limit=1)
    else:
        invoice.payment_methods_id = partner.payment_methods_id

    _logger.debug('FECR - load_lines: %s - account: %s' %
                  (load_lines, account_id))



    product = False
    if product_id:
        product = product_id.id

    analytic_account = False
    if analytic_account_id:
        analytic_account = analytic_account_id.id

    # if load_lines and not invoice.invoice_line_ids:
    if load_lines:
        lines = invoice_xml.xpath("inv:DetalleServicio/inv:LineaDetalle", namespaces=namespaces)
        new_lines = invoice.env['account.move.line']
        dict_lines = {}
        for line in lines:
            product_uom = invoice.env['uom.uom'].search(
                [('code', '=', line.xpath("inv:UnidadMedida", namespaces=namespaces)[0].text)],
                limit=1).id
            total_amount = float(line.xpath("inv:MontoTotal", namespaces=namespaces)[0].text)

            discount_percentage = 0.0
            discount_note = None

            if total_amount > 0:
                discount_node = line.xpath("inv:Descuento", namespaces=namespaces)
                if discount_node:
                    discount_amount_node = discount_node[0].xpath("inv:MontoDescuento", namespaces=namespaces)[0]
                    discount_amount = float(discount_amount_node.text or '0.0')
                    discount_percentage = discount_amount / total_amount * 100
                    discount_note = discount_node[0].xpath("inv:NaturalezaDescuento", namespaces=namespaces)[0].text
                else:
                    discount_amount_node = line.xpath("inv:MontoDescuento", namespaces=namespaces)
                    if discount_amount_node:
                        discount_amount = float(discount_amount_node[0].text or '0.0')
                        discount_percentage = discount_amount / total_amount * 100
                        discount_note = line.xpath("inv:NaturalezaDescuento", namespaces=namespaces)[0].text

            total_tax = 0.0
            taxes = []
            tax_nodes = line.xpath("inv:Impuesto", namespaces=namespaces)
            dict_tax = {}
            for tax_node in tax_nodes:
                tax_code = re.sub(r"[^0-9]+", "", tax_node.xpath("inv:Codigo", namespaces=namespaces)[0].text)
                tax_amount = float(tax_node.xpath("inv:Tarifa", namespaces=namespaces)[0].text)
                _logger.debug('FECR - tax_code: %s', tax_code)
                _logger.debug('FECR - tax_amount: %s', tax_amount)

                if product_id and product_id.non_tax_deductible:
                    tax = invoice.env['account.tax'].search(
                        [('tax_code', '=', tax_code),
                         ('amount', '=', tax_amount),
                         ('type_tax_use', '=', 'purchase'),
                         ('non_tax_deductible', '=', True),
                         ('active', '=', True)],
                        limit=1)
                else:
                    tax = invoice.env['account.tax'].search(
                        [('tax_code', '=', tax_code),
                         ('amount', '=', tax_amount),
                         ('type_tax_use', '=', 'purchase'),
                         ('non_tax_deductible', '=', False),
                         ('active', '=', True)],
                        limit=1)

                if tax:
                    # uno de los errores de por qué hay diferencia en los decimáles es
                    # porque el sistema no considera el campo total_tax para calcular el total de cada impuesto.
                    # El otro error de por qué hay diferencia al imprimir los reportes,
                    # es debido a que el monto de impuesto otros no lo toma del xml, sino se calcula desde el sql.
                    tax_node_amount = float(tax_node.xpath("inv:Monto", namespaces=namespaces)[0].text)
                    total_tax += tax_node_amount

                    if tax.id not in dict_tax:
                        dict_tax[tax.id] = {'amount': 0.0}

                    dict_tax[tax.id].update(amount=dict_tax[tax.id]['amount'] + tax_node_amount)

                    exonerations = tax_node.xpath("inv:Exoneracion", namespaces=namespaces)
                    if exonerations:
                        for exoneration_node in exonerations:
                            exoneration_percentage = float(
                                exoneration_node.xpath("inv:PorcentajeExoneracion", namespaces=namespaces)[0].text)
                            tax = invoice.env['account.tax'].search(
                                [('percentage_exoneration', '=', exoneration_percentage),
                                 ('type_tax_use', '=', 'purchase'),
                                 ('non_tax_deductible', '=', False),
                                 ('has_exoneration', '=', True),
                                 ('active', '=', True)],
                                limit=1)

                            if tax:
                                taxes.append((4, tax.id))
                    else:
                        taxes.append((4, tax.id))
                else:
                    if product_id and product_id.non_tax_deductible:
                        invoice.message_post(
                            body='Tax code %s and percentage %s as non-tax deductible is not registered in the system' % (
                            tax_code, tax_amount))
                        _logger.info(
                            'Tax code %s and percentage %s as non-tax deductible is not registered in the system' % (
                            tax_code, tax_amount))
                    else:
                        _logger.info('Tax code %s and percentage %s is not registered in the system' % (tax_code, tax_amount))
                        invoice.message_post(
                            body='Tax code %s and percentage %s is not registered in the system' % (
                                tax_code, tax_amount))

            _logger.debug('FECR - line taxes: %s' % (taxes))
            invoice_line = invoice.env['account.move.line'].create({
                'name': line.xpath("inv:Detalle", namespaces=namespaces)[0].text,
                'move_id': invoice.id,
                'price_unit': line.xpath("inv:PrecioUnitario", namespaces=namespaces)[0].text,
                'quantity': line.xpath("inv:Cantidad", namespaces=namespaces)[0].text,
                #'uom_id': product_uom,
                'sequence': line.xpath("inv:NumeroLinea", namespaces=namespaces)[0].text,
                'discount': discount_percentage,
                'discount_note': discount_note,
                # 'total_amount': total_amount,
                'product_id': product,
                #'account_id': account_id.id or False,
                #'account_analytic_id': analytic_account,
                # 'amount_untaxed': float(line.xpath("inv:SubTotal", namespaces=namespaces)[0].text),
                'total_tax': total_tax,
                'display_type': 'product',
                'economic_activity_id': invoice.economic_activity_id.id,
                "tax_ids": taxes
            })

            #invoice_line.price_unit = line.xpath("inv:PrecioUnitario", namespaces=namespaces)[0].text
            #invoice_line

            # This must be assigned after line is created
            # invoice_line.tax_ids = taxes
            # invoice_line.economic_activity_id = activity
            new_lines += invoice_line

            dict_lines[invoice_line.id] = {'price_unit': line.xpath("inv:PrecioUnitario", namespaces=namespaces)[0].text, 'taxes': dict_tax}

        invoice.invoice_line_ids = new_lines


        if not invoice.invoice_line_ids:
            invoice.unlink()
            raise UserError('Documento no cuenta con lineas de detalles.') 

    #invoice.amount_total_electronic_invoice = invoice_xml.xpath("inv:ResumenFactura/inv:TotalComprobante", namespaces=namespaces)[0].text

    #tax_node = invoice_xml.xpath("inv:ResumenFactura/inv:TotalImpuesto", namespaces=namespaces)
    #if tax_node:
    #    invoice.amount_tax_electronic_invoice = tax_node[0].text

    #dict_lines = dict_lines if invoice.type == 'in_invoice' else {}
    #invoice.with_context(dict_lines=dict_lines).compute_taxes()
