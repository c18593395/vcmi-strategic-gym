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
from .auth import (
    SharedKeyManager, AuthToken, TokenIssuer, TokenVerifier,
)
from .remote_connection import (
    RemoteVCMITCPConnection, RemoteConnConfig,
    RemoteConnectionError, AuthFailedError,
)
from .deployment import (
    DeploymentConfig, NodeConfig, DeploymentManager,
    ProcessManager, StatusFileWriter, KeyDistributor,
)

__all__ = [
    'BinarySerializer', 'BinaryDeserializer',
    'PlayerColor', 'ObjectInstanceID', 'QueryID', 'BattleID',
    'BattleSide', 'EActionType', 'int3',
    'CPackForServer', 'EndTurn', 'MoveHero', 'QueryReply',
    'RecruitCreatures', 'BuildStructure', 'MakeAction',
    'CPackForClient', 'NewTurn', 'PackageApplied', 'TryMoveHero',
    'PlayerStartsTurn', 'BattleStart', 'BattleResult',
    'VCMITCPConnection', 'VCMIProtocolClient', 'QueryManager',
    # P8-D 跨机器
    'SharedKeyManager', 'AuthToken', 'TokenIssuer', 'TokenVerifier',
    'RemoteVCMITCPConnection', 'RemoteConnConfig',
    'RemoteConnectionError', 'AuthFailedError',
    'DeploymentConfig', 'NodeConfig', 'DeploymentManager',
    'ProcessManager', 'StatusFileWriter', 'KeyDistributor',
]
