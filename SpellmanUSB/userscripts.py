def clear_setpoints():
    change_setpoint('Filament Limit',0)
    change_setpoint('Filament Preheat',0)
    change_setpoint('kV Setpoint',0)
    change_setpoint('mA Output Setpoint',0)

def initialize_setpoints():
    change_setpoint('Filament Limit',3.1)
    change_setpoint('Filament Preheat',1.5)
    change_setpoint('kV Setpoint',25)
    change_setpoint('mA Output Setpoint',1)

def maximum_power():
    change_setpoint('Filament Limit',3.12)
    change_setpoint('kV Setpoint',25)
    change_setpoint('mA Output Setpoint',2)