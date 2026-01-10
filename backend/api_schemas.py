# Dictionary defining available API schemas
API_SCHEMAS = {
    "custom": {
        "name": "Custom Request",
        "description": "Manual HTTP request configuration",
        "url": "",
        "method": "GET",
        "inputs": {
            "url": {"type": "string", "default": "https://httpbin.org/get"},
            "params": {"type": "json", "default": {}},
            "headers": {"type": "json", "default": {}},
            "body": {"type": "json", "default": {}}
        },
        "outputs": {
            "response_json": {"type": "json"},
            "status_code": {"type": "int"}
        }
    },
    "cat_fact": {
        "name": "Cat Fact",
        "description": "Get a random cat fact",
        "url": "https://catfact.ninja/fact",
        "method": "GET",
        "inputs": {},
        "outputs": {
            "fact": {"type": "string"},
            "length": {"type": "int"}
        }
    },
    "agify": {
        "name": "Agify",
        "description": "Predict age based on name",
        "url": "https://api.agify.io",
        "method": "GET",
        "inputs": {
            "name": {"type": "string", "default": "michael"}
        },
        "outputs": {
            "age": {"type": "int"},
            "count": {"type": "int"}
        }
    }
}
