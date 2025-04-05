# [API Name] API Documentation

*Version: 1.0.0*  
*Last Updated: [Date]*  
*Document Owner: [Name]*  
*Access Level: [Public/Internal/Restricted]*

## Overview

[Brief description of the API's purpose and capabilities]

## Authentication

[Authentication method and requirements]

### Authentication Headers

```http
Authorization: Bearer <token>
X-API-Key: <api_key>
```

## Base URL

```
https://api.guardsandrobers.com/v1
```

## Rate Limiting

- Requests per minute: [number]
- Burst capacity: [number]
- Rate limit headers:
  - `X-RateLimit-Limit`: Maximum requests per minute
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time until limit reset

## Endpoints

### [Endpoint Name]

**Description**: [Brief description of the endpoint's purpose]

**URL**: `[HTTP Method] /path/to/endpoint`

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| param1 | string | Yes | Description of param1 |
| param2 | integer | No | Description of param2 |

**Request Example**:

```http
GET /path/to/endpoint?param1=value1&param2=value2
Authorization: Bearer <token>
```

**Response Example**:

```json
{
  "status": "success",
  "data": {
    "field1": "value1",
    "field2": "value2"
  }
}
```

**Error Responses**:

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

## Data Models

### [Model Name]

```json
{
  "field1": "string",
  "field2": "integer",
  "field3": {
    "nestedField1": "string",
    "nestedField2": "boolean"
  }
}
```

## Best Practices

1. [Best practice 1]
2. [Best practice 2]
3. [Best practice 3]

## Examples

### [Example Use Case]

[Description of example use case]

```python
# Example code
import requests

headers = {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://api.guardsandrobers.com/v1/endpoint',
    headers=headers
)

print(response.json())
```

## Related Documents

- [Related Document 1](link)
- [Related Document 2](link)

## Change Log

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | [Date] | [Name] | Initial version |

## Review History

| Date | Reviewer | Comments | Status |
|------|----------|----------|--------|
| [Date] | [Name] | [Comments] | Approved/Rejected |

## Contact

For API-related questions or support:
- API Owner: [Name]
- Email: [email@example.com]
- Support: [support@example.com] 