from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.intent_parser_table import IntentParserTable

def create_fake_measurement_table():
    pass

def create_fake_controls_table(table_index):
    ip_table = IntentParserTable()
    ip_cell = IntentParserCell()
    ip_cell.add_paragraph('Table %d: Controls' % table_index)

    ip_table.add_row([ip_cell])
    header_row = _create_table_headers(['Control Type', 'Strains', 'Channel', 'Contents', 'Timepoint'])
    ip_table.add_row(header_row)
    ip_table.set_caption_row_index(0)
    ip_table.set_header_row_index(1)
    return ip_table

def create_control_table_row(control_type_cell=None,
                             strains_cell=None,
                             channel_cell=None,
                             contents_cell=None,
                             timepoint_cell=None):
    if control_type_cell is None:
        control_type_cell = IntentParserCell()
        control_type_cell.add_paragraph('')
    if strains_cell is None:
        strains_cell = IntentParserCell()
        strains_cell.add_paragraph('')
    if channel_cell is None:
        channel_cell = IntentParserCell()
        channel_cell.add_paragraph('')
    if contents_cell is None:
        contents_cell = IntentParserCell()
        contents_cell.add_paragraph('')
    if timepoint_cell is None:
        timepoint_cell = IntentParserCell()
        timepoint_cell.add_paragraph('')
    return [control_type_cell, strains_cell, channel_cell, contents_cell, timepoint_cell]

def create_fake_lab_table():
    pass

def create_fake_parameter():
    pass

def _create_table_headers(header_names):
    header_row = []
    for name in header_names:
        ip_cell = IntentParserCell()
        ip_cell.add_paragraph(name)
        header_row.append(ip_cell)
    return header_row

def _create_table_caption(caption):
    ip_cell = IntentParserCell()
    ip_cell.add_paragraph(caption)
