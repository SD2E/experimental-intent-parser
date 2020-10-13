from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.intent_parser_table import IntentParserTable
import intent_parser.constants.intent_parser_constants as ip_constants

def create_fake_controls_table(table_index=None):
    ip_table = IntentParserTable()
    curr_table_index = 0
    if table_index is not None:
        ip_cell = IntentParserCell()
        ip_cell.add_paragraph('Table %d: Controls' % table_index)
        ip_table.add_row([ip_cell])
        ip_table.set_caption_row_index(curr_table_index)
        curr_table_index += 1
    header_row = _create_table_headers(['Control Type', 'Strains', 'Channel', 'Contents', 'Timepoint'])
    ip_table.add_row(header_row)
    ip_table.set_header_row_index(curr_table_index)
    return ip_table

def create_fake_measurement_table(table_index=None, reagent_media_cells=None):
    ip_table = IntentParserTable()
    curr_table_index = 0
    if table_index is not None:
        ip_cell = IntentParserCell()
        ip_cell.add_paragraph('Table %d: Measurements' % table_index)
        ip_table.add_row([ip_cell])
        ip_table.set_caption_row_index(curr_table_index)
        curr_table_index += 1
    header_names = [ip_constants.HEADER_MEASUREMENT_TYPE_VALUE,
                    ip_constants.HEADER_FILE_TYPE_VALUE,
                    ip_constants.HEADER_REPLICATE_VALUE,
                    ip_constants.HEADER_STRAINS_VALUE,
                    ip_constants.HEADER_ODS_VALUE,
                    ip_constants.HEADER_TEMPERATURE_VALUE,
                    ip_constants.HEADER_TIMEPOINT_VALUE,
                    ip_constants.HEADER_BATCH_VALUE,
                    ip_constants.HEADER_CONTROL_VALUE,
                    ip_constants.HEADER_SAMPLES_VALUE,
                    ip_constants.HEADER_NOTES_VALUE,
                    ip_constants.HEADER_COLUMN_ID_VALUE,
                    ip_constants.HEADER_LAB_ID_VALUE,
                    ip_constants.HEADER_ROW_ID_VALUE,
                    ip_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE,
                    ip_constants.HEADER_USE_RNA_INHIBITOR_IN_REACTION_VALUE,
                    ip_constants.HEADER_DNA_REACTION_CONCENTRATION_VALUE,
                    ip_constants.HEADER_TEMPLATE_DNA_VALUE]
    header_row = _create_table_headers(header_names)
    if reagent_media_cells:
        header_row.extend(reagent_media_cells)

    ip_table.add_row(header_row)
    ip_table.set_header_row_index(curr_table_index)
    return ip_table

def create_fake_parameter(table_index=None):
    ip_table = IntentParserTable()
    curr_table_index = 0
    if table_index is not None:
        ip_cell = IntentParserCell()
        ip_cell.add_paragraph('Table %d: Parameter' % table_index)
        ip_table.add_row([ip_cell])
        ip_table.set_caption_row_index(curr_table_index)
        curr_table_index += 1
    header_names = [ip_constants.HEADER_PARAMETER_VALUE,
                    ip_constants.HEADER_PARAMETER_VALUE_VALUE]
    header_row = _create_table_headers(header_names)

    ip_table.add_row(header_row)
    ip_table.set_header_row_index(curr_table_index)
    return ip_table

def create_fake_experiment_status_table(table_index=None):
    ip_table = IntentParserTable()
    curr_table_index = 0
    if table_index is not None:
        ip_cell = IntentParserCell()
        ip_cell.add_paragraph('Table %d: Experiment Status' % table_index)
        ip_table.add_row([ip_cell])
        ip_table.set_caption_row_index(curr_table_index)
        curr_table_index += 1
    header_names = [ip_constants.HEADER_PIPELINE_STATUS_VALUE,
                    ip_constants.HEADER_LAST_UPDATED_VALUE,
                    ip_constants.HEADER_PATH_VALUE,
                    ip_constants.HEADER_STATE_VALUE]
    header_row = _create_table_headers(header_names)

    ip_table.add_row(header_row)
    ip_table.set_header_row_index(curr_table_index)
    return ip_table

def create_fake_experiment_specification_table(table_index=None):
    ip_table = IntentParserTable()
    curr_table_index = 0
    if table_index is not None:
        ip_cell = IntentParserCell()
        ip_cell.add_paragraph('Table %d: Experiment Specification' % table_index)
        ip_table.add_row([ip_cell])
        ip_table.set_caption_row_index(curr_table_index)
        curr_table_index += 1
    header_names = ['Experiment Id',
                    ip_constants.HEADER_EXPERIMENT_STATUS_VALUE]
    header_row = _create_table_headers(header_names)
    ip_table.add_row(header_row)
    ip_table.set_header_row_index(curr_table_index)
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

def create_experiment_status_table_row(pipeline_status_cell=None,
                                       last_updated_cell=None,
                                       path_cell=None,
                                       state_cell=None):
    if pipeline_status_cell is None:
        pipeline_status_cell = IntentParserCell()
        pipeline_status_cell.add_paragraph('')
    if last_updated_cell is None:
        last_updated_cell = IntentParserCell()
        last_updated_cell.add_paragraph('')
    if path_cell is None:
        path_cell = IntentParserCell()
        path_cell.add_paragraph('')
    if state_cell is None:
        state_cell = IntentParserCell()
        state_cell.add_paragraph('')
    return [pipeline_status_cell, last_updated_cell, path_cell, state_cell]

def create_experiment_specification_table_row(experiment_id_cell=None,
                                       experiment_status_cell=None):
    if experiment_id_cell is None:
        experiment_id_cell = IntentParserCell()
        experiment_id_cell.add_paragraph('')
    if experiment_status_cell is None:
        experiment_status_cell = IntentParserCell()
        experiment_status_cell.add_paragraph('')

    return [experiment_id_cell, experiment_status_cell]

def create_measurement_table_row(measurement_type_cell=None,
                                 file_type_cell=None,
                                 replicate_cell=None,
                                 strain_cell=None,
                                 ods_cell=None,
                                 temperature_cell=None,
                                 timepoint_cell=None,
                                 batch_cell=None,
                                 controls_cell=None,
                                 sample_cell=None,
                                 notes_cell=None,
                                 lab_id_cell=None,
                                 row_id_cell=None,
                                 col_id_cell=None,
                                 num_neg_controls_cell=None,
                                 rna_inhibitor_reaction_cell=None,
                                 dna_reaction_concentration_cell=None,
                                 template_dna_cell=None):
    if measurement_type_cell is None:
        measurement_type_cell = IntentParserCell()
        measurement_type_cell.add_paragraph('')
    if file_type_cell is None:
        file_type_cell = IntentParserCell()
        file_type_cell.add_paragraph('')
    if replicate_cell is None:
        replicate_cell = IntentParserCell()
        replicate_cell.add_paragraph('')
    if strain_cell is None:
        strain_cell = IntentParserCell()
        strain_cell.add_paragraph('')
    if ods_cell is None:
        ods_cell = IntentParserCell()
        ods_cell.add_paragraph('')
    if temperature_cell is None:
        temperature_cell = IntentParserCell()
        temperature_cell.add_paragraph('')
    if timepoint_cell is None:
        timepoint_cell = IntentParserCell()
        timepoint_cell.add_paragraph('')
    if batch_cell is None:
        batch_cell = IntentParserCell()
        batch_cell.add_paragraph('')
    if controls_cell is None:
        controls_cell = IntentParserCell()
        controls_cell.add_paragraph('')
    if sample_cell is None:
        sample_cell = IntentParserCell()
        sample_cell.add_paragraph('')
    if notes_cell is None:
        notes_cell = IntentParserCell()
        notes_cell.add_paragraph('')
    if lab_id_cell is None:
        lab_id_cell = IntentParserCell()
        lab_id_cell.add_paragraph('')
    if row_id_cell is None:
        row_id_cell = IntentParserCell()
        row_id_cell.add_paragraph('')
    if col_id_cell is None:
        col_id_cell = IntentParserCell()
        col_id_cell.add_paragraph('')
    if num_neg_controls_cell is None:
        num_neg_controls_cell = IntentParserCell()
        num_neg_controls_cell.add_paragraph('')
    if rna_inhibitor_reaction_cell is None:
        rna_inhibitor_reaction_cell = IntentParserCell()
        rna_inhibitor_reaction_cell.add_paragraph('')
    if dna_reaction_concentration_cell is None:
        dna_reaction_concentration_cell = IntentParserCell()
        dna_reaction_concentration_cell.add_paragraph('')
    if template_dna_cell is None:
        template_dna_cell = IntentParserCell()
        template_dna_cell.add_paragraph('')

    return [measurement_type_cell,
            file_type_cell,
            replicate_cell,
            strain_cell,
            ods_cell,
            temperature_cell,
            timepoint_cell,
            batch_cell,
            controls_cell,
            sample_cell,
            notes_cell,
            col_id_cell,
            lab_id_cell,
            row_id_cell,
            num_neg_controls_cell,
            rna_inhibitor_reaction_cell,
            dna_reaction_concentration_cell,
            template_dna_cell
            ]

def create_fake_lab_table(table_index=None):
    ip_table = IntentParserTable()
    if table_index is not None:
        ip_cell = IntentParserCell()
        ip_cell.add_paragraph('Table %d: Lab' % table_index)
        ip_table.add_row([ip_cell])
    ip_table.set_header_row_index(0)
    return ip_table

def create_parameter_table_row(parameter_cell=None,
                               parameter_value_cell=None):
    if parameter_cell is None:
        parameter_cell = IntentParserCell()
        parameter_cell.add_paragraph('')
    if parameter_value_cell is None:
        parameter_value_cell = IntentParserCell()
        parameter_value_cell.add_paragraph('')
    return [parameter_cell,
            parameter_value_cell]

def _create_table_headers(header_names):
    header_row = []
    for name in header_names:
        ip_cell = IntentParserCell()
        ip_cell.add_paragraph(name)
        header_row.append(ip_cell)
    return header_row
