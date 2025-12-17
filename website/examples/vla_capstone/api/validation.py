from pydantic import BaseModel, ValidationError
from typing import Any, Dict
import yaml
import json
from pathlib import Path


class OpenAPIValidator:
    """
    Validates requests and responses against the OpenAPI specification.
    """
    
    def __init__(self, spec_path: str = None):
        """
        Initialize the validator with an OpenAPI specification.
        
        :param spec_path: Path to the OpenAPI specification file
        """
        if spec_path is None:
            spec_path = Path(__file__).parent.parent / "contracts" / "vla-api.yaml"
        
        with open(spec_path, 'r') as f:
            self.spec = yaml.safe_load(f)
        
        # Extract schema definitions
        self.definitions = self.spec.get('components', {}).get('schemas', {})
    
    def validate_request(self, path: str, method: str, data: Dict[str, Any]) -> bool:
        """
        Validate a request against the OpenAPI specification.
        
        :param path: The API path
        :param method: The HTTP method (get, post, etc.)
        :param data: The request data to validate
        :return: True if valid, False otherwise
        """
        path_obj = self.spec.get('paths', {}).get(path, {})
        method_obj = path_obj.get(method.lower(), {})
        
        if not method_obj:
            raise ValueError(f"Path {path} with method {method} not defined in OpenAPI spec")
        
        # Extract request body schema if it exists
        request_body = method_obj.get('requestBody', {})
        content = request_body.get('content', {})
        
        # Check different content types for request body schema
        for content_type, content_spec in content.items():
            schema_ref = content_spec.get('schema', {}).get('$ref')
            if schema_ref:
                schema_name = schema_ref.split('/')[-1]  # Extract name from '#/components/schemas/SchemaName'
                schema = self.definitions.get(schema_name)
                if schema:
                    return self._validate_data_against_schema(data, schema)
        
        # If no specific validation found, assume valid
        return True
    
    def validate_response(self, path: str, method: str, data: Dict[str, Any]) -> bool:
        """
        Validate a response against the OpenAPI specification.
        
        :param path: The API path
        :param method: The HTTP method (get, post, etc.)
        :param data: The response data to validate
        :return: True if valid, False otherwise
        """
        path_obj = self.spec.get('paths', {}).get(path, {})
        method_obj = path_obj.get(method.lower(), {})
        
        if not method_obj:
            raise ValueError(f"Path {path} with method {method} not defined in OpenAPI spec")
        
        # Check response schemas
        responses = method_obj.get('responses', {})
        for status_code, response_spec in responses.items():
            content = response_spec.get('content', {})
            
            # Check different content types for response schema
            for content_type, content_spec in content.items():
                schema_ref = content_spec.get('schema', {}).get('$ref')
                if schema_ref:
                    schema_name = schema_ref.split('/')[-1]  # Extract name from '#/components/schemas/SchemaName'
                    schema = self.definitions.get(schema_name)
                    if schema:
                        return self._validate_data_against_schema(data, schema)
        
        # If no specific validation found, assume valid
        return True
    
    def _validate_data_against_schema(self, data: Any, schema: Dict[str, Any]) -> bool:
        """
        Validate data against a specific schema definition.
        This is a simplified implementation - in practice, you'd use a more robust validation library.
        """
        # This is a basic schema validation - in practice, you might use a library like prance or openapi-spec-validator
        schema_type = schema.get('type')
        
        if schema_type == 'object':
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            if not isinstance(data, dict):
                return False
            
            # Check required fields
            for req_field in required:
                if req_field not in data:
                    return False
            
            # Validate each property
            for field, field_schema in properties.items():
                if field in data:
                    if not self._validate_property(data[field], field_schema):
                        return False
        
        elif schema_type == 'array':
            items_schema = schema.get('items', {})
            if not isinstance(data, list):
                return False
            
            for item in data:
                if not self._validate_data_against_schema(item, items_schema):
                    return False
        
        return True
    
    def _validate_property(self, value: Any, schema: Dict[str, Any]) -> bool:
        """
        Validate an individual property against its schema.
        """
        schema_type = schema.get('type')
        
        if schema_type == 'string':
            return isinstance(value, str)
        elif schema_type == 'number' or schema_type == 'integer':
            return isinstance(value, (int, float))
        elif schema_type == 'boolean':
            return isinstance(value, bool)
        elif schema_type == 'object':
            if not isinstance(value, dict):
                return False
            return self._validate_data_against_schema(value, schema)
        elif schema_type == 'array':
            if not isinstance(value, list):
                return False
            items_schema = schema.get('items', {})
            for item in value:
                if not self._validate_data_against_schema(item, items_schema):
                    return False
            return True
        
        # If no type specified, consider valid
        return True


# Example usage:
if __name__ == "__main__":
    validator = OpenAPIValidator()
    
    # Example VoiceCommandResponse validation
    response_data = {
        "voice_command_id": "test-123",
        "transcribed_text": "Move forward 2 meters",
        "intent": "navigation",
        "parameters": {"distance": 2.0, "unit": "meters"},
        "action_sequence": {
            "id": "seq-123",
            "steps": [
                {
                    "id": "step-1",
                    "action_type": "navigation",
                    "parameters": {"x": 2.0, "y": 0.0, "theta": 0.0},
                    "timeout": 10,
                    "order": 0
                }
            ],
            "description": "Move robot forward by 2 meters",
            "status": "pending"
        },
        "processing_time": 1.2
    }
    
    is_valid = validator.validate_response("/voice/commands", "post", response_data)
    print(f"Response validation result: {is_valid}")