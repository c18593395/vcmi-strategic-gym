"""VCMI Protocol Client — 外挂 AI 架构 (T13)"""
from .serialization import BinarySerializer, BinaryDeserializer
from .types import PlayerColor, ObjectInstanceID, QueryID, BattleID, BattleSide, EActionType, int3
from .packs import (
    CPackForServer, EndTurn, MoveHero, QueryReply, RecruitCreatures,
    BuildStructure, MakeAction,
    CPackForClient, NewTurn, PackageApplied, TryMoveHero, PlayerStartsTurn,
    BattleStart, BattleResult,
)
from .connection import VCMITCPConnection
from .protocol import VCMIProtocolClient, QueryManager

__all__ = [
    'BinarySerializer', 'BinaryDeserializer',
    'PlayerColor', 'ObjectInstanceID', 'QueryID', 'BattleID',
    'BattleSide', 'EActionType', 'int3',
    'CPackForServer', 'EndTurn', 'MoveHero', 'QueryReply',
    'RecruitCreatures', 'BuildStructure', 'MakeAction',
    'CPackForClient', 'NewTurn', 'PackageApplied', 'TryMoveHero',
    'PlayerStartsTurn', 'BattleStart', 'BattleResult',
    'VCMITCPConnection', 'VCMIProtocolClient', 'QueryManager',
]
