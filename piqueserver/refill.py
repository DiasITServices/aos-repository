"""
Auto-refill script: Refills blocks, grenades and ammo when blocks <= threshold.
Keeps player HP unchanged.

Author: @SouDanielDias
Version: v1.0.0

Please add this section to Your config.toml piqueserver file

# refill script section
[refill]
# enable/disable auto-refill script
enabled = true
# Minimum number of blocks to trigger the recharge event (default: 25)
threshold = 25

"""

from piqueserver.config import config
from pyspades import contained as loaders

# Auto-refill configuration
auto_refill_config = config.section("auto_refill")
auto_refill_enabled_option = auto_refill_config.option("enabled", default=True)
auto_refill_threshold_option = auto_refill_config.option("threshold", default=25)

def apply_script(protocol, connection, config):
    """
    Adds auto-refill when blocks <= threshold.
    """
    class AutoRefillConnection(connection):
        def refill_partial(self, local: bool = False):
            """
            Partial refill: blocks, grenades and ammo only. Keeps HP.
            """
            if self.hp is None or self.hp <= 0:
                return
            
            current_hp = self.hp
            
            connection.refill(self, local)
            
            self.hp = current_hp
            
            if not local and current_hp != 100:
                set_hp = loaders.SetHP()
                set_hp.hp = self.hp
                set_hp.not_fall = 1
                set_hp.source_x = 0
                set_hp.source_y = 0
                set_hp.source_z = 0
                self.send_contained(set_hp)
        
        def on_block_build(self, x: int, y: int, z: int) -> None:
            """Called when a block is built"""
            connection.on_block_build(self, x, y, z)
            
            if auto_refill_enabled_option.get():
                threshold = auto_refill_threshold_option.get()

                if self.blocks is not None and self.blocks <= threshold and self.hp is not None and self.hp > 0:
                    self.refill_partial()
        
        def on_line_build(self, points) -> None:
            """Called when a line of blocks is built"""
            connection.on_line_build(self, points)

            if auto_refill_enabled_option.get():
                threshold = auto_refill_threshold_option.get()

                if self.blocks is not None and self.blocks <= threshold and self.hp is not None and self.hp > 0:
                    self.refill_partial()
    
    return protocol, AutoRefillConnection
