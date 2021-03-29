from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.intent.lab_intent import LabIntent
from intent_parser.intent.measure_property_intent import ReagentIntent, MediaIntent
from intent_parser.lab_experiment import LabExperiment
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
import intent_parser.constants.intent_parser_constants as ip_constants

class TableCreator(object):

    def __init__(self):
        self.doc_accessor = GoogleAccessor().get_google_doc_accessor()
        self.ip_table_factory = IntentParserTableFactory()

    def create_lab_table_from_intent(self, lab_intent: LabIntent):
        lab_table = [['%s: %s' % (ip_constants.HEADER_LAB_VALUE, lab_intent.get_lab_name())]]
        return lab_table

    def create_parameter_table_from_intent(self, parameter_intent):
        parameter_table = [[ip_constants.HEADER_PARAMETER_VALUE, ip_constants.HEADER_PARAMETER_VALUE_VALUE]]

        protocol_name = parameter_intent.get_protocol_name() if parameter_intent.get_protocol_name() else ' '
        parameter_table.append([ip_constants.PARAMETER_PROTOCOL_NAME, protocol_name])

        for name, value in parameter_intent.get_default_parameters().items():
            parameter_table.append([name, str(value)])
        return parameter_table

    def create_measurement_table_from_intents(self, measurement_intents):
        measurement_headers = self._create_measurement_table_header(measurement_intents)
        measurement_data = self._add_measurement_data(measurement_intents, measurement_headers)
        measurement_table = [list(measurement_headers.keys())] + measurement_data
        return measurement_table

    def _add_measurement_data(self, measurement_intents, measurement_headers):
        measurement_data = []
        for measurement_intent in measurement_intents:
            row_data = [' '] * len(measurement_headers)
            if ip_constants.HEADER_MEASUREMENT_TYPE_VALUE in measurement_headers:
                measurement_type = measurement_intent.get_measurement_type() if measurement_intent.has_measurement_type() else ' '
                index = measurement_headers[ip_constants.HEADER_MEASUREMENT_TYPE_VALUE]
                row_data[index] = measurement_type
            if ip_constants.HEADER_STRAINS_VALUE in measurement_headers:
                if measurement_intent.size_of_strains() > 0:
                    strain_values = ', '.join([strain.get_name().get_name() for strain in measurement_intent.get_strains()])
                    index = measurement_headers[ip_constants.HEADER_STRAINS_VALUE]
                    row_data[index] = strain_values
            if ip_constants.HEADER_TEMPERATURE_VALUE in measurement_headers:
                if measurement_intent.size_of_temperatures() > 0:
                    temperature_values = ', '.join(['%s %s' % (str(temperature.get_value()), str(temperature.get_unit()))
                                                   for temperature in measurement_intent.get_temperatures()])
                    index = measurement_headers[ip_constants.HEADER_TEMPERATURE_VALUE]
                    row_data[index] = temperature_values
            if ip_constants.HEADER_TIMEPOINT_VALUE in measurement_headers:
                if measurement_intent.size_of_timepoints() > 0:
                    timepoint_values = ', '.join(['%s %s' % (str(timepoint.get_value()), str(timepoint.get_unit()))
                                                  for timepoint in measurement_intent.get_timepoints()])
                    index = measurement_headers[ip_constants.HEADER_TIMEPOINT_VALUE]
                    row_data[index] = timepoint_values
            if not measurement_intent.contents_is_empty():
                for content_intent in measurement_intent.get_contents().get_contents():
                    if content_intent.size_of_reagents() > 0:
                        for reagent in content_intent.get_reagents():
                            reagent_name = reagent.get_reagent_name().get_name()
                            if reagent_name in measurement_headers and len(reagent.get_reagent_values()) > 0:
                                reagent_values = []
                                for reagent_value in reagent.get_reagent_values():
                                    if reagent_value.get_unit():
                                        reagent_values.append('%s %s' % (str(reagent_value.get_value()), str(reagent_value.get_unit())))
                                    else:
                                        reagent_values.append('%s' % (str(reagent_value.get_value())))
                                index = measurement_headers[reagent_name]
                            row_data[index] = ', '.join(reagent_values)
                    elif content_intent.size_of_medias() > 0:
                        for media in content_intent.get_medias():
                            media_name = media.get_media_name().get_name()
                            if media_name in measurement_headers and len(media.get_media_values()) > 0:
                                media_values = ', '.join(['%s' % media_value.get_name() for media_value in media.get_media_values()])
                                index = measurement_headers[media_name]
                                row_data[index] = media_values
            measurement_data.append(row_data)
        return measurement_data

    def _create_measurement_table_header(self, measurement_intents):
        header_indices = {}
        for measurement_intent in measurement_intents:
            if measurement_intent.has_measurement_type() and ip_constants.HEADER_MEASUREMENT_TYPE_VALUE not in header_indices:
                header_indices[ip_constants.HEADER_MEASUREMENT_TYPE_VALUE] = len(header_indices)
            if measurement_intent.size_of_strains() > 0 and ip_constants.HEADER_STRAINS_VALUE not in header_indices:
                header_indices[ip_constants.HEADER_STRAINS_VALUE] = len(header_indices)
            if measurement_intent.size_of_temperatures() > 0 and ip_constants.HEADER_TEMPERATURE_VALUE not in header_indices:
                header_indices[ip_constants.HEADER_TEMPERATURE_VALUE] = len(header_indices)
            if measurement_intent.size_of_timepoints() > 0 and ip_constants.HEADER_TIMEPOINT_VALUE not in header_indices:
                header_indices[ip_constants.HEADER_TIMEPOINT_VALUE] = len(header_indices)
            if not measurement_intent.contents_is_empty():
                for content_intent in measurement_intent.get_contents().get_contents():
                    if content_intent.size_of_reagents() > 0:
                        for reagent in content_intent.get_reagents():
                            reagent_name = reagent.get_reagent_name().get_name()
                            if reagent_name not in header_indices:
                                header_indices[reagent_name] = len(header_indices)
                    elif content_intent.size_of_medias() > 0:
                        for media in content_intent.get_medias():
                            media_name = media.get_media_name().get_name()
                            if media_name not in header_indices:
                                header_indices[media_name] = len(header_indices)
        return header_indices

    def create_experiment_specification_table(self, document_id, experiment_specification_table, location=None):
        if location is None:
            location = self.doc_accessor.create_end_of_segment_location()
        num_of_rows = experiment_specification_table.num_of_rows()
        num_of_cols = experiment_specification_table.num_of_columns()
        self.doc_accessor.create_table(document_id,
                                       num_of_rows,
                                       num_of_cols,
                                       additional_properties=location)
        lab_experiment = LabExperiment(document_id)
        lab_experiment.load_from_google_doc()
        table_template = lab_experiment.tables()[-1]
        ip_table_template = self.ip_table_factory.from_google_doc(table_template)

        cells_to_update = []
        experiment_ids = [x for x in experiment_specification_table.experiment_id_to_status_table().keys()]
        table_references = [x for x in experiment_specification_table.experiment_id_to_status_table().values()]

        for row_index in reversed(range(2, num_of_rows)):
            cells_to_update.append(self.update_cell_text(ip_table_template,
                                                         'Table %d' % table_references.pop(),
                                                         row_index, 1))
            cells_to_update.append(self.update_cell_text(ip_table_template,
                                                         experiment_ids.pop(),
                                                         row_index, 0))

        cells_to_update.extend(self._write_experiment_specification_header_row(ip_table_template))
        cells_to_update.extend(self._write_experiment_specification_table_caption(ip_table_template,
                                                                           experiment_specification_table.get_table_caption()))
        response = self.doc_accessor.execute_batch_request(cells_to_update, document_id)

    def _write_experiment_specification_header_row(self, ip_table_template):
        return [self.update_cell_text(ip_table_template, 'Experiment Status', 1, 1),
                self.update_cell_text(ip_table_template, 'Experiment ID', 1, 0)]

    def _write_experiment_specification_table_caption(self, ip_table_template, table_index):
        caption_row = self.update_cell_text(ip_table_template, 'Table %d: Experiment Specification' % table_index, 0, 0)
        merge_caption_cell = self.doc_accessor.merge_table_cells(1, 2, ip_table_template.get_table_start_index(), 0, 0)
        return [merge_caption_cell, caption_row]

    def update_experiment_specification_table(self, document_id, experiment_specification_table, new_spec_table):
        intent_parser_table = experiment_specification_table.get_intent_parser_table()
        delete_content = self.doc_accessor.delete_content(intent_parser_table.get_table_start_index(),
                                                          intent_parser_table.get_table_end_index())
        self.doc_accessor.execute_batch_request([delete_content], document_id)
        new_spec_table.set_table_caption(experiment_specification_table.get_table_caption())
        return self.create_experiment_specification_table(document_id, new_spec_table)

    def update_experiment_status_table(self, document_id, experiment_status_table, db_statuses_table):
        intent_parser_table = experiment_status_table.get_intent_parser_table()
        delete_content = self.doc_accessor.delete_content(intent_parser_table.get_table_start_index(),
                                                          intent_parser_table.get_table_end_index())
        self.doc_accessor.execute_batch_request([delete_content], document_id)
        db_statuses_table.set_table_caption(experiment_status_table.get_table_caption())
        return self.create_experiment_status_table(document_id, db_statuses_table)

    def create_experiment_status_table(self, document_id, experiment_status_table, location=None):
        if location is None:
            location = self.doc_accessor.create_end_of_segment_location()
        num_of_rows = experiment_status_table.num_of_rows()
        num_of_cols = experiment_status_table.num_of_columns()

        self.doc_accessor.create_table(document_id,
                                       num_of_rows,
                                       num_of_cols,
                                       additional_properties=location)

        lab_experiment = LabExperiment(document_id)
        lab_experiment.load_from_google_doc()
        table_template = lab_experiment.tables()[-1]
        ip_table_template = self.ip_table_factory.from_google_doc(table_template)

        cells_to_update = []
        list_of_status = experiment_status_table.get_statuses()

        status_index = 7
        for row_index in reversed(range(2, num_of_rows)):
            status = list_of_status[status_index]

            # Processed column
            cells_to_update.append(self.update_cell_text(ip_table_template, status.get_state(), row_index, 3))
            # Pipeline output column
            cells_to_update.append(self.update_cell_text(ip_table_template, status.get_path(), row_index, 2))
            # Last update column
            cells_to_update.append(self.update_cell_text(ip_table_template, status.get_last_updated(), row_index, 1))
            # Type column
            cells_to_update.append(self.update_cell_text(ip_table_template, status.get_status_type(), row_index, 0))
            status_index = status_index - 1

        cells_to_update.extend(self._write_experiment_status_header_row(ip_table_template))
        cells_to_update.extend(self._write_experiment_status_table_caption(ip_table_template,
                                                                           experiment_status_table.get_table_caption()))
        response = self.doc_accessor.execute_batch_request(cells_to_update, document_id)


    def _write_experiment_status_header_row(self, ip_table_template):
        return [self.update_cell_text(ip_table_template, 'Processed', 1, 3),
                self.update_cell_text(ip_table_template, 'Output From Pipeline', 1, 2),
                self.update_cell_text(ip_table_template, 'Last Update', 1, 1),
                self.update_cell_text(ip_table_template, 'Pipeline Status', 1, 0)]

    def _write_experiment_status_table_caption(self, ip_table_template, table_index):
        caption_row = self.update_cell_text(ip_table_template, 'Table %d: Experiment status' % table_index, 0, 0)
        merge_caption_cell = self.doc_accessor.merge_table_cells(1, 4, ip_table_template.get_table_start_index(), 0, 0)
        return [merge_caption_cell, caption_row]


    def update_cell_text(self, ip_table_template, text, row_index, col_index):
        template_cell = ip_table_template.get_cell(row_index, col_index)
        start_pos = template_cell.get_start_index()
        end_pos = template_cell.get_end_index()
        new_text = self.doc_accessor.insert_text(text, start_pos, end_pos)
        return new_text

    def delete_tables(self, ip_tables, document_id):
        order_to_delete = []
        sort_table_start_indices = [ip_table.get_table_start_index() for ip_table in ip_tables]
        sort_table_start_indices.sort()
        sort_table_start_indices.reverse()
        for table_start_index in sort_table_start_indices:
            for ip_table_index in range(len(ip_tables)):
                ip_table = ip_tables[ip_table_index]
                if ip_table.get_table_start_index() == table_start_index:
                    delete_cell_content = self.doc_accessor.delete_content(ip_table.get_table_start_index(),
                                                                           ip_table.get_table_end_index())
                    order_to_delete.append(delete_cell_content)
                    ip_tables.pop(ip_table_index)
                    break

        self.doc_accessor.execute_batch_request(order_to_delete, document_id)
