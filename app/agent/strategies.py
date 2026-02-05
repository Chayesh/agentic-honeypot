from enum import Enum

class Strategy(str, Enum):
    TRUST_BUILDING = "trust_building"
    VERIFICATION_TRAP = "verification_trap"
    EXTRACTION = "extraction"
    SLOW_PLAY = "slow_play"
