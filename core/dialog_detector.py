"""
Dialog Detector - Detecta cajas de texto y spam A automático
"""

class DialogDetector:
    def __init__(self):
        self.dialog_counter = 0
        self.last_check = False
        
    def is_in_dialog(self, emu):
        """
        Detecta si hay un diálogo activo
        
        Pokémon Red muestra diálogos en 0xC4A5 (0 = no dialog, 1+ = dialog activo)
        """
        dialog_flag = emu.memory[0xC4A5]
        text_box_flag = emu.memory[0xC4A4]
        joypad_disabled = emu.memory[0xC4A3]
        
        # Si alguna flag está activa, hay diálogo
        in_dialog = (dialog_flag > 0 or text_box_flag > 0) and joypad_disabled > 0
        
        if in_dialog:
            self.dialog_counter += 1
            self.last_check = True
        else:
            if self.last_check and self.dialog_counter < 3:
                self.dialog_counter = 0
            self.last_check = False
        
        return in_dialog
    
    def should_auto_advance(self):
        """
        Decide si debe hacer spam A automático
        
        Returns:
            True si detectó diálogo por 3+ frames consecutivos
        """
        return self.dialog_counter >= 3