class Measurement(object):

    def __init__(self):
        self.intent = {}
        self._file_type = None
        self._measurement_type = None
        self._batches = []
        self._column_ids = []
        self._controls = []
        self._dna_reaction_concentrations = []
        self._lab_ids = []
        self._num_neg_controls = []
        self._optical_densities = []
        self._reagents_or_medias = []
        self._replicates = []
        self._row_ids = []
        self._rna_inhibitor_reaction_flags = []
        self._strains = []
        self._temperatures = []
        self._template_dna_values = []
        self._timepoints = []

    def add_batches(self, batch):
        self._batches.append(batch)

    def add_column_id(self, col_id):
        self._column_ids.append(col_id)

    def add_control(self, control):
        self._controls.append(control)

    def add_dna_reaction_concentration(self, dna_reaction_concentration):
        self._dna_reaction_concentrations.append(dna_reaction_concentration)

    def add_field(self, field, value):
        self.intent[field] = value

    def add_lab_id(self, lab_id):
        self._lab_ids.append(lab_id)

    def add_num_neg_controls(self, neg_control):
        self._num_neg_controls.append(neg_control)

    def add_optical_density(self, ods):
        self._optical_densities.append(ods)

    def add_reagent_or_media(self, obj):
        self._reagents_or_medias.append(obj)

    def add_replicates(self, replicate):
        self._replicates.append(replicate)

    def add_rna_inhibitor_reaction_flag(self, boolean_value):
        self._rna_inhibitor_reaction_flags.append(boolean_value)

    def add_row_id(self, row_id):
        self._row_ids.append(row_id)

    def add_strains(self, strain):
        self._strains.append(strain)

    def add_temperature(self, temperature):
        self._temperatures.append(temperature)

    def add_template_dna_value(self, value):
        self._template_dna_values.append(value)

    def add_timepoint(self, timepoint):
        self._timepoints.append(timepoint)

    def get_column_ids(self):
        return self._column_ids

    def get_dna_reaction_concentrations(self):
        return self._dna_reaction_concentrations

    def get_file_type(self):
        return self._file_type

    def get_lab_ids(self):
        return self._lab_ids

    def get_measurement_type(self):
        return self._measurement_type

    def get_num_neg_controls(self):
        return self._num_neg_controls

    def get_optical_densities(self):
        return self._optical_densities

    def get_reagents_or_medias(self):
        return self._reagents_or_medias

    def get_replicates(self):
        return self._replicates

    def get_rna_inhibitor_reaction_flags(self):
        return self._rna_inhibitor_reaction_flags

    def get_row_ids(self):
        return self._row_ids

    def get_strains(self):
        return self._strains

    def get_temperatures(self):
        return self._temperatures

    def get_template_dna_values(self):
        return self._template_dna_values

    def get_timepoints(self):
        return self._timepoints

    def set_file_type(self, file_type):
        self._file_type = file_type

    def set_measurement_type(self, measurement_type):
        self._measurement_type = measurement_type



    def to_structured_request(self):
        return self.intent
