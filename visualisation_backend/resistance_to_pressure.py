class ResistanceToPressure:
    def __init__(self, sensor_design_backend):
        self.sensor_design_backend = sensor_design_backend

    def calculate_resistance_to_pressure(self, pressure):
        # Get the sensor design parameters
        sensor_params = self.sensor_design_backend.get_sensor_design_parameters()

        # Calculate resistance based on the sensor design parameters and pressure
        # This is a placeholder for the actual calculation logic
        resistance = sensor_params['base_resistance'] + (sensor_params['sensitivity'] * pressure)

        return resistance