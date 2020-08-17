from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.lab_experiment import LabExperiment
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory

class TableCreator(object):

    def __init__(self):
        self.doc_accessor = GoogleAccessor().get_google_doc_accessor()
        self.ip_table_factory = IntentParserTableFactory()

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


    def delete_content(self, document_id, start_index, end_index):
        delete_cell_content = self.doc_accessor.delete_content(start_index, end_index)
        self.doc_accessor.execute_batch_request([delete_cell_content], document_id)

    def delete_table_row(self, row_index, table_start_index, document_id):
        response = self.doc_accessor.delete_table_row(row_index, 0, table_start_index, document_id)

    def insert_table_row(self, row_index, table_start_index, document_id):
        lab_experiment = LabExperiment(document_id)
        document = lab_experiment.load_from_google_doc()
        doc_table = lab_experiment.tables()[-1]
        ip_table = self.ip_table_factory.from_google_doc(doc_table)
        table_start_index = ip_table.get_table_start_index()
        response = self.doc_accessor.insert_table_row(row_index, 0, table_start_index, document_id)

    def delete_table(self, document_id, table_start_index, table_end_index):
        delete_cell_content = self.doc_accessor.delete_content(table_start_index, table_end_index)
        self.doc_accessor.execute_batch_request([delete_cell_content], document_id)


