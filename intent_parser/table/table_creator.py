from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.lab_experiment import LabExperiment
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory

class TableCreator(object):

    def __init__(self):
        self.doc_accessor = GoogleAccessor().get_google_doc_accessor()
        self.ip_table_factory = IntentParserTableFactory()

    def create_experiment_status_table(self, document_id, ip_table=None):
        location_end_of_document = self.doc_accessor.create_end_of_segment_location()
        num_of_rows = 10
        num_of_cols = 4
        self.doc_accessor.create_table(document_id,
                                       num_of_rows,
                                       num_of_cols,
                                       additional_properties=location_end_of_document)

        lab_experiment = LabExperiment(document_id)
        lab_experiment.load_from_google_doc()
        table_template = lab_experiment.tables()[-1]
        ip_table_template = self.ip_table_factory.from_google_doc(table_template)

        cells_to_update = []
        value = 10
        for row_index in reversed(range(num_of_rows)):
            for col_index in reversed(range(num_of_cols)):
                template_cell = ip_table_template.get_cell(row_index, col_index)
                start_pos = template_cell.get_start_index()
                end_pos = template_cell.get_end_index()
                text = str(value)
                new_text = self.doc_accessor.insert_text(text, start_pos, end_pos)
                cells_to_update.append(new_text)
                value = value + 1

        response = self.doc_accessor.execute_batch_request(cells_to_update, document_id)

    def update_experiment_status_table(self, document_id, ip_table=None, statuses=None):
        lab_experiment = LabExperiment(document_id)
        lab_experiment.load_from_google_doc()
        table_template = lab_experiment.tables()[-1]
        ip_table_template = self.ip_table_factory.from_google_doc(table_template)
        cells_to_update = []
        value = 10
        for row_index in reversed(range(1)):
            current_row = ip_table_template.get_row(row_index)
            delete_cell_content = self.doc_accessor.delete_table_row(row_index, 0, document_id)
            for col_index in reversed(range(1)):
                cell = ip_table_template.get_cell(row_index, col_index)
                start_pos = cell.get_start_index()
                end_pos = cell.get_end_index()
                text ='new value %d' % value
                new_text = self.doc_accessor.insert_text(text, start_pos, end_pos)
                cells_to_update.append(delete_cell_content)
                cells_to_update.append(new_text)

        self.doc_accessor.execute_batch_request(cells_to_update, document_id)

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


