# apiscope/models.py
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

@dataclass
class Parameter:
    name: str
    location: str  # "query", "path", "header", "cookie"
    required: bool
    schema: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

@dataclass
class Response:
    status_code: str
    description: str
    content_type: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None

@dataclass
class Endpoint:
    path: str
    method: HTTPMethod
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Parameter] = None
    request_body: Optional[Dict[str, Any]] = None
    responses: List[Response] = None
    tags: List[str] = None
    security: Optional[List[Dict[str, List[str]]]] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.responses is None:
            self.responses = []
        if self.tags is None:
            self.tags = []

@dataclass
class APISpec:
    name: str  # Configuration name from apiscope.ini
    source: str  # URL or file path
    title: str
    version: str
    description: Optional[str] = None
    contact: Optional[Dict[str, str]] = None
    license: Optional[Dict[str, str]] = None
    servers: List[Dict[str, Any]] = None
    endpoints: List[Endpoint] = None
    security_schemes: Optional[Dict[str, Dict[str, Any]]] = None

    def __post_init__(self):
        if self.servers is None:
            self.servers = []
        if self.endpoints is None:
            self.endpoints = []
